# GalleryWeb

A self-hostable photo & video gallery with a built-in **editing studio** — crop, rotate, flip, color/light adjustments, filter presets, and video trimming. Runs entirely on your own machine with **no login and no cloud account required**, or as a multi-tenant hosted service.

> Fotoğraf ve video galeriniz + düzenleme stüdyosu. Kendi bilgisayarınızda, **giriş yapmadan** çalışır.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

---

## Two ways to run it

| | **Self-host (local mode)** | **Hosted (cloud mode)** |
|---|---|---|
| **Who** | Anyone, on their own PC | Users who don't want to self-host |
| **Login** | ❌ None — open the app and go | ✅ Accounts + multi-tenant |
| **Data** | Stays on your disk | Server + object storage |
| **Setup** | Double-click `run.sh` / `run.bat` (or `docker compose up`) | Supabase + PostgreSQL (see [SETUP.md](SETUP.md)) |
| **Cost** | Free forever | Your hosting / subscription |

The **same codebase** powers both. Local mode is the default and needs zero external services.

---

## Features

- **Editing studio** — rotate, flip (H/V), aspect-locked crop, live-preview adjustments (brightness, contrast, saturation, sharpness, temperature, gamma), and one-click filter presets (B&W, sepia, vintage, cool, warm, vivid).
- **Video trimming** — cut start/end with a two-handle timeline (ffmpeg). Non-destructive: originals are backed up and revertible.
- **Fast browsing** — thumbnails (SQLite cache), EXIF display, duplicate finder, favorites, tags, albums, ratings, map view (GPS EXIF).
- **PWA** — installable, works offline, optional phone access on your local network (`GALLERYWEB_LAN=1`).
- **Sharing & proofing** *(hosted mode)* — client galleries with comments, votes, selections, and timestamped video annotations.
- **AI semantic search** *(hosted mode)* — CLIP-based "find photos by describing them".

---

## Quick start — Self-host (no login)

### Option A · Desktop app (Windows · Linux)

