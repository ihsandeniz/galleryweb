"""Ortak test kurulumu.

Bu dosya test modüllerinden ÖNCE içe aktarılır — `main.py` import edilir edilmez
önbellek dizinini yaratıp SQLite'ı açtığı için veri dizinini burada, her şeyden
önce geçici bir yere yönlendiriyoruz. Aksi hâlde testler geliştirme
veritabanını (etiketler, favoriler, çöp kutusu) kirletirdi.
"""
import os
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK / "backend"))

os.environ.setdefault("GALLERYWEB_DATA_DIR", tempfile.mkdtemp(prefix="gw-test-"))
os.environ.setdefault("PORT", "5099")

import pytest  # noqa: E402


@pytest.fixture
def galeri(tmp_path):
    """İçinde gerçek bir JPEG bulunan geçici galeri klasörü."""
    from PIL import Image

    d = tmp_path / "galeri"
    d.mkdir()
    Image.new("RGB", (64, 48), (30, 90, 140)).save(d / "deneme.jpg", quality=90)
    return d


@pytest.fixture
def istemci(galeri):
    """Galeri klasörü seçilmiş hâlde TestClient."""
    from fastapi.testclient import TestClient
    import main

    c = TestClient(main.app)
    r = c.post("/api/set-directory", json={"path": str(galeri)})
    assert r.status_code == 200, r.text
    yield c
    c.post("/api/clear-directory")
