import asyncio
import random
from pathlib import Path
import pandas as pd
from pipe.cleaning import MATCH_COLUMNS, SCORE_COLUMNS, clean_fixtures, clean_results
from pipe.daily import leagues
from pipe.data import ScrapingConfig, parse_url, tab_seasons
from utils.s3_tool import upload_to_s3


config = ScrapingConfig(
    refresh_cache=False, max_concurrent_requests=10, request_per_second=3.0
)
MAX_SEASONS = 6


async def main():
    run_id = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d_%H-%M-%S_%f")
    output_dir = Path("data") / "historical_check" / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    output_clean_dir = Path("data") / "historical_check" / "processed" / run_id
    output_clean_dir.mkdir(parents=True, exist_ok=False)
    failed_leagues = []

    for league_name, league_url in leagues.items():
        try:
            league_id, _ = parse_url(league_url)
            print(f"Processing {league_name} (up to {MAX_SEASONS} seasons)...", flush=True)

            fixtures, results, _ = await tab_seasons(
                league_url, limit=MAX_SEASONS, include_stats=True, config=config
            )
            extracted_at = pd.Timestamp.now(tz="UTC")
            df_fixtures = pd.DataFrame(fixtures, columns=MATCH_COLUMNS)
            df_results = pd.DataFrame(results)
            if df_results.empty:
                df_results = pd.DataFrame(columns=[*MATCH_COLUMNS, *SCORE_COLUMNS])

            for frame in (df_fixtures, df_results):
                frame["extracted_at_utc"] = extracted_at
                frame["run_id"] = run_id

            season_ids = pd.concat(
                [df_fixtures["season_id"], df_results["season_id"]], ignore_index=True
            )
            if season_ids.empty or season_ids.isna().any():
                raise ValueError("No matches found or a match is missing its season ID.")

            for season_id in season_ids.drop_duplicates():
                season_fixtures = df_fixtures.loc[df_fixtures["season_id"].eq(season_id)]
                season_results = df_results.loc[df_results["season_id"].eq(season_id)]
                file_name = f"{league_id}_{season_id}_{run_id}.parquet"

                fixtures_path = output_dir / f"fixtures_{file_name}"
                results_path = output_dir / f"results_{file_name}"
                season_fixtures.to_parquet(fixtures_path, engine="pyarrow", index=False)
                season_results.to_parquet(results_path, engine="pyarrow", index=False)

                cleaned_fixtures = clean_fixtures(season_fixtures)
                cleaned_results = clean_results(season_results)
                clean_fixtures_path = output_clean_dir / f"cleaned_fixtures_{file_name}"
                clean_results_path = output_clean_dir / f"cleaned_results_{file_name}"
                cleaned_fixtures.to_parquet(clean_fixtures_path, engine="pyarrow", index=False)
                cleaned_results.to_parquet(clean_results_path, engine="pyarrow", index=False)

                fixtures_s3_key = upload_to_s3(f"raw/sofascore/fixtures/league_id={league_id}", fixtures_path)
                if fixtures_s3_key is False:
                    raise RuntimeError(f"Error uploading fixtures for season {season_id}.")

                results_s3_key = upload_to_s3(f"raw/sofascore/results/league_id={league_id}", results_path)
                if results_s3_key is False:
                    raise RuntimeError(f"Error uploading results for season {season_id}.")

                cleaned_fixtures_s3_key = upload_to_s3(
                    f"processed/sofascore/fixtures/league_id={league_id}", clean_fixtures_path
                )
                if cleaned_fixtures_s3_key is False:
                    raise RuntimeError(f"Error uploading cleaned fixtures for season {season_id}.")

                cleaned_results_s3_key = upload_to_s3(
                    f"processed/sofascore/results/league_id={league_id}", clean_results_path
                )
                if cleaned_results_s3_key is False:
                    raise RuntimeError(f"Error uploading cleaned results for season {season_id}.")

                print(f"  Season {season_id}: {len(season_fixtures)} fixtures, "
                    f"{len(season_results)} results.", flush=True,)

        except Exception as exc:
            print(f"Error processing league {league_name}: {exc}", flush=True)
            failed_leagues.append(league_name)

        await asyncio.sleep(random.uniform(10, 15))
        
    if failed_leagues:
        print(f"Failed leagues: {', '.join(failed_leagues)}", flush=True)
        return 1
    return 0


raise SystemExit(asyncio.run(main()))


