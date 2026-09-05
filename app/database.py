from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

db_url = settings.async_database_url

# Engine configuration arguments
engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# SQLite vs PostgreSQL specific settings
if settings.is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / Neon settings
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

    connect_args = {}
    if "neon.tech" in db_url or "ssl" in settings.DATABASE_URL.lower():
        connect_args["ssl"] = "require"
    if "-pooler" in db_url or "neon.tech" in db_url:
        connect_args["statement_cache_size"] = 0

    if connect_args:
        engine_kwargs["connect_args"] = connect_args

# Create async engine
async_engine = create_async_engine(db_url, **engine_kwargs)

# Create async sessionmaker factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    """Base declarative class for all SQLAlchemy database entities."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session per request.
    
    Guarantees automatic rollback on unhandled exceptions and session closure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database session rolled back due to error: {}", str(e))
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables during application lifespan startup."""
    logger.info("Initializing database schema on engine: {}", settings.DATABASE_URL)
    async with async_engine.begin() as conn:
        # Import models here to ensure metadata is registered before create_all
        from app.models import patient, call_log, appointment  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")


async def close_db() -> None:
    """Dispose of database engine connections during lifespan shutdown."""
    logger.info("Disposing database engine connection pool...")
    await async_engine.dispose()
    logger.info("Database engine connections disposed.")
