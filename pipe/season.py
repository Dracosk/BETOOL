import time
import pandas as pd
import ETL.scrapper_results as res
import random
import aws.S3 as s3

leagues = {'Premier League':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14',
           'Bundesliga':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=25&includeTopBettingOpportunity=1&topBookmaker=14',
           'Seria A':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=17&includeTopBettingOpportunity=1&topBookmaker=14',
           'Laliga':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=11&includeTopBettingOpportunity=1&topBookmaker=14',
           'Ligue 1':'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=35&includeTopBettingOpportunity=1&topBookmaker=14'}



for league_name,url in leagues.items():
    df = res.season(url)
    archive_name = f'{league_name}_results.parquet'
    df.to_parquet(archive_name, index=False)
    s3.upload_to_s3('fact_matches', archive_name)
    time.sleep(random.uniform(180, 300))


