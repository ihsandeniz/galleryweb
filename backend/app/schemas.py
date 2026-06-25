from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import uuid


# ── Auth ──────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter olmalı")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User / Profile ─────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    tier: str
    storage_quota_gb: int
    storage_used_gb: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Gallery ────────────────────────────────────────────────────────────────────

class GalleryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_client_proofing: bool = False
    is_public: bool = False


class GalleryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_client_proofing: Optional[bool] = None
    is_public: Optional[bool] = None


class GalleryOut(BaseModel):
    id: int
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_client_proofing: bool
    is_public: bool
    photo_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Photo ──────────────────────────────────────────────────────────────────────

class PhotoOut(BaseModel):
    id: int
    gallery_id: int
    user_id: uuid.UUID
    filename: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    taken_at: Optional[datetime] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    tags: list[str] = []
    rating: int
    is_favorite: bool
    r2_key: Optional[str] = None
    local_path: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoUpdate(BaseModel):
    tags: Optional[list[str]] = None
    rating: Optional[int] = None
    is_favorite: Optional[bool] = None
    description: Optional[str] = None
    gallery_id: Optional[int] = None


# ── Sharing ────────────────────────────────────────────────────────────────────

class SharingLinkCreate(BaseModel):
    gallery_id: int
    password: Optional[str] = None
    allow_download: bool = True
    allow_selection: bool = False
    expires_hours: Optional[int] = None


class SharingLinkOut(BaseModel):
    id: uuid.UUID
    gallery_id: int
    allow_download: bool
    allow_selection: bool
    expires_at: Optional[datetime] = None
    view_count: int
    share_url: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Proofing Gallery (Faz 6) ──────────────────────────────────────────────────

class CommentCreate(BaseModel):
    guest_name: Optional[str] = "Ziyaretçi"
    body: str
    photo_id: Optional[int] = None

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Yorum boş olamaz")
        if len(v) > 2000:
            raise ValueError("Yorum en fazla 2000 karakter olabilir")
        return v.strip()


class CommentOut(BaseModel):
    id: int
    link_id: uuid.UUID
    photo_id: Optional[int] = None
    guest_name: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class VoteOut(BaseModel):
    photo_id: int
    vote_count: int
    user_voted: bool


class SelectionOut(BaseModel):
    photo_id: int
    selected: bool


class MarkingCreate(BaseModel):
    mark: str  # none | flag | reject | star

    @field_validator("mark")
    @classmethod
    def valid_mark(cls, v: str) -> str:
        if v not in ("none", "flag", "reject", "star"):
            raise ValueError("mark: none | flag | reject | star olabilir")
        return v


class MarkingOut(BaseModel):
    photo_id: int
    mark: str
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int
