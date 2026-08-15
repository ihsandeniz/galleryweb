#!/usr/bin/env bash
# Linux paketlerini (deb + AppImage) ESKİ glibc'li bir kapta gerçekten kurup
# çalıştırarak doğrular.
#
#   tests/linux_paket_dogrula.sh <bundle-dizini>
#   tests/linux_paket_dogrula.sh desktop/src-tauri/target/release/bundle
#
# NEDEN VAR: v1.1.0'da AppImage yayınlanamadı. Paket ihsan'ın Arch makinesinde
# derlendiği için gömülü kütüphaneler `GLIBC_2.43` istiyordu; Debian 13 ve
# Ubuntu 24.04 dahil hiçbir LTS'te açılmıyordu. deb'in kusuru daha sinsiydi:
# `Depends:` satırında libc6 alt sınırı beyan edilmemişti → apt sorunsuz kurar,
# uygulama sonra başlamaz. İkisi de "derleme başarılı" diyen yeşil bir CI ile
# yan yana yaşayabilir. Bu betik satılan artefaktı hedef kabın içinde açar.
#
# NE ÖLÇER (hepsi kanıt):
#   • deb apt ile GERÇEKTEN kuruluyor mu           (Depends çözülüyor mu)
#   • kurulan GUI ikilisinin bağımlılıkları çözülüyor mu   (ldd, "not found" yok)
#   • paketlenmiş sunucu ikilisi kabın içinde AYAĞA KALKIYOR mu (duman testi)
#   • AppImage'ın GÖMÜLÜ kütüphaneleri AppRun'ın yükleme sırasıyla çözülüyor mu
#   • tüm ELF'lerin istediği en yüksek GLIBC sürümü taban sınırın altında mı
#
# NE ÖLÇMEZ (dürüstlük payı): GUI penceresi açılmaz — kapta ekran sunucusu ve
# GPU yok. WebKit'in çalışma anındaki davranışı burada sınanmaz; sınanan şey
# bağımlılıkların çözülmesi ve sunucu katmanının koşmasıdır.
set -euo pipefail

# Hedef kap: paketin açılmasını vaat ettiğimiz EN ESKİ dağıtım.
# debian:12 (bookworm) = glibc 2.36. Ubuntu 22.04 = 2.35, ondan da eski değil.
KAP_IMAJ="${KAP_IMAJ:-debian:12}"
# Paketleri 22.04 üzerinde derliyoruz → beklenen taban 2.35.
# Bu sayı büyürse paket eski dağıtımlarda ölür; o yüzden sınır burada.
GLIBC_TABANI="${GLIBC_TABANI:-2.35}"

renk() { printf '\033[1;36m%s\033[0m\n' "$*"; }
hata() { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }
tamam() { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }

# ─────────────────────────────────────────────────────────────────────────────
# KAP İÇİ — asıl ölçüm buradan aşağıda, hedef dağıtımın içinde koşar.
# ─────────────────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--kap-icinde" ]]; then
    export DEBIAN_FRONTEND=noninteractive
    export HOME=/tmp   # /kaynak salt-okunur bağlandı; testler HOME'a yazabilsin

    renk "▸ Kap: $(. /etc/os-release && echo "$PRETTY_NAME") · glibc $(ldd --version | head -1 | grep -oE '[0-9]+\.[0-9]+$')"

    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
        python3 python3-pil file binutils ca-certificates >/dev/null

    # ── 1. deb: apt ile kur (Depends gerçekten çözülüyor mu?) ────────────────
    DEB="$(find /paketler -name '*.deb' | head -1)"
    [[ -n "$DEB" ]] || hata "deb paketi bulunamadı"
    renk "▸ deb kuruluyor: $(basename "$DEB")"
    echo "  Depends: $(dpkg-deb -f "$DEB" Depends)"
    apt-get install -y -qq "$DEB" >/dev/null || hata "apt deb'i kuramadı — Depends çözülmedi"
    PKG="$(dpkg-deb -f "$DEB" Package)"
    tamam "deb kuruldu ($PKG)"

    # ── 2. Kurulan ikililerin bağımlılıkları çözülüyor mu? ───────────────────
    GUI="$(dpkg -L "$PKG" | grep -E '^/usr/bin/' | head -1)"
    [[ -x "$GUI" ]] || hata "GUI ikilisi kurulumda yok"
    EKSIK="$(ldd "$GUI" 2>&1 | grep -F 'not found' || true)"
    [[ -z "$EKSIK" ]] || hata "GUI ikilisinin bağımlılıkları ÇÖZÜLMEDİ:
