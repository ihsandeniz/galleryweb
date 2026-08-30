"""Toplu işlemler — dosya SİLEN, TAŞIYAN ve KOPYALAYAN uçlar.

Neden bu dosya var (2026-08-30): `/api/batch/delete`, `/api/batch/move` ve
`/api/batch/copy` uçlarının hiç testi yoktu. Harita görünümü tam olarak böyle bir
boşlukta üç sürüm boyunca ölü kaldı — ama o *yanlış sonuç* veriyordu, bunlar
*dosya kaybettirebilir*. Buradaki testlerin çoğu "çalışıyor mu"yu değil
**"üzerine yazıyor mu / veri düşürüyor mu"**yu ölçer.

Kapsam: toplu silme (kısmi başarı dahil) · kopyalama (kaynak korunuyor mu,
çakışmada üzerine yazıyor mu) · taşıma (metadata taşınıyor mu, hedef=kaynak
reddi) · ZIP dışa aktarma.
"""
import io
import zipfile

from PIL import Image

import main


def _foto(dizin, ad, renk=(200, 40, 40), boyut=(32, 32)):
    """Test için gerçek bir JPEG üret ve yolunu döndür."""
    p = dizin / ad
    Image.new("RGB", boyut, renk).save(p, quality=90)
    return p


# ── Toplu silme ────────────────────────────────────────────────────────────

def test_toplu_silme_cope_atar_ve_geri_yuklenebilir(istemci, galeri):
    _foto(galeri, "a.jpg")
    _foto(galeri, "b.jpg", (40, 200, 40))

    r = istemci.post("/api/batch/delete", json={"paths": ["a.jpg", "b.jpg"]})
    assert r.status_code == 200, r.text
    veri = r.json()
    assert veri["count"] == 2, veri
    assert veri["errors"] == []
    assert not (galeri / "a.jpg").exists()
    assert not (galeri / "b.jpg").exists()

    # Çöp kutusundan geri yükleme gerçekten dosyayı geri getirmeli
    cop_id = veri["deleted"][0]["trash_id"]
    assert istemci.post(f"/api/restore/{cop_id}").status_code == 200
    assert (galeri / "a.jpg").exists()


def test_toplu_silme_olmayan_dosyayi_atlar_digerini_siler(istemci, galeri):
    """Kısmi başarı: bir dosya yoksa işlem TAMAMEN durmamalı, ama sessiz de kalmamalı."""
    _foto(galeri, "var.jpg")

    r = istemci.post("/api/batch/delete", json={"paths": ["var.jpg", "yok.jpg"]})
    assert r.status_code == 200, r.text
    veri = r.json()

    assert veri["count"] == 1, veri
    assert not (galeri / "var.jpg").exists()
    assert len(veri["errors"]) == 1, veri
    assert veri["errors"][0]["path"] == "yok.jpg"


# ── Toplu kopyalama ────────────────────────────────────────────────────────

def test_toplu_kopyalama_kaynagi_yerinde_birakir(istemci, galeri, tmp_path):
    _foto(galeri, "k.jpg")
    hedef = tmp_path / "hedef"
    hedef.mkdir()

    r = istemci.post("/api/batch/copy", json={"paths": ["k.jpg"],
                                              "destination": str(hedef)})
    assert r.status_code == 200, r.text
    assert r.json()["success_count"] == 1, r.text

    assert (hedef / "k.jpg").exists(), "kopya hedefte yok"
    assert (galeri / "k.jpg").exists(), "kopyalama kaynağı silmiş — bu kopyalama değil taşıma"


def test_toplu_kopyalama_ayni_isimde_uzerine_YAZMAZ(istemci, galeri, tmp_path):
    """Hedefte aynı adlı dosya varsa içeriği KORUNMALI, yeni dosya ek adla gitmeli."""
    _foto(galeri, "c.jpg", (10, 10, 200), boyut=(64, 64))
    hedef = tmp_path / "hedef"
    hedef.mkdir()
    mevcut = _foto(hedef, "c.jpg", (200, 200, 10), boyut=(16, 16))
    mevcut_boyut = Image.open(mevcut).size

    r = istemci.post("/api/batch/copy", json={"paths": ["c.jpg"],
                                              "destination": str(hedef)})
    assert r.status_code == 200, r.text
    assert r.json()["success_count"] == 1

    # Eski dosya dokunulmamış olmalı
    assert Image.open(hedef / "c.jpg").size == mevcut_boyut, "mevcut dosyanın üzerine yazıldı"
    # Yeni dosya ayrı adla durmalı
    kopyalar = [p.name for p in hedef.iterdir() if p.name != "c.jpg"]
    assert kopyalar, f"kopya ayrı adla yazılmadı: {list(hedef.iterdir())}"


