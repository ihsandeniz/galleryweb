import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request

logger = logging.getLogger("galleryweb")
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import socket
from pathlib import Path
from typing import List, Dict
import asyncio
import itertools
import json
from cache_manager import CacheManager
from thumbnail_gen import ThumbnailGenerator
import mimetypes


def get_local_ip() -> str | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


_local_ip = get_local_ip()
_PORT = int(os.getenv("PORT", "5000"))
_env_origins = os.getenv("ALLOWED_ORIGINS", "")
if _env_origins:
    _origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
else:
    _origins = [f"http://127.0.0.1:{_PORT}", f"http://localhost:{_PORT}"]
    if _local_ip:
        _origins.append(f"http://{_local_ip}:{_PORT}")
        print(f"📱 Telefon erişimi: http://{_local_ip}:{_PORT}")

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
CACHE_DIR = BASE_DIR / "cache"

# Global state
current_directories: list[Path] = []   # Faz 5.2 — multi-folder support
cache_manager = CacheManager(str(CACHE_DIR / "thumbnails.db"))
thumbnail_gen = ThumbnailGenerator(cache_manager, cache_dir=CACHE_DIR / "thumbnails")


# ── Multi-folder helpers ──────────────────────────────────────────────────────

def _primary_dir() -> Path | None:
    """Return the first (primary) directory, or None."""
    return current_directories[0] if current_directories else None


def find_in_directories(rel_path: str) -> Path | None:
    """Find a relative path in any of the active directories. Returns resolved abs path or None."""
    for d in current_directories:
        candidate = (d / rel_path).resolve()
        try:
            if candidate.is_relative_to(d.resolve()) and candidate.exists():
                return candidate
        except ValueError:
            pass
    return None


def _relative_to_any(p: Path) -> str:
    """Return relative path string against whichever active directory contains p."""
    for d in current_directories:
        try:
            return str(p.relative_to(d))
        except ValueError:
            pass
    return p.name  # fallback: just the filename


def _dir_for_path(full_path: Path) -> Path | None:
    """Return which active directory owns full_path."""
    for d in current_directories:
        try:
            full_path.relative_to(d.resolve())
            return d
        except ValueError:
            pass
    return None


# current_directory: backward-compat alias — always equals current_directories[0] or None
# Updated by set_directory / add_directory / remove_directory / clear_directory
current_directory: Path | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    thumbnail_gen.executor.shutdown(wait=False)


