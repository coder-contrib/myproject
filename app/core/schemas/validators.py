import re
from uuid import UUID
from datetime import date, datetime
from typing import Any


_PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def validate_phone(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    v = v.strip()
    if not _PHONE_PATTERN.match(v):
        raise ValueError("Invalid phone number format")
    return v


def validate_future_date(v: date | None) -> date | None:
    if v is None:
        return None
    if v < date.today():
        raise ValueError("Date must be in the future")
    return v


def validate_date_range(start: date | None, end: date | None) -> tuple[date | None, date | None]:
    if start and end and start > end:
        raise ValueError("Start date must be before end date")
    return start, end


def validate_uuid_list(v: Any) -> list[UUID]:
    if v is None:
        return []
    if isinstance(v, str):
        parts = [p.strip() for p in v.split(",") if p.strip()]
        return [UUID(p) for p in parts]
    if isinstance(v, list):
        return [UUID(str(item)) if not isinstance(item, UUID) else item for item in v]
    raise ValueError("Must be a list of UUIDs or comma-separated UUID string")


def validate_percentage(v: float | None) -> float | None:
    if v is None:
        return None
    if v < 0 or v > 100:
        raise ValueError("Percentage must be between 0 and 100")
    return v
