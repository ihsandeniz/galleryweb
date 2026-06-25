from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..database import get_db, AsyncSessionLocal
from ..auth import get_current_user, get_current_user_optional
from ..models import Profile, Gallery, Photo, SharingLink
from ..schemas import PhotoOut, PhotoUpdate, PaginatedResponse
from ..storage import get_storage
from pathlib import Path
import asyncio
import io
import uuid
import math
import mimetypes
import logging
from datetime import datetime

logger = logging.getLogger("galleryweb.photos")

router = APIRouter(prefix="/api/photos", tags=["photos"])

SUPPORTED_MIME = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/heic", "image/avif", "image/tiff", "image/bmp",
    "video/mp4", "video/webm", "video/quicktime",
}

_IMAGE_MIME = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/heic", "image/avif", "image/tiff", "image/bmp",
}

_THUMB_SIZES = {"sm": 128, "md": 256, "lg": 1080}


def _extract_exif_and_thumbs(content: bytes, mime: str) -> dict:
    """Run synchronously in executor — returns metadata dict + thumb bytes per size."""
    result = {"width": None, "height": None, "taken_at": None,
              "camera_make": None, "camera_model": None,
              "lens": None, "focal_length_mm": None,
              "aperture": None, "shutter_speed": None, "iso": None,
              "gps_lat": None, "gps_lon": None,
              "thumbs": {}}

    if mime not in _IMAGE_MIME:
        return result

    try:
        from PIL import Image, ExifTags
        img = Image.open(io.BytesIO(content))
        result["width"], result["height"] = img.size

        # ── Thumbnails ─────────────────────────────────────────────────────────
        for name, max_px in _THUMB_SIZES.items():
            thumb = img.copy()
            thumb.thumbnail((max_px, max_px), Image.LANCZOS)
            buf = io.BytesIO()
            thumb.convert("RGB").save(buf, format="WEBP", quality=82)
            result["thumbs"][name] = buf.getvalue()

        # ── EXIF ───────────────────────────────────────────────────────────────
        raw_exif = img._getexif()  # returns None for non-JPEG or missing EXIF
        if not raw_exif:
            return result

        tag_map = {v: k for k, v in ExifTags.TAGS.items()}

        def _tag(name):
            tag_id = tag_map.get(name)
            return raw_exif.get(tag_id) if tag_id else None

        # Date/time
        dto = _tag("DateTimeOriginal") or _tag("DateTime")
        if dto:
            try:
                result["taken_at"] = datetime.strptime(dto, "%Y:%m:%d %H:%M:%S")
            except ValueError:
                pass

        result["camera_make"] = str(_tag("Make")).strip() if _tag("Make") else None
        result["camera_model"] = str(_tag("Model")).strip() if _tag("Model") else None
        result["lens"] = str(_tag("LensModel")).strip() if _tag("LensModel") else None

        fl = _tag("FocalLength")
        if fl:
            try:
                result["focal_length_mm"] = float(fl)
            except (TypeError, ZeroDivisionError):
                pass

        fn = _tag("FNumber")
        if fn:
            try:
                result["aperture"] = float(fn)
            except (TypeError, ZeroDivisionError):
                pass

        ss = _tag("ExposureTime")
        if ss:
            try:
                result["shutter_speed"] = str(ss)
            except Exception:
                pass

        iso = _tag("ISOSpeedRatings")
        if iso:
            try:
                result["iso"] = int(iso)
            except (TypeError, ValueError):
                pass

        # GPS
        gps_info = _tag("GPSInfo")
        if gps_info and isinstance(gps_info, dict):
            from PIL.ExifTags import GPSTAGS
            gps = {GPSTAGS.get(k, k): v for k, v in gps_info.items()}

            def _dms(vals, ref):
                try:
                    d, m, s = (float(x) for x in vals)
                    dec = d + m / 60 + s / 3600
                    return -dec if ref in ("S", "W") else dec
                except Exception:
                    return None

            lat = _dms(gps.get("GPSLatitude", []), gps.get("GPSLatitudeRef", ""))
            lon = _dms(gps.get("GPSLongitude", []), gps.get("GPSLongitudeRef", ""))
            result["gps_lat"] = lat
            result["gps_lon"] = lon

    except Exception:
        pass  # EXIF/thumb errors are non-fatal

    return result


