from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel

class BOMCreate(BaseModel):
    product_id: UUID
    material_id: UUID
    quantity: float

class BOMResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID | None
    material_id: UUID | None
    quantity: float
    created_at: datetime
    model_config = {"from_attributes": True}

class ProductionOrderCreate(BaseModel):
    product_id: UUID
    warehouse_id: UUID | None = None
    quantity: float
    planned_start_date: date | None = None
    planned_end_date: date | None = None

class ProductionOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID | None
    quantity: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
