# GalleryWeb masaüstü paketi — Windows derleme betiği (yap.sh'ın karşılığı).
#
#   .\yap.ps1              → sunucu exe'si + kurulum paketi (NSIS)
#   .\yap.ps1 sunucu       → sadece galleryweb-server.exe
#   .\yap.ps1 calistir     → geliştirme: derle + uygulamayı aç
#
# Gereksinimler:
#   • Python 3.10–3.13  (python.org — "Add Python to PATH" işaretli)
#   • Rust               (https://rustup.rs)
#   • cargo-tauri        (cargo install tauri-cli --version "^2.0")
#   • WebView2 çalışma zamanı — Windows 10/11'de genelde zaten kurulu
#   • (opsiyonel) ffmpeg — yalnız video poster karesi ve video kırpma için
#
# NOT: Windows paketi WINDOWS ÜZERİNDE derlenmelidir. PyInstaller çapraz
#      derleme yapamaz; Linux'ta üretilen sunucu binary'si Windows'ta çalışmaz.

param([string]$Komut = "hepsi")

$ErrorActionPreference = "Stop"
$DesktopDir = $PSScriptRoot
$RepoDir    = Split-Path $DesktopDir -Parent
$BuildVenv  = Join-Path $RepoDir ".build-venv"
$ServerExe  = Join-Path $DesktopDir "dist\galleryweb-server.exe"

function Renk($m) { Write-Host $m -ForegroundColor Cyan }
function Hata($m) { Write-Host "HATA: $m" -ForegroundColor Red; exit 1 }

function Python-Bul {
    foreach ($aday in @("python3.13", "python3.12", "python3.11", "python3.10", "python")) {
        $yol = (Get-Command $aday -ErrorAction SilentlyContinue)
        if (-not $yol) { continue }
        # Windows'un MS Store "python.exe" saplaması gerçek Python değildir:
        # çalıştırıp doğrula (run.bat'ta da aynı ders çıkmıştı).
        $sonuc = & $yol.Source -c "import sys; sys.exit(0 if (3,10) <= sys.version_info < (3,14) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return $yol.Source }
    }
    return $null
}

function Venv-Hazirla {
    if (-not (Test-Path (Join-Path $BuildVenv "Scripts\pyinstaller.exe"))) {
        $py = Python-Bul
        if (-not $py) {
            Hata "Uygun Python bulunamadı (3.10–3.13 gerekli).`n       python.org'dan kurun ve 'Add Python to PATH' seçeneğini işaretleyin.`n       Microsoft Store kısayolu gerçek Python DEĞİLDİR."
        }
        Renk "> Derleme ortamı kuruluyor ($py)..."
        & $py -m venv $BuildVenv
        & (Join-Path $BuildVenv "Scripts\python.exe") -m pip install -q --upgrade pip
        & (Join-Path $BuildVenv "Scripts\pip.exe") install -q -r (Join-Path $RepoDir "backend\requirements-selfhost.txt")
        & (Join-Path $BuildVenv "Scripts\pip.exe") install -q pyinstaller
    }
}

function Sunucu-Yap {
    Venv-Hazirla
    Renk "> Sunucu exe'si paketleniyor (PyInstaller)..."
    Push-Location $DesktopDir
    try {
        & (Join-Path $BuildVenv "Scripts\pyinstaller.exe") galleryweb-server.spec `
            --noconfirm --distpath dist --workpath build --log-level WARN
    } finally { Pop-Location }
    if (-not (Test-Path $ServerExe)) { Hata "Sunucu exe'si üretilemedi." }
    $mb = [math]::Round((Get-Item $ServerExe).Length / 1MB, 1)
    Renk "  + $ServerExe ($mb MB)"
}

function Uygulama-Yap {
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) { Hata "Rust (cargo) kurulu değil -> https://rustup.rs" }
    if (-not (Get-Command cargo-tauri -ErrorAction SilentlyContinue)) {
        Hata "cargo-tauri yok -> cargo install tauri-cli --version `"^2.0`""
    }
    Renk "> Masaüstü uygulaması derleniyor (Tauri)..."
    Push-Location (Join-Path $DesktopDir "src-tauri")
    try { & cargo tauri build } finally { Pop-Location }
    Renk "  + Paketler: $DesktopDir\src-tauri\target\release\bundle\"
}

switch ($Komut) {
    "sunucu"   { Sunucu-Yap }
    "calistir" { Sunucu-Yap; Push-Location (Join-Path $DesktopDir "src-tauri"); try { & cargo run } finally { Pop-Location } }
    "hepsi"    { Sunucu-Yap; Uygulama-Yap }
    default    { Hata "Bilinmeyen komut: $Komut (sunucu | calistir | hepsi)" }
}
