from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean,
    DateTime, Text, ForeignKey, ARRAY, Enum as PgEnum,
    func, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .database import Base
import uuid


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255))
    full_name = Column(String(255))
    tier = Column(String(20), default="free", nullable=False)
    storage_quota_gb = Column(Integer, default=5, nullable=False)
    storage_used_bytes = Column(BigInteger, default=0, nullable=False)
    paddle_customer_id = Column(String(255))
    paddle_subscription_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    galleries = relationship("Gallery", back_populates="owner", cascade="all, delete-orphan")

    @property
    def storage_used_gb(self) -> float:
        return round(self.storage_used_bytes / (1024 ** 3), 4)

    @property
    def storage_quota_bytes(self) -> int:
        return self.storage_quota_gb * (1024 ** 3)


class Gallery(Base):
    __tablename__ = "galleries"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("public.profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    cover_photo_id = Column(BigInteger, nullable=True)
    is_client_proofing = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    photo_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("Profile", back_populates="galleries")
    photos = relationship("Photo", back_populates="gallery", cascade="all, delete-orphan")
    sharing_links = relationship("SharingLink", back_populates="gallery", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    gallery_id = Column(BigInteger, ForeignKey("public.galleries.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("public.profiles.id", ondelete="CASCADE"), nullable=False)

    # Storage
    r2_key = Column(Text)           # R2 object key (Faz 3)
    local_path = Column(Text)       # Local disk path (Faz 1-2 fallback)
    thumbnail_key = Column(Text)    # R2 thumbnail key
    filename = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, default=0)
    mime_type = Column(String(100))

    # EXIF
    width = Column(Integer)
    height = Column(Integer)
    taken_at = Column(DateTime(timezone=True))
    camera_make = Column(String(100))
    camera_model = Column(String(100))
    lens = Column(String(200))
    focal_length_mm = Column(Float)
    aperture = Column(Float)
    shutter_speed = Column(String(50))
    iso = Column(Integer)
    gps_lat = Column(Float)
    gps_lon = Column(Float)

    # User metadata
    tags = Column(ARRAY(Text), default=list)
    rating = Column(Integer, default=0)
    is_favorite = Column(Boolean, default=False)
    description = Column(Text)
    is_deleted = Column(Boolean, default=False)

    # CLIP semantic embedding (Faz 7) — vector(512) for clip-ViT-B-32
    embedding = Column(Vector(512), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    gallery = relationship("Gallery", back_populates="photos")


class SharingLink(Base):
    __tablename__ = "sharing_links"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gallery_id = Column(BigInteger, ForeignKey("public.galleries.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("public.profiles.id", ondelete="CASCADE"), nullable=False)
    password_hash = Column(String(255))
    allow_download = Column(Boolean, default=True)
    allow_selection = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gallery = relationship("Gallery", back_populates="sharing_links")
    comments = relationship("GalleryComment", back_populates="sharing_link", cascade="all, delete-orphan")
    votes = relationship("GalleryVote", back_populates="sharing_link", cascade="all, delete-orphan")
    selections = relationship("PhotoSelection", back_populates="sharing_link", cascade="all, delete-orphan")


class GalleryComment(Base):
    __tablename__ = "gallery_comments"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    link_id = Column(UUID(as_uuid=True), ForeignKey("public.sharing_links.id", ondelete="CASCADE"), nullable=False)
    photo_id = Column(BigInteger, ForeignKey("public.photos.id", ondelete="CASCADE"), nullable=True)
    guest_name = Column(String(100), default="Ziyaretçi")
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sharing_link = relationship("SharingLink", back_populates="comments")


class GalleryVote(Base):
    __tablename__ = "gallery_votes"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    link_id = Column(UUID(as_uuid=True), ForeignKey("public.sharing_links.id", ondelete="CASCADE"), nullable=False)
    photo_id = Column(BigInteger, ForeignKey("public.photos.id", ondelete="CASCADE"), nullable=False)
    guest_fingerprint = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sharing_link = relationship("SharingLink", back_populates="votes")


class PhotoSelection(Base):
    __tablename__ = "photo_selections"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    link_id = Column(UUID(as_uuid=True), ForeignKey("public.sharing_links.id", ondelete="CASCADE"), nullable=False)
    photo_id = Column(BigInteger, ForeignKey("public.photos.id", ondelete="CASCADE"), nullable=False)
    guest_name = Column(String(100), default="Ziyaretçi")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sharing_link = relationship("SharingLink", back_populates="selections")


class PhotoMarking(Base):
    __tablename__ = "photo_markings"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    photo_id = Column(BigInteger, ForeignKey("public.photos.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("public.profiles.id", ondelete="CASCADE"), nullable=False)
    mark = Column(String(20), default="none")  # none, flag, reject, star
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
