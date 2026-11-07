# BETOOL Dashboard (frontend)

Panel web del motor de apuestas de valor (+EV) de BETOOL, construido con
**Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 + Recharts**.

## Requisitos

- Node.js >= 20
- El backend FastAPI corriendo en `http://localhost:8000` (ver `backend/README.md`)

## Puesta en marcha

```bash
npm install
npm run dev        # http://localhost:3000
```

## Configuración

Si el backend corre en otra dirección, define la variable de entorno:

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Estructura

```
app/                 # página (dashboard con tabs)
components/          # UI: tabla de apuestas, filtros, KPIs, paneles, gráficas
lib/api.ts           # tipos y cliente HTTP hacia la API FastAPI
lib/cn.ts            # utilidad de clases
```

## Tabs

- **Apuestas**: tabla de apuestas +EV con filtros (hoy / 3 días / todas) y mercado, KPIs y botón de actualizar predicciones.
- **Gráficas**: distribución de EV, probabilidad vs cuota, apuestas por mercado.
- **Bankroll**: liquidación de apuestas de papel (ganada/perdida/nula) y curva de P&L.
- **Pipeline**: ejecuta los módulos del pipeline (fixtures, results, odds, leagues, teams, daily, bot) con log en vivo.