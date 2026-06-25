from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # PostgreSQL (Supabase connection pooler)
    database_url: str = ""

    # R2 (optional — Faz 3)
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "galleryweb-prod"
    r2_endpoint: str = ""
    r2_public_url: str = ""

    app_env: str = "development"
    app_secret_key: str = "change-me"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # Storage quotas (GB)
    quota_free_gb: int = 5
    quota_vip1_gb: int = 50
    quota_vip2_gb: int = 500
    quota_vip3_gb: int = 5120

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "../../.env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def tier_quota(self) -> dict[str, int]:
        return {
            "free": self.quota_free_gb,
            "vip1": self.quota_vip1_gb,
            "vip2": self.quota_vip2_gb,
            "vip3": self.quota_vip3_gb,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