$EKSIK"
    tamam "GUI ikilisi: $GUI — tüm bağımlılıklar çözüldü"

    # ── 3. Sunucu ikilisi kabın içinde GERÇEKTEN kalkıyor mu? ────────────────
    # Asıl kanıt bu. PyInstaller tek-dosya arşivi kütüphaneleri SIKIŞTIRILMIŞ
    # taşır; hiçbir ELF aracı içeriğini göremez (v1.1.0'da deb'in gerçek tabanı
    # arşivin içindeki libpython'daydı ve dışarıdan "2.14" görünüyordu).
    # Ölçmenin tek dürüst yolu çalıştırmaktır.
    SUNUCU="$(dpkg -L "$PKG" | grep -E '/galleryweb-server$' | head -1)"
    [[ -x "${SUNUCU:-}" ]] || hata "paketlenmiş sunucu ikilisi kurulumda yok"
    renk "▸ Duman testi (deb içindeki sunucu): $SUNUCU"
    python3 /kaynak/tests/paket_duman_testi.py "$SUNUCU" || hata "deb'deki sunucu kapta koşmadı"
    tamam "deb'deki sunucu $KAP_IMAJ içinde çalıştı"

    # ── 4. AppImage: gömülü kütüphaneler AppRun sırasıyla çözülüyor mu? ──────
    APPIMG="$(find /paketler -name '*.AppImage' | head -1)"
    if [[ -z "$APPIMG" ]]; then
        echo "⚠ AppImage üretilmemiş — atlanıyor"
    else
        cd /tmp
        cp "$APPIMG" /tmp/uygulama.AppImage && chmod +x /tmp/uygulama.AppImage
        # Kapta FUSE yok; AppImage'ın kendi çıkarma modu FUSE istemez.
        ./uygulama.AppImage --appimage-extract >/dev/null
        KOK=/tmp/squashfs-root
        # AppRun gömülü kütüphaneleri LD_LIBRARY_PATH'in BAŞINA koyar — yani
        # sistemdekiler değil, bunlar yüklenir. Ölçümü aynı sırayla yap.
        LIBDIZIN="$(find "$KOK/usr/lib" -maxdepth 2 -type d | tr '\n' ':')"
        BOZUK=""
        while IFS= read -r f; do
            file -b "$f" | grep -q '^ELF' || continue
            cikti="$(LD_LIBRARY_PATH="$LIBDIZIN" ldd "$f" 2>&1 || true)"
            if grep -qF 'not found' <<<"$cikti"; then
                BOZUK+="$f
$(grep -F 'not found' <<<"$cikti" | sed 's/^/    /')
"
            fi
        done < <(find "$KOK" -type f \( -perm -u+x -o -name '*.so*' \))
        [[ -z "$BOZUK" ]] || hata "AppImage'ın GÖMÜLÜ kütüphaneleri $KAP_IMAJ'de çözülmüyor:
$BOZUK"
        tamam "AppImage: gömülü kütüphanelerin tamamı çözüldü"

        SUNUCU_AI="$(find "$KOK" -type f -name 'galleryweb-server' | head -1)"
        if [[ -x "${SUNUCU_AI:-}" ]]; then
            renk "▸ Duman testi (AppImage içindeki sunucu)"
            DUMAN_PORT=5099 python3 /kaynak/tests/paket_duman_testi.py "$SUNUCU_AI" \
                || hata "AppImage'daki sunucu kapta koşmadı"
            tamam "AppImage'daki sunucu $KAP_IMAJ içinde çalıştı"
        else
            hata "AppImage içinde galleryweb-server yok — kaynak eşlemesi bozuk"
        fi
    fi

    # ── 5. En yüksek GLIBC talebi taban sınırın altında mı? ──────────────────
    # Süzgeç şart: zayıf (WEAK) tanımsız semboller yükleme hatası VERMEZ.
    # v1.1.0 ölçümünde objdump `GLIBC_2.39` gösterdi, iki sembol de WEAK'ti,
    # gerçek sayı 2.34'tü. readelf `Bind` sütununu yazdığı için ayırt edilebiliyor.
    ENYUKSEK="$(
        { dpkg -L "$PKG" | while IFS= read -r p; do [[ -f "$p" ]] && echo "$p"; done
          find /tmp/squashfs-root -type f 2>/dev/null; } |
        while IFS= read -r f; do
            file -b "$f" | grep -q '^ELF' || continue
            readelf -W --dyn-syms "$f" 2>/dev/null |
                awk '$5=="GLOBAL" && $7=="UND" {print $8}' |
                grep -oE 'GLIBC_[0-9]+\.[0-9]+' || true
        done | sort -u -t_ -k2 -V | tail -1
    )"
    ENYUKSEK="${ENYUKSEK#GLIBC_}"
    if [[ -n "$ENYUKSEK" ]]; then
        echo "  Ölçülen en yüksek glibc talebi (sıkıştırılmamış ELF'ler): $ENYUKSEK · sınır: $GLIBC_TABANI"
        if [[ "$(printf '%s\n%s\n' "$GLIBC_TABANI" "$ENYUKSEK" | sort -V | tail -1)" != "$GLIBC_TABANI" ]]; then
            hata "glibc tabanı aşıldı: paket $ENYUKSEK istiyor, sınır $GLIBC_TABANI.
       Muhtemel sebep: paket daha yeni bir dağıtımda derlendi (CI runner'ı mı değişti?)."
        fi
        tamam "glibc tabanı korunuyor (≤ $GLIBC_TABANI)"
    fi

    renk "▸ Tüm Linux paket doğrulamaları geçti."
    exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# HOST — kabı ayağa kaldırır.
# ─────────────────────────────────────────────────────────────────────────────
BUNDLE="${1:-desktop/src-tauri/target/release/bundle}"
[[ -d "$BUNDLE" ]] || hata "bundle dizini yok: $BUNDLE"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE="$(cd "$BUNDLE" && pwd)"

command -v docker >/dev/null || hata "docker gerekli (paketi hedef dağıtımda sınıyoruz)"

renk "▸ Paketler $KAP_IMAJ kabında sınanıyor: $BUNDLE"
docker run --rm \
    -v "$REPO:/kaynak:ro" \
    -v "$BUNDLE:/paketler:ro" \
    -e "KAP_IMAJ=$KAP_IMAJ" \
    -e "GLIBC_TABANI=$GLIBC_TABANI" \
    "$KAP_IMAJ" bash /kaynak/tests/linux_paket_dogrula.sh --kap-icinde