app = FastAPI(title="Photo Gallery Pro", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.middleware("http")
async def no_cache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


# ──────────────────────────────────────────────
# Directory Management
# ──────────────────────────────────────────────

@app.get("/api/current-directory")
async def get_current_directory():
    return {
        "path": str(current_directory) if current_directory else None,
        "directories": [str(d) for d in current_directories]
    }


@app.post("/api/set-directory")
async def set_directory(data: dict):
    global current_directory, current_directories
    path = data.get("path")
    if not path:
        raise HTTPException(400, "Geçersiz klasör yolu")
    path = os.path.expanduser(path.strip())
    if not os.path.isdir(path):
        raise HTTPException(400, f"Geçersiz klasör yolu: {path}")
    p = Path(path)
    current_directories = [p]
    current_directory = p
    return {"status": "success", "path": str(p), "directories": [str(p)]}


@app.post("/api/add-directory")
async def add_directory(data: dict):
    """Add a second (or more) directory to the active set — Faz 5.2 multi-folder."""
    global current_directory, current_directories
    path = data.get("path")
    if not path:
        raise HTTPException(400, "Geçersiz klasör yolu")
    path = os.path.expanduser(path.strip())
    if not os.path.isdir(path):
        raise HTTPException(400, f"Geçersiz klasör yolu: {path}")
    p = Path(path)
    if p not in current_directories:
        current_directories.append(p)
    if not current_directory:
        current_directory = p
    return {"status": "success", "directories": [str(d) for d in current_directories]}


@app.delete("/api/directory")
async def remove_directory(data: dict):
    """Remove one directory from the active set."""
    global current_directory, current_directories
    path = data.get("path")
    if not path:
        raise HTTPException(400, "Geçersiz klasör yolu")
    p = Path(os.path.expanduser(path.strip()))
    current_directories = [d for d in current_directories if d != p]
    current_directory = current_directories[0] if current_directories else None
    return {"status": "success", "directories": [str(d) for d in current_directories]}


@app.post("/api/clear-directory")
async def clear_directory():
    global current_directory, current_directories
    current_directory = None
    current_directories = []
    return {"status": "success"}


@app.get("/api/browse")
async def browse_directory(path: str = "/"):
    target = Path(os.path.expanduser(path.strip()))
    if not target.is_dir():
        raise HTTPException(400, "Geçersiz yol")
    entries = []
    try:
        for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
            if entry.name.startswith('.'):
                continue
            entries.append({"name": entry.name, "path": str(entry), "is_dir": entry.is_dir()})
    except PermissionError:
        pass
    return {
        "current": str(target),
        "parent": str(target.parent) if str(target) != str(target.parent) else None,
        "entries": entries
    }


# ──────────────────────────────────────────────
# Images
# ──────────────────────────────────────────────

@app.get("/api/images")
async def get_images(
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    include_subfolders: bool = False,
    sort_by: str = "name",
    sort_dir: str = "asc",
    tags: str = "",
    favorites_only: bool = False,
    file_types: str = "",
    album_id: int = 0
):
    if not current_directories:
        raise HTTPException(400, "Önce bir klasör seçin")

    supported = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff',
                 '.heic', '.heif', '.avif',
                 '.mp4', '.webm', '.mov'}

    # Dosya türü filtresi — aktifse sadece seçilen uzantıları al
    if file_types:
        ft_list = {ext.strip().lower() for ext in file_types.split(',') if ext.strip()}
        # Noktasız geldiyse ekle
        ft_list = {'.' + ext if not ext.startswith('.') else ext for ext in ft_list}
        active_supported = supported & ft_list
        if not active_supported:
            active_supported = supported
    else:
        active_supported = supported

    # Aggregate from ALL active directories (Faz 5.2)
    image_paths = []
    seen_names: set[str] = set()
    for base_dir in current_directories:
        if include_subfolders:
            dir_paths = [p for p in base_dir.rglob("*") if p.suffix.lower() in active_supported]
        else:
            dir_paths = [p for p in base_dir.iterdir() if p.suffix.lower() in active_supported]
        for p in dir_paths:
            # Disambiguate same-name files across dirs with full rel path key
            key = str(p.relative_to(base_dir.parent))
            if key not in seen_names:
                seen_names.add(key)
                image_paths.append(p)

    if search:
        image_paths = [p for p in image_paths if search.lower() in p.name.lower()]

    # Tag filtresi
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        if tag_list:
            tagged = set(cache_manager.get_images_with_tags(tag_list))
            image_paths = [p for p in image_paths if str(p) in tagged]

    # Favori filtresi
    if favorites_only:
        favs = set(cache_manager.get_favorites())
        image_paths = [p for p in image_paths if str(p) in favs]

    # Album filtresi
    if album_id:
        album = cache_manager.get_album(album_id)
        if album:
            album_abs = set(album["images"])  # stored as abs paths in DB
            image_paths = [p for p in image_paths if str(p) in album_abs]

    # Sıralama
    reverse = (sort_dir == "desc")
    if sort_by == "size":
        image_paths.sort(key=lambda p: p.stat().st_size, reverse=reverse)
    elif sort_by == "mtime":
        image_paths.sort(key=lambda p: p.stat().st_mtime, reverse=reverse)
    elif sort_by == "type":
        image_paths.sort(key=lambda p: p.suffix.lower(), reverse=reverse)
    elif sort_by == "rating":
        all_ratings = cache_manager.get_all_ratings()  # {abs_path: stars}
        image_paths.sort(
            key=lambda p: all_ratings.get(str(p), 0),
            reverse=reverse
        )
    else:
        image_paths.sort(key=lambda p: p.name.lower(), reverse=reverse)

    images = [_relative_to_any(p) for p in image_paths]
    total = len(images)
    start = (page - 1) * per_page
    paginated_paths = image_paths[start:start + per_page]
    paginated = [_relative_to_any(p) for p in paginated_paths]

    # mtime map: relative_path → unix timestamp (for Timeline view)
    mtimes = {_relative_to_any(p): p.stat().st_mtime for p in paginated_paths}

    return {
        "images": paginated,
        "mtimes": mtimes,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page)
    }


@app.get("/api/image/{path:path}")
async def serve_image(path: str, thumb: bool = False, w: int = 300):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Resim bulunamadı")

    if thumb:
        size = max(100, min(800, w))
        thumb_path = await thumbnail_gen.get_thumbnail(full_path, size=size)
        return FileResponse(thumb_path)
    return FileResponse(full_path)


@app.get("/api/metadata/{path:path}")
async def get_metadata(path: str):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Resim bulunamadı")

    stat = full_path.stat()
    metadata = {
        "filename": full_path.name,
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
    }
    try:
        import pyexiv2
        img = pyexiv2.Image(str(full_path))
        metadata["exif"] = img.read_exif()
        img.close()
    except Exception:
        metadata["exif"] = None

    # Etiketleri de ekle
    metadata["tags"] = cache_manager.get_image_tags(str(full_path))

    return metadata


# ──────────────────────────────────────────────
# Delete / Trash / Restore
# ──────────────────────────────────────────────

@app.delete("/api/image/{path:path}")
async def delete_image(path: str):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Resim bulunamadı")

    base = _dir_for_path(full_path) or current_directories[0]
    trash_dir = base / ".gallery_trash"
    trash_dir.mkdir(exist_ok=True)

    timestamp = int(time.time() * 1000)
    trash_path = trash_dir / f"{timestamp}_{full_path.name}"
    try:
        full_path.rename(trash_path)
    except FileNotFoundError:
        raise HTTPException(404, "Dosya taşınırken bulunamadı")
    except OSError as e:
        logger.error("delete_image rename failed: %s", e)
        raise HTTPException(500, f"Dosya taşıma başarısız: {e}")

    trash_id = cache_manager.add_to_trash(str(full_path), str(trash_path))
    return {"trash_id": trash_id, "filename": full_path.name}


