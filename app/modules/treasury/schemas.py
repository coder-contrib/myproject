from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class TreasuryCreate(BaseModel):
    name: str
    currency_id: UUID | None = None

class TreasuryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    created_at: datetime
    model_config = {"from_attributes": True}

class PaymentCreate(BaseModel):
    treasury_id: UUID
    amount: float
    method: str
    sales_invoice_id: UUID | None = None
    purchase_invoice_id: UUID | None = None

class PaymentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    treasury_id: UUID
    amount: float
    method: str
    created_at: datetime
    model_config = {"from_attributes": True}

class ExpenseCreate(BaseModel):
    treasury_id: UUID
    category: str
    amount: float
    description: str | None = None

class ExpenseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    category: str
    amount: float
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
