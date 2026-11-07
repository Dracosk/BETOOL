import time
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from backend.app import cache
from backend.app.betfns import run_prediction
from backend.app.jobs import JOBS

router = APIRouter(tags=["bets"])

BETS_CACHE = cache.ValueCache("bets.json")
META_CACHE = cache.ValueCache("meta.json")


def _do_refresh() -> dict:
    bets = run_prediction()
    meta = {"updated_at": time.time(), "count": len(bets)}
    BETS_CACHE.write(bets)
    META_CACHE.write(meta)
    return meta


@router.get("/bets")
def get_bets(
    scope: str = Query("all", pattern="^(all|today|3d)$"),
    market: str | None = None,
):
    bets = BETS_CACHE.read() or []
    meta = META_CACHE.read() or {}
    filtered = _filter_bets(bets, scope, market)
    return {
        "bets": filtered,
        "total": len(bets),
        "count": len(filtered),
        "scope": scope,
        "market": market,
        "cached": bool(bets),
        "updated_at": meta.get("updated_at"),
    }


@router.post("/predict/refresh")
def refresh_predictions():
    started = JOBS.start("predict", _do_refresh)
    if not started:
        raise HTTPException(status_code=409, detail="Ya hay una predicción en ejecución.")
    return {"started": True, "status": JOBS.status()}


@router.get("/predict/status")
def predict_status():
    return JOBS.status()


def _filter_bets(bets: list, scope: str, market: str | None) -> list:
    today = date.today()
    end = today + timedelta(days=3)
    today_s = today.isoformat()
    end_s = end.isoformat()

    out = []
    for b in bets:
        gd = str(b.get("game_date", ""))[:10]
        if scope == "today" and gd != today_s:
            continue
        if scope == "3d" and not (today_s <= gd <= end_s):
            continue
        if market and market.lower() not in str(b.get("market", "")).lower():
            continue
        out.append(b)
    return out