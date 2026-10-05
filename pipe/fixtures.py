import random
import time
import pipe.scrapper_results as res
import utils.s3_tool as s3
import pandas as pd

leagues = {'Premier League':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=7',
            'Bundesliga':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=25',
           'Seria A':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=17',
           'Laliga':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=11',
           'Ligue 1':'https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=35'}
          

df_cols = ['Game_id', 'Home_id', 'Away_id']
tp = pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')
for league_name,url in leagues.items():
    try:
        try:
            df = res.fixtures(url)
        except Exception as e:
            if 'roundFilters' in str(e):
                df = res.pag_fixtures(url)
            else:
                raise e
        hash_data = str(pd.util.hash_pandas_object(df[df_cols], index=False).sum())
        hash_file_name = f'{league_name}_fixtures_hash.txt'
        upload_fixtures = s3.hash_get(f'latest_hash/{hash_file_name}', hash_data)
        if upload_fixtures == True:
            achieve_name = f'{league_name}_fixtures_{tp}.parquet'
            df.to_parquet(achieve_name, index=False)
            s3.upload_to_s3('fact_fixture', achieve_name)
            time.sleep(random.uniform(10, 15))
        else:
            print(f"[-]No new data for league {league_name}. Skipping.")
            time.sleep(random.uniform(10, 15))
            continue
    except Exception as e:  
        print(f"Error processing league {league_name}: {e}")
            
       

    

   