import hashlib
import unicodedata
from datetime import date
import pandas as pd
import pyarrow as pa


MATCH_COLUMNS = (
    "match_id", "league_id", "season_id", "season_name",
    "home_id", "home_team", "away_id", "away_team", "start_time",
)
ID_COLUMNS = ("match_id", "league_id", "season_id", "home_id", "away_id")
SCORE_COLUMNS = ("home_score", "away_score")
RUN_COLUMNS = ("run_id", "extracted_at_utc")
SIDES = ("home", "away")

ZERO_IF_BOTH_MISSING = (
    "penalty_saves", "red_cards", "yellow_cards", "hit_woodwork",
    "offsides", "fouled_in_final_third", "punches", "high_claims", "through_balls",
    "errors_lead_to_a_shot", "errors_lead_to_a_goal", "big_saves",
)

COUNT_STATS = (
    "total_shots", "shots_on_target", "shots_off_target", "blocked_shots",
    "shots_inside_box", "shots_outside_box", "hit_woodwork",
    "big_chances", "big_chances_scored", "big_chances_missed",
    "corner_kicks", "touches_in_penalty_area", "final_third_entries",
    "offsides", "fouled_in_final_third",
    "passes", "accurate_passes", "through_balls", "throw_ins", "dispossessed",
    "total_tackles", "interceptions", "recoveries", "clearances",
    "errors_lead_to_a_shot", "errors_lead_to_a_goal",
    "fouls", "free_kicks", "yellow_cards", "red_cards", "goal_kicks",
    "goalkeeper_saves", "big_saves", "high_claims", "punches", "penalty_saves",
)
DECIMAL_STATS = ("expected_goals", "expected_goals_on_target", "goals_prevented")
PERCENT_STATS = ("ball_possession", "duels", "tackles_won")
RATIO_STATS = (
    "long_balls", "crosses", "dribbles", "ground_duels", "aerial_duels",
    "final_third_phase",
)
RATIO_PATTERN = (
    r"^\s*(?P<numerator>\d+)\s*/\s*(?P<denominator>\d+)"
    r"(?:\s*\(\s*(?P<pct>\d+(?:\.\d+)?)\s*%\s*\))?\s*$"
)


def normalize_team_name(name: str) -> str:
    """Normalize a team name using the legacy game ID rules."""
    decomposed = unicodedata.normalize("NFD", name.lower().strip())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _make_game_id(home_team: str, away_team: str, match_date: date) -> str:
    """Hash the home team, away team and calendar date in legacy order."""
    if pd.isna(home_team) or pd.isna(away_team) or pd.isna(match_date):
        raise ValueError("Both team names and the match date are required for game_id.")

    home_name = normalize_team_name(home_team)
    away_name = normalize_team_name(away_team)
    if not home_name or not away_name:
        raise ValueError("Team names cannot be empty when generating game_id.")

    key = f"{home_name}_{away_name}_{match_date.isoformat()}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def clean_fixtures(raw: pd.DataFrame) -> pd.DataFrame:
    """Assign the game ID and keep the same calendar date as Betano."""
    if len(raw) == 0:
        clean = raw.reindex(columns=MATCH_COLUMNS).copy()
    else:
        clean = raw.loc[:, list(MATCH_COLUMNS)].copy()
    run_metadata = raw.reindex(columns=RUN_COLUMNS)

    for column in ID_COLUMNS:
        clean[column] = pd.to_numeric(clean[column], errors="raise").astype("Int64")
        if clean[column].isna().any():
            raise ValueError(f"Missing required identifier: {column}")

    kickoff = pd.to_numeric(clean["start_time"], errors="raise")
    # Betano also takes the date from the Unix timestamp without a local offset.
    clean["start_time"] = pd.to_datetime(kickoff, unit="s").dt.date.astype(
        pd.ArrowDtype(pa.date32())
    )
    for column in ("season_name", "home_team", "away_team"):
        clean[column] = clean[column].astype("string")

    game_ids = [
        _make_game_id(home, away, match_date)
        for home, away, match_date in zip(
            clean["home_team"], clean["away_team"], clean["start_time"]
        )
    ]
    clean.insert(0, "game_id", pd.array(game_ids, dtype="string"))
    clean = clean.drop(columns="match_id")

    clean["run_id"] = run_metadata["run_id"].astype("string")
    clean["extracted_at_utc"] = pd.to_datetime(
        run_metadata["extracted_at_utc"], utc=True
    ).dt.as_unit("us")
    return clean


def _parse_count(values: pd.Series) -> pd.Series:
    """Convert valid counts to nullable integers."""
    numbers = pd.to_numeric(values, errors="coerce")
    valid = numbers.ge(0) & numbers.mod(1).eq(0)
    return numbers.where(valid).astype("Int64")


def _parse_percent(values: pd.Series) -> pd.Series:
    """Parse percentages on a 0 to 100 scale, so '64%' becomes 64.0."""
    text = values.astype("string").str.strip().str.removesuffix("%").str.strip()
    numbers = pd.to_numeric(text, errors="coerce").astype("Float64")
    return numbers.where(numbers.between(0, 100))


