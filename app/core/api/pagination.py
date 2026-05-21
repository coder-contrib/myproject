from dataclasses import dataclass
from fastapi import Query


@dataclass
class PaginationParams:
    page: int
    per_page: int
    skip: int
    limit: int


def get_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    return PaginationParams(
        page=page,
        per_page=per_page,
        skip=(page - 1) * per_page,
        limit=per_page,
    )