@app.post("/api/restore/{trash_id}")
async def restore_image(trash_id: int):
    record = cache_manager.remove_from_trash(trash_id)
    if not record:
        raise HTTPException(404, "Çöp kaydı bulunamadı")
    original_path, trash_path_str = record
    tp = Path(trash_path_str)
    op = Path(original_path)
    if not tp.exists():
        raise HTTPException(404, "Dosya çöp kutusunda bulunamadı")
    op.parent.mkdir(parents=True, exist_ok=True)
    try:
        tp.rename(op)
    except OSError as e:
        logger.error("restore_image rename failed: %s", e)
        raise HTTPException(500, f"Dosya geri yükleme başarısız: {e}")
    return {"status": "restored", "filename": op.name}


@app.delete("/api/trash/{trash_id}")
async def permanently_delete(trash_id: int):
    record = cache_manager.remove_from_trash(trash_id)
    if not record:
        raise HTTPException(404, "Çöp kaydı bulunamadı")
    _, trash_path_str = record
    Path(trash_path_str).unlink(missing_ok=True)
    return {"status": "deleted"}


@app.get("/api/trash")
async def get_trash():
    if not current_directories:
        return {"items": []}
    result = []
    for d in current_directories:
        for item in cache_manager.get_trash_items(str(d)):
            result.append({
                **item,
                "filename": Path(item["original"]).name,
                "exists": Path(item["trash"]).exists()
            })
    return {"items": result}


# ──────────────────────────────────────────────
# Tags
# ──────────────────────────────────────────────

@app.get("/api/tags")
async def get_all_tags():
    if not current_directories:
        return {"tags": []}
    return {"tags": cache_manager.get_all_tags()}


@app.get("/api/tags/{path:path}")
async def get_image_tags(path: str):
    if not current_directories:
        return {"tags": []}
    full_path = find_in_directories(path)
    if full_path is None:
        return {"tags": []}
    return {"tags": cache_manager.get_image_tags(str(full_path))}


