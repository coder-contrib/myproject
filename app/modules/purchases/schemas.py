from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class PurchaseInvoiceCreate(BaseModel):
    invoice_number: str
    supplier_id: UUID | None = None
    branch_id: UUID | None = None

class PurchaseInvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_number: str
    supplier_id: UUID | None
    total: float
    amount_paid: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class PurchaseOrderCreate(BaseModel):
    order_number: str
    supplier_id: UUID | None = None

class PurchaseOrderResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    order_number: str
    total: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

class DebitNoteCreate(BaseModel):
    note_number: str
    supplier_id: UUID | None = None
    purchase_invoice_id: UUID | None = None
    amount: float
    reason: str | None = None

class DebitNoteResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    note_number: str
    amount: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
