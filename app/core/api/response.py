from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None
    errors: list[dict[str, Any]] | None = None
    meta: PaginationMeta | None = None


def paginated_response(
    data: list,
    total: int,
    page: int,
    per_page: int,
    message: str | None = None,
) -> dict:
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    return {
        "success": True,
        "data": data,
        "message": message,
        "errors": None,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def success_response(data: Any = None, message: str | None = None) -> dict:
    return {
        "success": True,
        "data": data,
        "message": message,
        "errors": None,
        "meta": None,
    }


def error_response(
    message: str,
    errors: list[dict[str, Any]] | None = None,
    status_code: int = 400,
) -> dict:
    return {
        "success": False,
        "data": None,
        "message": message,
        "errors": errors,
        "meta": None,
    }
