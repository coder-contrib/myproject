from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, field_validator


# --- Purchase Order ---

class PurchaseOrderItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    unit_price: float
    tax_percent: float = 0

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    warehouse_id: UUID | None = None
    order_date: date
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseOrderItemCreate]

class PurchaseOrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: float
    unit_price: float
    tax_percent: float
    received_quantity: float
    total: float
    model_config = {"from_attributes": True}

class PurchaseOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    order_number: str
    supplier_id: UUID
    warehouse_id: UUID | None
    order_date: date
    expected_date: date | None
    subtotal: float
    discount_amount: float
    tax_amount: float
    total: float
    notes: str | None
    status: str
    items: list[PurchaseOrderItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class PurchaseOrderStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"draft", "confirmed", "sent", "partial", "received", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


# --- Purchase Invoice ---

class PurchaseInvoiceItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    unit_price: float
    tax_percent: float = 0

class PurchaseInvoiceCreate(BaseModel):
    supplier_id: UUID
    purchase_order_id: UUID | None = None
    issue_date: date
    due_date: date | None = None
    notes: str | None = None
    items: list[PurchaseInvoiceItemCreate]

class PurchaseInvoiceItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: float
    unit_price: float
    tax_percent: float
    tax_amount: float
    total: float
    model_config = {"from_attributes": True}

class PurchaseInvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_number: str
    supplier_id: UUID
    purchase_order_id: UUID | None
    issue_date: date
    due_date: date | None
    subtotal: float
    tax_amount: float
    total: float
    amount_paid: float
    balance_due: float
    status: str
    items: list[PurchaseInvoiceItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Purchase Payment ---

class PurchasePaymentCreate(BaseModel):
    invoice_id: UUID
    amount: float
    payment_method: str
    payment_date: date
    reference: str | None = None
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


# --- Purchase Return ---

class PurchaseReturnItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    unit_price: float

class PurchaseReturnCreate(BaseModel):
    invoice_id: UUID
    supplier_id: UUID
    return_date: date
    reason: str | None = None
    items: list[PurchaseReturnItemCreate]

class PurchaseReturnItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: float
    unit_price: float
    total: float
    model_config = {"from_attributes": True}

class PurchaseReturnResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    return_number: str
    invoice_id: UUID
    supplier_id: UUID
    return_date: date
    total: float
    reason: str | None
    status: str
    items: list[PurchaseReturnItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}
