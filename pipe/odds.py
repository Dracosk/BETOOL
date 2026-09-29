import boto3
import pipe.odd_scrapper as od
import time
import random
import pandas as pd
import utils.s3_tool as s3
import awswrangler as wr
import rapidfuzz as rf
import hashlib

def team_id(team_name):
    """ Get the team ID for a given team name. """
    if pd.isnull(team_name):
        return None

    match = rf.process.extractOne(team_name, list(query_dict.keys()), score_cutoff=85)
    if match:
        cleaned_name = match[0]
    
        return query_dict[cleaned_name]
    return None

leagues = {
    'Premier League':'https://www.betanosports.com/sport/futbol/inglaterra/premier-league/1/?bt=matchresult',
   'LaLiga':'https://www.betanosports.com/sport/futbol/espana/laliga/5/?bt=matchresult',
    'Serie A':'https://www.betanosports.com/sport/futbol/italia/serie-a/1635/?bt=matchresult',
    'Bundesliga':'https://www.betanosports.com/sport/futbol/alemania/bundesliga/216/?bt=matchresult',
    'Ligue 1':'https://www.betanosports.com/sport/futbol/francia/ligue-1/215/?bt=matchresult'
}
session = boto3.Session(region_name='us-east-2')
query = wr.athena.read_sql_query("SELECT * FROM db_betool.dim_teams", database="db_betool", ctas_approach=False, s3_output='s3://betool-dl/query_results/', boto3_session=session)
query['clean_team_name'] = query['team_name']
query_dict = dict(zip(query['clean_team_name'], query['team_id'].astype('int16')))
to_name = dict(zip(query['team_id'].astype('int16'), query['clean_team_name']))

tp = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
for league_name, league_url in leagues.items():
    try:
        df = od.main(league_url)
        df['Home_id'] = df['Home'].apply(team_id)
        df['Away_id'] = df['Away'].apply(team_id)
        df.dropna(subset=['Home_id', 'Away_id'], inplace=True)

        df['Home_id'] = df['Home_id'].astype('Int16')
        df['Away_id'] = df['Away_id'].astype('Int16')

        hash_text = df['Home_id'].map(to_name).astype(str) + '_' + df['Away_id'].map(to_name).astype(str) + '_' + df['date'].astype(str)
        df['game_id'] = hash_text.apply(lambda x: hashlib.md5(x.encode('utf-8')).hexdigest()[:12])
        df.drop(columns= ['Home', 'Away', 'Home_id', 'Away_id'], inplace=True)
        df = df[['game_id', 'date', 'market', 'bet_name', 'odd', 'Timestamp']]

        archive_name = f'{league_name}_odds_{tp}.parquet'
        df.to_parquet(archive_name, index=False)
        s3.upload_to_s3('fact_odds', archive_name)
        time.sleep(random.uniform(3, 4))
    except Exception as e:
        print(f"Error processing league {league_name}: {e}")
