from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from ..config import get_settings
from ..schemas import SignupRequest, LoginRequest, AuthResponse, UserOut
from ..auth import get_current_user
from ..models import Profile
from functools import lru_cache


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


@lru_cache
def _supabase() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignupRequest):
    sb = _supabase()
    try:
        res = sb.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {"data": {"full_name": body.full_name or ""}},
        })
    except Exception as e:
        raise HTTPException(400, str(e))

    if not res.user or not res.session:
        raise HTTPException(400, "Kayıt başarısız — email zaten kayıtlı olabilir")

    return AuthResponse(
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        expires_in=res.session.expires_in,
        user=UserOut(
            id=res.user.id,
            email=res.user.email,
            full_name=res.user.user_metadata.get("full_name"),
            tier="free",
            storage_quota_gb=get_settings().quota_free_gb,
            storage_used_gb=0.0,
            created_at=res.user.created_at,
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    sb = _supabase()
    try:
        res = sb.auth.sign_in_with_password({"email": body.email, "password": body.password})
    except Exception as e:
        raise HTTPException(401, "Email veya şifre hatalı")

    if not res.user or not res.session:
        raise HTTPException(401, "Giriş başarısız")

    return AuthResponse(
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        expires_in=res.session.expires_in,
        user=UserOut(
            id=res.user.id,
            email=res.user.email,
            full_name=res.user.user_metadata.get("full_name"),
            tier="free",
            storage_quota_gb=get_settings().quota_free_gb,
            storage_used_gb=0.0,
            created_at=res.user.created_at,
        ),
    )


@router.post("/logout")
async def logout(current_user: Profile = Depends(get_current_user)):
    # Client-side token deletion is sufficient; server-side revocation optional
    return {"status": "ok", "message": "Çıkış yapıldı"}


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(body: dict):
    refresh = body.get("refresh_token")
    if not refresh:
        raise HTTPException(400, "refresh_token gerekli")
    sb = _supabase()
    try:
        res = sb.auth.refresh_session(refresh)
    except Exception as e:
        raise HTTPException(401, f"Token yenileme başarısız: {e}")
    if not res.session:
        raise HTTPException(401, "Token yenileme başarısız")
    return AuthResponse(
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        expires_in=res.session.expires_in,
        user=UserOut(
            id=res.user.id,
            email=res.user.email,
            full_name=res.user.user_metadata.get("full_name") if res.user else None,
            tier="free",
            storage_quota_gb=get_settings().quota_free_gb,
            storage_used_gb=0.0,
            created_at=res.user.created_at,
        ),
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    sb = _supabase()
    try:
        sb.auth.reset_password_for_email(body.email)
    except Exception:
        pass  # don't reveal if email exists
    return {"status": "ok", "message": "Şifre sıfırlama e-postası gönderildi"}


@router.get("/me", response_model=UserOut)
async def me(current_user: Profile = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email or "",
        full_name=current_user.full_name,
        tier=current_user.tier,
        storage_quota_gb=current_user.storage_quota_gb,
        storage_used_gb=current_user.storage_used_gb,
        created_at=current_user.created_at,
    )
