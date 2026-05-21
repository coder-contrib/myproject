from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    sku: str | None = None
    category_id: UUID | None = None
    sale_price: float = 0
    purchase_price: float = 0
    company_id: UUID | None = None

class ProductResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    sku: str | None
    sale_price: float
    purchase_price: float
    average_cost: float
    created_at: datetime
    model_config = {"from_attributes": True}

class WarehouseCreate(BaseModel):
    name: str
    company_id: UUID | None = None
    branch_id: UUID | None = None
    location: str | None = None

class WarehouseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    location: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class InventoryResponse(BaseModel):
    id: UUID
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reserved_quantity: int
    damaged_quantity: int
    model_config = {"from_attributes": True}

class MovementCreate(BaseModel):
    product_id: UUID
    from_warehouse_id: UUID | None = None
    to_warehouse_id: UUID | None = None
    quantity: int
    reason: str

class MovementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    quantity: int
    reason: str
    created_at: datetime
    model_config = {"from_attributes": True}

class StockTransferCreate(BaseModel):
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    notes: str | None = None

class StockTransferResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    transfer_number: str | None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
