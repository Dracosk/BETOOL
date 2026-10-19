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

        all_fixtures, all_results = await get_all_rounds_data(tab, league_id, season_id)
        all_halves = []
        for results in all_results:
            match_id = results.get('match_id')
            stats_all, stats_halves = await clean_stats(tab, match_id)
            results.update(stats_all)
            if stats_halves:
                all_halves.append(stats_halves)
            await asyncio.sleep(random.uniform(1.0, 2.5))
    return all_fixtures, all_results, all_halves


async def get_rounds(tab, league_id, season_id):
    api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/rounds"
    response = await timed_request(tab, api_url)
    return response.get('rounds', [])


async def get_season(tab, league_id):
        api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/seasons"
        response = await timed_request(tab, api_url)
        return response.get('seasons', [])

async def get_matches(tab, league_id, season_id, round_id):
        api_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/events/round/{round_id}"
        response = await timed_request(tab, api_url)
        return response.get('events', [])

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

async def clean_matches(tab, league_id, season_id, round_id):
    matches = await get_matches(tab, league_id, season_id, round_id)
    fixture_matches = []
    results_matches = []
    for match in matches:
        if match.get('status', {}).get('code') == 100:
            match_id = match.get('id', '')
            home_team = match.get('homeTeam', {}).get('name', '')
            away_team = match.get('awayTeam', {}).get('name', '')
            start_time = match.get('startTimestamp', '')
            home_score = match.get('homeScore', {}).get('current', '')
            away_score = match.get('awayScore', {}).get('current', '')
            results_matches.append({
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'start_time': start_time,
                'home_score': home_score,
                'away_score': away_score
            })
        elif match.get('status', {}).get('code') == 0:
            match_id = match.get('id', '')
            home_team = match.get('homeTeam', {}).get('name', '')
            away_team = match.get('awayTeam', {}).get('name', '')
            start_time = match.get('startTimestamp', '')
            fixture_matches.append({
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'start_time': start_time
            })
        else:
            continue
    return fixture_matches, results_matches

async def get_all_rounds_data(tab, league_id, season_id):
    rounds = await get_rounds(tab, league_id, season_id)
    all_fixtures = []
    all_results = []
    
    for round_info in rounds:
        round_id = round_info.get('round', '')
        fixture_matches, results_matches = await clean_matches(tab, league_id, season_id, round_id)
        all_fixtures.extend(fixture_matches)
        all_results.extend(results_matches)
        await asyncio.sleep(random.uniform(0.7, 0.9))
    
    return all_fixtures, all_results

async def get_stats(tab, match_id):
        api_url = f"https://www.sofascore.com/api/v1/event/{match_id}/statistics"
        response = await timed_request(tab, api_url)
        return response.get('statistics', [])

async def timed_request(tab,api_url, retries=3, timeout= 10):
    for attempt in range(retries):
        try:
            response = await asyncio.wait_for(tab.request.get(api_url), timeout=timeout)
            return response.json()
        except asyncio.TimeoutError:
            if attempt < retries - 1:
                await asyncio.sleep(random.uniform(1, 3)) 
            else:
                return {}
        except Exception as e:
            return {}

async def clean_stats(tab, match_id):
    stats = await get_stats(tab, match_id)
    stats_all = {'match_id': match_id}
    stats_halves = {'match_id': match_id}
    for stat in stats:
        period = stat.get('period', '').lower()
        group = stat.get('groups', [])
        for group_item in group:
            items = group_item.get('statisticsItems', [])
            for item in items:
                name = item.get('name','').replace(' ', '_').lower()
                home_value = item.get('home','')
                away_value = item.get('away','')
                if period == 'all':
                    stats_all[f"{name}_home"] = home_value
                    stats_all[f"{name}_away"] = away_value
                elif period == '1st' or period == '2nd':
                    stats_halves[f"{period}_{name}_home"] = home_value
                    stats_halves[f"{period}_{name}_away"] = away_value
                else:
                    continue
    return stats_all, stats_halves

async def tab_seasons(tournament_url):
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
        
        all_halves = []
        master_results = []
        master_fixtures = []

        cleaned_seasons = await clean_seasons(tab, league_id)
        for season in cleaned_seasons[:6]:
            season_id = season.get('season_id')
            season_name = season.get('season_name')
            all_fixtures, all_results = await get_all_rounds_data(tab, league_id, season_id)
            for fixture in all_fixtures:
                fixture.update({'season_name': season_name})
            master_fixtures.extend(all_fixtures)
            for results in all_results:
                match_id = results.get('match_id')
                stats_all, stats_halves = await clean_stats(tab, match_id)
                results.update({'season_name': season_name})
                results.update(stats_all)
                if stats_halves:
                    stats_halves.update({'season_name': season_name})
                    all_halves.append(stats_halves)
                await asyncio.sleep(random.uniform(1.0, 2.5))
            master_results.extend(all_results)
            await asyncio.sleep(random.uniform(2.0,2.7))
    return master_fixtures, master_results, all_halves

