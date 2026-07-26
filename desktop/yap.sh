#!/usr/bin/env bash
# GalleryWeb masaüstü paketi — tek komutla derleme.
#
#   ./yap.sh            → sunucu binary'si + Tauri uygulaması (release paketleri)
#   ./yap.sh sunucu     → sadece PyInstaller sunucu binary'si
#   ./yap.sh calistir   → geliştirme: sunucuyu derle + uygulamayı çalıştır
#
# Gereksinimler: Python 3.10–3.13, Rust (cargo), cargo-tauri, sistem webkit2gtk.
set -euo pipefail

DESKTOP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$DESKTOP_DIR")"
BUILD_VENV="$REPO_DIR/.build-venv"
SERVER_BIN="$DESKTOP_DIR/dist/galleryweb-server"

renk() { printf '\033[1;36m%s\033[0m\n' "$*"; }
hata() { printf '\033[1;31mHATA: %s\033[0m\n' "$*" >&2; exit 1; }

python_bul() {
    for cmd in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$cmd" >/dev/null 2>&1; then
            # 3.14+ bazı bağımlılıklarda kaynak derleme gerektiriyor → atla
            if "$cmd" -c 'import sys; sys.exit(0 if (3,10) <= sys.version_info < (3,14) else 1)' 2>/dev/null; then
                echo "$cmd"; return 0
            fi
        fi
    done
    return 1
}

venv_hazirla() {
    if [[ ! -x "$BUILD_VENV/bin/pyinstaller" ]]; then
        local py
        py="$(python_bul)" || hata "Uygun Python bulunamadı (3.10–3.13 gerekli)."
        renk "▸ Derleme ortamı kuruluyor ($py)…"
        "$py" -m venv "$BUILD_VENV"
        "$BUILD_VENV/bin/pip" -q install --upgrade pip
        "$BUILD_VENV/bin/pip" -q install -r "$REPO_DIR/backend/requirements-selfhost.txt"
        "$BUILD_VENV/bin/pip" -q install pyinstaller
    fi
}

sunucu_yap() {
    venv_hazirla
    renk "▸ Sunucu binary'si paketleniyor (PyInstaller)…"
    ( cd "$DESKTOP_DIR" && "$BUILD_VENV/bin/pyinstaller" galleryweb-server.spec \
        --noconfirm --distpath dist --workpath build --log-level WARN )
    [[ -x "$SERVER_BIN" ]] || hata "Sunucu binary'si üretilemedi."
    renk "  ✓ $SERVER_BIN ($(du -h "$SERVER_BIN" | cut -f1))"
}

uygulama_yap() {
    command -v cargo >/dev/null || hata "Rust (cargo) kurulu değil → https://rustup.rs"
    command -v cargo-tauri >/dev/null || hata "cargo-tauri yok → cargo install tauri-cli --version '^2.0'"
    renk "▸ Masaüstü uygulaması derleniyor (Tauri)…"
    # NO_STRIP: linuxdeploy'un içindeki eski `strip`, modern dağıtımların
    # `.relr.dyn` bölümlü kütüphanelerini tanımıyor ve AppImage adımı çöküyor
    # (Arch'ta doğrulandı). Strip'i atlamak yalnızca paket boyutunu etkiler.
    ( cd "$DESKTOP_DIR/src-tauri" && NO_STRIP=true cargo tauri build )
    renk "  ✓ Paketler: $DESKTOP_DIR/src-tauri/target/release/bundle/"
}

case "${1:-hepsi}" in
    sunucu)   sunucu_yap ;;
    calistir) sunucu_yap; ( cd "$DESKTOP_DIR/src-tauri" && cargo run ) ;;
    hepsi)    sunucu_yap; uygulama_yap ;;
    *)        hata "Bilinmeyen komut: $1 (sunucu | calistir | hepsi)" ;;
esac
