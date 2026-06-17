-- GalleryWeb SaaS — Supabase Bootstrap SQL
-- Bu SQL'i Supabase Dashboard → SQL Editor'da çalıştır
-- Faz 1 başlangıcında uygulanacak (DB Migration Faz 2'de tamamlanır)

-- ─────────────────────────────────────────────
-- EXTENSIONS
-- ─────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- CLIP semantic search (Faz 8)

-- ─────────────────────────────────────────────
-- TABLO: profiles (Supabase auth.users'a bağlı)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT,
    display_name VARCHAR(100),
    tier        VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'vip1', 'vip2', 'vip3')),
    storage_quota_gb    INT DEFAULT 5,
    storage_used_bytes  BIGINT DEFAULT 0,
    paddle_customer_id  TEXT,
    paddle_subscription_id TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- TABLO: galleries
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.galleries (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    cover_photo_id BIGINT,  -- FK sonradan eklenecek (circular ref kaçınma)
    is_client_proofing BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- TABLO: photos
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.photos (
    id              BIGSERIAL PRIMARY KEY,
    gallery_id      BIGINT REFERENCES galleries(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    r2_key          TEXT NOT NULL,          -- R2'deki nesne yolu
    r2_thumb_sm     TEXT,                   -- 128px thumbnail
    r2_thumb_md     TEXT,                   -- 256px thumbnail
    r2_thumb_lg     TEXT,                   -- 1080px thumbnail
    original_name   VARCHAR(500),
    file_size_bytes BIGINT,
    mime_type       VARCHAR(50),
    width           INT,
    height          INT,
    taken_at        TIMESTAMPTZ,
    exif_data       JSONB,
    gps_lat         DOUBLE PRECISION,
    gps_lng         DOUBLE PRECISION,
    tags            TEXT[] DEFAULT '{}',
    rating          SMALLINT DEFAULT 0 CHECK (rating BETWEEN 0 AND 5),
    is_favorite     BOOLEAN DEFAULT FALSE,
    is_deleted      BOOLEAN DEFAULT FALSE,  -- soft delete
    notes           TEXT,
    embedding       vector(512),            -- CLIP embedding (Faz 8)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- TABLO: sharing_links (Müşteri Proofing Gallery)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.sharing_links (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    gallery_id      BIGINT NOT NULL REFERENCES galleries(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    password_hash   VARCHAR(200),           -- NULL = şifresiz
    expires_at      TIMESTAMPTZ,            -- NULL = süresiz
    allow_download  BOOLEAN DEFAULT FALSE,
    allow_comments  BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- TABLO: client_selections (Proofing seçimleri)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.client_selections (
    id              BIGSERIAL PRIMARY KEY,
    sharing_link_id UUID NOT NULL REFERENCES sharing_links(id) ON DELETE CASCADE,
    photo_id        BIGINT NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    action          VARCHAR(20) DEFAULT 'selected' CHECK (action IN ('selected', 'rejected', 'flagged')),
    comment         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(sharing_link_id, photo_id)
);

-- ─────────────────────────────────────────────
-- ROW LEVEL SECURITY (RLS)
-- ─────────────────────────────────────────────

-- profiles: kişi sadece kendi profilini görebilir
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY profiles_self ON profiles FOR ALL
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- galleries: kişi sadece kendi galerilerini yönetir
ALTER TABLE public.galleries ENABLE ROW LEVEL SECURITY;
CREATE POLICY galleries_owner ON galleries FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- photos: kişi sadece kendi fotoğraflarını yönetir
ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY;
CREATE POLICY photos_owner ON photos FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- sharing_links: sahibi yönetir
ALTER TABLE public.sharing_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY sharing_links_owner ON sharing_links FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- client_selections: herkes okuyabilir (şifre kontrolü app katmanında yapılır)
ALTER TABLE public.client_selections ENABLE ROW LEVEL SECURITY;
CREATE POLICY client_selections_read ON client_selections FOR SELECT
    USING (TRUE);
CREATE POLICY client_selections_insert ON client_selections FOR INSERT
    WITH CHECK (TRUE);

-- ─────────────────────────────────────────────
-- İNDEKSLER
-- ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_photos_user_id ON photos(user_id);
CREATE INDEX IF NOT EXISTS idx_photos_gallery_id ON photos(gallery_id);
CREATE INDEX IF NOT EXISTS idx_photos_tags ON photos USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_photos_taken_at ON photos(taken_at DESC);
CREATE INDEX IF NOT EXISTS idx_galleries_user_id ON galleries(user_id);
CREATE INDEX IF NOT EXISTS idx_sharing_links_gallery ON sharing_links(gallery_id);

-- CLIP embedding index (Faz 8'de aktif edilir)
-- CREATE INDEX IF NOT EXISTS idx_photos_embedding ON photos USING ivfflat (embedding vector_cosine_ops);

-- ─────────────────────────────────────────────
-- TRIGGER: updated_at otomatik güncelle
-- ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER photos_updated_at
    BEFORE UPDATE ON photos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER galleries_updated_at
    BEFORE UPDATE ON galleries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─────────────────────────────────────────────
-- TRIGGER: Yeni auth.user kaydolunca profiles satırı oluştur
-- ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();
