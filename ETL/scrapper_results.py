import pandas as pd
import json
from curl_cffi import requests
import time

def json_response(page_url):
    
    response = requests.get(page_url, impersonate='chrome120', verify= False)
    if response.status_code == 200:
         to_json = response.json()
    elif response.status_code == 403:
        print(f"The scrapper has been detected {response.status_code}")
        return None
    else:
        print(f"Something went wrong {response.status_code}")
        return None
    return to_json



def url_extract(results_url):
    
    page = json_response(results_url)
    results = page['roundFilters']
    match = []
    
    for urls in results[1:]:
        if urls['isCurrent'] == False:
            desire = urls['key']
            desire_url = 'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&roundKey=' + desire
            match.append(desire_url)
    
    return match


def find_results(jornada_url):
    time.sleep(5)
    response = json_response(jornada_url)
    baul = response['games']    
    result = []
    for partidos in baul:
        jornada = partidos['roundNum']
        id = partidos['id']
        fecha = pd.to_datetime(partidos['startTime'])
        local_name = partidos['homeCompetitor']['name']
        score_local = partidos['homeCompetitor']['score']
        score_visita = partidos['awayCompetitor']['score']
        visita_name = partidos['awayCompetitor']['name']
        resultado = {
            "Jornada":jornada,
            "Game_Id": id,
            "Game_Date": fecha,
            "Local": local_name,
            "Visita": visita_name,
            "Resultado_Local": score_local,
            "Resultado_Visita": score_visita
                }
        result.append(resultado)
    return result
    
def finding_matchurl(jornada_url):
    page = json_response(jornada_url)
    cajon = page['games']
    stats_url = []

    for id in cajon:
        game_id = id['id']
        url = (f'https://webws.365scores.com/web/game/stats/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&games={game_id}')
        stats_url.append(url)

    return stats_url
                    
def stats(match_url):
    page = json_response(match_url)
    details = find_results(match_url)
    to_dict = dict(details[0])
    first_box = page['games']
    second_box = page['statistics']
    stats = []

    for ids in first_box:
        local_id = ids['homeCompetitor']['id']
        away_id = ids['awayCompetitor']['id']
    
    for statisticas in second_box:
        if statisticas['id'] == 10 and statisticas['competitorId'] == local_id:
            home_possesion = statisticas['value']
        if statisticas['id'] == 3 and statisticas['competitorId'] == local_id:
            home_total_shots = statisticas['value']
        if statisticas['id'] == 4 and statisticas['competitorId'] == local_id:
            home_total_target_shots = statisticas['value']
        if statisticas['id'] == 8 and statisticas['competitorId'] == local_id:
            home_corners = statisticas['value']
        if statisticas['id'] == 10 and statisticas['competitorId'] == away_id:
            away_possesion = statisticas['value']
        if statisticas['id'] == 3 and statisticas['competitorId'] == away_id:
            away_total_shots = statisticas['value']
        if statisticas['id'] == 4 and statisticas['competitorId'] == away_id:
            away_target_shots = statisticas['value']
        if statisticas['id'] == 8 and statisticas['competitorId'] == away_id:
            away_corners = statisticas['value']
    game = {
            "Home_Possesion":home_possesion,
            "Away_Possesion": away_possesion,
            "Home_Total_Shots":home_total_shots,
            "Away_Total_Shots":away_total_shots,
            "Home_Shots_in_Target": home_total_target_shots,
            "Away_Shots_in_Target": away_target_shots,
            "Home_Corners":home_corners,
            "Away_Corners":away_corners  
            }
    to_dict.update(game)
    stats.append(to_dict)
    return pd.DataFrame(stats)







             

#testing_results = find_results('https://webws.365scores.com/web/games/results/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&roundKey=7_131_1_1')
#print(testing_results[-1])

#testeando_otra_jornada = find_results('https://webws.365scores.com/web/games/results/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&roundKey=7_131_1_29')
#print(testeando_otra_jornada[0])

testing_url = finding_matchurl('https://webws.365scores.com/web/games/results/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&roundKey=7_131_1_29')
#print(testing_url[0])

finding = json_response('https://webws.365scores.com/web/game/stats/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&games=4452632')
#print(finding['statistics'][0])
#print(type(finding['statistics'][0]))
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', None)
estats = stats('https://webws.365scores.com/web/game/stats/?appTypeId=5&langId=14&timezoneName=America/Santiago&userCountryId=28&games=4452632')
print(estats)
proving = estats['Away_Shots_in_Target']
print(proving)