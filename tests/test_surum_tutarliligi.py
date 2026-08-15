"""Sürüm numarası dört yüzeyde de aynı mı?

Bu proje bu tuzağa bir kez düştü: paketler `1.1.0` derken çalışan uygulama
kendini OpenAPI'de `0.1.0` diye tanıtıyordu — yani "hangi sürümü
çalıştırıyorum?" sorusunun ürün içinde cevabı yoktu. Sürüm elle dört yerde
güncellendiği sürece er ya da geç yine ayrışır; bu test ayrışmayı **yayın
öncesinde** yakalar (her CI koşusunda, iki işletim sisteminde de koşar).

Yüzeyler:
  • desktop/src-tauri/tauri.conf.json → paket dosya adları + kurulum paketi
  • desktop/src-tauri/Cargo.toml      → masaüstü ikilisi
  • desktop/src-tauri/Cargo.lock      → kilit dosyası (bayatlarsa derleme uyarır)
  • backend/main.py SURUM             → çalışan uygulamanın kendi beyanı
"""
import json
import re
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
TAURI_CONF = KOK / "desktop" / "src-tauri" / "tauri.conf.json"
CARGO_TOML = KOK / "desktop" / "src-tauri" / "Cargo.toml"
CARGO_LOCK = KOK / "desktop" / "src-tauri" / "Cargo.lock"
MAIN_PY = KOK / "backend" / "main.py"

PAKET = "galleryweb-desktop"


def _tauri_surum() -> str:
    return json.loads(TAURI_CONF.read_text(encoding="utf-8"))["version"]


def _cargo_toml_surum() -> str:
    # [package] bloğundaki ilk `version = "..."` — bağımlılıklarınki değil.
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', CARGO_TOML.read_text(encoding="utf-8"), re.M)
    assert m, "Cargo.toml'da version satırı bulunamadı"
    return m.group(1)


def _cargo_lock_surum() -> str:
    # Kilit dosyasında HER paketin sürümü var; yalnız kendi paketimizi ara.
    m = re.search(
        r'name\s*=\s*"%s"\s*\nversion\s*=\s*"([^"]+)"' % re.escape(PAKET),
        CARGO_LOCK.read_text(encoding="utf-8"),
    )
    assert m, f"Cargo.lock'ta {PAKET} girdisi bulunamadı"
    return m.group(1)


def _main_py_surum() -> str:
    m = re.search(r'^SURUM\s*=\s*"([^"]+)"', MAIN_PY.read_text(encoding="utf-8"), re.M)
    assert m, "backend/main.py içinde SURUM tanımı bulunamadı"
    return m.group(1)


def test_dort_yuzey_ayni_surumu_soyluyor():
    surumler = {
        "tauri.conf.json": _tauri_surum(),
        "Cargo.toml": _cargo_toml_surum(),
        "Cargo.lock": _cargo_lock_surum(),
        "backend/main.py": _main_py_surum(),
    }
    assert len(set(surumler.values())) == 1, (
        "Sürüm numaraları ayrışmış — yayın öncesi hepsini eşitle:\n"
        + "\n".join(f"  {k}: {v}" for k, v in surumler.items())
    )


def test_surum_semver_biciminde():
    surum = _tauri_surum()
    assert re.fullmatch(r"\d+\.\d+\.\d+", surum), (
        f"Sürüm `{surum}` semver değil — Tauri paket adlarını buradan üretiyor "
        "ve NSIS/deb sürüm alanları biçim konusunda katıdır."
    )


def test_calisan_uygulama_surumunu_beyan_ediyor():
    """FastAPI'ye sürüm GERÇEKTEN geçiliyor mu (sabit tanımlanıp unutulmuş olmasın)."""
    kaynak = MAIN_PY.read_text(encoding="utf-8")
    assert re.search(r"FastAPI\([^)]*version\s*=\s*SURUM", kaynak), (
        "main.py'de SURUM tanımlı ama FastAPI(...) çağrısına geçirilmemiş — "
        "uygulama yine kendini 0.1.0 diye tanıtır."
    )
