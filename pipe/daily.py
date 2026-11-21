from pipe.data import tab_init, ScrapingConfig, parse_url
import pandas as pd
import asyncio
import random
from pathlib import Path
from utils.s3_tool import upload_to_s3
from pipe.cleaning import clean_results, clean_fixtures

leagues = {
    'Premier League': 'https://www.sofascore.com/es/football/tournament/england/premier-league/17',
    'La Liga': 'https://www.sofascore.com/es/football/tournament/spain/laliga/8',
    'Bundesliga': 'https://www.sofascore.com/es/football/tournament/germany/bundesliga/35',
    'Serie A': 'https://www.sofascore.com/es/football/tournament/italy/serie-a/23',
    'Ligue 1': 'https://www.sofascore.com/es/football/tournament/france/ligue-1/34',
    'Eredivisie': 'https://www.sofascore.com/es/football/tournament/netherlands/eredivisie/37',
    'Belgium Pro League': 'https://www.sofascore.com/es/football/tournament/belgium/pro-league/38',
    'Championship': 'https://www.sofascore.com/es/football/tournament/england/championship/18'
}

config = ScrapingConfig(refresh_cache=True, max_concurrent_requests=4, request_per_second=3.0)

async def main():
    run_id = pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d_%H-%M-%S_%f')
    output_dir = Path('data') / 'daily_check' / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    output_clean_dir = Path('data') / 'daily_check' / 'processed' / run_id
    output_clean_dir.mkdir(parents=True, exist_ok=False)
    failed_leagues = []

    for league_name, league_url in leagues.items():
        try:
            league_id, _ = parse_url(league_url)
            print(f'Processing {league_name}...', flush=True)

            fixtures, results, _ = await tab_init(league_url, include_stats=True, config=config)
            extracted_at = pd.Timestamp.now(tz='UTC')
            fixture_cols = ['match_id', 'home_team', 'home_id', 'away_team', 'away_id', 'start_time', 'season_id', 'league_id', 'season_name',]

            df_fixtures = pd.DataFrame(fixtures, columns=fixture_cols)
            df_results = pd.DataFrame(results)

            for frame in [df_fixtures, df_results]:
                frame['extracted_at_utc'] = extracted_at
                frame['run_id'] = run_id

            file_name = f'{league_id}_{run_id}.parquet'
            fixtures_path = output_dir / f'fixtures_{file_name}'
            matches_path = output_dir / f'results_{file_name}'
            
            df_fixtures.to_parquet(fixtures_path,engine='pyarrow', index=False)
            df_results.to_parquet(matches_path, engine='pyarrow', index=False)

            fixtures_s3_key = upload_to_s3(f'raw/sofascore/fixtures/league_id={league_id}', fixtures_path)
            if fixtures_s3_key is False:
                raise RuntimeError(f'Error uploading fixtures for league {league_name}. Skipping.')

            results_s3_key = upload_to_s3(f'raw/sofascore/results/league_id={league_id}', matches_path)
            if results_s3_key is False:
                raise RuntimeError(f'Error uploading results for league {league_name}. Skipping.')

            cleaned_fixtures = clean_fixtures(df_fixtures)
            cleaned_results = clean_results(df_results)

            clean_fixtures_path = output_clean_dir / f'cleaned_fixtures_{file_name}'
            clean_results_path = output_clean_dir / f'cleaned_results_{file_name}'

            cleaned_fixtures.to_parquet(clean_fixtures_path, engine='pyarrow', index=False)
            cleaned_results.to_parquet(clean_results_path, engine='pyarrow', index=False)

            cleaned_fixtures_s3_key = upload_to_s3(f'processed/sofascore/fixtures/league_id={league_id}', clean_fixtures_path)
            if cleaned_fixtures_s3_key is False:
                raise RuntimeError(f'Error uploading cleaned fixtures for league {league_name}. Skipping.')
            
            cleaned_results_s3_key = upload_to_s3(f'processed/sofascore/results/league_id={league_id}', clean_results_path)
            if cleaned_results_s3_key is False:
                raise RuntimeError(f'Error uploading cleaned results for league {league_name}. Skipping.')         
            
        except Exception as e:
            print(f'Error processing league {league_name}: {e}', flush=True)
            failed_leagues.append(league_name)

        await asyncio.sleep(random.uniform(10, 15))

    if failed_leagues:
        print(f'Failed leagues: {", ".join(failed_leagues)}', flush=True)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))

