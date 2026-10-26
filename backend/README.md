# BETOOL API (backend)

API FastAPI que expone el núcleo de BETOOL (`ml.predict`, `pipe.*`, `main`) como
endpoints HTTP para el dashboard web (`frontend/`).

## Requisitos

- Python 3.12 (instalado vía winget)
- Credenciales AWS configuradas (`.aws` o variables de entorno) con acceso a
  Athena (`db_betool`) y S3 (`betool-dl`), según el README del proyecto.

## Puesta en marcha

```bash
# desde la raíz del repo (BETOOL)
py -m venv venv
.\venv\Scripts\pip install -r requirements_ml.txt fastapi uvicorn
.\venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
```

Documentación interactiva: http://localhost:8000/docs

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado de la API y del gestor de tareas |
| GET | `/api/bets?scope=all\|today\|3d&market=` | Apuestas +EV cacheadas (filtros) |
| POST | `/api/predict/refresh` | Re-ejecuta `prediction_run()` en background |
| GET | `/api/predict/status` | Estado de la predicción |
| GET | `/api/stats` | Agregaciones para gráficas |
| POST | `/api/pipeline/{module}` | Ejecuta un módulo del pipeline |
| GET | `/api/pipeline/logs` | Log en vivo de la última ejecución |
| GET | `/api/bankroll` | `paper_bets_*.csv` + liquidaciones + curva P&L |
| POST | `/api/bankroll/settle` | Marca una apuesta `won`/`lost`/`void`/`pending` |
| GET | `/api/papers` | Lista los `paper_bets_*.csv` exportados |

## Notas

- Las predicciones se cachean en `backend/cache/*.json` (ignorados por git);
  el botón «Actualizar predicciones» re-ejecuta los modelos.
- Las liquidaciones del bankroll se guardan en `backend/data/settlements.json`.
- Los módulos del pipeline corren en subprocesos (como `python -m pipe.<modulo>`),
  con su salida capturada en el log en memoria.