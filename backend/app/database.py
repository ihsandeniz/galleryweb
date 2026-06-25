from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings
import re


def _build_db_url() -> str:
    settings = get_settings()
    if settings.database_url:
        url = settings.database_url
        # Convert postgres:// → postgresql+asyncpg://
        url = re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", url)
        if "asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        return url
    # Derive from Supabase URL (connection pooler port 6543)
    ref = settings.supabase_url.replace("https://", "").replace(".supabase.co", "")
    pw = ""  # Service role doesn't provide DB password — set DATABASE_URL in .env
    return f"postgresql+asyncpg://postgres:{pw}@db.{ref}.supabase.co:5432/postgres"


def _connect_args() -> dict:
    url = _build_db_url()
    # Supabase hosted → SSL required; local Docker → no SSL
    if "supabase.co" in url or "supabase.com" in url:
        return {"ssl": "require"}
    return {}


engine = create_async_engine(
    _build_db_url(),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=get_settings().app_env == "development",
    connect_args=_connect_args(),
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
