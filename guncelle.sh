#!/usr/bin/env bash
# ── GalleryWeb — Güncelleme (Linux / macOS) ──────────────────────────────────
# Bu dosyaya çift tıklayın (veya: ./guncelle.sh): en son sürümü GitHub'dan alır.
# Fotoğraflarınız, ayarlarınız ve .venv KORUNUR (yalnız uygulama kodu güncellenir).
# Güncelleme sonrası ./run.sh çalıştırın — değişen bağımlılıklar OTOMATİK kurulur.
set -e
cd "$(dirname "$0")"
echo "============================================"
echo "  GalleryWeb Güncelleme"
echo "============================================"

# ── Yol 1: git kopyasıysa git pull ───────────────────────────────────────────
if command -v git >/dev/null 2>&1 && [ -d ".git" ]; then
    echo "🔄 Depodan güncelleniyor (git)..."
    if git pull --ff-only; then
        echo "✅ Güncellendi. Şimdi ./run.sh ile başlatın."
    else
        echo "❌ git pull başarısız (yerel değişiklikleriniz çakışıyor olabilir)."
        echo "   Kod bozulmadı. Elle çözmek için: git status"
        exit 1
    fi
    exit 0
fi

# ── Yol 2: ZIP kullanıcısı — GitHub'dan son sürümü indir + üzerine kopyala ────
ZIPURL="https://github.com/ihsandeniz/galleryweb/archive/refs/heads/main.zip"
if ! command -v unzip >/dev/null 2>&1; then
    echo "❌ 'unzip' gerekli. Kurun: Ubuntu 'sudo apt install unzip' · macOS zaten var · Arch 'sudo pacman -S unzip'"
    exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "⬇️  GitHub'dan son sürüm indiriliyor..."
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$ZIPURL" -o "$TMP/gw.zip"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$ZIPURL" -O "$TMP/gw.zip"
else
    echo "❌ 'curl' veya 'wget' gerekli — internet erişimi için biri kurulu olmalı."
    exit 1
fi

unzip -q -o "$TMP/gw.zip" -d "$TMP"
SRC="$TMP/galleryweb-main"
if [ ! -d "$SRC" ]; then
    echo "❌ İndirilen arşiv beklenmedik yapıda — güncelleme iptal. Mevcut sürüm bozulmadı."
    exit 1
fi

# Kodun üstüne kopyala. Kullanıcı verisi (.venv/.env/photos/cache) zip'te YOK,
# dolayısıyla dokunulmaz. guncelle.sh'ı hariç tut (çalışırken üzerine yazma).
echo "📁 Uygulama kodu güncelleniyor..."
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude 'guncelle.sh' "$SRC/" .
else
    cp -R "$SRC/." .
fi
chmod +x run.sh guncelle.sh 2>/dev/null || true

echo "✅ Uygulama kodu güncellendi."
echo "   Şimdi ./run.sh ile başlatın (değişen bağımlılıklar otomatik kurulur)."
