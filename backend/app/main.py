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
    # El frontend de BETOOL corre en el 3010 (el 3000 lo usa otro proyecto).
    # El regex permite cualquier puerto local para no volver a romperse si cambia.
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3010",
        "http://127.0.0.1:3010",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bets.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(bankroll.router, prefix="/api")


@app.get("/api/health")
def health():
    from backend.app.jobs import JOBS

    return {"status": "ok", "jobs": JOBS.status()}