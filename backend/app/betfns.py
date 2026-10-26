"""Conecta la API FastAPI con el núcleo de BETOOL (ml.*, pipe.*, main)."""
import math
import os
import subprocess
import sys
from datetime import date

import pandas as pd

from backend.app.jobs import LOGS

# backend/app/betfns.py -> backend/app -> backend -> raíz del repo
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAPER_COLS = ["game_date", "home", "away", "market", "bet_name", "model_prob", "odd", "ev", "bank"]


def _ensure_repo_importable():
    """Garantiza que se puedan importar los paquetes ml/pipe/utils."""
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)


def jsonable(value):
    """Convierte valores (numpy/pandas/dates) a tipos JSON nativos."""
    import numpy as np

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return round(value, 6)
    return str(value)


def normalize_row(row: dict) -> dict:
    return {str(k): jsonable(v) for k, v in row.items()}


def run_prediction() -> list:
    """Ejecuta prediction_run() del ML y devuelve lista de apuestas JSON-able."""
    _ensure_repo_importable()
    from ml.predict import prediction_run

    LOGS.write("[backend] Ejecutando prediction_run() (descarga modelos, consulta Athena)...")
    df = prediction_run()
    LOGS.write(f"[backend] predicción lista: {len(df)} apuestas de valor.")
    return [normalize_row(r) for r in df.to_dict(orient="records")]


def run_module(module_name: str) -> dict:
    """Ejecuta un módulo del pipeline (pipe.<module>) como subproceso y captura su log."""
    _ensure_repo_importable()
    cmd = [sys.executable, "-m", f"pipe.{module_name}"]
    LOGS.write(f"[backend] Ejecutando módulo: {module_name}")
    LOGS.write("$ " + subprocess.list2cmdline(cmd))

    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    for line in proc.stdout:
        LOGS.write(line.rstrip())
    proc.wait()

    if proc.returncode != 0:
        LOGS.write(f"[backend] El módulo {module_name} falló (exit {proc.returncode})")
        raise RuntimeError(f"El módulo {module_name} falló con código {proc.returncode}")
    LOGS.write(f"[backend] Módulo {module_name} ejecutado correctamente.")
    return {"module": module_name, "status": "ok"}


def run_daily() -> dict:
    """Ejecuta la cadena de tareas diarias: fixtures -> results -> odds."""
    import random
    import time

    for mod in ["fixtures", "results", "odds"]:
        run_module(mod)
        time.sleep(random.uniform(0.5, 1.0))
    LOGS.write("[backend] Tareas diarias ejecutadas correctamente.")
    return {"status": "ok", "modules": ["fixtures", "results", "odds"]}


def run_bot(scope: str = "all") -> dict:
    """Versión no interactiva de main.run_bot(): genera apuestas y exporta CSV."""
    _ensure_repo_importable()
    from ml.predict import prediction_run

    LOGS.write("[backend] run_bot: generando predicciones...")
    df = prediction_run()
    df = df[[c for c in PAPER_COLS if c in df.columns]].copy()
    if not df.empty:
        df["game_date"] = pd.to_datetime(df["game_date"])

    today = pd.Timestamp(date.today())
    if scope == "today":
        df = df[df["game_date"] == today]
    elif scope in ("3d", "next3"):
        end = today + pd.Timedelta(days=3)
        df = df[(df["game_date"] >= today) & (df["game_date"] <= end)]
    df = df.reset_index(drop=True)

    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    filename = f"paper_bets_{timestamp}.csv"
    df.to_csv(os.path.join(REPO_ROOT, filename), index=False, encoding="utf-8-sig")
    LOGS.write(f"[backend] Exportadas {len(df)} apuestas a {filename}")
    return {
        "filename": filename,
        "count": int(len(df)),
        "bets": [normalize_row(r) for r in df.to_dict(orient="records")],
    }