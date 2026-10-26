from fastapi import APIRouter, HTTPException

from backend.app.betfns import run_bot, run_daily, run_module
from backend.app.jobs import JOBS, LOGS

router = APIRouter(tags=["pipeline"])

VALID_MODULES = {"fixtures", "results", "odds", "leagues", "teams", "daily", "bot"}


def _target(module: str, scope: str):
    if module == "daily":
        return run_daily()
    if module == "bot":
        return run_bot(scope)
    return run_module(module)


@router.post("/pipeline/{module}")
def start_pipeline(module: str, scope: str = "all"):
    if module not in VALID_MODULES:
        raise HTTPException(status_code=400, detail=f"Módulo inválido. Válidos: {sorted(VALID_MODULES)}")
    started = JOBS.start(module, lambda: _target(module, scope))
    if not started:
        raise HTTPException(status_code=409, detail="Ya hay una tarea en ejecución.")
    return {"started": True, "module": module}


@router.get("/pipeline/logs")
def pipeline_logs(limit: int = 250):
    return {"logs": LOGS.tail(limit), "status": JOBS.status()}


@router.get("/pipeline/status")
def pipeline_status():
    return JOBS.status()