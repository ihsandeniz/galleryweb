"""Uçtan uca galeri akışı — Windows CI'ın asıl değeri burada.

Bu testler platforma özel değil; ama `windows-latest` üzerinde koştuklarında
"uygulama Windows'ta gerçekten çalışıyor mu" sorusunu CI'ya cevaplatırlar.
Kapsam: klasör seçme · listeleme · küçük resim · etiket · favori · puan ·
çöp kutusu · düzenleme zinciri (geri/ileri al) · geri alma (revert).
"""
import io

from PIL import Image

import main


def test_klasor_secme_ve_listeleme(istemci, galeri):
    d = istemci.get("/api/current-directory").json()
    assert d["path"] == str(galeri.resolve())

    r = istemci.get("/api/images")
    assert r.status_code == 200, r.text
    assert "deneme.jpg" in r.json()["images"]


def test_kucuk_resim_uretiliyor(istemci):
    r = istemci.get("/api/image/deneme.jpg?thumb=true&w=200")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("image/")
    Image.open(io.BytesIO(r.content)).verify()


def test_turkce_ve_bosluklu_dosya_adi(istemci, galeri):
    """Windows'ta kodlama/URL kaçışı burada patlıyordu."""
    ad = "İstanbul Boğazı çekimi.jpg"
    Image.new("RGB", (32, 32), (10, 200, 120)).save(galeri / ad)

    liste = istemci.get("/api/images").json()["images"]
    assert ad in liste

    r = istemci.get(f"/api/image/{ad}?thumb=true")
    assert r.status_code == 200, r.text


def test_etiket_favori_puan_dongusu(istemci):
    assert istemci.post("/api/tag/deneme.jpg", json={"tag": "gün batımı"}).status_code == 200
    assert "gün batımı" in istemci.get("/api/tags/deneme.jpg").json()["tags"]

    assert istemci.post("/api/favorite/deneme.jpg").status_code == 200
    assert any(f.endswith("deneme.jpg") for f in istemci.get("/api/favorites").json()["favorites"])

    assert istemci.post("/api/rating/deneme.jpg", json={"stars": 4}).status_code == 200
    puanlar = istemci.get("/api/ratings").json()["ratings"]
    assert any(v == 4 for v in puanlar.values()), puanlar


def test_cop_kutusu_sil_ve_geri_yukle(istemci, galeri):
    r = istemci.delete("/api/image/deneme.jpg")
    assert r.status_code == 200, r.text
    cop_id = r.json()["trash_id"]
    assert not (galeri / "deneme.jpg").exists()

    kutu = istemci.get("/api/trash").json()["items"]
    assert any(i["id"] == cop_id for i in kutu), kutu

    assert istemci.post(f"/api/restore/{cop_id}").status_code == 200
    assert (galeri / "deneme.jpg").exists()


def test_duzenleme_zinciri_geri_ve_ileri_al(istemci, galeri):
    foto = galeri / "deneme.jpg"
    once = Image.open(foto).size

    r = istemci.post("/api/edit/deneme.jpg", json={"operation": "rotate",
                                                   "params": {"degrees": 90}})
    assert r.status_code == 200, r.text
    assert r.json()["can_undo"] is True
    assert Image.open(foto).size == (once[1], once[0])

    r = istemci.post("/api/edit/deneme.jpg/undo")
    assert r.status_code == 200, r.text
    assert Image.open(foto).size == once

    r = istemci.post("/api/edit/deneme.jpg/redo")
    assert r.status_code == 200, r.text
    assert Image.open(foto).size == (once[1], once[0])


def test_revert_orijinale_doner(istemci, galeri):
    foto = galeri / "deneme.jpg"
    once = Image.open(foto).size

    istemci.post("/api/edit/deneme.jpg", json={"operation": "filter",
                                               "params": {"preset": "grayscale"}})
    r = istemci.post("/api/edit/deneme.jpg/revert")
    assert r.status_code == 200, r.text
    assert r.json()["reverted"] is True
    assert Image.open(foto).size == once
    assert istemci.get("/api/edit/deneme.jpg/history").json()["ops"] == []


def test_veri_dizini_gecici_yere_yonlendi():
    """Testler geliştirme önbelleğini kirletmemeli (conftest güvencesi)."""
    assert "gw-test-" in str(main.CACHE_DIR)
