from uuid import UUID
from datetime import date
from pydantic import field_validator

from app.core.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, TenantResponseSchema, AuditResponseSchema
from app.core.schemas.decimal_type import Money, Quantity, Decimal2, Decimal4
from app.core.schemas.enums import InvoiceStatus, PurchaseOrderStatus, PaymentMethod


# --- Purchase Order ---

class PurchaseLineItemCreate(CreateSchema):
    product_id: UUID
    quantity: Quantity
    unit_price: Money


class PurchaseLineItemResponse(ResponseSchema):
    product_id: UUID
    quantity: Decimal4
    unit_price: Decimal2
    total: Decimal2


class PurchaseOrderCreate(CreateSchema):
    supplier_id: UUID
    currency_id: UUID | None = None
    items: list[PurchaseLineItemCreate]
    notes: str | None = None

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one line item is required")
        return v


class PurchaseOrderStatusUpdate(CreateSchema):
    status: PurchaseOrderStatus


class PurchaseOrderResponse(TenantResponseSchema):
    order_number: str
    supplier_id: UUID | None
    total: Decimal2
    status: PurchaseOrderStatus
    items: list[PurchaseLineItemResponse] = []


# --- Purchase Invoice ---

class PurchaseInvoiceCreate(CreateSchema):
    supplier_id: UUID
    purchase_order_id: UUID | None = None
    currency_id: UUID | None = None
    items: list[PurchaseLineItemCreate]
    due_date: date | None = None

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one line item is required")
        return v


class PurchaseInvoiceResponse(AuditResponseSchema):
    invoice_number: str
    supplier_id: UUID | None
    purchase_order_id: UUID | None
    total: Decimal2
    amount_paid: Decimal2
    balance_due: Decimal2 | None = None
    status: InvoiceStatus
    due_date: date | None
    items: list[PurchaseLineItemResponse] = []


# --- Payment ---

class PurchasePaymentCreate(CreateSchema):
    invoice_id: UUID
    amount: Money
    method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    treasury_id: UUID | None = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v):
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v


class PurchasePaymentResponse(ResponseSchema):
    invoice_id: UUID
    amount: Decimal2
    method: PaymentMethod


# --- Return ---

class PurchaseReturnCreate(CreateSchema):
    invoice_id: UUID
    items: list[dict]
    reason: str | None = None


class PurchaseReturnResponse(TenantResponseSchema):
    invoice_id: UUID
    status: str
    reason: str | None
