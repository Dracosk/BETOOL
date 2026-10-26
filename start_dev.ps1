# Levanta el backend (FastAPI) y el frontend (Next.js) en modo desarrollo.
# Requiere: venv con dependencias instaladas y node_modules en frontend/.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Falta el venv. Crea el entorno primero:" -ForegroundColor Red
    Write-Host '  py -m venv venv'
    Write-Host '  .\venv\Scripts\pip install -r requirements_ml.txt fastapi uvicorn'
    exit 1
}

if (-not (Test-Path ".\frontend\node_modules")) {
    Write-Host "Falta node_modules en frontend. Ejecuta:  cd frontend  npm install" -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando backend en http://localhost:8000  y frontend en http://localhost:3000" -ForegroundColor Green
Start-Process powershell -NoExit -WorkingDirectory $root -ArgumentList "-Command", ".\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000"
Start-Process powershell -NoExit -WorkingDirectory "$root\frontend" -ArgumentList "-Command", "npm run dev"