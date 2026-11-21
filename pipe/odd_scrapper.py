import unicodedata
from curl_cffi import requests
import pandas as pd
import json
import time
import warnings
from datetime import datetime as dt
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


MARKET_TABS = ('popular', 'statistics', 'goals', 'handicap', 'cornerkicks', 'cards')
PLAYER_MARKET_TYPES = {'PSCR', 'PTRC'}
ODDS_COLUMNS = ['Home', 'Away', 'date', 'market', 'bet_name', 'odd', 'Timestamp']

def betano_extract(url_name):
    """
    This fuction extract the html from betano to a pure JSON object, I recommend using it in the league url to scrapp all urls from matches later
    
    Args:
        url_name(str): an url from betano ideally a league url from football/competitions/league
    
    Returns:
        loader(JSON): A JSON object to be cleaned
    """
    loader = {}
    for retries in range(3):
        time.sleep(retries * 2)
        try:
            response = requests.get(url_name, impersonate="chrome120", verify=False, timeout=15)
        except requests.exceptions.RequestException as error:
            print(f"Error requesting {url_name} in attempt {retries + 1}: {error}")
            continue
        if response.status_code == 200:
            to_text = response.text
            start_line =  to_text.find("initial_state")
            if start_line == -1:
                print(f"No initial_state in {url_name} in attempt {retries + 1}.")
                continue
            corchetes = to_text.find('{', start_line)
            corchetes_end = to_text.find('</script>', start_line)
            bloque_grueso = to_text[corchetes: corchetes_end] 
            last_key = bloque_grueso.rfind('}')
            purify = bloque_grueso[0: last_key + 1]
            try:
                load = json.loads(purify)
            except json.JSONDecodeError as error:
                print(f"Invalid initial_state in {url_name} in attempt {retries + 1}: {error}")
                continue
            loader.update(load)
            break 
        elif response.status_code == 404:
            print(f"Error 404 in the attempt {retries + 1} matching not found, skipping this match")
            break
        else:
            print(f"Error {response.status_code} in the attempt {retries + 1}, retrying.")

    return loader
            


def beturl_extract(purify_json):
    """ 
    With this fuction we found the urls for each match that contains all bets we need
    
    Args:
        purfiy_json(dict): A loaded html to json object (use betano_extract fuction before)
    
    Returns:
        url_bets(list): Urls from each matches containing all possible bets """
    
    events = purify_json['data']['blocks'][0]['events']
    url_bets = []
    for index in range(len(events)):
        url = events[index]['url']
        if '/cuotas-de-partido/' in url:
            full_url = "https://www.betanosports.com" + url
            url_bets.append(full_url)
    return url_bets


def _match_markets(match_url, data):
    """Yield markets from the requested Betano tabs in their capture order."""
    event = data['event']
    tabs = data.get('nonBetBuilderTabs') or data.get('markets') or []
    tabs_by_type = {tab['type']: tab for tab in tabs}
    current_tab = next((tab['type'] for tab in tabs if tab.get('selected')), 'popular')
    url = urlsplit(match_url)
    query = dict(parse_qsl(url.query, keep_blank_values=True))

    for tab_type in MARKET_TABS:
        if tab_type == current_tab:
            yield from event.get('markets') or []
        elif tab_type in tabs_by_type:
            query['bt'] = tabs_by_type[tab_type]['id']
            tab_url = urlunsplit(url._replace(query=urlencode(query)))
            tab_data = betano_extract(tab_url).get('data', {})
            tab_event = tab_data.get('event') or {}
            tab_list = tab_data.get('nonBetBuilderTabs') or tab_data.get('markets') or []
            selected = next((tab['type'] for tab in tab_list if tab.get('selected')), None)
            if tab_event.get('id') != event['id'] or selected != tab_type or 'markets' not in tab_event:
                warnings.warn(f"Betano did not return the {tab_type} tab for {match_url}")
                continue
            yield from tab_event['markets'] or []


def markets_names(url_bets):
    """
    A fuction that extract the names and ids of all possible markets in a match

    Args:
        url_bets(str): a url of a match not accept a simple string
    
    Returns:
        names_bet(list): a list of dictionaries containing the id and name of each market"""
    
    data = betano_extract(url_bets).get('data', {})
    if not data.get('event'):
        return []

    names_bet = []
    seen_markets = set()
    for markets in _match_markets(url_bets, data):
        market_id = markets['id']
        if market_id not in seen_markets:
            names_bet.append({'id': market_id, 'name': markets['name']})
            seen_markets.add(market_id)
    return names_bet


def _market_selections(market):
    """Yield the names and selections from flat markets and grouped tables."""
    for selection in market.get('selections') or []:
        yield market['name'], selection['name'], selection

    table = market.get('tableLayout') or {}
    columns = table.get('columnTitles') or []
    for row in table.get('rows') or []:
        for group in row.get('groupSelections') or []:
            for selection in group.get('selections') or []:
                market_name = market['name']
                bet_name = selection['name']
                if market.get('type') in ('HGTO', 'AGTO') and columns:
                    team = columns[selection['columnIndex']]['title']
                    market_name = f"{team} Total de goles"
                elif market.get('type') == 'RNXT' and row.get('title'):
                    bet_name = f"{bet_name} a {row['title']}"
                yield market_name, bet_name, selection


def bet_finder(match_url):
    """ 
    Extract match and team odds from the configured tabs of a match.
    
    Args:
        match_url(str): a url of a match not accept a simple string
    
    Returns:
        DataFrame: a simple DataFrame containing bets"""
    
    data = betano_extract(match_url).get('data', {})
    event = data.get('event')
    if not event:
        return pd.DataFrame(columns=ODDS_COLUMNS)

    timestamp = dt.now()
    home = strip_accents(event['participants'][0]['name'].lower().strip())
    away = strip_accents(event['participants'][1]['name'].lower().strip())
    match_date = pd.to_datetime(event['startTime'], unit='ms').date()
    full_list = []
    seen_selections = set()

    for markets in _match_markets(match_url, data):
        if markets.get('playerId') or markets.get('type') in PLAYER_MARKET_TYPES:
            continue
        for market_name, bet_name, selection in _market_selections(markets):
            bet_price = selection.get('price')
            if not isinstance(bet_price, (int, float)) or bet_price <= 1:
                continue

            selection_key = (markets['id'], selection['id'])
            if selection_key in seen_selections:
                continue
            seen_selections.add(selection_key)

            market_name = strip_accents(market_name).lower().strip().replace('τiempo', 'tiempo')
            bet_name = strip_accents(bet_name).lower().strip()
            if market_name == 'doble oportunidad':
                if bet_name == f"{home} o empate":
                    bet_name = '1X'
                elif bet_name == f"{away} o empate":
                    bet_name = '2X'
                elif bet_name == f"{home} o {away}":
                    bet_name = '12'

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
    return pd.DataFrame(full_list, columns=ODDS_COLUMNS)
        

def main(league_url):
    """ 
    Extract match and team odds from the configured tabs of a league's matches.
    
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
    if not df_list:
        return pd.DataFrame(columns=ODDS_COLUMNS)
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