@router.get("", response_model=PaginatedResponse)
async def list_photos(
    gallery_id: int | None = None,
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    favorites_only: bool = False,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Photo).where(Photo.user_id == current_user.id, Photo.is_deleted == False)
    if gallery_id:
        q = q.where(Photo.gallery_id == gallery_id)
    if search:
        q = q.where(Photo.filename.ilike(f"%{search}%"))
    if favorites_only:
        q = q.where(Photo.is_favorite == True)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    q = q.order_by(Photo.taken_at.desc().nulls_last(), Photo.created_at.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    photos = (await db.execute(q)).scalars().all()

    return PaginatedResponse(
        items=[PhotoOut.model_validate(p) for p in photos],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 1,
    )


async def _embed_photo_background(photo_id: int, image_content: bytes) -> None:
    """Embed photo with CLIP after upload — runs outside request scope."""
    from ..services.clip_service import get_clip_service
    clip = get_clip_service()
    try:
        emb = await clip.encode_image_from_bytes(image_content)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Photo).where(Photo.id == photo_id))
            photo = result.scalar_one_or_none()
            if photo:
                photo.embedding = emb
                await db.commit()
                logger.info(f"Photo {photo_id} embedded (512-dim)")
    except Exception as exc:
        logger.warning(f"Embedding failed for photo {photo_id}: {exc}")


