from uuid import UUID
from pydantic import field_validator

from app.core.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, TenantResponseSchema, AuditResponseSchema
from app.core.schemas.decimal_type import Money, Quantity, Decimal2, Decimal4
from app.core.schemas.enums import InventoryReason, TransferStatus
from app.core.schemas.validators import validate_phone


# --- Category ---

class CategoryCreate(CreateSchema):
    name: str
    parent_id: UUID | None = None


class CategoryResponse(TenantResponseSchema):
    name: str
    parent_id: UUID | None


# --- Product ---

class ProductCreate(CreateSchema):
    name: str
    sku: str | None = None
    category_id: UUID | None = None
    unit_id: UUID | None = None
    sale_price: Money = Money(0)
    purchase_price: Money = Money(0)
    low_stock_threshold: int = 10
    tax_id: UUID | None = None

    @field_validator("low_stock_threshold")
    @classmethod
    def non_negative_threshold(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Threshold cannot be negative")
        return v


class ProductUpdate(UpdateSchema):
    name: str | None = None
    sku: str | None = None
    category_id: UUID | None = None
    sale_price: Money | None = None
    purchase_price: Money | None = None
    low_stock_threshold: int | None = None


class ProductResponse(AuditResponseSchema):
    name: str
    sku: str | None
    category_id: UUID | None
    sale_price: Decimal2
    purchase_price: Decimal2
    average_cost: Decimal2
    low_stock_threshold: int


# --- Warehouse ---

class WarehouseCreate(CreateSchema):
    name: str
    location: str | None = None
    branch_id: UUID | None = None


class WarehouseResponse(AuditResponseSchema):
    name: str
    location: str | None
    branch_id: UUID | None


# --- Inventory ---

class StockAdjustment(CreateSchema):
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reason: InventoryReason = InventoryReason.ADJUSTMENT

    @field_validator("quantity")
    @classmethod
    def non_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Quantity cannot be zero")
        return v


class InventoryResponse(ResponseSchema):
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reserved_quantity: int
    damaged_quantity: int
    available_quantity: int


# --- Movement ---

class MovementResponse(ResponseSchema):
    product_id: UUID
    from_warehouse_id: UUID | None
    to_warehouse_id: UUID | None
    quantity: int
    reason: InventoryReason


# --- Transfer ---

class TransferItemCreate(CreateSchema):
    product_id: UUID
    quantity: Quantity


class TransferCreate(CreateSchema):
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    items: list[TransferItemCreate]
    notes: str | None = None

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one transfer item is required")
        return v


class TransferStatusUpdate(CreateSchema):
    status: TransferStatus


class TransferResponse(TenantResponseSchema):
    transfer_number: str | None
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    status: TransferStatus
    notes: str | None
    items: list[dict] = []
