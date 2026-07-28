#!/usr/bin/env python3
"""Paketlenmiş sunucu binary'sini GERÇEKTEN çalıştırıp sınayan duman testi.

    python tests/paket_duman_testi.py <sunucu-binary-yolu>

Neden ayrı bir betik: `pytest` kaynak koda karşı koşar ve PyInstaller'ın
paketleme hatalarını (eksik gizli import, gömülmemiş frontend varlığı, yanlış
veri dizini) GÖRMEZ. Yuki v0.5.0 dersi tam buydu — kaynak yeşil, satılan
artefakt bozuktu. Bu betik satılan artefaktın kendisini açar.

Sınadıkları:
  • süreç ayağa kalkıyor ve porta bağlanıyor       (bootloader + bağımlılıklar)
  • ana sayfa + statik varlıklar geliyor           (frontend gömülmüş mü)
  • klasör seçilebiliyor, fotoğraf listeleniyor    (dosya sistemi erişimi)
  • küçük resim üretiliyor                         (Pillow + yazılabilir cache)
  • /api/network yanıt veriyor                     (güvenlik duvarı tespiti çökmüyor)
  • stdin kapanınca süreç kendini kapatıyor        (öksüz süreç bırakmıyor)
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PORT = int(os.getenv("DUMAN_PORT", "5098"))
KOK = f"http://127.0.0.1:{PORT}"


def yaz(m):
    print(m, flush=True)


def istek(yol, veri=None, yontem=None):
    url = KOK + yol
    gövde = json.dumps(veri).encode() if veri is not None else None
    r = urllib.request.Request(url, data=gövde, method=yontem or ("POST" if veri else "GET"))
    if veri is not None:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=20) as y:
        return y.status, y.read()


def bekle(saniye=90):
    son = None
    bitis = time.time() + saniye
    while time.time() < bitis:
        try:
            kod, _ = istek("/")
            if kod == 200:
                return True
        except (urllib.error.URLError, OSError, ConnectionError) as e:
            son = e
        time.sleep(0.5)
    yaz(f"  son hata: {son}")
    return False


def main() -> int:
    if len(sys.argv) < 2:
        yaz("Kullanım: paket_duman_testi.py <sunucu-binary-yolu>")
        return 2
    binary = Path(sys.argv[1]).resolve()
    if not binary.is_file():
        yaz(f"HATA: binary yok: {binary}")
        return 2

    from PIL import Image

    galeri = Path(tempfile.mkdtemp(prefix="gw-duman-"))
    veri = Path(tempfile.mkdtemp(prefix="gw-duman-veri-"))
    Image.new("RGB", (80, 60), (20, 120, 180)).save(galeri / "deneme.jpg")
    # Windows'ta kodlama/URL kaçışı en çok burada patlıyor
    Image.new("RGB", (40, 40), (200, 80, 20)).save(galeri / "İstanbul Boğazı.jpg")

    ortam = {**os.environ, "PORT": str(PORT), "GALLERYWEB_DATA_DIR": str(veri),
             "GALLERYWEB_DESKTOP": "1"}
    yaz(f"▸ Sunucu başlatılıyor: {binary}")
    # Sunucuyu KENDİ süreç grubunda başlat — masaüstü kabuğunun yaptığının aynısı
    # (Rust tarafında `cmd.process_group(0)`). Bu olmadan sunucunun kapanış
    # temizliği (`os.killpg`) bu test betiğini de öldürüyor ve test "sessizce"
    # yarıda kalıyor: çıktı kesiliyor, sonuç satırı hiç basılmıyor.
    ek = {} if os.name == "nt" else {"start_new_session": True}
    surec = subprocess.Popen([str(binary)], env=ortam, stdin=subprocess.PIPE, **ek)

    hatalar = []
    try:
        if not bekle():
            yaz("✗ Sunucu 90 saniyede ayağa kalkmadı")
            return 1
        yaz("✓ sunucu ayakta")

        kod, gövde = istek("/")
        if kod != 200 or b"<html" not in gövde.lower():
            hatalar.append("ana sayfa HTML dönmedi")
        else:
            yaz("✓ ana sayfa")

        for varlik in ("/static/js/gallery.js", "/static/css/style.css"):
            try:
                kod, gövde = istek(varlik)
                if kod != 200 or not gövde:
                    hatalar.append(f"{varlik} boş/hatalı")
                else:
                    yaz(f"✓ {varlik} ({len(gövde)} bayt)")
            except Exception as e:
                hatalar.append(f"{varlik}: {e}")

        kod, _ = istek("/api/set-directory", {"path": str(galeri)})
        yaz("✓ klasör seçildi")

        kod, gövde = istek("/api/images")
        liste = json.loads(gövde)["images"]
        if "deneme.jpg" not in liste or "İstanbul Boğazı.jpg" not in liste:
            hatalar.append(f"listeleme eksik: {liste}")
        else:
            yaz(f"✓ listeleme ({len(liste)} dosya, Türkçe ad dahil)")

        for ad in ("deneme.jpg", "İstanbul Boğazı.jpg"):
            kod, gövde = istek("/api/image/" + urllib.parse.quote(ad) + "?thumb=true&w=200")
            # Bayt sayısına BAKMA: düz renkli bir görselin WebP'si 96 bayta kadar
            # inebiliyor ve "küçük dosya = bozuk" varsayımı yanlış alarm veriyor.
            # Ölçüt, çıktının gerçekten açılabilir bir görüntü olmasıdır.
            try:
                import io
                Image.open(io.BytesIO(gövde)).verify()
                yaz(f"✓ küçük resim: {ad} ({len(gövde)} bayt)")
            except Exception as e:
                hatalar.append(f"küçük resim geçersiz ({ad}): {e}")

        kod, gövde = istek("/api/network")
        ag = json.loads(gövde)
        if "guvenlik_duvari" not in ag:
            hatalar.append("/api/network güvenlik duvarı alanı yok")
        else:
            yaz(f"✓ /api/network (güvenlik duvarı: {ag['guvenlik_duvari'].get('aktif')})")

        # Düzenleme zinciri paketli binary'de de çalışmalı (Pillow + yazma izni)
        kod, gövde = istek("/api/edit/deneme.jpg", {"operation": "rotate",
                                                    "params": {"degrees": 90}})
        if kod != 200 or not json.loads(gövde).get("can_undo"):
            hatalar.append("düzenleme zinciri çalışmadı")
        else:
            yaz("✓ düzenleme zinciri")

        if not (veri / "cache").exists():
            hatalar.append(f"veri dizini kullanılmadı: {veri}")
        else:
            yaz("✓ veri dizini yazılabilir")

    finally:
        yaz("▸ stdin kapatılıyor (kabuk ölümü taklidi)")
        try:
            surec.stdin.close()
        except Exception:
            pass
        try:
            surec.wait(timeout=20)
            yaz("✓ süreç kendini kapattı (öksüz kalmadı)")
        except subprocess.TimeoutExpired:
            hatalar.append("stdin kapandığı hâlde süreç kapanmadı")
            surec.kill()

    if hatalar:
        yaz("\n✗ DUMAN TESTİ BAŞARISIZ:")
        for h in hatalar:
            yaz(f"   • {h}")
        return 1
    yaz("\n✓ Paket duman testi geçti")
    return 0


if __name__ == "__main__":
    sys.exit(main())
