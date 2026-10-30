import argparse
import json
import math
import os
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import pandas as pd
import asyncio
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions
import random
import re
import time
from functools import partial
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.types import ResourceType

MAX_CONCURRENT_REQUESTS = 4
REQUEST_PER_SECOND = 3.0
CONSECUTIVE_ERRORS = 0
CACHE_DIR = Path("cache")
_request_state = ContextVar("sofa_score_request_state", default=None)
API = 'https://www.sofascore.com/api/v1'

@dataclass(frozen=True)
class ScrapingConfig:
    max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS
    request_per_second: float = REQUEST_PER_SECOND
    cache_dir: Path = CACHE_DIR
    cache_ttl_seconds: float = 86400.0  
    refresh_cache: bool = False
    allow_partial: bool = False
    checkpoint_interval: int = 20

    def __post_init__(self):
        if not math.isfinite(self.request_per_second) or self.request_per_second <= 0:
            raise ValueError("request_per_second must be a positive finite number.")
        if self.max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be at least 1.")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative.")
        if self.checkpoint_interval < 1:
            raise ValueError("checkpoint_interval must be at least 1.")
        
class rate_limiter:
    
    def __init__(self, rate_per_second, concurrency):
        if not math.isfinite(rate_per_second) or rate_per_second <= 0 or concurrency < 1:
            raise ValueError("rate_per_second and concurrency must be positive finite numbers.")
        self.interval = 1.0 / rate_per_second
        self._condition = asyncio.Condition()
        self._in_flight = 0
        self._next_start = 0.0
        self.concurrency = concurrency
        self._blocked_until = 0.0

    def penalize(self, seconds):
        self._blocked_until = max(self._blocked_until, time.monotonic() + seconds)

    @asynccontextmanager
    async def slot(self):
        async with self._condition:
            while True:
                if self._in_flight >= self.concurrency:
                    await self._condition.wait()
                    continue
                delay = max(self._next_start, self._blocked_until) - time.monotonic()
                if delay > 0:
                    try:
                        await asyncio.wait_for(self._condition.wait(), timeout=delay)
                    except asyncio.TimeoutError:
                        pass
                    continue
                self._in_flight += 1
                self._next_start = time.monotonic() + self.interval
                break
        try:
            yield
        finally:
            async with self._condition:
                self._in_flight -= 1
                self._condition.notify_all()

