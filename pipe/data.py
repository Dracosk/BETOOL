import pandas as pd
import numpy as np
import asyncio
from pydoll.constants import ScrollPosition
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
import random
import re

async def tab_init(tournament_url):
    patron = r'/tournament/([^/]+)/([^/]+)/(\d+)#id:(\d+)'
    match = re.search(patron, tournament_url)
    
    if not match:
        return None
        
    country = match.group(1)
    league = match.group(2)       
    league_id = match.group(3)  
    season_id = match.group(4)

    options = ChromiumOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        url_base = tournament_url
        await tab.go_to(url_base)
        
        for pause in range(3):
            await tab.scroll.by(ScrollPosition.DOWN, 600, humanize=True)
            timesleep = random.uniform(3.5, 7.5)
            await asyncio.sleep(timesleep)
            await tab.scroll.by(ScrollPosition.UP, 300, humanize=True)
            await asyncio.sleep(1.0)

        seasons = await clean_seasons(tab, league_id)
        await asyncio.sleep(random.uniform(0.5, 0.7))
        rounds = await get_rounds(tab, league_id, season_id)
        await asyncio.sleep(random.uniform(0.5, 0.7))

        #get_matches_data = await get_matches(tab, league_id, season_id, 6)
        
    return seasons, rounds, #get_matches_data


async def get_rounds(tab, league_id, season_id):
    try:
        api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/rounds"
        response = await tab.request.get(api_url)
        return response.json().get('rounds', [])
    except Exception as e:
        return []

async def get_season(tab, league_id):
    try:
        api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/seasons"
        response = await tab.request.get(api_url)
        return response.json().get('seasons', [])
    except Exception as e:
        return []

async def get_matches(tab, league_id, season_id, round_id):
    try:
        api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events/round/{round_id}"
        response = await tab.request.get(api_url)
        return response.json().get('events', [])
    except Exception as e:
        return []

async def clean_seasons(tab, league_id):
    seasons = await get_season(tab, league_id)
    cleaned_seasons = []
    for season in seasons:
        season_name = season.get('name', '')
        season_id = season.get('id', '')
        year = season.get('year', '')
        cleaned_seasons.append({
            'season_name': season_name,
            'season_id': season_id,
            'year': year
        })
    return cleaned_seasons

