# Rota la clave de acceso AWS de BETOOL sin exponer el secreto en la terminal
# ni en el historial.
#
# Uso:
#   1. En la consola AWS (usuario admin/root):
#        IAM -> Usuarios -> betool-scrapper -> Credenciales de seguridad
#        -> Crear clave de acceso
#   2. Ejecuta este script desde la raiz del repo:
#        .\rotate_aws_key.ps1 -AccessKeyId AKIA...
#      Te pedira el secret (no se muestra en pantalla).
#   3. Vuelve a la consola y DESACTIVA (o elimina) la clave vieja.
#   4. Reinicia el backend (.\start_dev.ps1) para que tome la clave nueva.
#
# El script actualiza .env y ~/.aws/credentials, restringe permisos y verifica
# la clave nueva contra AWS antes de darla por buena.

param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^AKIA[0-9A-Z]{16}$')]
    [string]$AccessKeyId
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root ".env"
$awsDir = Join-Path $env:USERPROFILE ".aws"
$awsCred = Join-Path $awsDir "credentials"
$awsConfig = Join-Path $awsDir "config"
$region = "us-east-2"

$secure = Read-Host "Pega el SECRET ACCESS KEY (no se vera en pantalla)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $secret = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

if ([string]::IsNullOrWhiteSpace($secret) -or $secret.Length -lt 20) {
    Write-Host "El secret no parece valido. Abortado sin cambiar nada." -ForegroundColor Red
    exit 1
}

# --- backup de lo actual (por si hay que volver atras) ---
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"

# Los ficheros viven con ACL cerrada: nos devolvemos escritura antes de tocarlos.
foreach ($f in @($envFile, $awsCred, $awsConfig)) {
    if (Test-Path $f) {
        icacls $f /inheritance:r /grant:r "$($env:USERNAME):(M)" | Out-Null
        Set-ItemProperty -Path $f -Name IsReadOnly -Value $false -ErrorAction SilentlyContinue
    }
}

if (Test-Path $envFile) { Copy-Item $envFile "$envFile.bak-$stamp" -Force }
if (Test-Path $awsCred) { Copy-Item $awsCred "$awsCred.bak-$stamp" -Force }

# --- ~/.aws/credentials ---
New-Item -ItemType Directory -Force -Path $awsDir | Out-Null
@"
[default]
aws_access_key_id = $AccessKeyId
aws_secret_access_key = $secret
"@ | Set-Content -Path $awsCred -Encoding ascii

if (-not (Test-Path $awsConfig)) {
    @"
[default]
region = $region
output = json
"@ | Set-Content -Path $awsConfig -Encoding ascii
}

# --- .env del repo, conservando el resto de variables ---
$lines = @()
if (Test-Path $envFile) {
    $lines = Get-Content $envFile | Where-Object {
        $_ -notmatch '^\s*AWS_ACCESS_KEY_ID\s*=' -and
        $_ -notmatch '^\s*AWS_SECRET_ACCESS_KEY\s*=' -and
        $_.Trim() -ne ''
    }
}
$lines += "AWS_ACCESS_KEY_ID=$AccessKeyId"
$lines += "AWS_SECRET_ACCESS_KEY=$secret"
$lines += "AWS_DEFAULT_REGION=$region"
$lines += "AWS_REGION=$region"
$lines | Set-Content -Path $envFile -Encoding ascii -Force

# --- permisos: solo tu usuario, con escritura para poder rotar de nuevo ---
foreach ($f in @($envFile, $awsCred, $awsConfig)) {
    if (Test-Path $f) {
        icacls $f /inheritance:r /grant:r "$($env:USERNAME):(M)" | Out-Null
    }
}

# --- verificacion real contra AWS (sin imprimir el secret) ---
$py = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "No encuentro el venv; no puedo verificar la clave. Revisa .env a mano." -ForegroundColor Yellow
    exit 1
}

$check = @'
import os, boto3
os.environ["AWS_ACCESS_KEY_ID"] = os.environ["NEW_KEY_ID"]
s = boto3.Session(region_name="us-east-2")
try:
    ident = s.client("sts").get_caller_identity()
    print("OK", ident["Arn"])
except Exception as e:
    print("FALLO", type(e).__name__)
'@
$tmp = Join-Path $env:TEMP "betool_key_check.py"
Set-Content -Path $tmp -Value $check -Encoding ascii

$env:NEW_KEY_ID = $AccessKeyId
$result = & $py $tmp 2>&1 | Select-Object -Last 1
Remove-Item $tmp -Force -ErrorAction SilentlyContinue
Remove-Item Env:\NEW_KEY_ID -ErrorAction SilentlyContinue

if ($result -like "OK*") {
    Write-Host ""
    Write-Host "Clave nueva funcionando: $result" -ForegroundColor Green
    Write-Host ""
    Write-Host "Siguiente paso OBLIGATORIO:" -ForegroundColor Yellow
    Write-Host "  En la consola IAM, desactiva o elimina la clave VIEJA." -ForegroundColor Yellow
    Write-Host "  Luego reinicia:  .\start_dev.ps1" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "La clave nueva NO funciona ($result)." -ForegroundColor Red
    Write-Host "Restauro los backups y dejo la clave anterior:" -ForegroundColor Yellow
    if (Test-Path "$envFile.bak-$stamp") { Copy-Item "$envFile.bak-$stamp" $envFile -Force }
    if (Test-Path "$awsCred.bak-$stamp") { Copy-Item "$awsCred.bak-$stamp" $awsCred -Force }
    Write-Host "Backups restaurados (*.bak-$stamp)." -ForegroundColor Yellow
    exit 1
}
