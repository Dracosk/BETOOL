import unicodedata
import pandas as pd


MATCH_COLUMNS = (
    "match_id", "league_id", "season_id", "season_name",
    "home_id", "home_team", "away_id", "away_team", "start_time",
)
ID_COLUMNS = ("match_id", "league_id", "season_id", "home_id", "away_id")
SCORE_COLUMNS = ("home_score", "away_score")
RUN_COLUMNS = ("run_id", "extracted_at_utc")
SIDES = ("home", "away")

COUNT_STATS = (
    "total_shots", "shots_on_target", "shots_off_target", "blocked_shots",
    "shots_inside_box", "shots_outside_box", "corner_kicks",
    "big_chances", "big_chances_scored", "big_chances_missed",
    "passes", "accurate_passes", "fouls", "offsides", "yellow_cards", "red_cards",
    "total_tackles", "interceptions", "recoveries", "clearances",
    "total_saves", "penalty_saves",
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
    """Normalize a team name for matching against Betano data."""
    normalized = unicodedata.normalize("NFD", name.lower().strip())
    without_accents = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return " ".join(without_accents.split())


def clean_fixtures(raw: pd.DataFrame) -> pd.DataFrame:
    """Preserve match identifiers and convert kickoff times to UTC."""
    if len(raw) == 0:
        clean = raw.reindex(columns=MATCH_COLUMNS).copy()
    else:
        clean = raw.loc[:, list(MATCH_COLUMNS)].copy()
    run_metadata = raw.reindex(columns=RUN_COLUMNS)

    for column in ID_COLUMNS:
        clean[column] = pd.to_numeric(clean[column], errors="raise").astype("Int64")

    clean["start_time"] = pd.to_datetime(
        pd.to_numeric(clean["start_time"], errors="raise"), unit="s", utc=True
    ).dt.as_unit("us")
    clean["season_name"] = clean["season_name"].astype("string")
    for side in SIDES:
        column = f"{side}_team"
        clean[column] = clean[column].astype("string")
        clean[f"{column}_normalized"] = (
            clean[column].map(normalize_team_name, na_action="ignore").astype("string")
        )
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


def clean_results(raw: pd.DataFrame) -> pd.DataFrame:
    """Add scores and typed statistics to the match schema."""
    clean = clean_fixtures(raw)
    scores = raw.loc[:, list(SCORE_COLUMNS)] if len(raw) else raw.reindex(columns=SCORE_COLUMNS)
    for column in SCORE_COLUMNS:
        clean[column] = pd.to_numeric(scores[column], errors="raise").astype("Int64")

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

    return pd.concat([clean, pd.DataFrame(stats, index=clean.index)], axis="columns")
