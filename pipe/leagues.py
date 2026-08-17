import random
import time
import pandas as pd
import pipe.scrapper_results as res
import utils.s3_tool as s3

leagues = {'Premier League':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&lastUpdateId=5718280220',
            'Bundesliga':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=25&includeTopBettingOpportunity=1&topBookmaker=14',
           'Seria A':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=17&includeTopBettingOpportunity=1&topBookmaker=14',
           'Laliga':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=11&includeTopBettingOpportunity=1&topBookmaker=14',
           'Ligue 1':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=35&includeTopBettingOpportunity=1&topBookmaker=14'}
          
df_list = []
tp = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
for league_name,url in leagues.items():
    try:
        df = res.league(url)
        df_list.append(df)
    except Exception as e:
        print(f"Error processing league {league_name}: {e}")

df = pd.concat(df_list, ignore_index=True)
df.to_parquet(f'top5_leagues_{tp}.parquet', index=False)
s3.upload_to_s3('dim_league', f'top5_leagues_{tp}.parquet')
