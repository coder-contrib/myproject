from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, field_validator


# --- BOM ---

class BOMItemCreate(BaseModel):
    material_id: UUID
    quantity: float
    unit: str = "pcs"
    waste_percent: float = 0

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

class BOMCreate(BaseModel):
    product_id: UUID
    name: str
    notes: str | None = None
    items: list[BOMItemCreate]

class BOMItemResponse(BaseModel):
    id: UUID
    material_id: UUID
    quantity: float
    unit: str
    waste_percent: float
    model_config = {"from_attributes": True}

class BOMResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    name: str
    version: int
    is_active: bool
    notes: str | None
    items: list[BOMItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Production Order ---

class ProductionOrderCreate(BaseModel):
    product_id: UUID
    bom_id: UUID | None = None
    warehouse_id: UUID | None = None
    quantity: float
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    notes: str | None = None

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

class ProductionOrderStatusUpdate(BaseModel):
    status: str
    produced_quantity: float | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"pending", "in_progress", "completed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v

class MaterialConsumptionResponse(BaseModel):
    id: UUID
    material_id: UUID
    warehouse_id: UUID | None
    planned_quantity: float
    actual_quantity: float
    status: str
    model_config = {"from_attributes": True}

class ProductionOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    order_number: str
    product_id: UUID
    bom_id: UUID | None
    warehouse_id: UUID | None
    quantity: float
    produced_quantity: float
    status: str
    planned_start_date: date | None
    planned_end_date: date | None
    actual_start_date: date | None
    actual_end_date: date | None
    notes: str | None
    consumptions: list[MaterialConsumptionResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Material Consumption ---

class ConsumeMaterialRequest(BaseModel):
    material_id: UUID
    warehouse_id: UUID | None = None
    quantity: float

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v