Grab an installer from **[Releases](https://github.com/ihsandeniz/galleryweb/releases)** —
no Python, no terminal, no browser tab:

| Platform | File | Notes |
|---|---|---|
| **Windows 10 / 11** | `GalleryWeb_x.y.z_x64-setup.exe` | Includes the WebView2 runtime — installs without internet |
| **Linux** | `.AppImage` (portable) or `.deb` | AppImage: `chmod +x` then run |

> **Windows: “Windows protected your PC”** — the installer is **unsigned** (a code-signing
> certificate costs $200–400/year and this is a free, open-source project). Click
> **More info → Run anyway**. You can verify what you're running: the package is built
> in public by [GitHub Actions](https://github.com/ihsandeniz/galleryweb/actions) from
> this repository, not on a developer's machine.

> 🇹🇷 **Windows'ta “Windows bilgisayarınızı korudu” uyarısı normaldir** — paket imzasızdır
> (sertifika yıllık $200-400, bu ücretsiz açık kaynak bir proje). **Ek bilgi → Yine de
> çalıştır** deyin. Paket GitHub Actions'ta herkesin görebileceği şekilde derleniyor.

**Video trimming** additionally needs `ffmpeg` on your system; everything else works without it.

### Option B · One click, from source (no terminal knowledge needed)

Download the project, then **double-click** the launcher for your system:

- **Linux / macOS** → `run.sh`
- **Windows** → `run.bat`

It sets everything up on first run (creates an isolated environment, installs
dependencies) and opens the gallery in your browser at `http://localhost:5000`.
You only need [Python 3.10+](https://www.python.org/downloads/) installed first
(on Windows, tick **"Add Python to PATH"** in the installer).

> Kolay yol: `run.sh` (Linux/macOS) veya `run.bat` (Windows) dosyasına **çift tıklayın** —
> gerisini kendisi halleder, tarayıcıda galeri açılır.

**Güncelleme / Updating:** en son sürümü almak için güncelleyiciyi çalıştırın —
**Windows:** `guncelle.bat` · **Linux/macOS:** `./guncelle.sh`. GitHub'dan son sürümü
indirir; fotoğraflarınız, ayarlarınız ve sanal ortamınız korunur. Sonraki
`run.bat` / `run.sh` çalıştırmasında değişen bağımlılıklar otomatik kurulur —
yani güncelleme için hiçbir şeyi silmenize gerek yok. (git ile klonladıysanız
`run` zaten açılışta otomatik `git pull` yapar.)

### Option C · Python by hand (zero extra services)

```bash
git clone https://github.com/ihsandeniz/galleryweb.git
cd galleryweb/backend
pip install -r requirements-selfhost.txt   # lightweight — no CLIP/Supabase
python main.py                              # → http://localhost:5000
```

Then open `http://localhost:5000`, click **Klasör Aç / Open Folder**, and pick a photo directory. That's it — no account, no database setup.

> **Video editing** needs `ffmpeg` on your system (`apt install ffmpeg` / `brew install ffmpeg` / `pacman -S ffmpeg`).

### Option D · Docker (no Python needed)

```bash
git clone https://github.com/ihsandeniz/galleryweb.git
cd galleryweb
mkdir photos                # put your photos/videos here
docker compose up --build   # → http://localhost:5000
```

Inside the app, open the `/photos` folder. `ffmpeg` is already included in the image.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **Port 5000 already in use** | Start on another port: `PORT=5001 python main.py` (or set `PORT` in `docker-compose.yml`). |
| **Video trimming does nothing** | `ffmpeg` isn't installed. `apt install ffmpeg` / `brew install ffmpeg` / `pacman -S ffmpeg`. Photos work without it. |
| **HEIC / iPhone photos don't open** | The `pillow-heif` dependency covers this — reinstall with `pip install -r backend/requirements-selfhost.txt`. |
| **`python: command not found`** | Install [Python 3.10+](https://www.python.org/downloads/). On Windows, tick **"Add Python to PATH"** during install. |
| **Phone can't reach the gallery** | Network access is off by default. Start with `GALLERYWEB_LAN=1`, then use the `📱 Telefon erişimi:` URL it prints, and make sure the phone is on the **same Wi-Fi**. |
| **Phone says “connection timed out”** | That's a **firewall**, not a bug — the server is listening correctly but packets are dropped. The app shows the exact command to fix it. Windows (run as **Administrator**): `netsh advfirewall firewall add rule name="GalleryWeb" dir=in action=allow protocol=TCP localport=5000`. Linux: see the 🧱 box in the app. |
| **Windows: editing a photo does nothing** | Check Defender's **Controlled folder access** (Ransomware protection). It blocks writes to `Pictures`/`Documents` for unrecognised apps — usually *silently*. Either allow GalleryWeb or keep photos in an unprotected folder. |
| **Windows: “file is used by another program”** | Windows won't move an open file. Stop video playback (or close the other program) and retry — the app deliberately refuses rather than pretending it deleted the file. |
| **Want developer auto-reload** | `GALLERYWEB_DEV=1 python main.py` (off by default for faster startup). |

---

## Hosted / cloud mode (advanced)

Cloud mode adds accounts, multi-tenancy, object storage (Cloudflare R2), realtime sync, client proofing, and CLIP search. It requires Supabase + PostgreSQL (with `pgvector`). See **[SETUP.md](SETUP.md)** and **[ARCHITECTURE.md](ARCHITECTURE.md)** for the full stack, and `requirements.txt` for the complete dependency set.

Local and cloud mode are switchable in the UI (📂 / ☁ toggle). Local mode never talks to any auth server.

---

## Tech

- **Backend:** FastAPI (Python), Pillow, ffmpeg. Local mode is a single self-contained app (`backend/main.py`) with an SQLite thumbnail cache — no server database.
- **Frontend:** Vanilla JS (no framework), PWA.
- **Cloud add-ons:** Supabase Auth, PostgreSQL + pgvector, Cloudflare R2, sentence-transformers (CLIP).

---

## Security & privacy

- Local mode stores everything on your machine and makes **no outbound calls** for auth.
- ⚠️ **Local mode has no authentication — this is by design (single-user desktop use).** Because of that the server now binds to **`127.0.0.1` only**: nothing leaves your machine unless you ask for it. Network access is opt-in:

  ```bash
  GALLERYWEB_LAN=1 python main.py     # phone / same-Wi-Fi access
  ```

  When you enable it, **anyone on that network can read, tag, and delete your photos** via the API — the server prints a warning to remind you. Only do it on a network you trust, and never expose local mode directly to the internet — use the hosted/cloud mode (with accounts) for multi-user or public deployments.

  > 🇹🇷 **Yerel modda giriş/parola yoktur — bu bilinçli bir tasarım (tek kişilik masaüstü kullanımı).** Bu yüzden sunucu artık **yalnızca `127.0.0.1`** dinler; hiçbir şey makinenizden dışarı çıkmaz. Ağa açmak isteğe bağlıdır: `GALLERYWEB_LAN=1 python main.py`. Açtığınızda **aynı ağdaki herkes** fotoğraflarınızı görebilir, etiketleyebilir ve silebilir — sunucu bunu açılışta uyarı olarak yazar. Yalnızca güvendiğiniz bir ağda açın, yerel modu **doğrudan internete açmayın**.

- If you deploy behind a reverse proxy for cloud mode, set `ALLOWED_ORIGINS` to your exact domains (never `*` — the server rejects `*` and falls back to localhost).
- Never commit your `.env` (it's git-ignored). Copy `.env.example` and fill in your own keys for cloud mode.
- See [SECURITY_AUDIT.md](SECURITY_AUDIT.md).

---

## License

**GNU AGPL-3.0** — see [LICENSE](LICENSE).

You are free to use, modify, and self-host GalleryWeb. If you run a **modified version as a network service**, the AGPL requires you to make your source code available to its users. This keeps the project open while allowing the original authors to offer a hosted service.

---

## Contributing

Issues and pull requests welcome. Please keep the frontend framework-free (Vanilla JS) to match the existing codebase.