@app.post("/api/tag/{path:path}")
async def add_tag(path: str, data: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    tag = data.get("tag", "").strip()
    if not tag:
        raise HTTPException(400, "Tag boş olamaz")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Dosya bulunamadı")
    added = cache_manager.add_tag(str(full_path), tag)
    return {"added": added, "tag": tag.lower()}


@app.delete("/api/tag/{path:path}/{tag}")
async def remove_tag(path: str, tag: str):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Dosya bulunamadı")
    removed = cache_manager.remove_tag(str(full_path), tag)
    return {"removed": removed}


# ──────────────────────────────────────────────
# Favorites / Watch / Thumbnails
# ──────────────────────────────────────────────

@app.post("/api/favorite/{path:path}")
async def toggle_favorite(path: str):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Dosya bulunamadı")
    is_fav = cache_manager.toggle_favorite(str(full_path))
    return {"is_favorite": is_fav, "path": path}


@app.get("/api/favorites")
async def get_favorites():
    if not current_directories:
        return {"favorites": []}
    all_favs = set(cache_manager.get_favorites())
    result = []
    for d in current_directories:
        d_str = str(d.resolve())
        for f in all_favs:
            if f.startswith(d_str + '/') or f.startswith(d_str + os.sep):
                try:
                    result.append(str(Path(f).relative_to(d)))
                except ValueError:
                    pass
    return {"favorites": result}


# ──────────────────────────────────────────────
# Batch Operations
# ──────────────────────────────────────────────

@app.post("/api/batch/delete")
async def batch_delete(data: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    paths = data.get("paths", [])
    results = []
    errors = []
    for idx, path in enumerate(paths):
        try:
            full_path = find_in_directories(path)
            if full_path is None or not full_path.exists():
                errors.append({"path": path, "error": "Dosya bulunamadı"})
                continue
            base = _dir_for_path(full_path) or current_directories[0]
            trash_dir = base / ".gallery_trash"
            trash_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)
            trash_path = trash_dir / f"{timestamp}_{idx:04d}_{full_path.name}"
            try:
                full_path.rename(trash_path)
            except FileNotFoundError:
                errors.append({"path": path, "error": "Dosya taşınırken bulunamadı"})
                continue
            except OSError as e:
                logger.error("batch_delete rename failed: %s", e)
                errors.append({"path": path, "error": str(e)})
                continue
            trash_id = cache_manager.add_to_trash(str(full_path), str(trash_path))
            results.append({"path": path, "trash_id": trash_id, "filename": full_path.name})
        except Exception as e:
            logger.error("batch_delete unexpected error for %s: %s", path, e)
            errors.append({"path": path, "error": "Beklenmeyen hata"})
    return {"deleted": results, "count": len(results), "errors": errors}


@app.post("/api/batch/favorite")
async def batch_favorite(data: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    paths = data.get("paths", [])
    action = data.get("action", "add")   # "add" | "remove"
    count = 0
    favs = set(cache_manager.get_favorites())
    for path in paths:
        full_path = find_in_directories(path)
        if full_path is None:
            continue
        full = str(full_path)
        if action == "add" and full not in favs:
            cache_manager.toggle_favorite(full)
            count += 1
        elif action == "remove" and full in favs:
            cache_manager.toggle_favorite(full)
            count += 1
    return {"count": count, "action": action}


@app.post("/api/batch/tag")
async def batch_tag(data: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    paths = data.get("paths", [])
    tag = data.get("tag", "").strip()
    if not tag:
        raise HTTPException(400, "Tag boş olamaz")
    count = 0
    for path in paths:
        full_path = find_in_directories(path)
        if full_path is None:
            continue
        if cache_manager.add_tag(str(full_path), tag):
            count += 1
    return {"count": count, "tag": tag.lower()}


# ──────────────────────────────────────────────
# Export (Zip)
# ──────────────────────────────────────────────

def _apply_watermark(img, config: dict):
    """Apply text watermark to a PIL Image copy. Returns new image (original unchanged)."""
    from PIL import ImageDraw, ImageFont
    img = img.copy().convert("RGBA")
    overlay = img.copy()
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    text = config.get("text", "GalleryWeb") or "GalleryWeb"
    font_size = max(12, int(max(w, h) * float(config.get("size", 0.04))))
    font = None
    for font_path in [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if Path(font_path).exists():
            try:
                from PIL import ImageFont as _IF
                font = _IF.truetype(font_path, font_size)
                break
            except Exception:
                pass
    if font is None:
        from PIL import ImageFont as _IF
        font = _IF.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = max(10, int(min(w, h) * 0.02))
    pos_map = {
        "bottom-right": (w - tw - margin, h - th - margin),
        "bottom-left":  (margin, h - th - margin),
        "top-right":    (w - tw - margin, margin),
        "top-left":     (margin, margin),
        "center":       ((w - tw) // 2, (h - th) // 2),
    }
    x, y = pos_map.get(config.get("position", "bottom-right"), (w - tw - margin, h - th - margin))
    opacity = int(255 * max(0.0, min(1.0, float(config.get("opacity", 0.6)))))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
    from PIL import Image as _Img
    return _Img.alpha_composite(img, overlay).convert("RGB")


MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500 MB


@app.post("/api/export")
async def export_zip(data: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    paths = data.get("paths", [])
    if not paths:
        raise HTTPException(400, "Dışa aktarılacak dosya yok")

    watermark_config = data.get("watermark")  # None or dict

    import zipfile
    import io

    # Toplam dosya boyutu ön kontrolü
    total_size = 0
    for path in paths:
        fp = find_in_directories(path)
        if fp and fp.exists():
            try:
                total_size += fp.stat().st_size
            except OSError:
                pass
    if total_size > MAX_ZIP_SIZE:
        raise HTTPException(400, f"Toplam dosya boyutu sınırı aşıldı (maks {MAX_ZIP_SIZE // 1024 // 1024} MB)")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            full_path = find_in_directories(path)
            if full_path is None or not full_path.exists():
                continue

            if watermark_config and full_path.suffix.lower() in {
                '.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'
            }:
                try:
                    from PIL import Image as _Img
                    img = _Img.open(full_path)
                    img = _apply_watermark(img, watermark_config)
                    img_buf = io.BytesIO()
                    fmt = full_path.suffix.lstrip('.').upper()
                    if fmt in ('JPG',):
                        fmt = 'JPEG'
                    save_kw = {'quality': 92} if fmt == 'JPEG' else {}
                    img.save(img_buf, format=fmt, **save_kw)
                    img_buf.seek(0)
                    zf.writestr(full_path.name, img_buf.read())
                    continue
                except Exception:
                    pass  # fallback: add original

            zf.write(full_path, full_path.name)
    buf.seek(0)

    from fastapi.responses import Response
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="gallery-export.zip"'}
    )


# ──────────────────────────────────────────────
# Notes
# ──────────────────────────────────────────────

@app.get("/api/note/{path:path}")
async def get_note(path: str):
    if not current_directories:
        return {"note": ""}
    full_path = find_in_directories(path)
    if full_path is None:
        return {"note": ""}
    return {"note": cache_manager.get_note(str(full_path))}


@app.post("/api/note/{path:path}")
async def set_note(path: str, data: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Dosya bulunamadı")
    content = data.get("content", "")
    cache_manager.set_note(str(full_path), content)
    return {"status": "saved"}


# ──────────────────────────────────────────────
# Ratings
# ──────────────────────────────────────────────

@app.get("/api/ratings")
async def get_ratings():
    if not current_directories:
        return {"ratings": {}}
    all_ratings = cache_manager.get_all_ratings()
    rel = {}
    for abs_path, stars in all_ratings.items():
        ap = Path(abs_path)
        for d in current_directories:
            try:
                rel_path = str(ap.relative_to(d))
                rel[rel_path] = stars
                break
            except ValueError:
                pass
    return {"ratings": rel}


@app.post("/api/rating/{path:path}")
async def set_rating(path: str, data: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Dosya bulunamadı")
    stars = data.get("stars")
    if not isinstance(stars, int) or not (1 <= stars <= 5):
        raise HTTPException(400, "stars must be 1-5")
    cache_manager.set_rating(str(full_path), stars)
    return {"ok": True, "stars": stars}


@app.delete("/api/rating/{path:path}")
async def delete_rating(path: str):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Dosya bulunamadı")
    cache_manager.delete_rating(str(full_path))
    return {"ok": True}


# ──────────────────────────────────────────────
# Bookmarks
# ──────────────────────────────────────────────

@app.get("/api/bookmarks")
async def get_bookmarks():
    return {"bookmarks": cache_manager.get_bookmarks()}


@app.post("/api/bookmark")
async def add_bookmark(data: dict):
    path = data.get("path", "").strip()
    label = data.get("label", "").strip()
    if not path:
        raise HTTPException(400, "path gerekli")
    bm_id = cache_manager.add_bookmark(path, label)
    return {"ok": True, "id": bm_id}


@app.delete("/api/bookmark/{bm_id}")
async def remove_bookmark(bm_id: int):
    removed = cache_manager.remove_bookmark(bm_id)
    return {"ok": removed}


# ──────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats():
    if not current_directories:
        return {"error": "Klasör seçilmemiş"}

    supported_images = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    supported_videos = {'.mp4', '.webm', '.mov'}
    supported = supported_images | supported_videos

    MAX_SCAN = 100_000  # büyük kütüphanelerde takılmayı önle
    all_files = list(itertools.islice(
        itertools.chain.from_iterable(d.rglob("*") for d in current_directories),
        MAX_SCAN,
    ))
    media_files = [p for p in all_files if p.is_file() and p.suffix.lower() in supported]
    image_files = [p for p in media_files if p.suffix.lower() in supported_images]
    video_files = [p for p in media_files if p.suffix.lower() in supported_videos]

    total_bytes = sum(p.stat().st_size for p in media_files if p.exists())

    favs = cache_manager.get_favorites()
    dir_prefixes = tuple(str(d.resolve()) + os.sep for d in current_directories)
    fav_count = sum(1 for f in favs if any(f.startswith(pf) for pf in dir_prefixes))

    top_tags = cache_manager.get_all_tags()[:10]
    tagged_paths = set()
    for tag_info in cache_manager.get_all_tags():
        imgs = cache_manager.get_images_with_tags([tag_info["name"]])
        tagged_paths.update(imgs)
    tagged_count = len([p for p in tagged_paths if any(p.startswith(pf) for pf in dir_prefixes)])

    rating_dist = cache_manager.get_rating_distribution()
    total_rated = sum(rating_dist.values())
    avg_rating = (
        sum(k * v for k, v in rating_dist.items()) / total_rated
        if total_rated > 0 else None
    )

    mtimes = [p.stat().st_mtime for p in media_files if p.exists()]
    oldest = min(mtimes) if mtimes else None
    newest = max(mtimes) if mtimes else None

    import datetime
    def ts_to_date(ts):
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts else None

    return {
        "total_files": len(all_files),
        "images_count": len(image_files),
        "videos_count": len(video_files),
        "storage_gb": round(total_bytes / (1024 ** 3), 3),
        "favorite_count": fav_count,
        "tagged_count": tagged_count,
        "top_tags": top_tags,
        "rating_distribution": rating_dist,
        "avg_rating": round(avg_rating, 2) if avg_rating else None,
        "oldest_file": ts_to_date(oldest),
        "newest_file": ts_to_date(newest),
    }


# ──────────────────────────────────────────────
# Duplicate Detection
# ──────────────────────────────────────────────

@app.get("/api/duplicates")
async def find_duplicate_images(threshold: int = 8, include_subfolders: bool = False):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    try:
        from duplicate_finder import find_duplicates
    except ImportError:
        raise HTTPException(500, "imagehash kütüphanesi yüklü değil (pip install imagehash)")

    supported_images = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    image_paths = []
    for d in current_directories:
        scanner = d.rglob("*") if include_subfolders else d.iterdir()
        image_paths.extend(p for p in scanner if p.is_file() and p.suffix.lower() in supported_images)

    if not image_paths:
        return {"groups": [], "count": 0}

    groups = await asyncio.get_running_loop().run_in_executor(
        thumbnail_gen.executor,
        lambda: find_duplicates(image_paths, threshold=max(0, min(20, threshold)))
    )

    result = []
    for group in groups:
        result.append([
            {
                "path": _relative_to_any(Path(p)),
                "size": Path(p).stat().st_size
            }
            for p in group if Path(p).exists()
        ])

    return {"groups": result, "count": sum(len(g) for g in result)}


@app.post("/api/generate-thumbnails")
async def generate_all_thumbnails():
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    for d in current_directories:
        asyncio.create_task(thumbnail_gen.batch_generate(d))
    return {"status": "started"}


@app.get("/api/watch")
async def watch_directory(request: Request):
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    class Handler(FileSystemEventHandler):
        def dispatch(self, event):
            if not event.is_directory:
                asyncio.run_coroutine_threadsafe(
                    queue.put({"type": event.event_type}), loop
                )

    async def stream():
        if not current_directories:
            yield 'data: {"type":"no_directory"}\n\n'
            return
        observer = Observer()
        for d in current_directories:
            observer.schedule(Handler(), str(d), recursive=False)
        observer.start()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=25)
                    yield f"data: {json.dumps(ev)}\n\n"
                except asyncio.TimeoutError:
                    yield 'data: {"type":"ping"}\n\n'
        finally:
            observer.stop()
            observer.join()

    return StreamingResponse(
        stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ──────────────────────────────────────────────
# Albums
# ──────────────────────────────────────────────

@app.get("/api/albums")
async def get_albums():
    return {"albums": cache_manager.get_albums()}


@app.post("/api/albums")
async def create_album(body: dict):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(400, "Album adı gerekli")
    description = body.get("description", "")
    try:
        album_id = cache_manager.create_album(name, description)
        return {"id": album_id, "name": name}
    except Exception:
        raise HTTPException(409, "Bu isimde bir album zaten var")


@app.get("/api/albums/{album_id}")
async def get_album(album_id: int):
    album = cache_manager.get_album(album_id)
    if not album:
        raise HTTPException(404, "Album bulunamadı")
    if current_directories:
        rel_images = []
        for p in album["images"]:
            ap = Path(p)
            converted = False
            for d in current_directories:
                try:
                    rel_images.append(str(ap.relative_to(d)))
                    converted = True
                    break
                except ValueError:
                    pass
            if not converted:
                rel_images.append(p)
        album["images"] = rel_images
    return album


@app.put("/api/albums/{album_id}")
async def update_album(album_id: int, body: dict):
    if not cache_manager.get_album(album_id):
        raise HTTPException(404, "Album bulunamadı")
    cache_manager.update_album(
        album_id,
        name=body.get("name"),
        description=body.get("description"),
        cover_path=body.get("cover_path")
    )
    return {"ok": True}


@app.delete("/api/albums/{album_id}")
async def delete_album(album_id: int):
    if not cache_manager.get_album(album_id):
        raise HTTPException(404, "Album bulunamadı")
    cache_manager.delete_album(album_id)
    return {"ok": True}


@app.post("/api/albums/{album_id}/images")
async def add_to_album(album_id: int, body: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    if not cache_manager.get_album(album_id):
        raise HTTPException(404, "Album bulunamadı")
    paths = body.get("paths", [])
    abs_paths = []
    for p in paths:
        full_path = find_in_directories(p)
        if full_path is not None:
            abs_paths.append(str(full_path))
    cache_manager.add_images_to_album(album_id, abs_paths)
    return {"ok": True, "added": len(abs_paths)}


@app.delete("/api/albums/{album_id}/images/{path:path}")
async def remove_from_album(album_id: int, path: str):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")
    full_path = find_in_directories(path)
    if full_path is None:
        raise HTTPException(404, "Dosya bulunamadı")
    cache_manager.remove_image_from_album(album_id, str(full_path))
    return {"ok": True}


# ──────────────────────────────────────────────
# Batch Copy / Move
# ──────────────────────────────────────────────

@app.post("/api/batch/copy")
async def batch_copy(body: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")

    paths = body.get("paths", [])
    destination = body.get("destination", "").strip()
    if not paths or not destination:
        raise HTTPException(400, "paths ve destination gerekli")

    dest = Path(os.path.expanduser(destination)).resolve()
    if not dest.is_dir():
        raise HTTPException(400, f"Hedef klasör bulunamadı: {destination}")

    import shutil as _shutil
    results = []
    for p in paths:
        try:
            src = find_in_directories(p)
            if src is None:
                results.append({"path": p, "ok": False, "error": "Dosya bulunamadı"})
                continue
            target = dest / src.name
            # İsim çakışması önleme
            if target.exists():
                stem, suffix = src.stem, src.suffix
                counter = 1
                while target.exists():
                    target = dest / f"{stem}_copy{counter}{suffix}"
                    counter += 1
            _shutil.copy2(src, target)
            results.append({"path": p, "ok": True, "dest": str(target.name)})
        except Exception as e:
            results.append({"path": p, "ok": False, "error": str(e)})

    return {"results": results, "success_count": sum(r["ok"] for r in results)}


@app.post("/api/batch/move")
async def batch_move(body: dict):
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")

    paths = body.get("paths", [])
    destination = body.get("destination", "").strip()
    if not paths or not destination:
        raise HTTPException(400, "paths ve destination gerekli")

    dest = Path(os.path.expanduser(destination)).resolve()
    if not dest.is_dir():
        raise HTTPException(400, f"Hedef klasör bulunamadı: {destination}")

    # Hedef = kaynak kontrolü (herhangi bir aktif dizinle çakışmasın)
    if any(dest == d.resolve() for d in current_directories):
        raise HTTPException(400, "Hedef ve kaynak aynı klasör olamaz")

    results = []
    import shutil as _shutil
    for p in paths:
        try:
            src = find_in_directories(p)
            if src is None:
                results.append({"path": p, "ok": False, "error": "Dosya bulunamadı"})
                continue
            target = dest / src.name
            if target.exists():
                stem, suffix = src.stem, src.suffix
                counter = 1
                while target.exists():
                    target = dest / f"{stem}_moved{counter}{suffix}"
                    counter += 1
            _shutil.move(str(src), str(target))
            cache_manager.move_metadata(str(src), str(target))
            results.append({"path": p, "ok": True, "dest": str(target.name)})
        except Exception as e:
            results.append({"path": p, "ok": False, "error": str(e)})

    return {"results": results, "success_count": sum(r["ok"] for r in results)}


# ──────────────────────────────────────────────
# Faz 5.3 — Batch EXIF Editing
# ──────────────────────────────────────────────

@app.post("/api/batch/exif")
async def batch_exif(body: dict):
    """Write EXIF fields to multiple images. Empty/missing fields are skipped."""
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")

    paths = body.get("paths", [])
    fields = body.get("fields", {})
    if not paths:
        raise HTTPException(400, "paths gerekli")
    if not fields:
        raise HTTPException(400, "fields boş — hiçbir şey yazılmaz")

    try:
        import pyexiv2
    except ImportError:
        raise HTTPException(500, "pyexiv2 paketi yüklü değil: pip install pyexiv2")

    # Supported writable EXIF keys
    _FIELD_MAP = {
        "artist":      "Exif.Image.Artist",
        "copyright":   "Exif.Image.Copyright",
        "description": "Exif.Image.ImageDescription",
        "datetime":    "Exif.Image.DateTime",
    }

    results = []
    for p in paths:
        try:
            full_path = find_in_directories(p)
            if full_path is None:
                results.append({"path": p, "ok": False, "error": "Dosya bulunamadı"})
                continue

            img = pyexiv2.Image(str(full_path))
            exif = img.read_exif()

            updated = {}
            for field_key, exif_tag in _FIELD_MAP.items():
                value = fields.get(field_key, "").strip()
                if not value:
                    continue
                if field_key == "datetime":
                    # Accept ISO format yyyy-mm-ddThh:mm:ss or yyyy-mm-dd
                    from datetime import datetime
                    try:
                        if "T" in value:
                            dt = datetime.fromisoformat(value)
                        else:
                            dt = datetime.strptime(value, "%Y-%m-%d")
                        # EXIF DateTime format: "YYYY:MM:DD HH:MM:SS"
                        value = dt.strftime("%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        results.append({"path": p, "ok": False, "error": f"Geçersiz tarih: {value}"})
                        img.close()
                        continue
                exif[exif_tag] = value
                updated[field_key] = value

            img.modify_exif(exif)
            img.close()
            results.append({"path": p, "ok": True, "updated": updated})
        except Exception as e:
            results.append({"path": p, "ok": False, "error": str(e)})

    success = sum(1 for r in results if r.get("ok"))
    return {"results": results, "success_count": success, "total": len(results)}


# ──────────────────────────────────────────────
# QR Code
# ──────────────────────────────────────────────

@app.get("/api/qr")
async def get_qr():
    try:
        import qrcode
        import io
        from fastapi.responses import Response
    except ImportError:
        raise HTTPException(500, "qrcode paketi yüklü değil: pip install 'qrcode[pil]'")

    port = _PORT
    if _local_ip:
        url = f"http://{_local_ip}:{port}"
    else:
        url = f"http://localhost:{port}"

    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@app.get("/api/qr-url")
async def get_qr_url():
    port = _PORT
    if _local_ip:
        return {"url": f"http://{_local_ip}:{port}", "ip": _local_ip}
    return {"url": f"http://localhost:{port}", "ip": None}


# ──────────────────────────────────────────────
# Map View (GPS/EXIF)
# ──────────────────────────────────────────────

def _dms_to_decimal(dms_list, ref: str) -> float | None:
    """Convert EXIF DMS (list of fractions as 'num/den' strings) to decimal degrees."""
    try:
        def frac(s):
            n, d = s.split('/')
            return int(n) / int(d)
        d, m, s = [frac(v) for v in dms_list]
        dec = d + m / 60 + s / 3600
        return -dec if ref in ('S', 'W') else dec
    except Exception:
        return None


def _extract_gps(exif_dict: dict) -> tuple[float | None, float | None]:
    try:
        lat_dms = exif_dict.get('Exif.GPSInfo.GPSLatitude')
        lat_ref = exif_dict.get('Exif.GPSInfo.GPSLatitudeRef', 'N')
        lon_dms = exif_dict.get('Exif.GPSInfo.GPSLongitude')
        lon_ref = exif_dict.get('Exif.GPSInfo.GPSLongitudeRef', 'E')
        if lat_dms and lon_dms:
            lat = _dms_to_decimal(lat_dms, lat_ref)
            lon = _dms_to_decimal(lon_dms, lon_ref)
            return lat, lon
    except Exception:
        pass
    return None, None


@app.get("/api/images/map")
async def get_map_images():
    if not current_directories:
        raise HTTPException(400, "Klasör seçilmemiş")

    supported = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.avif', '.tiff'}
    image_paths = []
    for d in current_directories:
        image_paths.extend(p for p in d.rglob("*") if p.suffix.lower() in supported)

    results = []
    for p in image_paths:
        rel = _relative_to_any(p)
        # Check cached metadata first
        cached = cache_manager.get_image_metadata(str(p))
        lat, lon = None, None
        if cached and cached.get('gps_latitude') is not None:
            lat, lon = cached['gps_latitude'], cached['gps_longitude']
        else:
            try:
                import pyexiv2
                img = pyexiv2.Image(str(p))
                exif = img.read_exif()
                img.close()
                lat, lon = _extract_gps(exif)
                if lat is not None:
                    cache_manager.upsert_image_metadata(str(p), gps_latitude=lat, gps_longitude=lon)
            except Exception:
                pass

        if lat is not None and lon is not None:
            results.append({"path": rel, "lat": lat, "lng": lon})

    return {"images": results, "total": len(results)}


# ──────────────────────────────────────────────
# Faz 5.1 — Image Editing (rotate / crop / adjust)
# ──────────────────────────────────────────────

@app.post("/api/edit/{path:path}")
async def edit_image(path: str, body: dict):
    """Edit image in-place. Backs up original to .gallery_originals/ on first edit."""
    full_path = find_in_directories(path)
    if not full_path:
        raise HTTPException(404, "Resim bulunamadı")

    # Only allow editing actual image files (not videos)
    if full_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp', '.tiff', '.bmp'}:
        raise HTTPException(400, "Bu dosya türü düzenlenemez")

    # Backup original (only once — first edit)
    backup_dir = full_path.parent / '.gallery_originals'
    backup_path = backup_dir / full_path.name
    if not backup_path.exists():
        backup_dir.mkdir(exist_ok=True)
        import shutil as _shutil
        _shutil.copy2(full_path, backup_path)

    try:
        from PIL import Image as _Image, ImageEnhance as _Enhance
        img = _Image.open(full_path)

        operation = body.get("operation")
        params = body.get("params", {})

        if operation == "rotate":
            degrees = int(params.get("degrees", 90))
            img = img.rotate(-degrees, expand=True)
        elif operation == "crop":
            x = int(params.get("x", 0))
            y = int(params.get("y", 0))
            w = int(params.get("w", img.width))
            h = int(params.get("h", img.height))
            # Clamp to image bounds
            x2 = min(x + w, img.width)
            y2 = min(y + h, img.height)
            img = img.crop((x, y, x2, y2))
        elif operation == "adjust":
            brightness = float(params.get("brightness", 1.0))
            contrast = float(params.get("contrast", 1.0))
            if brightness != 1.0:
                img = _Enhance.Brightness(img).enhance(brightness)
            if contrast != 1.0:
                img = _Enhance.Contrast(img).enhance(contrast)
        else:
            raise HTTPException(400, f"Bilinmeyen operasyon: {operation}")

        # Save — keep original format, use quality=92 for lossy
        save_kwargs = {}
        fmt = img.format or full_path.suffix.lstrip('.').upper()
        if fmt in ('JPEG', 'JPG'):
            fmt = 'JPEG'
            save_kwargs['quality'] = 92
            save_kwargs['subsampling'] = 0
        img.save(full_path, format=fmt, **save_kwargs)
        cache_manager.invalidate_thumbnail(str(full_path))
        return {"ok": True, "has_backup": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Düzenleme hatası: {e}")


@app.post("/api/edit/{path:path}/revert")
async def revert_edit(path: str):
    """Restore original file from .gallery_originals/ backup."""
    full_path = find_in_directories(path)
    if not full_path:
        raise HTTPException(404, "Resim bulunamadı")

    backup_path = full_path.parent / '.gallery_originals' / full_path.name
    if not backup_path.exists():
        return {"ok": False, "reverted": False, "reason": "Yedek bulunamadı"}

    import shutil as _shutil
    _shutil.copy2(backup_path, full_path)
    cache_manager.invalidate_thumbnail(str(full_path))
    return {"ok": True, "reverted": True}


@app.get("/api/edit/{path:path}/has-backup")
async def has_backup(path: str):
    full_path = find_in_directories(path)
    if not full_path:
        return {"has_backup": False}
    backup_path = full_path.parent / '.gallery_originals' / full_path.name
    return {"has_backup": backup_path.exists()}


# ──────────────────────────────────────────────
# PWA Manifest + Service Worker
# ──────────────────────────────────────────────

@app.get("/manifest.json")
async def get_manifest():
    return JSONResponse({
        "name": "GalleryPro",
        "short_name": "Gallery",
        "description": "Yerel fotoğraf galerisi",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1a1a1a",
        "theme_color": "#3b82f6",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    })


@app.get("/sw.js")
async def get_service_worker():
    sw_path = FRONTEND_DIR / "sw.js"
    if not sw_path.exists():
        raise HTTPException(404, "Service worker bulunamadı")
    from fastapi.responses import FileResponse as FR
    return FR(str(sw_path), media_type="application/javascript")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=_PORT, reload=True, log_level="info")
