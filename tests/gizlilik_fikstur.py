#!/usr/bin/env python3
"""Gizlilik sızıntı testi için GPS EXIF'li fotoğraf klasörü üretir.

    python tests/gizlilik_fikstur.py <hedef-klasor>

Neden GPS şart: sızıntının asıl olduğu yer harita görünümüydü — altlık
döşemeleri istenirken fotoğrafların **çekildiği yer** OpenStreetMap'e
bildiriliyordu (fotoğrafın kendisi gitmiyordu, koordinat ima ediliyordu).
Koordinatsız bir fotoğrafla harita boş açılır ve test hiçbir şey ölçmeden
"sıfır dış istek" der — yani yeşil yanar ama kanıt üretmez.
"""
import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image

# İzmir Saat Kulesi civarı — gerçek bir koordinat olması yeterli, hassas değil.
ENLEM = 38.4189
BOYLAM = 27.1287


def _dms(derece_ondalik: float):
    """Ondalık dereceyi EXIF'in beklediği (derece, dakika, saniye) üçlüsüne çevirir.

    Pillow'un modern `Image.Exif` API'si rasyonelleri `Fraction` olarak ister;
    `(pay, payda)` tuple'ı verirsen kaydetme `TypeError: bad operand type for
    abs(): 'tuple'` ile düşer (ölçüldü).
    """
    derece_ondalik = abs(derece_ondalik)
    d = int(derece_ondalik)
    dakika_ondalik = (derece_ondalik - d) * 60
    m = int(dakika_ondalik)
    s = Fraction(dakika_ondalik - m).limit_denominator(10000) * 60
    return (Fraction(d), Fraction(m), s)


def uret(hedef: Path) -> None:
    hedef.mkdir(parents=True, exist_ok=True)

    exif = Image.Exif()
    exif.get_ifd(0x8825).update({
        1: "N", 2: _dms(ENLEM),      # GPSLatitudeRef / GPSLatitude
        3: "E", 4: _dms(BOYLAM),     # GPSLongitudeRef / GPSLongitude
    })

    Image.new("RGB", (640, 480), (40, 90, 140)).save(
        hedef / "konumlu.jpg", "JPEG", exif=exif
    )
    # Türkçe karakterli ad da bilinçli: dosya adı kodlaması bu projede birden
    # çok kez hata kaynağı oldu (Windows konsolu, LIKE desenleri).
    Image.new("RGB", (640, 480), (140, 90, 40)).save(
        hedef / "İzmir Kordon.jpg", "JPEG"
    )
    print(f"✓ fikstür hazır: {hedef} (2 fotoğraf, biri GPS EXIF'li)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    uret(Path(sys.argv[1]))
