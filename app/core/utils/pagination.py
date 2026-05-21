from uuid import UUID
from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


async def paginate(
    db: AsyncSession,
    query,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence, int]:
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    results = await db.execute(query.offset(offset).limit(page_size))
    items = results.scalars().all()

    return items, total


def build_paginated_response(items, total: int, page: int, page_size: int, schema) -> dict:
    return {
        "items": [schema.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
