import pandas as pd
import numpy as np
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
import random
import re

async def tab_init(tournament_url):
    options = ChromiumOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    async with Chrome(options=options) as browser:
        tab = await browser.start()
        url_base = f"https://www.sofascore.com/es/football/tournament/england/premier-league/17#id:96668"
        await tab.go_to(url_base)
        await asyncio.sleep(3)
    

async def get_rounds(tab, tournament_url):
    league_id = re.search(r'/(\d+)#id:', tournament_url).group(1)
    season_id = re.search(r'#id:(\d+)', tournament_url).group(1)
    api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/rounds"
    response = await tab.request.get(api_url)
    return response.json().get('rounds', [])

async def get_season(tab, tournament_url):
    league_id = re.search(r'/(\d+)#id:', tournament_url).group(1)
    api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/seasons"
    response = await tab.request.get(api_url)
    return response.json().get('seasons', [])
    