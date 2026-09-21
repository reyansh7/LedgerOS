"""Database engine, sessionmaker, and Base declarative model."""

from __future__ import annotations

from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import settings


class Base(DeclarativeBase):
    pass


# Async engine for FastAPI endpoints and agent workers
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Synchronous engine for fast bulk ingestion and DuckDB bridging
sync_database_url = settings.sync_database_url
if settings.database_url.startswith("postgresql+psycopg"):
    sync_database_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
elif settings.database_url.startswith("sqlite+aiosqlite"):
    sync_database_url = settings.database_url.replace("sqlite+aiosqlite://", "sqlite://")

sync_engine = create_engine(
    sync_database_url,
    echo=False,
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
