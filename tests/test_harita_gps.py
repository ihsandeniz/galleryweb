"""Harita görünümü GPS'i gerçekten okuyor mu?

🐞 GEÇMİŞ (2026-08-15'te ölçüldü): `/api/images/map` **hiçbir zaman** tek bir
fotoğraf döndürmedi — iki bağımsız kırık üst üste binmişti ve ikisi de sessizdi:

  1. GPS'in tek kaynağı `pyexiv2`'ydi, o da hiçbir requirements dosyasında yok.
     `import pyexiv2` → ImportError → `except Exception: pass` → boş harita.
  2. pyexiv2 kurulsa bile bozuktu: o `'38/1 25/1 201/25'` biçiminde tek bir
     STRING döndürür, ayrıştırıcı ise `['38/1','25/1','201/25']` LİSTESİ
     bekliyordu → string üzerinde döngü karakterleri gezer → ValueError →
     yine sessizce yutulur.

Yani özellik README'de ve sitede tanıtılıyordu ama çalışmıyordu ve hata da
vermiyordu. Bu testler tam olarak o iki kırığı bekler: biri geri gelirse
kırmızı yanar.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gizlilik_fikstur import ENLEM, BOYLAM, uret  # noqa: E402

import main  # noqa: E402


# ── Ayrıştırıcı: ÜÇ biçimi de kabul etmeli ───────────────────────────────────

@pytest.mark.parametrize("dms, beklenen", [
    ("38/1 25/1 201/25",             38.4189),   # pyexiv2 — tek string (eskiden ÇÖKÜYORDU)
    (["38/1", "25/1", "201/25"],     38.4189),   # ayrılmış liste
    ((38.0, 25.0, 8.04),             38.4189),   # Pillow IFDRational / float üçlüsü
])
def test_dms_uc_bicimi_de_ayni_sonucu_verir(dms, beklenen):
    assert main._dms_to_decimal(dms, "N") == pytest.approx(beklenen, abs=1e-4)


def test_guney_ve_bati_negatif():
    assert main._dms_to_decimal("38/1 25/1 201/25", "S") == pytest.approx(-38.4189, abs=1e-4)
    assert main._dms_to_decimal("27/1 7/1 1083/25", "W") == pytest.approx(-27.1287, abs=1e-4)


@pytest.mark.parametrize("bozuk", ["", "38/1 25/1", "abc", None, ("38",), ["1/0", "2/1", "3/1"]])
def test_bozuk_girdi_coktumez(bozuk):
    """Eksik/bozuk EXIF fotoğrafı galeriyi düşürmemeli — None dönmeli."""
    assert main._dms_to_decimal(bozuk, "N") is None


# ── Uçtan uca: GPS'li fotoğraf haritada görünüyor mu ─────────────────────────

def test_gpsli_fotograf_harita_ucunda_gorunuyor(tmp_path):
    """Asıl regresyon testi: dosyadan uca kadar zincir çalışıyor mu.

    Bilinçli olarak `pyexiv2`'ye HİÇ dokunmuyor — self-host kullanıcısında o
    paket kurulu değildir ve özellik yine de çalışmak zorundadır.
    """
    from fastapi.testclient import TestClient

    klasor = tmp_path / "gps-galeri"
    uret(klasor)

    c = TestClient(main.app)
    assert c.post("/api/set-directory", json={"path": str(klasor)}).status_code == 200
    try:
        veri = c.get("/api/images/map").json()
    finally:
        c.post("/api/clear-directory")

    assert veri["total"] == 1, f"harita boş döndü — GPS okunmuyor: {veri}"
    pin = veri["images"][0]
    assert pin["path"].endswith("konumlu.jpg")
    assert pin["lat"] == pytest.approx(ENLEM, abs=1e-4)
    assert pin["lng"] == pytest.approx(BOYLAM, abs=1e-4)


def test_gpssiz_fotograf_haritaya_girmiyor(tmp_path):
    """Koordinatı olmayan fotoğraf pin üretmemeli (uydurma konum yok)."""
    from fastapi.testclient import TestClient
    from PIL import Image

    klasor = tmp_path / "gpssiz"
    klasor.mkdir()
    Image.new("RGB", (64, 48), (200, 60, 60)).save(klasor / "konumsuz.jpg")

    c = TestClient(main.app)
    assert c.post("/api/set-directory", json={"path": str(klasor)}).status_code == 200
    try:
        veri = c.get("/api/images/map").json()
    finally:
        c.post("/api/clear-directory")

    assert veri["total"] == 0, f"koordinatsız fotoğraf haritaya girdi: {veri}"
