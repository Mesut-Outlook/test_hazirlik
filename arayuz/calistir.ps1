# arayuz/calistir.ps1 — Windows yerel web arayüzünü kurar/başlatır.
# Kullanım: powershell -ExecutionPolicy Bypass -File arayuz/calistir.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) { $ScriptDir = "." }
$BackendDir = Resolve-Path (Join-Path $ScriptDir "backend")
$VenvDir = Join-Path $BackendDir "venv"
$Port = 8756

# Sunucu zaten çalışıyorsa ikinci bir kopya başlatma — sadece tarayıcıyı aç.
# (Masaüstü kısayolundan çift tıklamalarda güvenli davranış.)
$zaten = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($zaten) {
    Write-Host "[arayuz] Sunucu zaten çalışıyor — tarayıcı açılıyor: http://127.0.0.1:$Port" -ForegroundColor Green
    Start-Process "http://127.0.0.1:$Port"
    exit 0
}

# Python yolunu bul
$PythonExe = "C:\Users\egemen\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$VenvUvicorn = Join-Path $VenvDir "Scripts\uvicorn.exe"

if ((-not (Test-Path $VenvPython)) -or (-not (Test-Path $VenvUvicorn))) {
    if (-not (Test-Path $VenvPython)) {
        Write-Host "[arayuz] Sanal ortam (venv) bulunamadı, kuruluyor: $VenvDir" -ForegroundColor Yellow
        & $PythonExe -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Sanal ortam oluşturulamadı!"
            exit 1
        }
    }
    Write-Host "[arayuz] pip güncelleniyor ve bağımlılıklar kuruluyor..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip -q
    & $VenvPython -m pip install -r "$BackendDir\requirements.txt" -q
} else {
    Write-Host "[arayuz] Bağımlılıklar kontrol ediliyor..." -ForegroundColor Cyan
    & $VenvPython -m pip install -r "$BackendDir\requirements.txt" -q
}

Write-Host "[arayuz] uvicorn başlatılıyor: http://127.0.0.1:$Port" -ForegroundColor Green

# Tarayıcıyı aç
Start-Process "http://127.0.0.1:$Port"

# Sunucuyu başlat (otomatik reload aktif)
& $VenvUvicorn main:app --app-dir $BackendDir --host 127.0.0.1 --port $Port --reload
