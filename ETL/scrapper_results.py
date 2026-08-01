import pandas as pd
import hashlib
from curl_cffi import requests
import time
import unicodedata
import random

def json_response(page_url, max_retries=3):
    """
    Perform a GET requests to an URL and convert the response to JSON.

    Args:
        page_url(str): Complete URL to perform a requests.
    
    Returns:
        dict: A Python dictionary containing the JSON response. Returns None if the requests fails.

    """
    for attempt in range(max_retries):
        try: 
            response = requests.get(page_url, impersonate='chrome120', verify= False)
            if response.status_code == 200:
             to_json = response.json()
             return to_json
            elif response.status_code == 403:
                print(f"The scrapper has been detected {response.status_code}")
                return None
            else:
                print(f"Something went wrong {response.status_code}")
                time.sleep(2)

        except requests.exceptions.Timeout:
            tiempo_espera = 5 * (attempt + 1) 
            print(f"Timeout. Retrying in {tiempo_espera}s (Attempt {attempt + 1}/{max_retries})")
            time.sleep(tiempo_espera)

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            time.sleep(2)
    return to_json



def url_extract(results_url):
    """
    Extract all rounds key to create a complete URL for each round.

    Args:
        results_url(str): URL from results page.
    
    Returns:
        list: A list with each round URL
    """
    
    page = json_response(results_url)
    results = page['roundFilters']
    match = []
    
    for urls in results[1:]:
        desire = urls['key']
        desire_url = 'https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&roundKey=' + desire
        match.append(desire_url)
        
    return match
    


def find_results(jornada_url):
    """
    Extracts basic information and scores for each game within a specific round.

    Args:
        jornada_url(str): URL from rounds page.
    
    Returns:
        list: A list of dictionaries, where each dictionary contains basic details of a match.
    """
    response = json_response(jornada_url)
    if response is None:
        return []
    if 'games' not in response:
        print(f"No game data found for URL: {jornada_url}")
        return []
    baul = response['games']    
    result = []
    for matches in baul:
        if matches['gameTime'] >= 90.0:
            
            round = matches['roundNum']
            local_name = strip_accents(matches['homeCompetitor']['name'].lower().strip())
            away_name = strip_accents(matches['awayCompetitor']['name'].lower().strip())
            date = pd.to_datetime(matches['startTime']).date()
            id = hashlib.md5(f"{local_name}_{away_name}_{date}".encode('utf-8')).hexdigest()[:12]
            score_local = matches['homeCompetitor']['score']
            score_away = matches['awayCompetitor']['score']
            local_id = matches['homeCompetitor']['id']
            away_id = matches['awayCompetitor']['id']
            match = {
                "Round":round,
                "Game_Id": id,
                "Game_Date": date,
                "Local_ID": local_id,
                "Away_ID": away_id,
                "Local_Score": score_local,
                "Away_Score": score_away
                        }
            result.append(match)
        else:
            print(f"Match excluded due to unfinished status: game_id {matches['id']} with game time {matches['gameTime']}")
            continue
            
    return result
            

    
def finding_matchurl(jornada_url):
    """
    Extracts the statistics URLs for all matches in a given round.

    Args:
        jornada_url(str): Complete URL from a specific round.

    Returns:
        stats_url(list): A list of matches URLs pointing to the detailed statistics of each match. 
    """
    page = json_response(jornada_url)
    if not page or 'games' not in page:
        return []
    if not page['games']:
        print(f"No games found for URL: {jornada_url}")
        return []
    cajon = page['games']
    stats_url = []

    for id in cajon:
        game_id = id['id']
        url = (f'https://webws.365scores.com/web/game/stats/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&games={game_id}')
        stats_url.append(url)

    return stats_url
                    
def stats(match_url):
    """
    Extracts essential statistics from a specific match URL providing the complete information for each match.

    Args:
        match_url(str): A URL from a match.
    
    Returns:
        stats(DataFrame): A pandas DataFrame that contains essential information and statistics from a match.
    """
    page = json_response(match_url)
    details = find_results(match_url)
    
    if not details:
        return pd.DataFrame()
    if 'games' not in page:
        print(f"No game data found for URL: {match_url}")
        return pd.DataFrame()
    
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

def main(round_url):
    """
    Orchestrates data extraction by calling key fuctions to extract statistics for each round and compiles the results into a single DataFrame.
    
    Args:
        round_url(str): URL from results page.
    
    Returns:
        DataFrame: A pandas DataFrame containing the compiled statistics for all matches across the rounds.

    """
    rounds = url_extract(round_url)
    league = []
    for matches in rounds:
        print(f"Extracting round {matches} ")
        game = finding_matchurl(matches)
        for statistics in game:
            try:
                df_details = stats(statistics)
                league.append(df_details)
            except Exception as e:
                print(f"Error in match {statistics}: {e}")
            time.sleep(2)

    df = pd.concat(league, ignore_index=True)
    return df

