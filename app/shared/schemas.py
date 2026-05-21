from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}


class IDSchema(BaseSchema):
    id: UUID


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime | None = None


class TenantSchema(BaseSchema):
    tenant_id: UUID


class PaginationParams(BaseSchema):
    page: int = 1
    page_size: int = 20
