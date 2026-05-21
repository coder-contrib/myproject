import asyncio
import logging
from typing import Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

SeedFunction = Callable[[AsyncSession], Awaitable[None]]

_seed_registry: list[tuple[str, int, SeedFunction]] = []


class DatabaseSeeder:
    @staticmethod
    def register(name: str, order: int = 100):
        def decorator(func: SeedFunction):
            _seed_registry.append((name, order, func))
            return func
        return decorator


async def run_seeds(only: str | None = None) -> None:
    sorted_seeds = sorted(_seed_registry, key=lambda x: x[1])

    async with AsyncSessionLocal() as session:
        for name, order, seed_fn in sorted_seeds:
            if only and name != only:
                continue

            logger.info(f"Running seed: {name} (order={order})")
            try:
                await seed_fn(session)
                await session.commit()
                logger.info(f"Seed completed: {name}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Seed failed: {name} - {e}")
                raise


# Import seed modules to register them
from app.core.database.seeds import default_seeds  # noqa
