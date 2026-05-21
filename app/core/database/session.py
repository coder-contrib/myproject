from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable
from functools import wraps, lru_cache
from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


@lru_cache
def get_sync_engine() -> Engine:
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    return create_engine(
        sync_url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def transaction() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session


@asynccontextmanager
async def nested_transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    async with session.begin_nested():
        yield session


def transactional(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db = kwargs.get("db")
        if db:
            return await func(*args, **kwargs)

        async with transaction() as session:
            kwargs["db"] = session
            return await func(*args, **kwargs)
    return wrapper
