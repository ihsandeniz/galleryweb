"""FAZ W — Windows uyum regresyon testleri.

Buradaki her test, "Linux'ta sorunsuz çalışıp Windows'ta SESSİZCE yanlış olan"
bir davranışı hedefler. Hepsi iki platformda da koşar: Linux'ta mantığı
doğrular, Windows'ta (CI'daki `windows-latest` işi) gerçek hatayı yakalar.

Ders (Yuki v0.5.0): kaynağın yeşil olması paketin çalıştığını göstermez —
bu yüzden testler gerçek dosya sistemi üzerinde iş yapar, mock'lamaz.
"""
import os
import sys

import pytest

import main


WINDOWS = os.name == "nt"
sadece_windows = pytest.mark.skipif(not WINDOWS, reason="yalnız Windows'ta anlamlı")


# ── 1) Uzun yol (MAX_PATH = 260) ──────────────────────────────────────────────

def test_lp_kisa_yolu_degistirmez(tmp_path):
    p = tmp_path / "a.jpg"
    assert main._lp(p) == str(p)


@sadece_windows
def test_lp_uzun_yola_onek_ekler():
    uzun = "C:\\" + "\\".join("k" * 30 for _ in range(10)) + "\\foto.jpg"
    assert len(uzun) > main._UZUN_YOL_ESIGI
    assert main._lp(uzun).startswith("\\\\?\\")


@sadece_windows
def test_lp_unc_yolunu_dogru_cevirir():
    unc = "\\\\sunucu\\pay\\" + "\\".join("k" * 30 for _ in range(8)) + "\\foto.jpg"
    assert main._lp(unc).startswith("\\\\?\\UNC\\sunucu\\pay")


def test_derin_klasorde_duzenleme_zinciri_kaydediliyor(tmp_path):
    """260 karakteri aşan yolda düzenleme sidecar'ı yazılıp geri okunabilmeli.

    Kırıldığında belirtisi: fotoğraf açılır, düzenlenir, "kaydedildi" görünür —
    ama geri al/ileri al geçmişi boştur. Hiçbir hata mesajı çıkmaz.
    """
    from PIL import Image

    derin = tmp_path
    for _ in range(8):
        derin = derin / ("uzun-klasor-adi-" + "x" * 20)
    main._mkdir(derin)

    foto = derin / ("f" * 40 + ".jpg")
    assert len(str(foto)) > 260, f"test kurgusu yetersiz: {len(str(foto))} karakter"
    Image.new("RGB", (20, 20)).save(main._lp(foto))

    zincir = main._new_chain()
    zincir["ops"].append({"op": "rotate", "params": {"degrees": 90}, "at": 0})
    zincir["cursor"] = 1
    main._save_chain(foto, zincir)

    geri = main._load_chain(foto)
    assert geri["cursor"] == 1
    assert geri["ops"][0]["op"] == "rotate"


# ── 2) Dosya kilidi (WinError 32) ─────────────────────────────────────────────

def test_kilitli_mi_yalnizca_paylasim_ihlaline_evet_der():
    e = OSError("meşgul")
    e.winerror = 32
    assert main._kilitli_mi(e)
    e2 = OSError("yok")
    e2.winerror = 2
    assert not main._kilitli_mi(e2)
    assert not main._kilitli_mi(OSError("posix"))


def test_kilit_hatasi_409_ve_anlasilir_mesaj():
    e = OSError()
    e.winerror = 32
    h = main._kilit_hatasi(e, "silme")
    assert h.status_code == 409
    assert "başka bir program" in h.detail

    h2 = main._kilit_hatasi(OSError("disk dolu"), "silme")
    assert h2.status_code == 500


@sadece_windows
def test_acik_dosya_silinince_409_doner_ve_dosya_yerinde_kalir(istemci, galeri):
    """Windows açık dosyayı taşıtmaz; kullanıcıya 'silindi' DENMEMELİ."""
    foto = galeri / "deneme.jpg"
    with open(foto, "rb") as tutulan:      # lightbox'ta oynayan videonun taklidi
        tutulan.read(1)
        r = istemci.delete("/api/image/deneme.jpg")
        assert r.status_code == 409, r.text
        assert "başka bir program" in r.json()["detail"]
        assert foto.exists()

    r2 = istemci.delete("/api/image/deneme.jpg")     # tanıtıcı kapandı → geçmeli
    assert r2.status_code == 200, r2.text
    assert not foto.exists()


def test_geri_yukleme_ayni_isimli_dosyayi_ezmez(istemci, galeri):
    from PIL import Image

    r = istemci.delete("/api/image/deneme.jpg")
    assert r.status_code == 200, r.text
    cop_id = r.json()["trash_id"]

    Image.new("RGB", (8, 8), (200, 10, 10)).save(galeri / "deneme.jpg")  # yeni dosya
    r2 = istemci.post(f"/api/restore/{cop_id}")
    assert r2.status_code == 409
    assert (galeri / "deneme.jpg").stat().st_size < 5000   # yeni dosya duruyor


# ── 3) Sürücü harfi / büyük-küçük harf tutarlılığı ────────────────────────────

def test_dir_prefix_like_os_ayraci_kullanir():
    """Desen, OS'un kendi ayracıyla bitmeli — yollar DB'ye o ayraçla yazılıyor.

    Sabit '/' kullanmak Windows'ta klasör kapsamlı sorguları boş döndürüyordu
    (2026-07-24'te kapatıldı; bu test nöbeti devraldı).
    """
    from cache_manager import CacheManager

    desen = CacheManager._dir_prefix_like("/tmp/galeri")
    assert desen.endswith(CacheManager._like_escape(os.sep) + "%")


