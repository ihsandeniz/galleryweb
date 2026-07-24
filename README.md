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
- **PWA** — installable, works offline, phone access on your local network.
- **Sharing & proofing** *(hosted mode)* — client galleries with comments, votes, selections, and timestamped video annotations.
- **AI semantic search** *(hosted mode)* — CLIP-based "find photos by describing them".

---

## Quick start — Self-host (no login)

### Option A · One click (easiest — no terminal knowledge needed)

Download the project, then **double-click** the launcher for your system:

- **Linux / macOS** → `run.sh`
- **Windows** → `run.bat`

It sets everything up on first run (creates an isolated environment, installs
dependencies) and opens the gallery in your browser at `http://localhost:5000`.
You only need [Python 3.10+](https://www.python.org/downloads/) installed first
(on Windows, tick **"Add Python to PATH"** in the installer).

> Kolay yol: `run.sh` (Linux/macOS) veya `run.bat` (Windows) dosyasına **çift tıklayın** —
> gerisini kendisi halleder, tarayıcıda galeri açılır.

**Güncelleme / Updating (Windows):** `guncelle.bat` dosyasına çift tıklayın —
en son sürümü GitHub'dan indirir. Fotoğraflarınız, ayarlarınız ve sanal ortamınız
korunur; sonraki `run.bat` çalıştırmasında değişen bağımlılıklar otomatik kurulur.
Yani güncelleme için hiçbir şeyi silmenize gerek yok. (Linux/macOS: `git pull`.)

### Option B · Python by hand (zero extra services)

```bash
git clone https://github.com/ihsandeniz/galleryweb.git
cd galleryweb/backend
pip install -r requirements-selfhost.txt   # lightweight — no CLIP/Supabase
python main.py                              # → http://localhost:5000
```

Then open `http://localhost:5000`, click **Klasör Aç / Open Folder**, and pick a photo directory. That's it — no account, no database setup.

> **Video editing** needs `ffmpeg` on your system (`apt install ffmpeg` / `brew install ffmpeg` / `pacman -S ffmpeg`).

### Option C · Docker (no Python needed)

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
| **Phone can't reach the gallery** | Use the `📱 Telefon erişimi:` URL printed on startup, and make sure the phone is on the **same Wi-Fi**. |
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
- ⚠️ **Local mode has no authentication — this is by design (single-user desktop use).** The server binds to `0.0.0.0`, so **anyone on the same network/Wi-Fi can read, tag, and delete your photos** via the API. Only run it on a network you trust. To restrict it to your own machine, start with `HOST=127.0.0.1` (or keep it behind a firewall). Do **not** expose local mode directly to the internet — use the hosted/cloud mode (with accounts) for multi-user or public deployments.

  > 🇹🇷 **Yerel modda giriş/parola yoktur — bu bilinçli bir tasarım (tek kişilik masaüstü kullanımı).** Sunucu `0.0.0.0`'a bağlanır, yani **aynı ağdaki/Wi-Fi'daki herkes** API üzerinden fotoğraflarınızı görebilir, etiketleyebilir ve silebilir. Yalnızca güvendiğiniz bir ağda çalıştırın. Sadece kendi makinenize kısıtlamak için `HOST=127.0.0.1` ile başlatın. Yerel modu **doğrudan internete açmayın** — çok kullanıcılı/herkese açık kurulumlar için hesaplı bulut modunu kullanın.

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
