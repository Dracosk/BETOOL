"""Lectura de paper_bets_*.csv y liquidación de apuestas (ganada/perdida/nula)."""
import glob
import json
import os
import re

import pandas as pd

from backend.app.betfns import PAPER_COLS, REPO_ROOT, jsonable

SETTLEMENTS_PATH = os.path.join(REPO_ROOT, "backend", "data", "settlements.json")
STATUSES = ("won", "lost", "void", "pending")


def _load_settlements() -> dict:
    if os.path.exists(SETTLEMENTS_PATH):
        try:
            with open(SETTLEMENTS_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


def _save_settlements(data: dict):
    os.makedirs(os.path.dirname(SETTLEMENTS_PATH), exist_ok=True)
    with open(SETTLEMENTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def list_paper_files() -> list:
    files = sorted(glob.glob(os.path.join(REPO_ROOT, "paper_bets_*.csv")))
    result = []
    for path in files:
        name = os.path.basename(path)
        match = re.search(r"paper_bets_(\d{8})_(\d{6})\.csv", name)
        created = None
        if match:
            raw = match.group(1) + match.group(2)
            created = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]} {raw[8:10]}:{raw[10:12]}:{raw[12:]}"
        result.append({"filename": name, "created": created})
    return result


def read_bankroll() -> dict:
    files = list_paper_files()
    settlements = _load_settlements()
    bets = []
    totals = {"potential_ev": 0.0, "bank": 0.0}

    for item in files:
        name = item["filename"]
        path = os.path.join(REPO_ROOT, name)
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        for index, row in df.iterrows():
            record = {
                c: (jsonable(row[c]) if c in df.columns else None) for c in PAPER_COLS
            }
            record["filename"] = name
            record["index"] = int(index)
            record["settlement"] = settlements.get(name, {}).get(str(index), "pending")
            bets.append(record)
            totals["bank"] += float(record.get("bank") or 0)
            totals["potential_ev"] += float(record.get("ev") or 0)

    totals["bets"] = len(bets)
    totals["settled"] = sum(1 for b in bets if b["settlement"] != "pending")

    settled = sorted(
        [b for b in bets if b["settlement"] != "pending"],
        key=lambda b: str(b.get("game_date", "")),
    )
    pl, curve = 0.0, []
    for b in settled:
        bank = float(b.get("bank") or 0)
        odd = float(b.get("odd") or 1)
        if b["settlement"] == "won":
            pl += bank * (odd - 1)
        elif b["settlement"] == "lost":
            pl -= bank
        curve.append(
            {
                "game_date": str(b.get("game_date", ""))[:10],
                "label": f"{b.get('home', '?')} vs {b.get('away', '?')} · {b.get('bet_name', '')}",
                "settlement": b["settlement"],
                "pl": round(pl, 2),
            }
        )

    return {"files": files, "bets": bets, "totals": totals, "curve": curve}


def settle(filename: str, index: int, status: str):
    if status not in STATUSES:
        return None
    data = _load_settlements()
    data.setdefault(filename, {})[str(index)] = status
    _save_settlements(data)
    return {"filename": filename, "index": index, "status": status}