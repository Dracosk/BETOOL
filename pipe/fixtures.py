import random
import time
import pipe.scrapper_results as res
import utils.s3_tool as s3

leagues = {'Premier League':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&lastUpdateId=5718280220',
            'Bundesliga':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=25&includeTopBettingOpportunity=1&topBookmaker=14',
           'Seria A':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=17&includeTopBettingOpportunity=1&topBookmaker=14',
           'Laliga':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=11&includeTopBettingOpportunity=1&topBookmaker=14',
           'Ligue 1':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=35&includeTopBettingOpportunity=1&topBookmaker=14'}
          


for league_name,url in leagues.items():
    try:
        df = res.fixtures(url)
        achieve_name = f'{league_name}_fixtures.parquet'
        print(f"Uploading {achieve_name} to bucket")
        df.to_parquet(achieve_name, index=False)
        s3.upload_to_s3('fact_fixture', achieve_name)
        time.sleep(random.uniform(180, 300))

    except Exception as e:
        print(f"Error processing league {league_name}: {e}")
        

   