# ── Toplu taşıma ───────────────────────────────────────────────────────────

def test_toplu_tasima_dosyayi_ve_etiketini_birlikte_tasir(istemci, galeri, tmp_path):
    """Taşınan dosyanın etiketi kaybolmamalı (`move_metadata`)."""
    kaynak = _foto(galeri, "t.jpg")
    hedef = tmp_path / "hedef"
    hedef.mkdir()

    assert istemci.post("/api/tag/t.jpg", json={"tag": "deniz"}).status_code == 200
    assert "deniz" in main.cache_manager.get_image_tags(str(kaynak))

    r = istemci.post("/api/batch/move", json={"paths": ["t.jpg"],
                                              "destination": str(hedef)})
    assert r.status_code == 200, r.text
    assert r.json()["success_count"] == 1, r.text

    assert not (galeri / "t.jpg").exists(), "taşıma kaynağı bırakmış — bu kopyalama"
    assert (hedef / "t.jpg").exists()
    assert "deniz" in main.cache_manager.get_image_tags(str(hedef / "t.jpg")), \
        "etiket taşınmadı — kullanıcı dosyayı taşıyınca etiketleri sessizce kaybediyor"


def test_toplu_tasima_hedef_kaynakla_ayniysa_reddedilir(istemci, galeri):
    _foto(galeri, "m.jpg")
    r = istemci.post("/api/batch/move", json={"paths": ["m.jpg"],
                                              "destination": str(galeri)})
    assert r.status_code == 400, r.text
    assert (galeri / "m.jpg").exists(), "reddedilen istek yine de dosyaya dokunmuş"


def test_toplu_tasima_ayni_isimde_uzerine_YAZMAZ(istemci, galeri, tmp_path):
    _foto(galeri, "d.jpg", (10, 10, 200), boyut=(64, 64))
    hedef = tmp_path / "hedef"
    hedef.mkdir()
    mevcut = _foto(hedef, "d.jpg", (200, 200, 10), boyut=(16, 16))
    mevcut_boyut = Image.open(mevcut).size

    r = istemci.post("/api/batch/move", json={"paths": ["d.jpg"],
                                              "destination": str(hedef)})
    assert r.status_code == 200, r.text
    assert r.json()["success_count"] == 1

    assert Image.open(hedef / "d.jpg").size == mevcut_boyut, "mevcut dosyanın üzerine yazıldı"
    assert len(list(hedef.iterdir())) == 2, f"taşınan dosya ayrı adla yazılmadı: {list(hedef.iterdir())}"


def test_hedef_klasor_yoksa_reddedilir(istemci, galeri, tmp_path):
    _foto(galeri, "y.jpg")
    yok = tmp_path / "olmayan-klasor"

    for uc in ("/api/batch/copy", "/api/batch/move"):
        r = istemci.post(uc, json={"paths": ["y.jpg"], "destination": str(yok)})
        assert r.status_code == 400, f"{uc} → {r.status_code}: {r.text}"
    assert (galeri / "y.jpg").exists()


# ── ZIP dışa aktarma ───────────────────────────────────────────────────────

def test_disa_aktarma_gecerli_zip_uretir(istemci, galeri):
    _foto(galeri, "z1.jpg")
    _foto(galeri, "z2.jpg", (40, 40, 200))

    r = istemci.post("/api/export", json={"paths": ["z1.jpg", "z2.jpg"]})
    assert r.status_code == 200, r.text

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert z.testzip() is None, "bozuk ZIP"
        adlar = z.namelist()
    assert any(a.endswith("z1.jpg") for a in adlar), adlar
    assert any(a.endswith("z2.jpg") for a in adlar), adlar


def test_disa_aktarma_bos_liste_reddedilir(istemci):
    r = istemci.post("/api/export", json={"paths": []})
    assert r.status_code == 400, r.text
