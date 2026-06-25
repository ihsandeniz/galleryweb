from fastapi import APIRouter
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
async def public_config():
    s = get_settings()
    return {
        "supabase_url": s.supabase_url,
        "supabase_anon_key": s.supabase_anon_key,
    }
