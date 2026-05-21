from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class SalesInvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: UUID | None = None
    branch_id: UUID | None = None
    payment_type: str = "cash"
    due_date: datetime | None = None

class SalesInvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_number: str
    customer_id: UUID | None
    subtotal: float
    discount: float
    total: float
    amount_paid: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class SalesItemCreate(BaseModel):
    product_id: UUID
    quantity: float
    unit_price: float
    discount: float = 0
    tax_percent: float = 0

class SalesItemResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    product_id: UUID
    quantity: float
    unit_price: float
    total: float
    model_config = {"from_attributes": True}

class QuotationCreate(BaseModel):
    quotation_number: str
    customer_id: UUID | None = None

class QuotationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    quotation_number: str
    total: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class CreditNoteCreate(BaseModel):
    note_number: str
    customer_id: UUID | None = None
    sales_invoice_id: UUID | None = None
    amount: float
    reason: str | None = None

class CreditNoteResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    note_number: str
    amount: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
