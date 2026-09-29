import unicodedata
from curl_cffi import requests
import pandas as pd
import json
import time
from datetime import datetime as dt

def betano_extract(url_name):
    """
    This fuction extract the html from betano to a pure JSON object, I recommend using it in the league url to scrapp all urls from matches later
    
    Args:
        url_name(str): an url from betano ideally a league url from football/competitions/league
    
    Returns:
        loader(JSON): A JSON object to be cleaned
    """
    loader = {}
    for intento in range(3):
        time.sleep(intento * 2)
        response = requests.get(url_name, impersonate="chrome120", verify=False)
        if response.status_code == 200:
            to_text = response.text
            start_line =  to_text.find("initial_state")
            corchetes = to_text.find('{', start_line)
            corchetes_end = to_text.find('</script>', start_line)
            bloque_grueso = to_text[corchetes: corchetes_end] 
            last_key = bloque_grueso.rfind('}')
            purify = bloque_grueso[0: last_key + 1]
            load = json.loads(purify)
            loader.update(load)
            break 
        elif response.status_code == 404 and intento > 2:
            print(f"Error 404 en intento {intento + 1} partido no encontrado")
            break
        else:
            print(f"Fallo en el codigo {response.status_code} en intento {intento + 1}. Reitentando..")

            
    return loader


def beturl_extract(purify_json):
    """ 
    With this fuction we found the urls for each match that contains all bets we need
    
    Args:
        purfiy_json(dict): A loaded html to json object (use betano_extract fuction before)
    
    Returns:
        url_bets(list): Urls from each matches containing all possible bets """
    events = purify_json['data']['blocks'][0]['events']
    url_bets =[]
    for index in range(len(events)):
        url = events[index]['url']
        if '/cuotas-de-partido/' in url:
            full_url = "https://www.betanosports.com" + url
            url_bets.append(full_url)
    return url_bets


def markets_names(url_bets):
    """
    A fuction that extract the names and ids of all possible markets in a match

    Args:
        url_bets(str): a url of a match not accept a simple string
    
    Returns:
        names_bet(list): a list of dictionaries containing the id and name of each market"""
    
    pathfinder = betano_extract(url_bets)
    names_finder = pathfinder['data']['event']['markets']
    names_bet = []
    for markets in names_finder:
        id = markets['id']
        names = markets['name']
        dict = {'id': id, 'name': names}
        names_bet.append(dict)
    return names_bet

    
def bet_finder(match_url):
    """ 
    A fuction that exctract all possible bets in Main Market of a match
    
    Args:
        match_url(str): a url of a match not accept a simple string
    
    Returns:
        DataFrame: a simple DataFrame containing bets"""
    extract = betano_extract(match_url)
    if 'data' not in extract:
        return pd.DataFrame()

    timestamp = dt.now()
    home = strip_accents(extract['data']['event']['participants'][0]['name'].lower().strip())
    away = strip_accents(extract['data']['event']['participants'][1]['name'].lower().strip())
    match_date = pd.to_datetime(extract['data']['event']['startTime'], unit = 'ms').date()
    market_list = extract['data']['event']['markets']
    full_list = []

    valid_markets = ['resultado del partido', 'doble oportunidad', 'goles totales mas/menos', 'ambos equipos anotan', 'corners mas/menos']

    for markets in market_list:
        market_name = strip_accents(markets['name']).lower().strip()
        if market_name not in valid_markets:
            continue
        if 'selections' in markets and len(markets['selections']) > 0:
            selections = markets['selections']
            for selecciones in selections:
                bet_name = strip_accents(selecciones['name']).lower().strip()
                if market_name == 'doble oportunidad':
                    if bet_name == f"{home} o empate":
                        bet_name = '1X'
                    elif bet_name == f"{away} o empate":
                        bet_name = '2X'
                    elif bet_name == f"{home} o {away}":
                        bet_name = '12'
                        
                bet_price = selecciones['price']
                match = {
                         'Home': home,
                         'Away': away,
                         'date': match_date,
                         'market': market_name,
                         'bet_name': bet_name,
                         'odd': bet_price,
                         'Timestamp': timestamp
                             }
                full_list.append(match)
        elif 'tableLayout' in markets:
            for group in markets['tableLayout']['rows']:
                for rows in group['groupSelections']:
                    for selections in rows['selections']:
                        bet_name = selections['name']
                        bet_price = selections['price']
                        match = {'Home': home,
                         'Away': away,
                         'date': match_date,
                         'market': market_name,
                         'bet_name': bet_name,
                         'odd': bet_price,
                         'Timestamp': timestamp
                             }
                        full_list.append(match)
    return pd.DataFrame(full_list)
        

def main(league_url):
    """ 
    A fuction that exctract all possible bets in Main Market of all matches in a league
    
    Args: 
        league_url(str): a url of a league not accept a simple string
    
    Returns: 
        DataFrame: Concat all DataFrames containing all bets for each match in a league"""
    league_scrap = betano_extract(league_url)
    league = beturl_extract(league_scrap)
    df_list = []
    for match in league[:11]:
        #print(f"Analyzing {match}")
        df_match = bet_finder(match)
        df_list.append(df_match)
    conection = pd.concat(df_list, ignore_index=True)
    return conection
    
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



