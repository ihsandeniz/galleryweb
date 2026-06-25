"""CLIP Semantic Search — Faz 7.

GET /api/search?q=<query>[&gallery_id=<id>][&limit=20]
VIP2+ only. Returns photos ordered by cosine similarity to the text query.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from ..database import get_db
from ..auth import get_current_user
from ..models import Profile, Photo
from ..schemas import PhotoOut

router = APIRouter(prefix="/api/search", tags=["search"])

_VIP_TIERS = {"vip2", "vip3"}


@router.get("")
async def semantic_search(
    q: str = Query(..., min_length=1, max_length=300, description="Türkçe veya İngilizce doğal dil sorgusu"),
    gallery_id: int | None = Query(None, description="Belirli bir galeride ara"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic photo search using CLIP embeddings (VIP2+)."""
    if current_user.tier not in _VIP_TIERS:
        raise HTTPException(
            403,
            detail={
                "code": "upgrade_required",
                "message": "CLIP semantik arama VIP2 ve üzeri planlarda kullanılabilir.",
                "current_tier": current_user.tier,
                "upgrade_url": "/upgrade",
            },
        )

    from ..services.clip_service import get_clip_service
    clip = get_clip_service()
    query_vec = await clip.encode_text(q)
    vec_literal = "[" + ",".join(f"{x:.6f}" for x in query_vec) + "]"

    gallery_filter = ""
    params: dict = {
        "vec": vec_literal,
        "user_id": str(current_user.id),
        "limit": limit,
    }
    if gallery_id is not None:
        gallery_filter = "AND p.gallery_id = :gallery_id"
        params["gallery_id"] = gallery_id

    sql = text(f"""
        SELECT p.id,
               (p.embedding <=> CAST(:vec AS vector)) AS distance
        FROM   public.photos p
        WHERE  p.user_id     = CAST(:user_id AS uuid)
          AND  p.is_deleted  = FALSE
          AND  p.embedding   IS NOT NULL
          {gallery_filter}
        ORDER  BY distance ASC
        LIMIT  :limit
    """)

    rows = (await db.execute(sql, params)).fetchall()
    if not rows:
        return {"results": [], "query": q, "count": 0}

    photo_ids = [row[0] for row in rows]
    distances = {row[0]: float(row[1]) for row in rows}

    photos = (await db.execute(
        select(Photo).where(Photo.id.in_(photo_ids))
    )).scalars().all()

    photos_by_id = {p.id: p for p in photos}
    ordered = [photos_by_id[pid] for pid in photo_ids if pid in photos_by_id]

    return {
        "results": [
            {
                **PhotoOut.model_validate(p).model_dump(),
                "similarity": round(1.0 - distances[p.id], 4),
            }
            for p in ordered
        ],
        "query": q,
        "count": len(ordered),
    }
