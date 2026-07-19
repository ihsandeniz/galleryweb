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
| **Setup** | `python main.py` or `docker compose up` | Supabase + PostgreSQL (see [SETUP.md](SETUP.md)) |
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

### Option A · Python (zero extra services)

```bash
git clone https://github.com/<you>/galleryweb.git
cd galleryweb/backend
pip install -r requirements-selfhost.txt   # lightweight — no CLIP/Supabase
python main.py                              # → http://localhost:5000
```

Then open `http://localhost:5000`, click **Klasör Aç / Open Folder**, and pick a photo directory. That's it — no account, no database setup.

> **Video editing** needs `ffmpeg` on your system (`apt install ffmpeg` / `brew install ffmpeg` / `pacman -S ffmpeg`).

### Option B · Docker (no Python needed)

```bash
git clone https://github.com/<you>/galleryweb.git
cd galleryweb
mkdir photos                # put your photos/videos here
docker compose up --build   # → http://localhost:5000
```

Inside the app, open the `/photos` folder. `ffmpeg` is already included in the image.

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
- Never commit your `.env` (it's git-ignored). Copy `.env.example` and fill in your own keys for cloud mode.
- See [SECURITY_AUDIT.md](SECURITY_AUDIT.md).

---

## License

**GNU AGPL-3.0** — see [LICENSE](LICENSE).

You are free to use, modify, and self-host GalleryWeb. If you run a **modified version as a network service**, the AGPL requires you to make your source code available to its users. This keeps the project open while allowing the original authors to offer a hosted service.

---

## Contributing

Issues and pull requests welcome. Please keep the frontend framework-free (Vanilla JS) to match the existing codebase.
