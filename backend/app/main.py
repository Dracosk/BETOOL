from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import bankroll, bets, pipeline, stats

app = FastAPI(
    title="BETOOL API",
    version="0.1.0",
    description="API del pipeline de apuestas de valor (+EV) de BETOOL.",
)

app.add_middleware(
    CORSMiddleware,
    # El frontend de BETOOL corre en el 3010 y solo en loopback.
    # Lista cerrada a proposito: no se permite cualquier puerto local para que
    # otra pagina servida en localhost no pueda llamar a esta API con cookies.
    allow_origins=[
        "http://localhost:3010",
        "http://127.0.0.1:3010",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(bets.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(bankroll.router, prefix="/api")


@app.get("/api/health")
def health():
    from backend.app.jobs import JOBS

    return {"status": "ok", "jobs": JOBS.status()}