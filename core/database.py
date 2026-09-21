"""Database engine, sessionmaker, and Base declarative model."""

from __future__ import annotations

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import settings


class Base(DeclarativeBase):
    pass


# Normalize database URLs
raw_url = settings.database_url
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

async_db_url = raw_url
if async_db_url.startswith("sqlite://"):
    async_db_url = async_db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

sync_db_url = raw_url
if sync_db_url.startswith("sqlite+aiosqlite://"):
    sync_db_url = sync_db_url.replace("sqlite+aiosqlite://", "sqlite://", 1)

# Async engine for FastAPI endpoints and agent workers
engine_kwargs = {"echo": False}
if "sqlite" not in async_db_url:
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True})

async_engine = create_async_engine(
    async_db_url,
    future=True,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

sync_engine_kwargs = {"echo": False}
if "sqlite" not in sync_db_url:
    sync_engine_kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True})

sync_engine = create_engine(
    sync_db_url,
    **sync_engine_kwargs,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI route handlers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """Context manager or utility for synchronous scripts."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


async def init_db() -> None:
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
