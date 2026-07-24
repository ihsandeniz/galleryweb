@echo off
REM ── GalleryWeb — Tek tikla baslat (Windows) ──────────────────────────────────
REM Python/pip bilmenize gerek yok. Bu dosyaya cift tiklayin.
REM Ilk calistirmada bagimliliklari kurar, sonra galeriyi acar: http://localhost:5000
REM Guncelleme geldiginde bagimliliklar OTOMATIK tazelenir (elle silme gerekmez).
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ── Python bul — hazir wheel'i olan surumleri (3.11-3.13) tercih et ───────────
REM Cok yeni surumler (3.14) bazi paketleri kaynaktan derlemeye zorlar ve cokebilir.
REM ONEMLI: Sadece PATH'te "var mi" bakmak yetmez — Windows'un Microsoft Store
REM "python.exe" kisayolu where'de gorunur ama GERCEK Python DEGILDIR. Her adayi
REM "-c import sys" ile CALISTIRARAK dogrula; stub bu testte hata dondurur.
set "PY="
where py >nul 2>&1
if not errorlevel 1 (
    for %%V in (3.13 3.12 3.11) do (
        if not defined PY (
            py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
        )
    )
    if not defined PY (
        py -c "import sys" >nul 2>&1 && set "PY=py"
    )
)
if not defined PY (
    python -c "import sys" >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo [HATA] Calisan bir Python bulunamadi.
    echo.
    echo Python 3.11 - 3.13 kurmaniz gerekiyor:
    echo   https://www.python.org/downloads/
    echo   ^(kurulum ekraninda "Add Python to PATH" kutusunu ISARETLEYIN^)
    echo.
    echo Not: Windows'un "Microsoft Store'dan yukle" kisayolu GERCEK Python degildir.
    echo      Gerekirse Ayarlar ^> Uygulama Yurutme Diger Adlari icinden
    echo      python.exe / python3.exe kisayollarini KAPATIN.
    pause
    exit /b 1
)

REM ── Otomatik guncelleme (yalniz git kopyasiysa; internet/degisiklik yoksa atlanir) ──
REM ZIP olarak indirdiyseniz guncelleme icin: guncelle.bat dosyasina cift tiklayin.
where git >nul 2>&1
if not errorlevel 1 if exist ".git\" (
    echo [GUNCELLEME] Son surum kontrol ediliyor...
    git pull --ff-only 2>nul
)

REM ── Izole ortam (venv) ───────────────────────────────────────────────────────
if not exist ".venv\" (
    echo [KURULUM] Ilk calistirma: sanal ortam olusturuluyor...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [HATA] Sanal ortam olusturulamadi. Python kurulumunuzu kontrol edin.
        pause
        exit /b 1
    )
)
call ".venv\Scripts\activate.bat"

REM ── Bagimliliklar guncel mi? ─────────────────────────────────────────────────
REM requirements dosyasi son kurulumdan farkliysa OTOMATIK yeniden kur. Boylece
REM guncelleme geldiginde kullanicinin .venv'i silmesine gerek kalmaz.
set "REQ=backend\requirements-selfhost.txt"
set "STAMP=.venv\installed-reqs.txt"
set "NEED_INSTALL="
if not exist "%STAMP%" (
    set "NEED_INSTALL=1"
) else (
    fc /b "%REQ%" "%STAMP%" >nul 2>&1 || set "NEED_INSTALL=1"
)
if defined NEED_INSTALL (
    echo [KURULUM] Bagimliliklar kuruluyor/guncelleniyor ^(bir kereye mahsus, birkac dakika^)...
    python -m pip install --upgrade pip >nul
    python -m pip install -r "%REQ%"
    if errorlevel 1 (
        echo [HATA] Bagimliliklar kurulamadi. Internet baglantinizi kontrol edip tekrar deneyin.
        pause
        exit /b 1
    )
    copy /y "%REQ%" "%STAMP%" >nul
)

REM ── ffmpeg uyarisi ───────────────────────────────────────────────────────────
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [BILGI] 'ffmpeg' kurulu degil - video kirpma calismaz ^(fotograflar sorunsuz^).
    echo         Kurmak icin: https://www.gyan.dev/ffmpeg/builds/  veya  winget install ffmpeg
)

REM ── Tarayiciyi ac ve sunucuyu baslat ─────────────────────────────────────────
echo [BASLIYOR] GalleryWeb -^> http://localhost:5000  ^(durdurmak icin bu pencereyi kapatin^)
echo [BILGI] Guncellemek icin istediginiz zaman: guncelle.bat
start "" http://localhost:5000
cd backend
python main.py
pause
