from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from ..database import get_db
from ..auth import get_current_user
from ..models import Profile, Gallery, Photo
from ..schemas import GalleryCreate, GalleryUpdate, GalleryOut, PaginatedResponse
import math

router = APIRouter(prefix="/api/galleries", tags=["galleries"])


@router.get("", response_model=PaginatedResponse)
async def list_galleries(
    page: int = 1,
    per_page: int = 20,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    total_q = await db.execute(
        select(func.count()).select_from(Gallery).where(Gallery.user_id == current_user.id)
    )
    total = total_q.scalar_one()
    result = await db.execute(
        select(Gallery)
        .where(Gallery.user_id == current_user.id)
        .order_by(Gallery.updated_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    galleries = result.scalars().all()
    return PaginatedResponse(
        items=[GalleryOut.model_validate(g) for g in galleries],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 1,
    )


@router.post("", response_model=GalleryOut, status_code=201)
async def create_gallery(
    body: GalleryCreate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # VIP1 proofing gallery limit: 1/month
    if body.is_client_proofing and current_user.tier == "free":
        raise HTTPException(403, "Müşteri proofing galerisi VIP1+ gerektirir")

    gallery = Gallery(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        is_client_proofing=body.is_client_proofing,
        is_public=body.is_public,
    )
    db.add(gallery)
    await db.commit()
    await db.refresh(gallery)
    return GalleryOut.model_validate(gallery)


@router.get("/{gallery_id}", response_model=GalleryOut)
async def get_gallery(
    gallery_id: int,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Gallery).where(Gallery.id == gallery_id, Gallery.user_id == current_user.id)
    )
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(404, "Galeri bulunamadı")
    return GalleryOut.model_validate(gallery)


@router.patch("/{gallery_id}", response_model=GalleryOut)
async def update_gallery(
    gallery_id: int,
    body: GalleryUpdate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Gallery).where(Gallery.id == gallery_id, Gallery.user_id == current_user.id)
    )
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(404, "Galeri bulunamadı")

    changes = body.model_dump(exclude_none=True)
    for k, v in changes.items():
        setattr(gallery, k, v)
    await db.commit()
    await db.refresh(gallery)
    return GalleryOut.model_validate(gallery)


@router.delete("/{gallery_id}", status_code=204)
async def delete_gallery(
    gallery_id: int,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Gallery).where(Gallery.id == gallery_id, Gallery.user_id == current_user.id)
    )
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(404, "Galeri bulunamadı")
    await db.delete(gallery)
    await db.commit()
