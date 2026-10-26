# Levanta el backend (FastAPI) y el frontend (Next.js) en modo desarrollo.
# Requiere: venv con dependencias instaladas y node_modules en frontend/.
# Puertos: backend 8000, frontend 3010 (el 3000 lo usa otro proyecto).
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

# Carga las credenciales AWS desde .env en este proceso (las heredan los hijos).
if (Test-Path ".\.env") {
    Get-Content ".\.env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $idx = $line.IndexOf("=")
            $key = $line.Substring(0, $idx).Trim()
            $value = $line.Substring($idx + 1).Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "Credenciales AWS cargadas desde .env" -ForegroundColor DarkGray
} else {
    Write-Host "Aviso: no hay .env; se usara ~/.aws/credentials" -ForegroundColor Yellow
}

Write-Host "Iniciando backend en http://127.0.0.1:8000  y frontend en http://127.0.0.1:3010" -ForegroundColor Green
Write-Host "Ambos escuchan solo en loopback (no accesibles desde la red local)." -ForegroundColor DarkGray
Start-Process powershell -NoExit -WorkingDirectory $root -ArgumentList "-Command", ".\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -NoExit -WorkingDirectory "$root\frontend" -ArgumentList "-Command", "npm run dev -- --hostname 127.0.0.1 --port 3010"
