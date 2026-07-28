# -*- mode: python ; coding: utf-8 -*-
"""GalleryWeb yerel-mod sunucusunu tek dosya binary'ye paketler (Tauri sidecar).

Çalıştırma:
    cd desktop && ../.build-venv/bin/pyinstaller galleryweb-server.spec --noconfirm

Çıktı:
    Linux/macOS → desktop/dist/galleryweb-server            (tek dosya)
    Windows     → desktop/dist/galleryweb-server/…exe       (klasör, "onedir")

Neden Windows'ta klasör? Tek-dosya paket her AÇILIŞTA ~55 MB'ı `%TEMP%`'e
açar: Defender bunu her seferinde baştan tarar, açılış saniyeler sürer ve
kabuğun 30 sn'lik "sunucu hazır" tavanı zorlanır. Ayrıca kendini geçici
dizine açan tek-dosya exe'ler virüs tarayıcılarında yanlış pozitife yatkındır.
Klasör düzeninde açma adımı hiç yoktur — dosyalar diskte zaten durur.
Linux'ta AppImage kendisi bir kap olduğu için tek-dosya kalıyor.

Sadece YEREL mod paketlenir: `backend/main.py` bağımsızdır — Supabase/pgvector/CLIP
import etmez. Bulut modu (main_saas.py) kasıtlı olarak dışarıda; onu da almak
paket boyutunu ~2.5GB'a çıkarırdı.
"""
import sys
from pathlib import Path

REPO = Path(SPECPATH).parent
BACKEND = REPO / "backend"
WINDOWS = sys.platform == "win32"

a = Analysis(
    [str(BACKEND / "main.py")],
    pathex=[str(BACKEND)],
    binaries=[],
    # Frontend varlıkları binary'nin içine gömülür; çalışırken sys._MEIPASS/frontend
    # altında açılır (bkz. main.py `_FROZEN` dalı).
    datas=[(str(REPO / "frontend"), "frontend")],
    hiddenimports=[
        # uvicorn bunları dinamik (string) import eder → statik analiz göremez
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        # yerel modun kendi modülleri
        "cache_manager",
        "thumbnail_gen",
        "duplicate_finder",
        # Pillow HEIC/HEIF eklentisi
        "pillow_heif",
    ],
    hookspath=[],
    runtime_hooks=[],
    # Bulut modunun ağır bağımlılıkları — yerel mod bunları kullanmaz, sızarlarsa
    # paket yüzlerce MB şişer.
    excludes=[
        "torch", "torchvision", "transformers", "sentence_transformers",
        "sklearn", "scipy", "pandas", "matplotlib", "tkinter",
        "supabase", "boto3", "botocore", "sqlalchemy", "asyncpg", "pgvector",
        "IPython", "pytest", "notebook",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    # Windows'ta ikili dosyalar/veriler exe'nin İÇİNE gömülmez; COLLECT ile yan
    # klasöre konur (onedir). `exclude_binaries` bu ayrımı yapan anahtardır.
    *([] if WINDOWS else [a.binaries, a.datas]),
    [],
    exclude_binaries=WINDOWS,
    name="galleryweb-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX bazı dağıtımlarda AV/başlatma sorunları çıkarıyor
    console=True,       # Tauri sidecar olarak stdout'u kabuk okur (hazır-olma sinyali)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if WINDOWS:
    # dist/galleryweb-server/galleryweb-server.exe + _internal/…
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="galleryweb-server",
    )
