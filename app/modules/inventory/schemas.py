from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


# --- Product Category ---

class CategoryCreate(BaseModel):
    name: str
    parent_id: UUID | None = None
    description: str | None = None

class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None

class CategoryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    parent_id: UUID | None
    description: str | None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Product ---

class ProductCreate(BaseModel):
    name: str
    sku: str | None = None
    barcode: str | None = None
    barcode_type: str | None = None
    category_id: UUID | None = None
    unit: str = "pcs"
    description: str | None = None
    sale_price: float = 0
    purchase_price: float = 0
    min_stock_level: int = 0
    max_stock_level: int = 0
    reorder_point: int = 10
    is_batch_tracked: bool = False
    is_serialized: bool = False
    weight: float | None = None
    dimensions: str | None = None
    tax_rate: float = 0
    image_url: str | None = None

class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    barcode: str | None = None
    barcode_type: str | None = None
    category_id: UUID | None = None
    unit: str | None = None
    description: str | None = None
    sale_price: float | None = None
    purchase_price: float | None = None
    min_stock_level: int | None = None
    max_stock_level: int | None = None
    reorder_point: int | None = None
    is_batch_tracked: bool | None = None
    weight: float | None = None
    dimensions: str | None = None
    tax_rate: float | None = None
    image_url: str | None = None
    is_active: bool | None = None
    version: int | None = None

class ProductResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    name: str
    sku: str | None
    barcode: str | None
    barcode_type: str | None
    category_id: UUID | None
    unit: str
    description: str | None
    sale_price: float
    purchase_price: float
    average_cost: float
    min_stock_level: int
    max_stock_level: int
    reorder_point: int
    is_batch_tracked: bool
    is_serialized: bool
    is_active: bool
    tax_rate: float
    version: int
    created_at: datetime
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


# --- Warehouse ---

class WarehouseCreate(BaseModel):
    name: str
    code: str | None = None
    address: str | None = None
    capacity: int | None = None
    is_default: bool = False
    manager_id: UUID | None = None

class WarehouseUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    address: str | None = None
    capacity: int | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    manager_id: UUID | None = None
    version: int | None = None

class WarehouseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    branch_id: UUID | None
    name: str
    code: str | None
    address: str | None
    capacity: int | None
    is_active: bool
    is_default: bool
    version: int
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Inventory ---

class InventoryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reserved_quantity: int
    damaged_quantity: int
    in_transit_quantity: int
    available_quantity: int
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}

class InventoryAdjustment(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reason: str
    notes: str | None = None

    @field_validator("quantity")
    @classmethod
    def quantity_not_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Adjustment quantity cannot be zero")
        return v


# --- Batch ---

class BatchCreate(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    batch_number: str
    lot_number: str | None = None
    quantity: int
    manufacturing_date: datetime | None = None
    expiry_date: datetime | None = None
    supplier_id: UUID | None = None
    purchase_price: float | None = None
    notes: str | None = None

class BatchResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    warehouse_id: UUID
    batch_number: str
    lot_number: str | None
    quantity: int
    manufacturing_date: datetime | None
    expiry_date: datetime | None
    status: str
    purchase_price: float | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Movements ---

class MovementCreate(BaseModel):
    product_id: UUID
    from_warehouse_id: UUID | None = None
    to_warehouse_id: UUID | None = None
    batch_id: UUID | None = None
    quantity: int
    movement_type: str
    reason: str
    reference_type: str | None = None
    reference_id: UUID | None = None
    unit_cost: float | None = None
    notes: str | None = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

class MovementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    from_warehouse_id: UUID | None
    to_warehouse_id: UUID | None
    batch_id: UUID | None
    quantity: int
    movement_type: str
    reason: str
    reference_type: str | None
    unit_cost: float | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Stock Transfer ---

class TransferItemCreate(BaseModel):
    product_id: UUID
    batch_id: UUID | None = None
    requested_quantity: int

    @field_validator("requested_quantity")
    @classmethod
    def qty_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

class StockTransferCreate(BaseModel):
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    items: list[TransferItemCreate]
    notes: str | None = None

class TransferItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    batch_id: UUID | None
    requested_quantity: int
    shipped_quantity: int
    received_quantity: int
    model_config = {"from_attributes": True}

class StockTransferResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    transfer_number: str
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    status: str
    notes: str | None
    requested_by: UUID | None
    approved_by: UUID | None
    shipped_at: datetime | None
    received_at: datetime | None
    items: list[TransferItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class TransferStatusUpdate(BaseModel):
    status: str
    items: list[dict] | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"draft", "approved", "shipped", "in_transit", "received", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


# --- Stock Alert ---

class StockAlertResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    warehouse_id: UUID
    alert_type: str
    current_quantity: int
    threshold: int
    is_resolved: bool
    created_at: datetime
    resolved_at: datetime | None
    model_config = {"from_attributes": True}
