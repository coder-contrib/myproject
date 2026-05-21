from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, field_validator


class LineItemCreate(BaseModel):
    product_id: UUID
    description: str | None = None
    quantity: float
    unit_price: float
    discount_percent: float = 0
    tax_percent: float = 0
    cost_price: float = 0

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v): 
        if v <= 0: raise ValueError("Quantity must be positive")
        return v

class LineItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    description: str | None
    quantity: float
    unit_price: float
    discount_percent: float
    tax_percent: float
    tax_amount: float = 0
    total: float
    model_config = {"from_attributes": True}

# --- Quotation ---
class QuotationCreate(BaseModel):
    customer_id: UUID | None = None
    valid_until: date | None = None
    discount_amount: float = 0
    notes: str | None = None
    terms: str | None = None
    items: list[LineItemCreate]

class QuotationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    quotation_number: str
    customer_id: UUID | None
    valid_until: date | None
    subtotal: float
    discount_amount: float
    tax_amount: float
    total: float
    status: str
    items: list[LineItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class QuotationStatusUpdate(BaseModel):
    status: str

# --- Invoice ---
class InvoiceCreate(BaseModel):
    customer_id: UUID | None = None
    warehouse_id: UUID | None = None
    issue_date: date | None = None
    due_date: date | None = None
    payment_terms: str | None = None
    discount_amount: float = 0
    notes: str | None = None
    items: list[LineItemCreate]

class InvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_number: str
    customer_id: UUID | None
    quotation_id: UUID | None
    issue_date: date
    due_date: date | None
    subtotal: float
    discount_amount: float
    tax_amount: float
    total: float
    amount_paid: float
    balance_due: float
    status: str
    items: list[LineItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class InvoiceStatusUpdate(BaseModel):
    status: str

# --- Payment ---
class PaymentCreate(BaseModel):
    amount: float
    payment_method: str
    payment_date: date | None = None
    reference: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0: raise ValueError("Amount must be positive")
        return v

class PaymentResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    amount: float
    payment_method: str
    payment_date: date
    reference: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

# --- Return ---
class ReturnItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    unit_price: float
    tax_percent: float = 0

class ReturnCreate(BaseModel):
    invoice_id: UUID
    items: list[ReturnItemCreate]
    reason: str | None = None
    restock: bool = True

class ReturnItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: float
    unit_price: float
    total: float
    model_config = {"from_attributes": True}

class ReturnResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    return_number: str
    invoice_id: UUID
    return_date: date
    subtotal: float
    tax_amount: float
    total: float
    reason: str | None
    status: str
    items: list[ReturnItemResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}

class ConvertQuotationRequest(BaseModel):
    warehouse_id: UUID | None = None
