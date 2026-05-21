from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class CustomerCreate(BaseModel):
    full_name: str
    phone: str | None = None
    address: str | None = None
    credit_limit: float = 0
    company_id: UUID | None = None


class CustomerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    full_name: str
    phone: str | None
    address: str | None
    credit_limit: float
    created_at: datetime
    model_config = {"from_attributes": True}


class SupplierCreate(BaseModel):
    company_name: str
    phone: str | None = None
    company_id: UUID | None = None


class SupplierResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_name: str
    phone: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class LeadCreate(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    assigned_to: UUID | None = None


class LeadResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    full_name: str
    email: str | None
    phone: str | None
    source: str | None
    status: str
    assigned_to: UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}


class OpportunityCreate(BaseModel):
    title: str
    lead_id: UUID | None = None
    customer_id: UUID | None = None
    expected_value: float | None = None
    stage: str = "prospecting"
    probability: float = 0
    assigned_to: UUID | None = None


class OpportunityResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    expected_value: float | None
    stage: str
    probability: float
    created_at: datetime
    model_config = {"from_attributes": True}
