@echo off
REM ── GalleryWeb — Guncelleme (Windows) ────────────────────────────────────────
REM Bu dosyaya cift tiklayin: en son surumu GitHub'dan alir.
REM Fotograflariniz, ayarlariniz ve .venv KORUNUR (yalniz uygulama kodu guncellenir).
REM Guncelleme sonrasi run.bat calistirin — degisen bagimliliklar OTOMATIK kurulur.
setlocal
cd /d "%~dp0"
echo ============================================
echo   GalleryWeb Guncelleme
echo ============================================
echo.

REM ── Yol 1: git kopyasi ise git pull ──────────────────────────────────────────
where git >nul 2>&1
if not errorlevel 1 if exist ".git\" (
    echo [GIT] Depodan guncelleniyor...
    git pull --ff-only
    if errorlevel 1 (
        echo.
        echo [HATA] git pull basarisiz oldu ^(yerel degisiklikleriniz cakisiyor olabilir^).
        echo        Kod bozulmadi. Elle cozmek icin: git status
        pause
        exit /b 1
    )
    echo.
    echo [TAMAM] Guncellendi. Simdi run.bat ile baslatin.
    pause
    exit /b 0
)

REM ── Yol 2: ZIP kullanicisi — GitHub'dan son surumu indir + uzerine kopyala ────
echo [WEB] GitHub'dan son surum indiriliyor...
set "ZIPURL=https://github.com/ihsandeniz/galleryweb/archive/refs/heads/main.zip"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { $tmp=Join-Path $env:TEMP ('gw_'+[guid]::NewGuid().ToString()); New-Item -ItemType Directory -Path $tmp | Out-Null; $zip=Join-Path $tmp 'gw.zip'; Invoke-WebRequest -UseBasicParsing -Headers @{'User-Agent'='galleryweb'} '%ZIPURL%' -OutFile $zip; Expand-Archive -Path $zip -DestinationPath $tmp -Force; $src=Join-Path $tmp 'galleryweb-main'; robocopy $src '.' /E /XF guncelle.bat /NFL /NDL /NJH /NJS /NP /NC /NS | Out-Null; if ($LASTEXITCODE -ge 8) { throw 'dosya kopyalama hatasi (robocopy '+$LASTEXITCODE+')' }; Remove-Item $tmp -Recurse -Force; Write-Host '[TAMAM] Uygulama kodu guncellendi.'; exit 0 } catch { Write-Host ('[HATA] ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
    echo.
    echo [HATA] Guncelleme basarisiz - internet baglantinizi kontrol edip tekrar deneyin.
    echo        Mevcut surumunuz BOZULMADI, calismaya devam eder.
    pause
    exit /b 1
)
echo.
echo [TAMAM] Simdi run.bat ile baslatin ^(degisen bagimliliklar otomatik kurulur^).
pause
