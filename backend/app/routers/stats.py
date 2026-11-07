from collections import defaultdict

from fastapi import APIRouter

from backend.app import cache

router = APIRouter(tags=["stats"])

BETS_CACHE = cache.ValueCache("bets.json")


@router.get("/stats")
def get_stats():
    bets = BETS_CACHE.read() or []
    if not bets:
        return {"empty": True, "count": 0}

    evs = [b.get("ev") or 0 for b in bets]
    banks = [b.get("bank") or 0 for b in bets]

    histogram = _ev_histogram(evs)
    by_market = defaultdict(lambda: {"count": 0, "ev_sum": 0.0})
    for b in bets:
        market = b.get("market") or "otros"
        by_market[market]["count"] += 1
        by_market[market]["ev_sum"] += b.get("ev") or 0

    market_stats = [
        {"market": m, "count": v["count"], "avg_ev": round(v["ev_sum"] / v["count"], 2)}
        for m, v in sorted(by_market.items(), key=lambda kv: kv[1]["count"], reverse=True)
    ]

    scatter = [
        {
            "ev": b.get("ev"),
            "odd": b.get("odd"),
            "model_prob": b.get("model_prob"),
            "market": b.get("market"),
        }
        for b in bets
    ]

    return {
        "empty": False,
        "count": len(bets),
        "avg_ev": round(sum(evs) / len(evs), 2),
        "max_ev": round(max(evs), 2) if evs else 0,
        "total_bank": round(sum(banks), 2),
        "ev_histogram": histogram,
        "by_market": market_stats,
        "scatter": scatter,
    }


def _ev_histogram(evs: list, step: float = 1.0, top: int = 12) -> list:
    hist = defaultdict(int)
    for ev in evs:
        idx = min(int(ev // step), top)
        hist[idx] += 1
    labels = [f"{i * step:.0f}-{i * step + step:.0f}%" for i in range(top)] + [f">{top}%"]
    return [{"label": labels[i], "count": hist[i]} for i in range(top + 1)]