def _parse_ratio(values: pd.Series) -> pd.DataFrame:
    """Split a value like '21/32 (66%)' and keep the reported percentage."""
    parts = values.astype("string").str.extract(RATIO_PATTERN)
    numerator = _parse_count(parts["numerator"])
    denominator = _parse_count(parts["denominator"])
    valid_counts = numerator.le(denominator)
    return pd.DataFrame(
        {
            "numerator": numerator.where(valid_counts),
            "denominator": denominator.where(valid_counts),
            "pct": _parse_percent(parts["pct"]).where(valid_counts & denominator.gt(0)),
        }
    )


def _unblocked_shots(results: pd.DataFrame, side: str) -> pd.Series:
    return results[f"shots_on_target_{side}"] + results[f"shots_off_target_{side}"]


def _event_zero_coverage(results: pd.DataFrame, stats_ok: pd.Series) -> dict[str, pd.Series]:
    """Estimate event coverage separately for each league and season in the batch."""
    season = [results["league_id"], results["season_id"]]
    dates = pd.to_datetime(results["start_time"])
    first = dates.groupby(season).transform("min")
    last = dates.groupby(season).transform("max")
    span_days = (last - first).dt.days + 1
    third = (dates - first).dt.days.mul(3).floordiv(span_days)
    enough_history = span_days.ge(28) & third.groupby(season).transform("nunique").eq(3)

    coverage = {}
    for stat in (*ZERO_IF_BOTH_MISSING, "big_chances"):
        if stat == "penalty_saves":
            continue
        columns = [f"{stat}_home", f"{stat}_away"]
        reported = stats_ok & results[columns].notna().all(axis="columns")
        reported_dates = dates.where(reported)
        dates_per_third = reported_dates.groupby([*season, third]).transform("nunique")
        coverage[stat] = enough_history & dates_per_third.ge(2).groupby(season).transform("all")

    # Penalty saves are rare. Require repeated reports and sustained keeper coverage.
    reported = stats_ok & results[["penalty_saves_home", "penalty_saves_away"]].notna().all(axis="columns")
    penalty_save_days = dates.where(reported).groupby(season).transform("nunique")
    coverage["penalty_saves"] = penalty_save_days.ge(2) & coverage["big_saves"]
    return coverage


def summarize_stat_coverage(raw: pd.DataFrame) -> pd.DataFrame:
    """Count raw reports by league, season, metric and calendar week."""
    source = raw.rename(columns={"throw-ins_home": "throw_ins_home", "throw-ins_away": "throw_ins_away"})
    groups = source[["league_id", "season_id"]].copy()
    kickoff = pd.to_datetime(source["start_time"], unit="s")
    groups["week_start"] = kickoff.dt.to_period("W-SUN").dt.start_time
    stats_ok = source["stat_status"].eq("ok").fillna(False)
    reports = []
    for stat in (*COUNT_STATS, *DECIMAL_STATS, *PERCENT_STATS, *RATIO_STATS):
        columns = [f"{stat}_home", f"{stat}_away"]
        reported = source.reindex(columns=columns).notna()
        counts = groups.assign(
            matches=1,
            stats_ok=stats_ok,
            reported_both=stats_ok & reported.all(axis="columns"),
            reported_one=stats_ok & reported.sum(axis="columns").eq(1),
        )
        counts = counts.groupby(list(groups.columns), as_index=False, dropna=False).sum()
        reports.append(counts.assign(stat=stat))
    return pd.concat(reports, ignore_index=True)


def _fill_missing_chance_zeros(
    results: pd.DataFrame,
    source: pd.DataFrame,
    stats_ok: pd.Series,
    covered: pd.Series,
    imputed: pd.Series,
) -> None:
    """Fill validated all-missing groups and zeros supported by the breakdown."""
    chance_stats = ("big_chances", "big_chances_scored", "big_chances_missed")
    chance_columns = [f"{stat}_{side}" for stat in chance_stats for side in SIDES]
    # The coverage rule applies only when the entire breakdown is absent.
    fill = (
        stats_ok
        & source[chance_columns].isna().all(axis="columns")
        & covered
    )
    results.loc[fill, chance_columns] = 0
    imputed.loc[fill] += ",".join(chance_stats) + ","

    rules = (
        ("big_chances_scored", "big_chances_missed"),
        ("big_chances_missed", "big_chances_scored"),
    )
    for missing, reported in rules:
        columns = [f"{missing}_{side}" for side in SIDES]
        fill = stats_ok & source[columns].isna().all(axis="columns")
        for side in SIDES:
            total = source[f"big_chances_{side}"].notna()
            matches_total = results[f"big_chances_{side}"].eq(results[f"{reported}_{side}"])
            fill &= total & matches_total.fillna(False)

        results.loc[fill, columns] = 0
        imputed.loc[fill] += f"{missing},"