@router.post("", response_model=PhotoOut, status_code=201)
async def upload_photo(
    gallery_id: int = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate gallery ownership
    gallery_res = await db.execute(
        select(Gallery).where(Gallery.id == gallery_id, Gallery.user_id == current_user.id)
    )
    gallery = gallery_res.scalar_one_or_none()
    if not gallery:
        raise HTTPException(404, "Galeri bulunamadı")

    # MIME check
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime not in SUPPORTED_MIME:
        raise HTTPException(400, f"Desteklenmeyen dosya türü: {mime}")

    # Read & quota check
    content = await file.read()
    file_size = len(content)
    if current_user.storage_used_bytes + file_size > current_user.storage_quota_bytes:
        raise HTTPException(
            413,
            f"Depolama kotası doldu ({current_user.storage_quota_gb} GB). "
            "Planı yükselt veya eski dosyaları sil."
        )

    # EXIF + thumbnail extraction (non-blocking)
    loop = asyncio.get_event_loop()
    meta = await loop.run_in_executor(None, _extract_exif_and_thumbs, content, mime)

    # Build storage keys
    ext = Path(file.filename or "photo").suffix or ".jpg"
    base_key = f"{current_user.id}/{uuid.uuid4()}"
    file_key = f"{base_key}{ext}"

    storage = get_storage()

    # Upload original
    result = await storage.put(content, file_key, mime)

    # Upload thumbnails
    thumb_key_base: str | None = None
    if meta["thumbs"]:
        thumb_key_base = f"{base_key}_thumb"
        for size_name, thumb_bytes in meta["thumbs"].items():
            await storage.put(thumb_bytes, f"{thumb_key_base}_{size_name}.webp", "image/webp")

    # Persist photo record
    photo = Photo(
        gallery_id=gallery_id,
        user_id=current_user.id,
        filename=file.filename or Path(file_key).name,
        file_size_bytes=file_size,
        mime_type=mime,
        r2_key=file_key if storage.is_r2 else None,
        local_path=result.url if not storage.is_r2 else None,
        thumbnail_key=thumb_key_base,
        width=meta["width"],
        height=meta["height"],
        taken_at=meta["taken_at"],
        camera_make=meta["camera_make"],
        camera_model=meta["camera_model"],
        lens=meta["lens"],
        focal_length_mm=meta["focal_length_mm"],
        aperture=meta["aperture"],
        shutter_speed=meta["shutter_speed"],
        iso=meta["iso"],
        gps_lat=meta["gps_lat"],
        gps_lon=meta["gps_lon"],
    )
    db.add(photo)

    gallery.photo_count = (gallery.photo_count or 0) + 1
    current_user.storage_used_bytes = (current_user.storage_used_bytes or 0) + file_size

    await db.commit()
    await db.refresh(photo)

    # Kick off CLIP embedding in background (images only)
    if mime in _IMAGE_MIME and background_tasks is not None:
        background_tasks.add_task(_embed_photo_background, photo.id, content)

    return PhotoOut.model_validate(photo)


@router.get("/{photo_id}", response_model=PhotoOut)
async def get_photo(
    photo_id: int,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == current_user.id)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Fotoğraf bulunamadı")
    return PhotoOut.model_validate(photo)


@router.get("/{photo_id}/file")
async def serve_photo(
    photo_id: int,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve photo: R2 presigned redirect or local FileResponse."""
    result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == current_user.id, Photo.is_deleted == False)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    storage = get_storage()
    if storage.is_r2 and photo.r2_key:
        url = storage.presigned_get_url(photo.r2_key, expires=3600)
        return RedirectResponse(url=url, status_code=302)

    if photo.local_path and Path(photo.local_path).exists():
        return FileResponse(photo.local_path, media_type=photo.mime_type)

    raise HTTPException(404, "Dosya bulunamadı")


@router.get("/{photo_id}/thumb")
async def serve_thumbnail(
    photo_id: int,
    size: str = "md",
    share_token: str | None = None,
    token: str | None = None,
    current_user: Profile | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Serve thumbnail.

    Auth: JWT token (Authorization header or ?token= query param for <img> tags)
    OR share_token query param (public share page).
    """
    if size not in _THUMB_SIZES:
        raise HTTPException(400, "Geçersiz boyut — sm | md | lg")

    # token in URL fallback — for <img> tags that cannot send Authorization headers
    if token and not current_user:
        try:
            from ..auth import _verify_token
            import uuid as _uuid
            payload = await _verify_token(token)
            uid = _uuid.UUID(payload["sub"])
            r = await db.execute(select(Profile).where(Profile.id == uid))
            current_user = r.scalar_one_or_none()
        except Exception:
            pass

    if share_token:
        # Validate: sharing_link exists and the photo belongs to its gallery
        link_res = await db.execute(
            select(SharingLink).where(SharingLink.id == share_token)
        )
        link = link_res.scalar_one_or_none()
        if not link:
            raise HTTPException(403, "Geçersiz paylaşım linki")
        photo_res = await db.execute(
            select(Photo).where(
                Photo.id == photo_id,
                Photo.gallery_id == link.gallery_id,
                Photo.is_deleted == False,
            )
        )
        photo = photo_res.scalar_one_or_none()
    elif current_user:
        photo_res = await db.execute(
            select(Photo).where(
                Photo.id == photo_id,
                Photo.user_id == current_user.id,
                Photo.is_deleted == False,
            )
        )
        photo = photo_res.scalar_one_or_none()
    else:
        raise HTTPException(401, "Kimlik doğrulama gerekli")

    if not photo:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    if not photo.thumbnail_key:
        # Fall back to full image (local path)
        if photo.local_path and Path(photo.local_path).exists():
            return FileResponse(photo.local_path, media_type=photo.mime_type)
        raise HTTPException(404, "Thumbnail bulunamadı")

    thumb_key = f"{photo.thumbnail_key}_{size}.webp"
    storage = get_storage()

    if storage.is_r2:
        url = storage.presigned_get_url(thumb_key, expires=3600)
        return RedirectResponse(url=url, status_code=302)

    local_path = Path(storage.url(thumb_key) or "")
    if local_path.exists():
        return FileResponse(str(local_path), media_type="image/webp")

    raise HTTPException(404, "Thumbnail bulunamadı")


@router.get("/{photo_id}/presigned")
async def get_presigned_url(
    photo_id: int,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return R2 presigned GET URL (1h). Local fallback returns the /file URL."""
    result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == current_user.id, Photo.is_deleted == False)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    storage = get_storage()
    if storage.is_r2 and photo.r2_key:
        return {"url": storage.presigned_get_url(photo.r2_key), "backend": "r2"}

    return {"url": f"/api/photos/{photo_id}/file", "backend": "local"}


@router.patch("/{photo_id}", response_model=PhotoOut)
async def update_photo(
    photo_id: int,
    body: PhotoUpdate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == current_user.id)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    changes = body.model_dump(exclude_none=True)
    if "gallery_id" in changes:
        gallery_res = await db.execute(
            select(Gallery).where(
                Gallery.id == changes["gallery_id"],
                Gallery.user_id == current_user.id
            )
        )
        if not gallery_res.scalar_one_or_none():
            raise HTTPException(404, "Hedef galeri bulunamadı")

    for k, v in changes.items():
        setattr(photo, k, v)
    await db.commit()
    await db.refresh(photo)
    return PhotoOut.model_validate(photo)


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: int,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == current_user.id)
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(404, "Fotoğraf bulunamadı")

    # Soft delete; optionally delete from storage (deferred to async cleanup job)
    photo.is_deleted = True
    current_user.storage_used_bytes = max(0, (current_user.storage_used_bytes or 0) - (photo.file_size_bytes or 0))
    await db.commit()
