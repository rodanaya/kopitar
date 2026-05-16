"""
Database Session Management

Async SQLAlchemy session factory for FastAPI dependency injection.
Falls back to SQLite so the application starts without PostgreSQL.
"""

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from .config import get_settings

logger = logging.getLogger(__name__)

_SQLITE_FALLBACK_URL = "sqlite+aiosqlite:///./kopitar.db"

_engine = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _get_engine():
    global _engine, _session_factory

    if _engine is not None:
        return _engine

    settings = get_settings()
    database_url: str = settings.DATABASE_URL or _SQLITE_FALLBACK_URL

    # SQLAlchemy async drivers require explicit async prefixes.
    # Map common sync URLs to their async equivalents.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("sqlite://") and not database_url.startswith("sqlite+aiosqlite://"):
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    is_sqlite = database_url.startswith("sqlite")

    connect_args = {"check_same_thread": False} if is_sqlite else {}
    pool_kwargs = (
        {"poolclass": StaticPool, "connect_args": connect_args}
        if is_sqlite
        else {"pool_pre_ping": True}
    )

    try:
        _engine = create_async_engine(
            database_url,
            echo=settings.DATABASE_ECHO,
            **pool_kwargs,
        )
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Database engine created: %s", database_url.split("@")[-1])
    except Exception:
        logger.warning(
            "Failed to create engine for %s — falling back to SQLite",
            database_url,
            exc_info=True,
        )
        _engine = create_async_engine(
            _SQLITE_FALLBACK_URL,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _engine


async def get_db_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    """
    FastAPI dependency that yields an async SQLAlchemy session.

    On connection failure the generator yields ``None`` and logs a warning
    so endpoints can degrade gracefully rather than crashing at startup.
    """
    _get_engine()

    if _session_factory is None:
        logger.warning("Database session factory unavailable — yielding None")
        yield None
        return

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
