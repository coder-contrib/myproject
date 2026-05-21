import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def main():
    from app.core.database.seeds import run_seeds

    only = sys.argv[1] if len(sys.argv) > 1 else None
    await run_seeds(only=only)


if __name__ == "__main__":
    asyncio.run(main())
