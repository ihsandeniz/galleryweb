#!/usr/bin/env bash
# ── GalleryWeb — Tek tıkla başlat (Linux / macOS) ─────────────────────────────
# Python/pip bilmenize gerek yok. Bu dosyaya çift tıklayın (veya: ./run.sh).
# İlk çalıştırmada bağımlılıkları kurar, sonra galeriyi açar → http://localhost:5000
set -e

# Script'in bulunduğu dizine geç (çift tıkta cwd farklı olabilir)
cd "$(dirname "$0")"

# Otomatik güncelleme (yalnız git kopyasıysa; internet/değişiklik yoksa atlanır).
# ZIP olarak indirdiyseniz güncelleme için: ./guncelle.sh
if command -v git >/dev/null 2>&1 && [ -d ".git" ]; then
    echo "🔄 Son sürüm kontrol ediliyor..."
    git pull --ff-only 2>/dev/null || true
fi

# Python bul — bağımlılıkların hazır wheel'i olan sürümleri (3.10–3.13) tercih et.
# Çok yeni sürümler (ör. 3.14) bazı paketleri kaynaktan derlemeye zorlar ve kurulum
# derleyici hatasıyla çöker; o yüzden önce uyumlu bir yorumlayıcı ararız.
PY=""
for cand in python3.13 python3.12 python3.11 python3.10; do
    if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
    # Uyumlu sürüm yok — python3/python'a düş (3.10–3.13 ise kullan, değilse uyar)
    for cand in python3 python; do
        if command -v "$cand" >/dev/null 2>&1; then
            minor=$("$cand" -c 'import sys; print(sys.version_info[1])' 2>/dev/null)
            major=$("$cand" -c 'import sys; print(sys.version_info[0])' 2>/dev/null)
            PY="$cand"
            if [ "$major" = "3" ] && { [ "$minor" -lt 10 ] || [ "$minor" -gt 13 ]; }; then
                echo "⚠️  Bulunan Python ($("$cand" --version 2>&1)) çok yeni/eski olabilir —"
                echo "    bazı paketler için hazır wheel bulunmayabilir. Önerilen: Python 3.11–3.13."
            fi
            break
        fi
    done
fi
if [ -z "$PY" ]; then
    echo "❌ Python bulunamadı. Lütfen Python 3.11–3.13 kurun: https://www.python.org/downloads/"
    read -r -p "Kapatmak için Enter'a basın..." _
    exit 1
fi

# İzole ortam (venv) — sistem Python'unu kirletmez
if [ ! -d ".venv" ]; then
    echo "📦 İlk kurulum: sanal ortam oluşturuluyor..."
    "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Bağımlılıklar güncel mi? requirements dosyası son kurulumdan farklıysa OTOMATİK
# yeniden kur. Böylece güncelleme geldiğinde .venv'i silmeye gerek kalmaz.
REQ="backend/requirements-selfhost.txt"
STAMP=".venv/installed-reqs.txt"
if ! cmp -s "$REQ" "$STAMP" 2>/dev/null; then
    echo "📦 Bağımlılıklar kuruluyor/güncelleniyor (bir kereye mahsus, birkaç dakika)..."
    pip install --upgrade pip >/dev/null
    pip install -r "$REQ"
    cp "$REQ" "$STAMP"
fi

# ffmpeg uyarısı (video düzenleme için gerekli, zorunlu değil)
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ℹ️  Not: 'ffmpeg' kurulu değil — video kırpma çalışmaz (fotoğraflar sorunsuz)."
    echo "   Kurmak için: Ubuntu 'sudo apt install ffmpeg' · macOS 'brew install ffmpeg' · Arch 'sudo pacman -S ffmpeg'"
fi

# Tarayıcıyı 2 sn sonra aç (sunucu ayağa kalksın)
( sleep 2
  if command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:5000" >/dev/null 2>&1
  elif command -v open >/dev/null 2>&1; then open "http://localhost:5000" >/dev/null 2>&1
  fi
) &

echo "🚀 GalleryWeb başlıyor → http://localhost:5000  (durdurmak için Ctrl+C)"
echo "ℹ️  Güncellemek için istediğiniz zaman: ./guncelle.sh"
cd backend
exec python main.py
