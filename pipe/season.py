import time
import pipe.scrapper_results as res
import random
import utils.s3_tool as s3
import pandas as pd

leagues = {
           'Laliga':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=11&includeTopBettingOpportunity=1&topBookmaker=14',
            'Premier League':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14',
           'Bundesliga':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=25&includeTopBettingOpportunity=1&topBookmaker=14',
           'Seria A':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=17&includeTopBettingOpportunity=1&topBookmaker=14',
           'Ligue 1':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=35&includeTopBettingOpportunity=1&topBookmaker=14'}


tp = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
for league_name,url in leagues.items():
    df = res.season(url)
    archive_name = f'{league_name}_results_{tp}.parquet'
    df.to_parquet(archive_name, index=False)
    s3.upload_to_s3('fact_matches', archive_name)
    time.sleep(random.uniform(10, 30))



