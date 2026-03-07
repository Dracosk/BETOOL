import pandas as pd
import json
from curl_cffi import requests

def result_extract(results_url):
    response = requests.get(results_url, impersonate='chrome120', verify= False)
    if response.status_code == 200:
        match = []
        to_json = response.json()
        results = to_json['roundFilters']
        for urls in results:
            desire = urls['key']
            desire_url = 'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&roundKey=' + desire
            match.append(desire_url)
    else:
        print(F"Something went wrong {response.status_code}")
    return match




testing = result_extract('https://webws.365scores.com/web/games/results/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14')
print(testing[1])
print(type(testing))

                
                
            
            
                
