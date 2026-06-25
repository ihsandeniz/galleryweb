from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import hashlib
from ..database import get_db
from ..auth import get_current_user
from ..models import Profile, Gallery, SharingLink, Photo, GalleryComment, GalleryVote, PhotoSelection, PhotoMarking
from ..schemas import (
    SharingLinkCreate, SharingLinkOut, PhotoOut,
    CommentCreate, CommentOut, VoteOut, SelectionOut,
    MarkingCreate, MarkingOut,
)

router = APIRouter(prefix="/api/sharing", tags=["sharing"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _make_share_url(request: Request, link_id: str) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/share/{link_id}"


@router.post("", response_model=SharingLinkOut, status_code=201)
async def create_sharing_link(
    body: SharingLinkCreate,
    request: Request,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gallery_res = await db.execute(
        select(Gallery).where(Gallery.id == body.gallery_id, Gallery.user_id == current_user.id)
    )
    gallery = gallery_res.scalar_one_or_none()
    if not gallery:
        raise HTTPException(404, "Galeri bulunamadı")

    expires_at = None
    if body.expires_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=body.expires_hours)

    link = SharingLink(
        gallery_id=body.gallery_id,
        user_id=current_user.id,
        password_hash=pwd_ctx.hash(body.password) if body.password else None,
        allow_download=body.allow_download,
        allow_selection=body.allow_selection,
        expires_at=expires_at,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    out = SharingLinkOut.model_validate(link)
    out.share_url = _make_share_url(request, str(link.id))
    return out


@router.get("/{link_id}/photos")
async def view_shared_gallery(
    link_id: str,
    password: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — no auth required."""
    result = await db.execute(
        select(SharingLink).where(SharingLink.id == link_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Paylaşım linki bulunamadı")

    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "Bu paylaşım linki süresi dolmuş")

    if link.password_hash:
        if not password or not pwd_ctx.verify(password, link.password_hash):
            raise HTTPException(401, "Şifre yanlış")

    # Increment view count
    link.view_count = (link.view_count or 0) + 1
    await db.commit()

    photos_res = await db.execute(
        select(Photo).where(
            Photo.gallery_id == link.gallery_id,
            Photo.is_deleted == False,
        ).order_by(Photo.taken_at.asc().nulls_last())
    )
    photos = photos_res.scalars().all()

    return {
        "gallery_id": link.gallery_id,
        "allow_download": link.allow_download,
        "allow_selection": link.allow_selection,
        "photos": [PhotoOut.model_validate(p) for p in photos],
    }


@router.get("", response_model=list[SharingLinkOut])
async def list_my_links(
    request: Request,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SharingLink)
        .where(SharingLink.user_id == current_user.id)
        .order_by(SharingLink.created_at.desc())
    )
    links = result.scalars().all()
    out = []
    for link in links:
        item = SharingLinkOut.model_validate(link)
        item.share_url = _make_share_url(request, str(link.id))
        out.append(item)
    return out


@router.delete("/{link_id}", status_code=204)
async def delete_sharing_link(
    link_id: str,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SharingLink).where(
            SharingLink.id == link_id,
            SharingLink.user_id == current_user.id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Link bulunamadı")
    await db.delete(link)
    await db.commit()


# ── GET single link info (public) ─────────────────────────────────────────────

@router.get("/{link_id}", response_model=SharingLinkOut)
async def get_sharing_link(
    link_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SharingLink).where(SharingLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Paylaşım linki bulunamadı")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "Paylaşım linki süresi dolmuş")
    out = SharingLinkOut.model_validate(link)
    out.share_url = _make_share_url(request, str(link.id))
    return out


# ── Comments ───────────────────────────────────────────────────────────────────

@router.get("/{link_id}/comments", response_model=list[CommentOut])
async def list_comments(link_id: str, db: AsyncSession = Depends(get_db)):
    await _get_valid_link(link_id, db)
    result = await db.execute(
        select(GalleryComment)
        .where(GalleryComment.link_id == link_id)
        .order_by(GalleryComment.created_at.asc())
    )
    return [CommentOut.model_validate(c) for c in result.scalars().all()]


@router.post("/{link_id}/comments", response_model=CommentOut, status_code=201)
async def add_comment(
    link_id: str,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    await _get_valid_link(link_id, db)
    comment = GalleryComment(
        link_id=link_id,
        photo_id=body.photo_id,
        guest_name=body.guest_name or "Ziyaretçi",
        body=body.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentOut.model_validate(comment)


# ── Votes (likes) ──────────────────────────────────────────────────────────────

@router.get("/{link_id}/votes", response_model=list[VoteOut])
async def list_votes(
    link_id: str,
    fingerprint: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    await _get_valid_link(link_id, db)
    counts = await db.execute(
        select(GalleryVote.photo_id, func.count().label("cnt"))
        .where(GalleryVote.link_id == link_id)
        .group_by(GalleryVote.photo_id)
    )
    rows = counts.all()
    user_voted_ids: set[int] = set()
    if fingerprint:
        uv = await db.execute(
            select(GalleryVote.photo_id)
            .where(GalleryVote.link_id == link_id, GalleryVote.guest_fingerprint == fingerprint)
        )
        user_voted_ids = {r[0] for r in uv.all()}
    return [VoteOut(photo_id=r[0], vote_count=r[1], user_voted=r[0] in user_voted_ids) for r in rows]


@router.post("/{link_id}/photos/{photo_id}/vote", response_model=VoteOut)
async def toggle_vote(
    link_id: str,
    photo_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _get_valid_link(link_id, db)
    fp = _fingerprint(request)
    existing = await db.execute(
        select(GalleryVote).where(
            GalleryVote.link_id == link_id,
            GalleryVote.photo_id == photo_id,
            GalleryVote.guest_fingerprint == fp,
        )
    )
    vote = existing.scalar_one_or_none()
    if vote:
        await db.delete(vote)
    else:
        db.add(GalleryVote(link_id=link_id, photo_id=photo_id, guest_fingerprint=fp))
    await db.commit()
    count = await db.execute(
        select(func.count()).where(GalleryVote.link_id == link_id, GalleryVote.photo_id == photo_id)
    )
    return VoteOut(photo_id=photo_id, vote_count=count.scalar() or 0, user_voted=vote is None)


# ── Selections ─────────────────────────────────────────────────────────────────

@router.get("/{link_id}/selections", response_model=list[SelectionOut])
async def list_selections(link_id: str, db: AsyncSession = Depends(get_db)):
    link = await _get_valid_link(link_id, db)
    if not link.allow_selection:
        raise HTTPException(403, "Bu paylaşım seçim özelliği kapalı")
    result = await db.execute(
        select(PhotoSelection.photo_id).where(PhotoSelection.link_id == link_id)
    )
    selected_ids = {r[0] for r in result.all()}
    return [SelectionOut(photo_id=pid, selected=True) for pid in selected_ids]


@router.post("/{link_id}/photos/{photo_id}/select", response_model=SelectionOut)
async def toggle_selection(
    link_id: str,
    photo_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    link = await _get_valid_link(link_id, db)
    if not link.allow_selection:
        raise HTTPException(403, "Bu paylaşım seçim özelliği kapalı")
    guest_name = body.get("guest_name", "Ziyaretçi")
    existing = await db.execute(
        select(PhotoSelection).where(PhotoSelection.link_id == link_id, PhotoSelection.photo_id == photo_id)
    )
    sel = existing.scalar_one_or_none()
    if sel:
        await db.delete(sel)
        await db.commit()
        return SelectionOut(photo_id=photo_id, selected=False)
    else:
        db.add(PhotoSelection(link_id=link_id, photo_id=photo_id, guest_name=guest_name))
        await db.commit()
        return SelectionOut(photo_id=photo_id, selected=True)


# ── Photo markings (photographer only) ────────────────────────────────────────

@router.post("/photos/{photo_id}/mark", response_model=MarkingOut)
async def mark_photo(
    photo_id: int,
    body: MarkingCreate,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(PhotoMarking).where(PhotoMarking.photo_id == photo_id)
    )
    marking = existing.scalar_one_or_none()
    if marking:
        marking.mark = body.mark
    else:
        marking = PhotoMarking(photo_id=photo_id, user_id=current_user.id, mark=body.mark)
        db.add(marking)
    await db.commit()
    await db.refresh(marking)
    return MarkingOut(photo_id=marking.photo_id, mark=marking.mark, updated_at=marking.updated_at)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_valid_link(link_id: str, db: AsyncSession) -> SharingLink:
    result = await db.execute(select(SharingLink).where(SharingLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Paylaşım linki bulunamadı")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(410, "Paylaşım linki süresi dolmuş")
    return link


def _fingerprint(request: Request) -> str:
    raw = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    return hashlib.sha256(f"{raw}:{ua}".encode()).hexdigest()[:32]
