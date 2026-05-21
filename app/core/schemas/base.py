from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Self
from pydantic import BaseModel, ConfigDict, field_serializer, model_validator


class BaseSchema(BaseModel):
    """Base schema with decimal serialization and ORM mode."""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: lambda v: float(round(v, 4)),
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    @field_serializer("*", when_used="json")
    @classmethod
    def serialize_decimals(cls, v: Any) -> Any:
        if isinstance(v, Decimal):
            return float(round(v, 4))
        return v


class CreateSchema(BaseSchema):
    """Base for creation requests. Strips whitespace, validates required fields."""
    pass


class UpdateSchema(BaseSchema):
    """Base for update requests. All fields optional, only set fields are applied."""

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        set_fields = self.model_fields_set
        if not set_fields:
            raise ValueError("At least one field must be provided for update")
        return self


class ResponseSchema(BaseSchema):
    """Base for response schemas with common fields."""
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TenantResponseSchema(ResponseSchema):
    """Response schema including tenant_id."""
    tenant_id: UUID


class AuditResponseSchema(TenantResponseSchema):
    """Response schema with full audit fields."""
    version: int = 1
    created_by: UUID | None = None
    updated_by: UUID | None = None


class PaginatedRequest(BaseSchema):
    """Standardized pagination request parameters."""
    page: int = 1
    per_page: int = 20
    sort: str | None = None
    order: str = "desc"
    q: str | None = None
