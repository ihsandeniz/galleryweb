"""GalleryWeb — gizlilik sızıntı regresyon testi.

NE KORUYOR: Yerel (self-host) modda uygulama HİÇBİR dış sunucuya istek
atmamalı. Fotoğrafların kendisi zaten yüklenmiyor, ama üçüncü taraf istekleri
IP adresini ve — harita altlığı söz konusuysa — fotoğrafların çekildiği GPS
konumlarını dışarı bildirir.

Bu yüzden kodda kapatılanlar:
  · Inter + JetBrains Mono   → frontend/vendor/fonts/  (Google Fonts YOK)
  · Leaflet CSS/JS + ikonlar → frontend/vendor/leaflet/ (unpkg YOK)
  · Supabase JS / jsdelivr   → bulut (SaaS) katmanıyla birlikte tamamen KALDIRILDI
                               (2026-08-07); CSP'de artık izinli değil
  · OpenStreetMap altlığı    → açık kullanıcı onayına bağlı (varsayılan KAPALI)

Bu test bir CDN linki geri sızarsa kırılır ve bunu yakalar.

ÇALIŞTIRMA:
    # Uygulama ayakta olmalı (docker compose ... up -d veya ./run.sh)
    pip install playwright && playwright install chromium
    python tests/gizlilik_sizinti_testi.py

Çıkış kodu 0 = temiz, 1 = sızıntı var.
BASE'i ortam değişkeniyle değiştirebilirsin: GW_BASE=http://127.0.0.1:5099
"""
import os
import sys
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

BASE = os.environ.get("GW_BASE", "http://127.0.0.1:5000")
LOCAL = {"127.0.0.1", "localhost"}

def run():
    hits = []          # (asama, host, url)
    stage = ["1-acilis"]

    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context()
        pg = ctx.new_page()

        def on_req(r):
            h = urlparse(r.url).hostname
            if h and h not in LOCAL:
                hits.append((stage[0], h, r.url[:110]))
        pg.on("request", on_req)

        console = []
        pg.on("console", lambda m: console.append(f"{m.type}: {m.text[:160]}"))

        # ── Aşama 1: sayfayı aç, her şey otursun ──
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_timeout(2500)

        # ── Aşama 2: harita görünümünü aç (GPS sızıntısının olacağı yer) ──
        stage[0] = "2-harita-acildi"
        opened = False
        for sel in ["#mapBtn", "#mapViewBtn", "[title*='Harita']", "text=Harita"]:
            try:
                el = pg.query_selector(sel)
                if el:
                    el.click()
                    opened = True
                    break
            except Exception:
                pass
        if not opened:
            # Modal'ı doğrudan aç — fonksiyon global
            try:
                pg.evaluate("openMapView()")
                opened = True
            except Exception as e:
                print(f"⚠️  Harita açılamadı: {e}")
        pg.wait_for_timeout(3000)

        # Onay kutusu göründü mü?
        consent_visible = pg.evaluate(
            "!document.getElementById('mapTileConsent')?.classList.contains('hidden')"
        )
        tile_layer_present = pg.evaluate("typeof _mapTileLayer !== 'undefined' && _mapTileLayer !== null")

        # ── Aşama 3: kullanıcı ALTLIĞI AÇARSA gerçekten OSM'e gidiyor mu? ──
        stage[0] = "3-altlik-onaylandi"
        try:
            pg.click("#mapTileAllowBtn")
            pg.wait_for_timeout(3000)
        except Exception as e:
            print(f"⚠️  Onay butonu tıklanamadı: {e}")

        # ── Font gerçekten yüklendi mi (self-host çalışıyor mu)? ──
        font_ok = pg.evaluate("document.fonts.check('16px Inter')")

        br.close()

    print("=" * 66)
    print("AŞAMA 1 — SAYFA AÇILIŞI (burada SIFIR dış host olmalı)")
    print("=" * 66)
    s1 = sorted({h for st, h, _ in hits if st == "1-acilis"})
    print("✅ SIFIR dış istek — hiçbir yere bağlanılmadı." if not s1
          else "❌ SIZINTI:\n" + "\n".join(f"   → {h}" for h in s1))

    print()
    print("=" * 66)
    print("AŞAMA 2 — HARİTA AÇILDI, onay verilmedi (yine SIFIR olmalı)")
    print("=" * 66)
    print(f"Onay kutusu göründü mü : {consent_visible}")
    print(f"Altlık katmanı eklendi mi: {tile_layer_present}  (False olmalı)")
    s2 = sorted({h for st, h, _ in hits if st == "2-harita-acildi"})
    print("✅ SIFIR dış istek — GPS konumları sızmadı." if not s2
          else "❌ SIZINTI:\n" + "\n".join(f"   → {h}" for h in s2))

    print()
    print("=" * 66)
    print("AŞAMA 3 — kullanıcı altlığı AÇTI (kontrol: burada OSM görünmeli)")
    print("=" * 66)
    s3 = sorted({h for st, h, _ in hits if st == "3-altlik-onaylandi"})
    print("\n".join(f"   → {h}" for h in s3) if s3 else "   (istek yok)")
    print(f"\nInter fontu yüklendi mi (self-host çalışıyor): {font_ok}")

    print()
    print("=" * 66)
    print("KONSOL")
    print("=" * 66)
    for c in console[:15]:
        print("  " + c)

    return 0 if not s1 and not s2 else 1

sys.exit(run())
