"""Albümler ve kopya bulucu — testi hiç olmayan iki özellik.

Neden (2026-08-30): `/api/albums/*` (5 uç) ve `/api/duplicates` hiç test edilmiyordu.
Albüm, kullanıcının elle kurduğu tek veri yapısıdır — kaybolursa geri getirecek bir
kaynak yoktur (etiket/puan gibi dosyadan yeniden türetilemez).

Kapsam: albüm CRUD · aynı ad reddi · albüme foto ekleme/çıkarma · olmayan albüm 404 ·
kopya bulucunun aynı görselin iki kopyasını gruplaması.
"""
import random
import shutil

from PIL import Image


def _foto(dizin, ad, renk=(120, 60, 180), boyut=(48, 48)):
    p = dizin / ad
    Image.new("RGB", boyut, renk).save(p, quality=90)
    return p


def _gurultu(dizin, ad, seed, boyut=(96, 96)):
    """Detaylı (gerçek fotoğrafa benzer) görsel — phash'in anlamlı çalıştığı girdi.

    Aynı `seed` aynı görseli üretir; farklı seed algısal olarak uzak bir görsel verir.
    """
    r = random.Random(seed)
    im = Image.new("RGB", boyut)
    for x in range(boyut[0]):
        for y in range(boyut[1]):
            im.putpixel((x, y), (r.randrange(256), r.randrange(256), r.randrange(256)))
    p = dizin / ad
    im.save(p, quality=95)
    return p


# ── Albüm CRUD ─────────────────────────────────────────────────────────────

def test_album_olustur_listele_guncelle_sil(istemci):
    r = istemci.post("/api/albums", json={"name": "Tatil", "description": "yaz"})
    assert r.status_code == 200, r.text
    album_id = r.json()["id"]

    liste = istemci.get("/api/albums").json()["albums"]
    assert any(a["id"] == album_id for a in liste), liste

    assert istemci.get(f"/api/albums/{album_id}").status_code == 200

    r = istemci.put(f"/api/albums/{album_id}", json={"name": "Tatil 2026"})
    assert r.status_code == 200, r.text
    assert istemci.get(f"/api/albums/{album_id}").json()["name"] == "Tatil 2026"

    assert istemci.delete(f"/api/albums/{album_id}").status_code == 200
    assert istemci.get(f"/api/albums/{album_id}").status_code == 404


def test_ayni_isimde_ikinci_album_reddedilir(istemci):
    assert istemci.post("/api/albums", json={"name": "Benzersiz"}).status_code == 200
    r = istemci.post("/api/albums", json={"name": "Benzersiz"})
    assert r.status_code == 409, r.text


def test_adsiz_album_reddedilir(istemci):
    assert istemci.post("/api/albums", json={"name": "   "}).status_code == 400


def test_olmayan_album_uclari_404_doner(istemci):
    yok = 999999
    assert istemci.get(f"/api/albums/{yok}").status_code == 404
    assert istemci.put(f"/api/albums/{yok}", json={"name": "x"}).status_code == 404
    assert istemci.delete(f"/api/albums/{yok}").status_code == 404
    assert istemci.post(f"/api/albums/{yok}/images", json={"paths": ["deneme.jpg"]}).status_code == 404


# ── Albüm içeriği ──────────────────────────────────────────────────────────

def test_albume_foto_ekle_ve_cikar(istemci, galeri):
    _foto(galeri, "albumluk.jpg")
    album_id = istemci.post("/api/albums", json={"name": "Seçmeler"}).json()["id"]

    r = istemci.post(f"/api/albums/{album_id}/images", json={"paths": ["albumluk.jpg"]})
    assert r.status_code == 200, r.text
    assert r.json()["added"] == 1

    icerik = istemci.get(f"/api/albums/{album_id}").json()["images"]
    assert any(i.endswith("albumluk.jpg") for i in icerik), icerik

    r = istemci.delete(f"/api/albums/{album_id}/images/albumluk.jpg")
    assert r.status_code == 200, r.text
    assert istemci.get(f"/api/albums/{album_id}").json()["images"] == []


def test_albume_olmayan_dosya_eklenmez(istemci):
    """Var olmayan yol sessizce albüme yazılmamalı (hayalet kayıt)."""
    album_id = istemci.post("/api/albums", json={"name": "Hayalet"}).json()["id"]

    r = istemci.post(f"/api/albums/{album_id}/images", json={"paths": ["yok.jpg"]})
    assert r.status_code == 200, r.text
    assert r.json()["added"] == 0, r.text
    assert istemci.get(f"/api/albums/{album_id}").json()["images"] == []


# ── Kopya bulucu ───────────────────────────────────────────────────────────

def test_kopya_bulucu_ayni_fotografi_gruplar(istemci, galeri):
    """Birebir aynı iki dosya tek grupta buluşmalı."""
    asil = _foto(galeri, "asil.jpg", boyut=(96, 96))
    shutil.copy2(asil, galeri / "kopya.jpg")

    r = istemci.get("/api/duplicates")
    assert r.status_code == 200, r.text
    gruplar = r.json()["groups"]

    assert gruplar, "birebir aynı iki dosya kopya olarak bulunamadı"
    adlar = {p["path"] for g in gruplar for p in g}
    assert any(a.endswith("asil.jpg") for a in adlar), adlar
    assert any(a.endswith("kopya.jpg") for a in adlar), adlar


def test_kopya_bulucu_farkli_fotograflari_gruplamaz(istemci, galeri):
    """Yanlış pozitif kapısı: birbirinden farklı görseller kopya sayılmamalı.

    ⚠️ Bu test DETAYLI (gürültülü) görsel kullanır, düz renk DEĞİL — ve bu bilinçli.
    Kullanılan `phash` DCT tabanlıdır ve detaysız görselde dejenere olur:
    2026-08-30'da ölçüldü → düz siyah ↔ dama deseni mesafesi **1** (eşik 8 → "kopya"),
    ama gürültülü iki görsel arasında **28**. Yani düz renkli fikstürle yazılan bir
    yanlış-pozitif testi ürünü haksız yere suçlar; bu phash'in bilinen sınırıdır,
    gerçek fotoğraflar detaylıdır.
    """
    _gurultu(galeri, "manzara-1.jpg", seed=1)
    _gurultu(galeri, "manzara-2.jpg", seed=2)

    gruplar = istemci.get("/api/duplicates").json()["groups"]
    for g in gruplar:
        adlar = {p["path"] for p in g}
        assert not (any(a.endswith("manzara-1.jpg") for a in adlar)
                    and any(a.endswith("manzara-2.jpg") for a in adlar)), \
            f"farklı iki görsel kopya sayıldı: {adlar}"
