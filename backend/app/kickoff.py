"""Hora de inicio de los partidos desde 365scores.

El pipeline solo persiste la fecha (`Game_Date`), así que la hora se consulta a
la misma fuente que usa el scraper y se cruza por `game_id`, que no es más que
el hash de local + visitante + fecha. La respuesta se guarda en caché para no
golpear la API en cada refresco y, si la consulta falla, las predicciones
siguen funcionando sin hora.
"""

import hashlib
import logging
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from curl_cffi import requests

from backend.app.cache import ValueCache

logger = logging.getLogger(__name__)

# Mismos identificadores que usa pipe/fixtures.py.
LEAGUES = {
    "Premier League": 7,
    "Bundesliga": 25,
    "Seria A": 17,
    "Laliga": 11,
    "Ligue 1": 35,
}

URL = (
    "https://webws.365scores.com/web/games/fixtures/"
    "?appTypeId=5&langId=1&timezoneName=America/Santiago"
    "&userCountryId=28&competitions={competition}"
)

CACHE_TTL = 15 * 60  # 15 minutos
TIMEOUT = 15
KICKOFF_CACHE = ValueCache("kickoff.json")

_memory: dict = {"at": 0.0, "times": {}}


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _game_id(home: str, away: str, game_date: str) -> str:
    """Reproduce el id que genera pipe/scrapper_results.py."""
    home_name = _strip_accents(home.lower().strip())
    away_name = _strip_accents(away.lower().strip())
    raw = f"{home_name}_{away_name}_{game_date}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:12]


def _clock(start_time: str) -> str | None:
    """Devuelve HH:MM en la hora local que trae la propia API (Chile)."""
    try:
        return datetime.fromisoformat(start_time.replace("Z", "+00:00")).strftime("%H:%M")
    except ValueError:
        return None


def _fetch_league(competition: int) -> dict:
    url = URL.format(competition=competition)
    response = requests.get(url, impersonate="chrome120", verify=False, timeout=TIMEOUT)
    if response.status_code != 200:
        logger.warning("365scores respondió %s para la competición %s", response.status_code, competition)
        return {}

    games = response.json().get("games", []) or []
    times = {}
    for game in games:
        start_time = str(game.get("startTime") or "")
        if not start_time:
            continue
        home = (game.get("homeCompetitor") or {}).get("name") or ""
        away = (game.get("awayCompetitor") or {}).get("name") or ""
        if not home or not away:
            continue
        gid = _game_id(home, away, start_time[:10])
        times[gid] = {
            "start_time": start_time,
            "kickoff": _clock(start_time),
            "status": game.get("statusText"),
        }
    return times


def _fetch_all() -> dict:
    times: dict = {}
    with ThreadPoolExecutor(max_workers=len(LEAGUES)) as pool:
        futures = {pool.submit(_fetch_league, comp): name for name, comp in LEAGUES.items()}
        for future, name in futures.items():
            try:
                times.update(future.result())
            except Exception as exc:  # red caída, DNS, timeout...
                logger.warning("No se pudo leer la hora de %s: %s", name, exc)
    return times


def get_kickoff_times(force: bool = False) -> dict:
    """Mapa game_id -> {start_time, kickoff, status}, con memoria y disco."""
    now = time.time()
    if not force and _memory["times"] and now - _memory["at"] < CACHE_TTL:
        return _memory["times"]

    stored = KICKOFF_CACHE.read() or {}
    stored_times = stored.get("times") or {}
    if not force and stored_times and now - float(stored.get("updated_at") or 0) < CACHE_TTL:
        _memory.update(at=now, times=stored_times)
        return stored_times

    times = _fetch_all()
    if not times:
        # Sin red: se conserva lo que hubiera de antes.
        if stored_times:
            _memory.update(at=now, times=stored_times)
        return stored_times

    KICKOFF_CACHE.write({"updated_at": now, "times": times})
    _memory.update(at=now, times=times)
    return times


def attach_kickoff_times(records: list) -> list:
    """Añade `start_time` y `kickoff` a cada apuesta, si se conoce el partido."""
    try:
        times = get_kickoff_times()
    except Exception as exc:
        logger.warning("Sin horas de partido: %s", exc)
        return records

    for row in records:
        info = times.get(str(row.get("game_id") or ""))
        if info:
            row["start_time"] = info.get("start_time")
            row["kickoff"] = info.get("kickoff")
    return records
