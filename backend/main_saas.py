"""
GalleryWeb SaaS — Entry point (Faz 1+)
Çalıştır: uvicorn main_saas:app --reload --port 8000
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from app.config import get_settings
from app.routers import auth, galleries, photos, sharing, config, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("galleryweb.saas")

settings = get_settings()
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("GalleryWeb SaaS başlatılıyor (Faz 1)")
    yield
    logger.info("GalleryWeb SaaS kapatılıyor")


app = FastAPI(
    title="GalleryWeb SaaS",
    version="1.0.0",
    description="Multi-tenant fotoğraf galerisi — SaaS",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(galleries.router)
app.include_router(photos.router)
app.include_router(sharing.router)
app.include_router(config.router)
app.include_router(search.router)


# ── Health & info ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.app_env}


@app.get("/api/version")
async def version():
    return {"version": "1.0.0", "faz": 1}


# ── Yerel (local filesystem) sub-app ─────────────────────────────────────────
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent))
try:
    from main import app as _local_app
    app.mount("/yerel", _local_app)
    logger.info("Yerel mod aktif: /yerel prefix")
except Exception as _e:
    logger.warning(f"Yerel mod yüklenemedi: {_e}")


# ── Frontend static files ─────────────────────────────────────────────────────

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def root():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/login")
    async def login_page():
        return FileResponse(str(FRONTEND_DIR / "login.html"))

    @app.get("/share/{link_id}")
    async def share_page(link_id: str):
        return FileResponse(str(FRONTEND_DIR / "share.html"))


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Sunucu hatası"})
