from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator


# --- Customer ---

class CustomerCreate(BaseModel):
    full_name: str
    phone: str | None = None
    address: str | None = None
    credit_limit: float = 0
    notes: str | None = None

class CustomerUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    credit_limit: float | None = None
    notes: str | None = None
    version: int | None = None

class CustomerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    full_name: str
    phone: str | None
    address: str | None
    credit_limit: float
    notes: str | None
    version: int
    created_at: datetime
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


# --- Supplier ---

class SupplierCreate(BaseModel):
    company_name: str
    phone: str | None = None

class SupplierUpdate(BaseModel):
    company_name: str | None = None
    phone: str | None = None
    version: int | None = None

class SupplierResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_name: str
    phone: str | None
    version: int
    created_at: datetime
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


# --- Lead ---

class LeadCreate(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    assigned_to: UUID | None = None

class LeadUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    status: str | None = None
    assigned_to: UUID | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"new", "contacted", "qualified", "unqualified", "converted", "lost"}
            if v not in allowed:
                raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v

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


# --- Opportunity ---

class OpportunityCreate(BaseModel):
    title: str
    lead_id: UUID | None = None
    customer_id: UUID | None = None
    expected_value: float | None = None
    stage: str = "prospecting"
    probability: float = 0
    close_date: datetime | None = None
    assigned_to: UUID | None = None

class OpportunityUpdate(BaseModel):
    title: str | None = None
    expected_value: float | None = None
    stage: str | None = None
    probability: float | None = None
    close_date: datetime | None = None
    assigned_to: UUID | None = None

    @field_validator("stage")
    @classmethod
    def valid_stage(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"}
            if v not in allowed:
                raise ValueError(f"Stage must be one of: {', '.join(allowed)}")
        return v

class OpportunityResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    lead_id: UUID | None
    customer_id: UUID | None
    expected_value: float | None
    stage: str
    probability: float
    close_date: datetime | None
    assigned_to: UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Activity ---

class ActivityCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    activity_type: str
    description: str | None = None
    due_date: datetime | None = None
    assigned_to: UUID | None = None

class ActivityUpdate(BaseModel):
    description: str | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None

class ActivityResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    entity_type: str | None
    entity_id: UUID | None
    activity_type: str | None
    description: str | None
    due_date: datetime | None
    completed_at: datetime | None
    assigned_to: UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}
