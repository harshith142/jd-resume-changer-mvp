from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from app.config import get_settings


class Base(DeclarativeBase):
    pass


# Global variables for engine and session factory
engine = None
AsyncSessionLocal = None


def _migrate_sqlite_users_table() -> None:
    """Upgrade the local SQLite users table for email/password login while preserving existing data."""
    if not engine:
        return

    import sqlite3

    settings = get_settings()
    if not settings.database_url.startswith("sqlite"):
        return

    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    if not db_path or db_path == ".":
        return

    conn = sqlite3.connect(db_path)
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchall()
        if not tables:
            return

        cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "password_hash" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")

        table_info = conn.execute("PRAGMA table_info(users)").fetchall()
        oauth_flags = {row[1]: row[3] for row in table_info}
        if oauth_flags.get("oauth_provider") == 1:
            conn.execute("ALTER TABLE users RENAME TO users_old")
            conn.execute(
                """
                CREATE TABLE users (
                    id CHAR(36) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    avatar_url VARCHAR(500),
                    password_hash VARCHAR(255),
                    oauth_provider VARCHAR(50),
                    oauth_subject VARCHAR(255),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    last_login DATETIME,
                    refresh_token_hash VARCHAR(255)
                )
                """
            )
            conn.execute(
                """
                INSERT INTO users (
                    id, email, name, avatar_url, password_hash, oauth_provider,
                    oauth_subject, created_at, updated_at, is_active, last_login,
                    refresh_token_hash
                )
                SELECT
                    id, email, name, avatar_url, NULL, oauth_provider,
                    oauth_subject, created_at, updated_at, is_active, last_login,
                    refresh_token_hash
                FROM users_old
                """
            )
            conn.execute("DROP TABLE users_old")

        conn.commit()
    finally:
        conn.close()


def get_engine():
    """Get or create the database engine."""
    global engine, AsyncSessionLocal
    if engine is None:
        settings = get_settings()
        engine = create_async_engine(
            settings.database_url,
            echo=settings.environment == "development",
            pool_pre_ping=True,
            # SQLite doesn't support pool_size/max_overflow
            **({} if settings.database_url.startswith("sqlite") else {"pool_size": 10, "max_overflow": 20}),
        )
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return engine


async def init_db() -> None:
    """Initialize database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _migrate_sqlite_users_table()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes."""
    engine = get_engine()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Close database connections."""
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None