def _fill_missing_event_zeros(results: pd.DataFrame, source: pd.DataFrame) -> pd.Series:
    """Record imputed zeros and return rows with inconsistent goal errors."""
    stats_ok = results["stat_status"].eq("ok").fillna(False)
    coverage = _event_zero_coverage(results, stats_ok)
    imputed = pd.Series("", index=results.index, dtype="string")

    for stat in (*ZERO_IF_BOTH_MISSING, "blocked_shots"):
        columns = [f"{stat}_home", f"{stat}_away"]
        missing_pair = source[columns].isna().all(axis="columns")

        if stat == "blocked_shots":
            # Both totals must be fully accounted for by shots on and off target.
            supported = pd.Series(True, index=results.index)
            for side in SIDES:
                total = results[f"total_shots_{side}"]
                supported &= total.eq(_unblocked_shots(results, side)).fillna(False)
        else:
            supported = coverage[stat]

        fill = stats_ok & missing_pair & supported
        results.loc[fill, columns] = 0
        imputed.loc[fill] += f"{stat},"

    _fill_missing_chance_zeros(results, source, stats_ok, coverage["big_chances"], imputed)

    inconsistent_goal_errors = pd.Series(False, index=results.index)
    for side, opponent in (("home", "away"), ("away", "home")):
        column = f"errors_lead_to_a_goal_{side}"
        goals_conceded = results[f"{opponent}_score"]
        inconsistent = results[column].gt(goals_conceded).fillna(False)
        inconsistent_goal_errors |= inconsistent
        results.loc[inconsistent, column] = pd.NA

        # A team cannot give away a goal if its opponent did not score.
        fill = stats_ok & source[column].isna() & results[column].isna() & goals_conceded.eq(0)
        results.loc[fill, column] = 0
        imputed.loc[fill] += f"{column},"

    results["imputed_zero_stats"] = imputed.str.removesuffix(",")
    return inconsistent_goal_errors


def _quality_status(results: pd.DataFrame) -> pd.Series:
    """Flag contradictory or incomplete chance counts and other event gaps."""
    needs_review = pd.Series(False, index=results.index)
    for side in SIDES:
        shots = results[f"total_shots_{side}"]
        shot_breakdown = _unblocked_shots(results, side) + results[f"blocked_shots_{side}"]
        shot_locations = results[f"shots_inside_box_{side}"] + results[f"shots_outside_box_{side}"]
        chances = results[f"big_chances_{side}"]
        scored_chances = results[f"big_chances_scored_{side}"]
        missed_chances = results[f"big_chances_missed_{side}"]
        chance_breakdown = scored_chances + missed_chances

        needs_review |= shots.ne(shot_breakdown).fillna(False)
        needs_review |= shots.ne(shot_locations).fillna(False)
        needs_review |= chances.ne(chance_breakdown).fillna(False)
        needs_review |= chances.isna() | scored_chances.isna() | missed_chances.isna()

    for stat in (*ZERO_IF_BOTH_MISSING, "blocked_shots"):
        needs_review |= results[f"{stat}_home"].isna() ^ results[f"{stat}_away"].isna()

    return needs_review.map({False: "ok", True: "review"}).astype("string")


def clean_results(raw: pd.DataFrame) -> pd.DataFrame:
    """Add scores and typed statistics to the match schema."""
    clean = clean_fixtures(raw)
    scores = raw.loc[:, list(SCORE_COLUMNS)] if len(raw) else raw.reindex(columns=SCORE_COLUMNS)
    for column in SCORE_COLUMNS:
        clean[column] = _parse_count(scores[column])
        if clean[column].isna().any():
            raise ValueError(f"Missing or invalid score: {column}")

    raw = raw.rename(columns={"throw-ins_home": "throw_ins_home", "throw-ins_away": "throw_ins_away"})
    # SofaScore can omit a statistic entirely for a league.
    input_columns = [
        f"{stat}_{side}"
        for stat in (*COUNT_STATS, *DECIMAL_STATS, *PERCENT_STATS, *RATIO_STATS)
        for side in SIDES
    ]
    source = raw.reindex(columns=[*input_columns, "stat_status"])
    clean["stat_status"] = source["stat_status"].astype("string")

    stats = {}
    for stat in COUNT_STATS:
        for side in SIDES:
            column = f"{stat}_{side}"
            stats[column] = _parse_count(source[column])

    for stat in DECIMAL_STATS:
        for side in SIDES:
            column = f"{stat}_{side}"
            stats[column] = pd.to_numeric(source[column], errors="coerce").astype("Float64")

    for stat in PERCENT_STATS:
        for side in SIDES:
            stats[f"{stat}_pct_{side}"] = _parse_percent(source[f"{stat}_{side}"])

    for stat in RATIO_STATS:
        for side in SIDES:
            parts = _parse_ratio(source[f"{stat}_{side}"])
            for part in ("numerator", "denominator", "pct"):
                stats[f"{stat}_{part}_{side}"] = parts[part]

    results = pd.concat([clean, pd.DataFrame(stats, index=clean.index)], axis="columns")
    inconsistent_goal_errors = _fill_missing_event_zeros(results, source)
    results["data_quality_status"] = _quality_status(results).mask(
        inconsistent_goal_errors, "review"
    )
    return results
