"""Async SQLAlchemy engine & session helpers."""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from ..config import get_settings

__all__ = [
    "Base",
    "engine",
    "async_session",
    "get_async_session",
]

settings = get_settings()

# Create async engine (uses asyncpg driver)
engine: AsyncEngine = create_async_engine(
    settings.sqlalchemy_database_uri,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

# Session factory
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)

# Base class for declarative models
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an :class:`AsyncSession`."""
    async with async_session() as session:
        yield session
