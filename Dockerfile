# ── GalleryWeb — Self-host (Yerel Mod) container ──────────────────────────────
# Login YOK, dış servis YOK. Fotoğraf/video galerisi + düzenleme stüdyosu.
# Build:  docker compose up --build
# Erişim: http://localhost:5000

FROM python:3.12-slim

# ffmpeg = video trim + poster kare · libheif = HEIC/HEIF desteği
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sadece hafif self-host bağımlılıkları (CLIP/Supabase/boto3 YOK)
COPY backend/requirements-selfhost.txt ./requirements-selfhost.txt
RUN pip install --no-cache-dir -r requirements-selfhost.txt

# Uygulama kodu + frontend
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# SEC-F002: root olarak çalıştırma — konteyner escape/uygulama zafiyetinde
# host mount'ları (photos volume) tam yetkiyle yazılamasın diye ayrı kullanıcı.
RUN groupadd -r galleryweb && useradd -r -g galleryweb galleryweb \
    && chown -R galleryweb:galleryweb /app
USER galleryweb

WORKDIR /app/backend
ENV PORT=5000
EXPOSE 5000

# Production: reload kapalı. MIM-F003: shell-form CMD → $PORT env'i gerçekten uygulanır
# (exec-form JSON array env substitution yapmaz, port hep 5000'de sabitlenirdi).
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000}