def test_klasor_kapsamli_sorgular_secilen_yol_biciminden_bagimsiz(istemci, galeri):
    """Etiket ekle → klasör bazlı etiket listesi ONU görmeli.

    Kırıldığında belirtisi: kenar çubuğundaki etiket/puan filtreleri BOŞ gelir.
    Kök neden, fotoğraf yollarının `.resolve()` edilip klasör yolunun ham
    bırakılmasıydı (Windows'ta büyük-küçük harf, Linux'ta sembolik bağ).
    """
    r = istemci.post("/api/tag/deneme.jpg", json={"tag": "manzara"})
    assert r.status_code == 200, r.text

    etiketler = istemci.get("/api/tags").json()["tags"]
    assert any(e["name"] == "manzara" for e in etiketler), etiketler


def test_secilen_klasor_kanonik_hale_getirilir(tmp_path):
    """Sembolik bağ / göreli parça ile seçilen klasör kanonikleştirilmeli."""
    gercek = tmp_path / "gercek"
    gercek.mkdir()
    dolambacli = tmp_path / "gercek" / ".." / "gercek"
    assert main._kanonik(dolambacli) == gercek.resolve()


# ── 4) ffmpeg yokluğu ─────────────────────────────────────────────────────────

def test_ffmpeg_yoksa_trim_anlasilir_hata_verir(istemci, galeri, monkeypatch):
    """Windows'ta ffmpeg pratikte kurulu değildir.

    Eskiden `FileNotFoundError` sızıyor ve kullanıcı çıplak 500 görüyordu.
    """
    import shutil as _sh
    (galeri / "video.mp4").write_bytes(b"sahte")
    monkeypatch.setattr(_sh, "which", lambda ad: None)

    r = istemci.post("/api/edit/video.mp4/trim", json={"start_ms": 0, "end_ms": 1000})
    assert r.status_code == 501, r.text
    assert "ffmpeg" in r.json()["detail"]


# ── 6) Konsol kodlaması ───────────────────────────────────────────────────────

def test_turkce_cikti_cp1252_akista_cokmez():
    """Windows konsolu cp1252'dir ve 'ğ'/'ş'/emoji orada YOKTUR.

    Kırıldığında belirtisi: kullanıcı telefon erişimini açar, sunucu
    `print("⚠️ Sunucu AĞA AÇIK…")` satırında UnicodeEncodeError ile ÇÖKER.
    CI'ın ikinci turunda gerçekten yakalandı.
    """
    import io

    ham = io.BytesIO()
    akis = io.TextIOWrapper(ham, encoding="cp1252", errors="strict")
    main._akisi_utf8_yap(akis)

    akis.write("⚠️ Sunucu AĞA AÇIK — İstanbul Boğazı 📱")   # eskiden burada çökerdi
    akis.flush()
    assert "AĞA AÇIK".encode("utf-8") in ham.getvalue()


# ── 7) MIME türleri (Windows kayıt defterine bağımlılık) ─────────────────────

def test_medya_turu_uzantidan_belirleniyor():
    from pathlib import Path

    assert main._medya_turu(Path("a.webp")) == "image/webp"
    assert main._medya_turu(Path("A.MP4")) == "video/mp4"
    assert main._medya_turu(Path("a.heic")) == "image/heic"
    assert main._medya_turu(Path("a.bilinmeyen")) is None


def test_kucuk_resim_dogru_mime_ile_gelir(istemci):
    """Windows'ta `.webp` kayıt defterinde olmadığı için Starlette
    `application/octet-stream` gönderiyordu — CI bunu ilk turda yakaladı."""
    r = istemci.get("/api/image/deneme.jpg?thumb=true&w=200")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/webp"


def test_tam_boy_gorsel_dogru_mime_ile_gelir(istemci):
    r = istemci.get("/api/image/deneme.jpg")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/jpeg"


def test_konsol_penceresi_bayragi_platforma_gore():
    from thumbnail_gen import ThumbnailGenerator

    beklenen = 0x0800_0000 if WINDOWS else 0
    assert main._NO_WINDOW == beklenen
    assert ThumbnailGenerator._NO_WINDOW == beklenen


# ── 5) Güvenlik duvarı ────────────────────────────────────────────────────────

@sadece_windows
def test_windows_guvenlik_duvari_netsh_komutu_verir():
    main._guvenlik_duvari_onbellek.clear()
    d = main._guvenlik_duvari()
    if not d.get("aktif"):
        pytest.skip("bu makinede güvenlik duvarı kapalı raporlandı")
    assert "netsh advfirewall" in d["komut"]
    assert str(main._PORT) in d["komut"]
    assert d.get("yonetici") is True
    assert d.get("not")


@pytest.mark.skipif(sys.platform != "linux", reason="Linux davranışı")
def test_linux_guvenlik_duvari_sozlesmesi_bozulmadi():
    d = main._guvenlik_duvari()
    assert "aktif" in d
    if d["aktif"]:
        assert str(main._PORT) in d["komut"]


def test_ag_durumu_guvenlik_duvari_alanini_iceriyor(istemci):
    d = istemci.get("/api/network").json()
    assert "guvenlik_duvari" in d
    assert isinstance(d["guvenlik_duvari"].get("aktif"), bool)
