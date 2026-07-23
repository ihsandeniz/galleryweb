@echo off
REM ── GalleryWeb — Tek tikla baslat (Windows) ──────────────────────────────────
REM Python/pip bilmenize gerek yok. Bu dosyaya cift tiklayin.
REM Ilk calistirmada bagimliliklari kurar, sonra galeriyi acar: http://localhost:5000
setlocal
cd /d "%~dp0"

REM Python bul — hazir wheel'i olan surumleri (3.11-3.13) tercih et.
REM Cok yeni surumler (3.14) bazi paketleri kaynaktan derlemeye zorlar ve cokebilir.
set "PY="
where py >nul 2>&1
if not errorlevel 1 (
    for %%V in (3.13 3.12 3.11) do (
        if not defined PY (
            py -%%V --version >nul 2>&1 && set "PY=py -%%V"
        )
    )
    if not defined PY set "PY=py"
)
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo [HATA] Python bulunamadi. Lutfen Python 3.11-3.13 kurun:
    echo https://www.python.org/downloads/  ^(kurulumda "Add Python to PATH" isaretleyin^)
    pause
    exit /b 1
)

REM Izole ortam ^(venv^)
if not exist ".venv\" (
    echo [KURULUM] Ilk calistirma: sanal ortam olusturuluyor...
    %PY% -m venv .venv
)
call ".venv\Scripts\activate.bat"

REM Bagimliliklar kurulu mu?
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [KURULUM] Bagimliliklar kuruluyor ^(bir kereye mahsus, birkac dakika^)...
    python -m pip install --upgrade pip >nul
    python -m pip install -r backend\requirements-selfhost.txt
)

REM ffmpeg uyarisi
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [BILGI] 'ffmpeg' kurulu degil - video kirpma calismaz ^(fotograflar sorunsuz^).
    echo         Kurmak icin: https://www.gyan.dev/ffmpeg/builds/  veya  winget install ffmpeg
)

REM Tarayiciyi ac ve sunucuyu baslat
echo [BASLIYOR] GalleryWeb -^> http://localhost:5000  ^(durdurmak icin bu pencereyi kapatin^)
start "" http://localhost:5000
cd backend
python main.py
pause
