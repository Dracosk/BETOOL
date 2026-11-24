import boto3
import pipe.odd_scrapper as od
import time
import random
import pandas as pd
import utils.s3_tool as s3
import awswrangler as wr
import rapidfuzz as rf
from pathlib import Path
from pipe.cleaning import _make_game_id, normalize_team_name

BETANO_TEAM_IDS = {
    8: {
        '107153': 2835,  # Racing Santander
        '107463': 2825,  # Athletic Bilbao
    },
    34: {
        '106645': 1661,  # OGC Niza
    },
    35: {
        '108687': 2527,  # Borussia Monchengladbach
    },
    38: {
        '106647': 2898,  # Royal Charleroi SC
        '106396': 4859,  # KV RS Waasland Beveren
    },
}

def team_id(team_name, betano_id, names_to_ids, betano_to_sofascore):
    """Resolve a team by Betano ID, exact name or fuzzy name within its league."""
    mapped_id = betano_to_sofascore.get(betano_id)
    if mapped_id is not None:
        return mapped_id
    if pd.isnull(team_name):
        return None

    normalized_name = normalize_team_name(team_name)
    if normalized_name in names_to_ids:
        return names_to_ids[normalized_name]

    match = rf.process.extractOne(normalized_name, list(names_to_ids), score_cutoff=85)
    return names_to_ids[match[0]] if match else None

leagues = {
    'Premier League': (17, 'https://www.betanosports.com/sport/futbol/inglaterra/premier-league/1/?bt=matchresult'),
    'LaLiga': (8, 'https://www.betanosports.com/sport/futbol/espana/laliga/5/?bt=matchresult'),
    'Serie A': (23, 'https://www.betanosports.com/sport/futbol/italia/serie-a/1635/?bt=matchresult'),
    'Bundesliga': (35, 'https://www.betanosports.com/sport/futbol/alemania/bundesliga/216/?bt=matchresult'),
    'Ligue 1': (34, 'https://www.betanosports.com/sport/futbol/francia/ligue-1/215/?bt=matchresult'),
    'Eredivisie': (37, 'https://www.betanosports.com/sport/futbol/paises-bajos/eredivisie/17067/?bt=matchresult'),
    'Belgium Pro League': (38, 'https://www.betanosports.com/sport/futbol/belgica/1a-pro-league/16849/?bt=matchresult'),
    'Championship': (18, 'https://www.betanosports.com/sport/futbol/inglaterra/championship/2/?bt=matchresult'),
}

session = boto3.Session(region_name='us-east-2')
query = wr.athena.read_sql_query(
    "SELECT league_id, team_id, team_name FROM db_betool_v2.teams",
    database="db_betool_v2",
    ctas_approach=False,
    s3_output='s3://betool-dl/query_results/',
    boto3_session=session,
)
query['team_id'] = query['team_id'].astype('int64')
query['team_name'] = query['team_name'].map(normalize_team_name)
query['league_id'] = query['league_id'].astype('int64')
teams_by_league = {league_id: teams for league_id, teams in query.groupby('league_id')}

run_id = pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d_%H-%M-%S_%f')
output_dir = Path('data') / 'odds_check' / run_id
output_dir.mkdir(parents=True, exist_ok=False)

for league_name, (league_id, league_url) in leagues.items():
    try:
        league_teams = teams_by_league.get(league_id)
        if league_teams is None:
            raise ValueError(f'No teams in the catalog for league {league_id}.')

        names_to_ids = dict(zip(league_teams['team_name'], league_teams['team_id']))
        ids_to_names = dict(zip(league_teams['team_id'], league_teams['team_name']))
        betano_to_sofascore = {
            betano_id: sofascore_id
            for betano_id, sofascore_id in BETANO_TEAM_IDS.get(league_id, {}).items()
            if sofascore_id in ids_to_names
        }

        df = od.main(league_url)
        for side in ('Home', 'Away'):
            id_column = f'{side.lower()}_betano_id'
            df[id_column] = df[id_column].astype('string')
            df[f'{side}_id'] = pd.array([
                team_id(name, betano_id, names_to_ids, betano_to_sofascore)
                for name, betano_id in zip(df[side], df[id_column])
            ], dtype='Int64')

        unresolved = df['Home_id'].isna() | df['Away_id'].isna()
        if unresolved.any():
            details = df.loc[unresolved, ['Home', 'Away', 'date', 'home_betano_id', 'away_betano_id']]
            print(f'Unmatched {league_name} fixtures:\n{details.drop_duplicates().to_string(index=False)}')
        df = df.loc[~unresolved].copy()
        df['game_id'] = pd.array([
            _make_game_id(ids_to_names[home_id], ids_to_names[away_id], match_date)
            for home_id, away_id, match_date in zip(df['Home_id'], df['Away_id'], df['date'])
        ], dtype='string')
        df = df[['game_id', 'date', 'market', 'bet_name', 'odd', 'Timestamp',
                 'home_betano_id', 'away_betano_id']]

        archive_path = output_dir / f'{league_name}_odds_{run_id}.parquet'
        df.to_parquet(archive_path, engine='pyarrow', index=False)
        #s3_key = s3.upload_to_s3('processed/betano/odds', archive_path)
        #if s3_key is False:
            #raise RuntimeError(f'Error uploading odds for {league_name}.')
        time.sleep(random.uniform(3, 4))
    except Exception as e:
        print(f"Error processing league {league_name}: {e}")