def teams(page_url):
    """ 
    Extracts the teams information from a league and compiles it into a DataFrame.

    Args:
        page_url(str): URL from league page.

    Returns:
        DataFrame: A pandas DataFrame containing the team IDs and names for the league.
    """
    response = json_response(page_url)
    folder = response['competitors']
    team_list = []

    for teams in folder:
        team_id = teams['id']
        team_name = teams['name']
        loader = {'team_id': team_id,
                  'team_name': team_name}
        team_list.append(loader)
    clean = tuple(team_list)
    return pd.DataFrame(clean)

def league(page_url):
    """ 
    Extracts the league information from a league page and compiles it into a DataFrame.

    Args:
        page_url(str): URL from league page.
    
    Returns:
        DataFrame: A pandas DataFrame containing the league ID and name for the league.
    """

    response = json_response(page_url)
    page = response['competitions']
    league_namer = []
    
    for league in page:
        league_id = league['id']
        league_name = league['name']
        apply = {'league_id': league_id,
                 'name': league_name}
        league_namer.append(apply)
    
    cleaner = tuple(league_namer)
    df = pd.DataFrame(cleaner)
    return df

def strip_accents(text):
    """
    Removes accents from a given string.

    Args:
        text(str): Input string potentially containing accented characters.

    Returns:
        str: The input string with all accents removed.
    """
    nfkd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')

def fixtures(fixtures_url):
    """
    Extracts the fixtures information from a league page and compiles it into a DataFrame.

    Args:
        fixtures_url(str): URL from fixtures page.

    Returns:
        DataFrame: A pandas DataFrame containing the fixtures information for the league.
    """

    response = json_response(fixtures_url)
    page = response['games']    
    fixture_list = []

    for games in page:
        round = games['roundNum']
        date = pd.to_datetime(games['startTime']).date()
        local_name = strip_accents(games['homeCompetitor']['name'].lower().strip())
        away_name = strip_accents(games['awayCompetitor']['name'].lower().strip())
        id = hashlib.md5(f"{local_name}_{away_name}_{date}".encode('utf-8')).hexdigest()[:12]
        local_id = games['homeCompetitor']['id']
        away_id = games['awayCompetitor']['id']
        fixture = {
            "Round":round,
            "Game_Id": id,
            "Game_Date": date,
            "Local_Id": local_id,
            "Away_Id": away_id
        }
        fixture_list.append(fixture)
    return pd.DataFrame(fixture_list)

def season(results_url):
    """ Extracts the season information from a results page and compiles it into a DataFrame, handling pagination to retrieve all historical matches.

    Args:
        results_url(str): URL from results page.

    Returns:
        DataFrame: A pandas DataFrame containing the season information for the league.
    """
    
    season_list = []
    game = finding_matchurl(results_url)
    for statistics in game:
        try:
            df_details = stats(statistics)
            season_list.append(df_details)
        except Exception as e:
            print(f"Error in match {statistics}: {e}")
            time.sleep(2)

    actual_url = results_url    
    while True:
        next_page_url = scroll_url(actual_url) 
        
        if not next_page_url:
            print("Se alcanzó el final de la historia de la liga.")
            break
            
    
        nuevas_urls_partidos = finding_matchurl(next_page_url)
        if not nuevas_urls_partidos:
            print("No hay más partidos en esta página.")
            break
        print(f"Extracting round {next_page_url} ")
        
        if not nuevas_urls_partidos:
            print("No hay más partidos históricos disponibles.")
            break
        
        for url_partido in nuevas_urls_partidos:
            try:
                match_stats = stats(url_partido)
                if not match_stats.empty:
                    season_list.append(match_stats)
            except Exception as e:
                print(f"Error en partido histórico {url_partido}: {e}")
        actual_url = next_page_url
        time.sleep(random.uniform(1, 2)) 
        
    df_final = pd.concat(season_list, ignore_index=True)
    df_limpio = df_final.drop_duplicates(subset=['Game_Id'], keep='first')

    return df_limpio
        


def scroll_url(results_url):
    """
    Extracts the URL for the next page of historical matches based on the last match ID from the current results page.
    
    Args:
        results_url(str): URL from results page.
    
    Returns:
        str: A URL for the next page of historical matches. Returns None if there are no more matches to extract."""

    response = json_response(results_url)
    if not response or 'games' not in response or not response['games']:
        return []
    page = response['games']
    urls = page[-1]
    game_id = urls['id']
    scroll_url = f'https://webws.365scores.com/web/games/?langId=1&timezoneId=72&userCountryId=28&apptype=5&competitions=7&games=1&aftergame={game_id}&direction=-1'
    
    return scroll_url


pd.set_option("display.max_columns", None)
pd.set_option('display.width', 1000)


#premier = season('https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=7&includeTopBettingOpportunity=1&topBookmaker=14&lastUpdateId=5708976322')
#print(premier)
#laliga_csv = premier.to_csv('PremierFullSeason2.csv', index = False)

bundes =season('https://webws.365scores.com/web/games/results/?appTypeId=5&langId=1&timezoneName=America/Santiago&userCountryId=28&competitions=25&includeTopBettingOpportunity=1&topBookmaker=14&')
print(bundes)
bundes_csv = bundes.to_csv('BundesligaFullSeason.csv', index = False)

test_flash = json_response('https://www.flashscore.cl/futbol/inglaterra/premier-league/partidos/')
print(test_flash)