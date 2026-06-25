-- GalleryWeb — Local Dev Schema (Docker PostgreSQL, no Supabase auth dependency)
-- Apply: psql -h localhost -p 5436 -U postgres -d galleryweb -f local_dev_schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- profiles: no auth.users FK for local dev
CREATE TABLE IF NOT EXISTS public.profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                   VARCHAR(255),
    full_name               VARCHAR(255),
    tier                    VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'vip1', 'vip2', 'vip3')),
    storage_quota_gb        INT DEFAULT 5 NOT NULL,
    storage_used_bytes      BIGINT DEFAULT 0 NOT NULL,
    paddle_customer_id      VARCHAR(255),
    paddle_subscription_id  VARCHAR(255),
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.galleries (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    cover_photo_id      BIGINT,
    is_client_proofing  BOOLEAN DEFAULT FALSE,
    is_public           BOOLEAN DEFAULT FALSE,
    photo_count         INT DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.photos (
    id                  BIGSERIAL PRIMARY KEY,
    gallery_id          BIGINT NOT NULL REFERENCES public.galleries(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    r2_key              TEXT,
    local_path          TEXT,
    thumbnail_key       TEXT,
    filename            VARCHAR(500) NOT NULL,
    file_size_bytes     BIGINT DEFAULT 0,
    mime_type           VARCHAR(100),
    width               INT,
    height              INT,
    taken_at            TIMESTAMPTZ,
    camera_make         VARCHAR(100),
    camera_model        VARCHAR(100),
    lens                VARCHAR(200),
    focal_length_mm     DOUBLE PRECISION,
    aperture            DOUBLE PRECISION,
    shutter_speed       VARCHAR(50),
    iso                 INT,
    gps_lat             DOUBLE PRECISION,
    gps_lon             DOUBLE PRECISION,
    tags                TEXT[] DEFAULT '{}',
    rating              INT DEFAULT 0 CHECK (rating BETWEEN 0 AND 5),
    is_favorite         BOOLEAN DEFAULT FALSE,
    description         TEXT,
    is_deleted          BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.sharing_links (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    gallery_id      BIGINT NOT NULL REFERENCES public.galleries(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    password_hash   VARCHAR(255),
    allow_download  BOOLEAN DEFAULT TRUE,
    allow_selection BOOLEAN DEFAULT FALSE,
    expires_at      TIMESTAMPTZ,
    view_count      INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_photos_user_id      ON public.photos(user_id);
CREATE INDEX IF NOT EXISTS idx_photos_gallery_id   ON public.photos(gallery_id);
CREATE INDEX IF NOT EXISTS idx_photos_taken_at     ON public.photos(taken_at DESC);
CREATE INDEX IF NOT EXISTS idx_photos_is_deleted   ON public.photos(is_deleted);
CREATE INDEX IF NOT EXISTS idx_galleries_user_id   ON public.galleries(user_id);
CREATE INDEX IF NOT EXISTS idx_sharing_links_gallery ON public.sharing_links(gallery_id);

-- updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'photos_updated_at') THEN
        CREATE TRIGGER photos_updated_at BEFORE UPDATE ON public.photos
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'galleries_updated_at') THEN
        CREATE TRIGGER galleries_updated_at BEFORE UPDATE ON public.galleries
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'profiles_updated_at') THEN
        CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON public.profiles
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
END $$;
