"""Async SQLAlchemy engine and session factory.

Only initialised when DATABASE_URL is set — the rest of the app works without it.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# None when no database is configured; checked before mounting auth routes.
engine = None
async_session_factory = None

if settings.database_url:
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one session per request, auto-rolled-back on error."""
    assert async_session_factory is not None
    async with async_session_factory() as session:
        yield session
