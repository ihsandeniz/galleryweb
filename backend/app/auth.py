from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from supabase import create_client, Client
from functools import lru_cache
from .config import get_settings
from .database import get_db
from .models import Profile
import uuid

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _supabase() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_anon_key)


async def _verify_token(token: str) -> dict:
    """Verify JWT via Supabase auth.get_user (handles ES256 & HS256 transparently)."""
    sb = _supabase()
    try:
        res = sb.auth.get_user(token)
        if not res or not res.user:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        return {
            "sub": str(res.user.id),
            "email": res.user.email or "",
            "full_name": (res.user.user_metadata or {}).get("full_name"),
        }
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e).lower()
        if "expired" in msg:
            raise HTTPException(status_code=401, detail="Token süresi dolmuş")
        raise HTTPException(status_code=401, detail="Geçersiz token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kimlik doğrulama gerekli",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await _verify_token(credentials.credentials)
    user_id = uuid.UUID(payload["sub"])

    result = await db.execute(select(Profile).where(Profile.id == user_id))
    profile = result.scalar_one_or_none()

    if not profile:
        # Auto-create profile for first login
        settings = get_settings()
        profile = Profile(
            id=user_id,
            email=payload.get("email", ""),
            full_name=payload.get("full_name"),
            tier="free",
            storage_quota_gb=settings.quota_free_gb,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Profile | None:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