class SeasonCache:
    def __init__(self, config, league_id, season_id):
        self.config = config
        self.league_id, self.season_id = str(league_id), str(season_id)
        self.path = None if config.cache_dir is None else (
            Path(config.cache_dir) / self.league_id / f'{self.season_id}.json'
        )
        self.entries = {}
        self.dirty = 0
        if self.path is not None and self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8'))
                if (data['schema_version'] != 1 or data['league_id'] != self.league_id
                        or data['season_id'] != self.season_id or not isinstance(data['entries'], dict)):
                    raise ValueError('Invalid cache file structure.')
                self.entries = data['entries']
            except (ValueError, KeyError, TypeError) as exc:
                logging.warning(f"Error reading {self.path}: {exc}")
                self.entries = {}

    def get(self, match_id):
        if self.path is None or self.config.refresh_cache:
            return None
        entry = self.entries.get(str(match_id))
        try:
            age = time.time() - entry['fetched_at']
            all_stats, halves = entry['all'], entry['halves']
            if (not 0 <= age < self.config.cache_ttl_seconds
                    or not isinstance(all_stats, dict) or not isinstance(halves, dict)
                    or all_stats.get('match_id') != match_id or halves.get('match_id') != match_id
                    or (len(all_stats) <= 1 and len(halves) <= 1)):
                return None
            return dict(all_stats), dict(halves)
        except (KeyError, TypeError):
            return None

    def invalidate(self, match_id):
        if str(match_id) in self.entries:
            del self.entries[str(match_id)]
            self.dirty += 1

    def put(self, match_id, all_stats, halves):
        if self.path is None or (len(all_stats) <= 1 and len(halves) <= 1):
            return
        self.entries[str(match_id)] = {
            'fetched_at': time.time(), 'all': dict(all_stats), 'halves': dict(halves),
        }
        self.dirty += 1
        if self.dirty >= self.config.checkpoint_interval:
            self.flush()

    def flush(self):
        if self.path is None or not self.dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {'schema_version': 1, 'league_id': self.league_id,
                   'season_id': self.season_id, 'entries': self.entries}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                    dir=self.path.parent, prefix=self.path.name + '.', suffix='.tmp', delete=False) as file:
                temporary = Path(file.name)
                json.dump(payload, file, ensure_ascii=False, allow_nan=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
            self.dirty = 0
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

class RequestState:
    def __init__(self, config = None):
        self.config = config or ScrapingConfig()
        self.limiter = rate_limiter(self.config.request_per_second, self.config.max_concurrent_requests)
        self.requests = 0
        self.errors = 0
        self.cache_hits = 0

def request_state():
    state = _request_state.get()
    if state is None:
        state = RequestState()
        _request_state.set(state)
    return state

@asynccontextmanager
async def open_tab(tournament_url, warmup = 2.0):
        options = ChromiumOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        async with Chrome(options=options) as browser:
            tab = await browser.start()
            url_base = tournament_url
            await tab.enable_fetch_events()
            await tab.on(FetchEvent.REQUEST_PAUSED, partial(requests_filter, tab))
            await tab.go_to(url_base)
            await asyncio.sleep(warmup)
            yield tab # I use yield to avoid closing the tab when the context manager exits, allowing the caller to continue using it.

def retry_after_seconds(headers):
    pairs = headers.items() if isinstance(headers, dict) else (
        (entry.get("name", ""), entry.get("value", "")) for entry in (headers or [])
    )
    value = next((value for name, value in pairs if name.lower() == "retry-after"), None)
    return max(0.0, float(value)) if value is not None else None

def parse_url(tournament_url, require_season=False):
    split = urlsplit(tournament_url)
    match = re.search(r'/tournament/[^/]+/[^/]+/(\d+)/?$', split.path)
    if split.hostname not in ["www.sofascore.com", "sofascore.com"] or not match:
        raise ValueError("Invalid tournament URL. Must be a valid Sofascore tournament URL.")
    season = re.search(r'(?:^|[,&])id:(\d+)(?=$|[,&])', split.fragment)
    if require_season and not season:
        raise ValueError("Season ID is required but not found in the URL fragment.")
    return match.group(1), season.group(1) if season else None

def payload_list(payload, key):
    if key not in payload or not isinstance(payload[key], list):
        raise ValueError(f"Expected a list for key '{key}' in payload, but got: {payload.get(key)}")
    return payload[key]

def unique_matches(matches):
    return list({match['match_id']: match for match in matches}.values())

async def bounded_workers(fuction, items, concurrency=None):
    items = list(items)
    if not items:
        return []
    concurrrency = request_state().config.max_concurrent_requests if concurrency is None else concurrency
    if concurrrency < 1:
        raise ValueError("Concurrency must be positive.")
    request_state()
    pending = iter(enumerate(items)) 
    results = [None] * len(items) # Preallocate results list to maintain order

    async def worker():
        for index, item in pending:
            results[index] = await fuction(item) 
    workers = [asyncio.create_task(worker()) for _ in range(min(concurrrency, len(items)))]
    try:
        await asyncio.gather(*workers)
    finally:
        for worker_task in workers:
            if not worker_task.done():
                worker_task.cancel() # To avoid leaving tasks running in the background if an exception occurs.
        await asyncio.gather(*workers, return_exceptions=True)
    return results

async def scrape_season(tab, league_id, season_id, season_name=None,*,include_stats=True):
    state = request_state()
    fixtures, results = await get_all_rounds_data(tab, league_id, season_id)
    for row in fixtures + results:
        row['season_id'] = season_id
        if season_name is not None:
            row['season_name'] = season_name
    if not include_stats:
        return fixtures, [{**row, 'stat_status': 'skipped', 'stat_source': None, 'stats_error': None} for row in results], []
    
    cache = SeasonCache(state.config, league_id, season_id)
    hits_before = state.cache_hits

    async def enrich(row):
        cached = cache.get(row['match_id'])
        if cached is not None:
            state.cache_hits += 1
            return assamble_results(row, *cached, season_name, source='cache')
        cache.invalidate(row['match_id'])
        try:
           all_stats, halves = await clean_stats(tab, row['match_id'])
        except Exception as e:
            logging.error(f"Error fetching stats for match {row['match_id']}: {e}")
            return {**row, 'stat_status': 'failed', 'stat_source': None, 'stats_error': str(e)}
        cache.put(row['match_id'], all_stats, halves)
        return assamble_results(row, all_stats, halves, season_name)

    try:
        completed = await bounded_workers(enrich, results)
    finally:
        cache.flush()
    results = [result for result, _ in completed]
    halves = [half for _, half in completed if half is not None]
    return fixtures, results, halves

async def scrape_multi_seasons(tournament_url, league_id, season_id=None, limit=6,include_stats=True,warmup=2.0,config=None):
    if not math.isfinite(warmup) or warmup < 0:
        raise ValueError("Warmup must be a non-negative finite number.")
    state = RequestState(config)
    token = _request_state.set(state)
    async with open_tab(tournament_url, warmup=warmup) as tab:
        seasons = await clean_seasons(tab, league_id)[:limit] if season_id is None else [
        {'season_id': season_id, 'season_name': None}]
        master_fixtures, master_results, master_halves = [], [], []
        for season in seasons:
            current_id = season['season_id']
            if not current_id:
                raise ValueError(f"Season ID is missing for season: {season}")
            fixtures, results, halves = await scrape_season(tab, league_id, current_id, season['season_name'], include_stats=include_stats)
            master_fixtures.extend(fixtures)
            master_results.extend(results)
            master_halves.extend(halves)
    return master_fixtures, master_results, master_halves



async def tab_init(tournament_url,*, include_stats=True, warmup=2.0, config=None):
    league_id, season_id = parse_url(tournament_url, require_season=True)
    
    return await scrape_multi_seasons(tournament_url, league_id, season_id=season_id, config=config, include_stats=include_stats, warmup=warmup)
     

async def get_rounds(tab, league_id, season_id):
    api_url = f'{API}/unique-tournament/{league_id}/season/{season_id}/rounds'
    response = await timed_request(tab, api_url)
    return payload_list(response, 'rounds')


async def get_season(tab, league_id):
        api_url = f"{API}/unique-tournament/{league_id}/seasons"
        response = await timed_request(tab, api_url)
        return payload_list(response, 'seasons')

async def get_matches(tab, league_id, season_id, round_id):
        api_url = f"{API}/unique-tournament/{league_id}/season/{season_id}/events/round/{round_id}"
        response = await timed_request(tab, api_url)
        return payload_list(response, 'events')

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
    fixture, results = [], []

    for match in await get_matches(tab, league_id, season_id, round_id):
        code = (match.get('status') or {}).get('code')
        if not code in (0, 100): # 0 = fixture, 100 = result
            continue
        schema = {
            'match_id': match['id'],
            'home_team':(match.get('homeTeam') or {}).get('name', ''),
            'away_team':(match.get('awayTeam') or {}).get('name', ''),
            'start_time': match.get('startTimestamp'),
        }
        if code == 100:
            results.append({
            **schema,
            'home_score': (match.get('homeScore') or {}).get('current', None),
            'away_score': (match.get('awayScore') or {}).get('current', None),
            })
        else:
            fixture.append(schema)
    return fixture, results

async def get_all_rounds_data(tab, league_id, season_id):
    rounds = await get_rounds(tab, league_id, season_id)
    rounds_data = await bounded_workers(lambda round_info: clean_matches(tab, league_id, season_id, round_info['round']), rounds,)
    fixtures, results = [], []
    for fixture_matches, results_matches in rounds_data:
        fixtures.extend(fixture_matches)
        results.extend(results_matches)

    results = unique_matches(results)
    finished_ids = {row['match_id'] for row in results}
    return [row for row in unique_matches(fixtures) if row['match_id'] not in finished_ids], results


async def get_stats(tab, match_id):
        api_url = f"{API}/event/{match_id}/statistics"
        response = await timed_request(tab, api_url)
        return payload_list(response, 'statistics')

def parse_stats(match_id, stats):
    stats_all, stats_halves = {'match_id': match_id}, {'match_id': match_id}
    for stat in stats:
        period = (stat.get('period') or '').lower()
        if period not in ('all', '1st', '2nd'):
            continue
        for group in stat.get('groups') or []:
            for item in group.get('statisticsItems') or []:
                name = (item.get('name') or '').lower().replace(' ', '_')
                if not name:
                    continue
                target = stats_all if period == 'all' else stats_halves
                prefix = '' if period == 'all' else f"{period}_"
                for side in ('home', 'away'):
                    value = item.get(side)
                    target[f"{prefix}{name}_{side}"] = None if value is None else str(value) # Convert to string to avoid issues with NaN or None values in pandas DataFrame

    return stats_all, stats_halves

def assamble_results(result, stats_all, stats_halves, season_name=None, *, source='network'):
    avalaible = len(stats_all) > 1 or len(stats_halves) > 1
    final = {**result, **stats_all,
            'stat_status': 'ok' if avalaible else 'unavailable',
            'stat_source': source, 'stats_error': None}
    halves = dict(stats_halves) if len(stats_halves) > 1 else None
    for row in (final, halves):
        if row is not None:
            if season_name is not None:
                row['season_name'] = season_name
            if 'season_id' in result:
                row['season_id'] = result['season_id'] 
    return final, halves


async def timed_request(tab,api_url, retries=3, timeout= 10):
    if retries < 1 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Retries must be at least 1 and timeout must be a positive finite number.")
    state = request_state()
    for attempt in range(retries):
            retry_delay = None
            try:
                async with state.limiter.slot():
                    state.requests += 1
                    response = await asyncio.wait_for(tab.request.get(api_url), timeout=timeout)
                    if not 200 <= response.status_code < 300:
                        if response.status_code in (429, 503):
                            retry_delay = retry_after_seconds(response.headers)
                            state.limiter.penalize(max(retry_delay or 0, 2 ** attempt))
                            print(f"Request failed with status {response.status_code} for URL: {api_url}. Retrying in {retry_delay:.2f} seconds.")
                return response.json()
            except (asyncio.TimeoutError, Exception) as e:
                state.errors += 1
                if attempt < retries - 1:
                    delay = max(retry_delay or 0, 2 ** attempt)
                    print(f"Request failed (attempt {attempt + 1}/{retries}) for URL: {api_url}. Retrying in {delay:.2f} seconds. Error: {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"Request failed after {retries} attempts for URL: {api_url}. Error: {e}")
                    raise e

async def clean_stats(tab, match_id):
    return parse_stats(match_id, await get_stats(tab, match_id))

async def requests_filter(tab, event):

    request_id = event['params']['requestId']
    resource_type = event['params'].get('resourceType', '')
    url = event['params'].get('request', {}).get('url', '')
    blocked_types = resource_type in [ResourceType.IMAGE, ResourceType.MEDIA, ResourceType.FONT]
    if blocked_types or'google-analytics' in url or 'doubleclick' in url or 'score-api' in url:
        await tab.fail_request(request_id, error_reason='Aborted')   
    else:
        await tab.continue_request(request_id)


async def tab_seasons(tournament_url):
    return None

async def match_task(tab, result_dict, season_name=None):
   stats_all, stats_halves = await clean_stats(tab, result_dict['match_id'])
   return assamble_results(result_dict, stats_all, stats_halves, season_name)





