# Respaldo cifrado de las credenciales AWS de BETOOL (AES-256 + PBKDF2)
#
# Cifra ~/.aws/credentials y el .env del repo en un unico fichero .enc, o lo
# descifra cuando lo necesites. El texto plano nunca se escribe en disco.
#
# Uso:
#   .\backup_keys.ps1 -Mode Encrypt
#   .\backup_keys.ps1 -Mode Decrypt            (imprime por pantalla)
#   .\backup_keys.ps1 -Mode Decrypt -OutFile "C:\ruta\credentials.txt"
#
# Te pedira una contrasena (no se muestra). Guarda el .enc donde quieras
# (USB, Drive...) y la contrasena aparte, en tu cabeza o en un gestor.
# Sin la contrasena el .enc no se puede abrir.

param(
    [ValidateSet("Encrypt", "Decrypt")]
    [string]$Mode = "Encrypt",

    [string]$Path = (Join-Path $env:USERPROFILE "betool-keys.enc"),

    [string]$OutFile,

    # Solo para automatizacion; si se omite, se pide por pantalla.
    [string]$Password
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root ".env"
$awsCred = Join-Path $env:USERPROFILE ".aws\credentials"
$awsConfig = Join-Path $env:USERPROFILE ".aws\config"

$MAGIC = "BETOOL-ENC-v1"
$ITERATIONS = 200000

function Get-PasswordOnce {
    if ($Password) { return $Password }
    $secure = Read-Host "Contrasena" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function New-Key([string]$pw, [byte[]]$salt) {
    $kdf = New-Object System.Security.Cryptography.Rfc2898DeriveBytes(
        $pw, $salt, $ITERATIONS, [System.Security.Cryptography.HashAlgorithmName]::SHA256)
    return $kdf.GetBytes(32)
}

if ($Mode -eq "Encrypt") {
    foreach ($f in @($envFile, $awsCred)) {
        if (-not (Test-Path $f)) {
            Write-Host "Falta $f. Nada que cifrar." -ForegroundColor Red
            exit 1
        }
    }

    $pw = Get-PasswordOnce
    if ([string]::IsNullOrWhiteSpace($pw) -or $pw.Length -lt 12) {
        Write-Host "Usa una contrasena de al menos 12 caracteres." -ForegroundColor Red
        exit 1
    }

    # Un solo bloque de texto con las dos credenciales, marcadas por seccion.
    $payload = @()
    $payload += "### aws-credentials"
    $payload += (Get-Content $awsCred -Raw).Trim()
    if (Test-Path $awsConfig) {
        $payload += "### aws-config"
        $payload += (Get-Content $awsConfig -Raw).Trim()
    }
    $payload += "### dotenv"
    $payload += (Get-Content $envFile -Raw).Trim()
    $plain = [Text.Encoding]::UTF8.GetBytes(($payload -join "`n"))

    $salt = [byte[]]::new(16)
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($salt)
    $key = New-Key $pw $salt

    $aes = [System.Security.Cryptography.Aes]::Create()
    try {
        $aes.KeySize = 256
        $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
        $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
        $aes.Key = $key
        $aes.GenerateIV()
        $iv = $aes.IV
        $enc = $aes.CreateEncryptor()
        $cipher = $enc.TransformFinalBlock($plain, 0, $plain.Length)
    } finally { $aes.Dispose() }

    $blob = [byte[]]::new($salt.Length + $iv.Length + $cipher.Length)
    [Array]::Copy($salt, 0, $blob, 0, $salt.Length)
    [Array]::Copy($iv, 0, $blob, $salt.Length, $iv.Length)
    [Array]::Copy($cipher, 0, $blob, $salt.Length + $iv.Length, $cipher.Length)

    $out = $MAGIC + "`n" + [Convert]::ToBase64String($blob)
    # Si ya existe un respaldo anterior, nos devolvemos permiso de escritura
    # antes de sobrescribirlo (el fichero vive con ACL cerrada).
    if (Test-Path $Path) {
        icacls $Path /inheritance:r /grant:r "$($env:USERNAME):(M)" | Out-Null
        Set-ItemProperty -Path $Path -Name IsReadOnly -Value $false -ErrorAction SilentlyContinue
    }
    Set-Content -Path $Path -Value $out -Encoding ascii -Force
    # Solo el usuario, con modify para poder rehacer el respaldo.
    icacls $Path /inheritance:r /grant:r "$($env:USERNAME):(M)" | Out-Null

    Write-Host "Respaldo cifrado creado: $Path" -ForegroundColor Green
    Write-Host "Tamano: $((Get-Item $Path).Length) bytes" -ForegroundColor DarkGray
    Write-Host "Guarda la contrasena aparte. Sin ella el fichero no se puede abrir." -ForegroundColor Yellow
}
else {
    if (-not (Test-Path $Path)) {
        Write-Host "No existe $Path" -ForegroundColor Red
        exit 1
    }
    $lines = Get-Content $Path
    if ($lines[0] -ne $MAGIC) {
        Write-Host "El fichero no tiene el formato esperado." -ForegroundColor Red
        exit 1
    }
    $blob = [Convert]::FromBase64String(($lines[1..($lines.Count - 1)] -join ""))

    $salt = $blob[0..15]
    $iv = $blob[16..31]
    $cipher = $blob[32..($blob.Length - 1)]

    $pw = Get-PasswordOnce
    $key = New-Key $pw $salt

    $aes = [System.Security.Cryptography.Aes]::Create()
    try {
        $aes.KeySize = 256
        $aes.Mode = [System.Security.Cryptography.CipherMode]::CBC
        $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
        $aes.Key = $key
        $aes.IV = [byte[]]$iv
        $dec = $aes.CreateDecryptor()
        $plain = $dec.TransformFinalBlock($cipher, 0, $cipher.Length)
    }
    catch {
        Write-Host "Contrasena incorrecta o fichero danado." -ForegroundColor Red
        exit 1
    }
    finally { $aes.Dispose() }

    $text = [Text.Encoding]::UTF8.GetString($plain)
    if ($OutFile) {
        if (Test-Path $OutFile) {
            icacls $OutFile /inheritance:r /grant:r "$($env:USERNAME):(M)" | Out-Null
            Set-ItemProperty -Path $OutFile -Name IsReadOnly -Value $false -ErrorAction SilentlyContinue
        }
        Set-Content -Path $OutFile -Value $text -Encoding ascii -Force
        icacls $OutFile /inheritance:r /grant:r "$($env:USERNAME):(M)" | Out-Null
        Write-Host "Descifrado en: $OutFile" -ForegroundColor Green
        Write-Host "Borra ese fichero cuando termines de usarlo." -ForegroundColor Yellow
    }
    else {
        Write-Output $text
    }
}
