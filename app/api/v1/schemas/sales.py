from uuid import UUID
from datetime import datetime, date
from pydantic import field_validator, model_validator
from typing import Self

from app.core.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, TenantResponseSchema, AuditResponseSchema
from app.core.schemas.decimal_type import Money, Quantity, Percentage, Decimal2, Decimal4
from app.core.schemas.enums import InvoiceStatus, PaymentMethod, PaymentType, QuotationStatus
from app.core.schemas.validators import validate_future_date


# --- Line Items ---

class SalesLineItemCreate(CreateSchema):
    product_id: UUID
    quantity: Quantity
    unit_price: Money
    discount: Decimal2 = Decimal2(0)
    tax_id: UUID | None = None
    discount_percent: Percentage = Percentage(0)


class SalesLineItemResponse(ResponseSchema):
    product_id: UUID
    quantity: Decimal4
    unit_price: Decimal2
    discount: Decimal2
    tax_percent: Decimal2
    tax_amount: Decimal2
    total: Decimal2


# --- Quotation ---

class QuotationCreate(CreateSchema):
    customer_id: UUID | None = None
    currency_id: UUID | None = None
    items: list[SalesLineItemCreate]
    valid_until: date | None = None
    notes: str | None = None

    @field_validator("valid_until")
    @classmethod
    def future_date(cls, v: date | None) -> date | None:
        return validate_future_date(v)

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one line item is required")
        return v


class QuotationStatusUpdate(CreateSchema):
    status: QuotationStatus


class QuotationResponse(TenantResponseSchema):
    quotation_number: str
    customer_id: UUID | None
    subtotal: Decimal2
    discount: Decimal2
    total: Decimal2
    status: QuotationStatus
    valid_until: date | None
    items: list[SalesLineItemResponse] = []


# --- Invoice ---

class SalesInvoiceCreate(CreateSchema):
    customer_id: UUID | None = None
    currency_id: UUID | None = None
    payment_type: PaymentType = PaymentType.CASH
    items: list[SalesLineItemCreate]
    due_date: date | None = None
    notes: str | None = None

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one line item is required")
        return v


class SalesInvoiceResponse(AuditResponseSchema):
    invoice_number: str
    customer_id: UUID | None
    subtotal: Decimal2
    discount: Decimal2
    total: Decimal2
    amount_paid: Decimal2
    balance_due: Decimal2 | None = None
    payment_type: PaymentType
    status: InvoiceStatus
    due_date: date | None
    items: list[SalesLineItemResponse] = []


# --- Payment ---

class SalesPaymentCreate(CreateSchema):
    invoice_id: UUID
    amount: Money
    method: PaymentMethod = PaymentMethod.CASH
    treasury_id: UUID | None = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v):
        if v <= 0:
            raise ValueError("Payment amount must be positive")
        return v


class SalesPaymentResponse(ResponseSchema):
    invoice_id: UUID
    amount: Decimal2
    method: PaymentMethod
    treasury_id: UUID | None


# --- Return ---

class SalesReturnItemCreate(CreateSchema):
    product_id: UUID
    quantity: Quantity
    reason: str | None = None


class SalesReturnCreate(CreateSchema):
    invoice_id: UUID
    items: list[SalesReturnItemCreate]
    reason: str | None = None

    @field_validator("items")
    @classmethod
    def at_least_one_item(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one return item is required")
        return v


class SalesReturnResponse(TenantResponseSchema):
    invoice_id: UUID
    status: str
    reason: str | None
    items: list[dict] = []
