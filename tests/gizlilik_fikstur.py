#!/usr/bin/env python3
"""Test fikstürü: GPS EXIF'li fotoğraf klasörü üretir.

    python tests/gizlilik_fikstur.py <hedef-klasor>

Neden GPS şart: harita görünümü ve gizlilik sızıntı testi koordinatsız fotoğrafla
hiçbir şey ölçmez — harita boş açılır, testler "sorun yok" der ve **yeşile boşa
yanarlar**.

Neden EXIF'i elle kuruyoruz (Pillow'un `Image.Exif` API'si yerine):
    Pillow 9.4 (Debian 12'nin sistem paketi) GPS IFD'sini **sessizce yazmıyor** —
    hata vermiyor, dosyayı kaydediyor, GPS içinde yok. 2026-08-15'te CI'da tam
    olarak bu oldu: paket doğrulaması `debian:12` kabında koşuyor, fikstür orada
    koordinatsız fotoğraf üretti ve "harita bozuk" gibi göründü. Ürün sağlamdı,
    fikstür bozuktu. Elle kurulan EXIF her Pillow sürümünde aynı davranır.

Bu dosya kendi çıktısını **geri okuyup doğrular**; GPS okunamıyorsa sessizce
geçmek yerine `RuntimeError` fırlatır.
"""
import struct
import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image

# İzmir Saat Kulesi civarı — gerçek bir koordinat olması yeterli, hassasiyet önemsiz.
ENLEM = 38.4189
BOYLAM = 27.1287


def _dms_rational(derece_ondalik: float):
    """Ondalık dereceyi EXIF RATIONAL üçlüsüne çevirir: ((pay, payda), ...)."""
    derece_ondalik = abs(derece_ondalik)
    d = int(derece_ondalik)
    dakika_ondalik = (derece_ondalik - d) * 60
    m = int(dakika_ondalik)
    sn = Fraction(dakika_ondalik - m).limit_denominator(100) * 60
    return ((d, 1), (m, 1), (sn.numerator, sn.denominator))


def _exif_app1(enlem: float, boylam: float) -> bytes:
    """GPS IFD'si taşıyan minimal bir EXIF APP1 bloğu üretir (big-endian TIFF).

    Yerleşim (ofsetler TIFF başlığının başına göredir):
        0   TIFF başlığı           8 bayt
        8   IFD0 (1 girdi: GPSTag) 18 bayt
        26  GPS IFD (4 girdi)      54 bayt
        80  enlem rationalleri     24 bayt
        104 boylam rationalleri    24 bayt
    """
    GPS_IFD, ENLEM_VERI, BOYLAM_VERI = 26, 80, 104

    tiff = struct.pack(">2sHI", b"MM", 42, 8)

    # IFD0: yalnızca GPS IFD'sine işaret eder
    ifd0 = struct.pack(">H", 1)
    ifd0 += struct.pack(">HHII", 0x8825, 4, 1, GPS_IFD)   # GPSTag → LONG
    ifd0 += struct.pack(">I", 0)                          # sonraki IFD yok

    def ascii_girdi(tag, harf):
        # 2 bayta sığdığı için değer alanına GÖMÜLÜR (offset değil)
        return struct.pack(">HHI", tag, 2, 2) + harf.encode() + b"\x00\x00\x00"

    gps = struct.pack(">H", 4)
    gps += ascii_girdi(1, "N" if enlem >= 0 else "S")
    gps += struct.pack(">HHII", 2, 5, 3, ENLEM_VERI)      # GPSLatitude → RATIONAL×3
    gps += ascii_girdi(3, "E" if boylam >= 0 else "W")
    gps += struct.pack(">HHII", 4, 5, 3, BOYLAM_VERI)     # GPSLongitude → RATIONAL×3
    gps += struct.pack(">I", 0)

    veri = b"".join(struct.pack(">II", p, q) for p, q in _dms_rational(enlem))
    veri += b"".join(struct.pack(">II", p, q) for p, q in _dms_rational(boylam))

    govde = b"Exif\x00\x00" + tiff + ifd0 + gps + veri
    return b"\xff\xe1" + struct.pack(">H", len(govde) + 2) + govde


def _gpsli_jpeg_yaz(hedef: Path, renk, enlem: float, boylam: float) -> None:
    """JPEG'i kaydeder, sonra APP1'i SOI'nin hemen ardına ekler."""
    from io import BytesIO

    tampon = BytesIO()
    Image.new("RGB", (320, 240), renk).save(tampon, "JPEG", quality=85)
    ham = tampon.getvalue()
    assert ham[:2] == b"\xff\xd8", "beklenmeyen JPEG başlığı"
    hedef.write_bytes(ham[:2] + _exif_app1(enlem, boylam) + ham[2:])


def _dogrula(yol: Path) -> None:
    """Yazdığımız GPS gerçekten geri okunuyor mu? Okunmuyorsa SUS-MA."""
    gps = Image.open(yol).getexif().get_ifd(0x8825)
    if not gps or 2 not in gps or 4 not in gps:
        raise RuntimeError(
            f"GPS EXIF yazılamadı: {yol} (Pillow {getattr(__import__('PIL'), '__version__', '?')}). "
            "Fikstür sessizce koordinatsız fotoğraf üretmemeli — testler boşa yeşil yanar."
        )


def uret(hedef: Path) -> None:
    hedef.mkdir(parents=True, exist_ok=True)

    konumlu = hedef / "konumlu.jpg"
    _gpsli_jpeg_yaz(konumlu, (40, 90, 140), ENLEM, BOYLAM)
    _dogrula(konumlu)

    # Türkçe karakterli ad da bilinçli: dosya adı kodlaması bu projede birden çok
    # kez hata kaynağı oldu (Windows konsolu, SQL LIKE desenleri).
    Image.new("RGB", (320, 240), (140, 90, 40)).save(hedef / "İzmir Kordon.jpg", "JPEG")

    print(f"✓ fikstür hazır: {hedef} (2 fotoğraf, biri GPS EXIF'li — geri okunarak doğrulandı)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    uret(Path(sys.argv[1]))
