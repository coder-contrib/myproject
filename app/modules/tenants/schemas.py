from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class TenantCreate(BaseModel):
    name: str


class TenantResponse(BaseModel):
    id: UUID
    name: str
    subscription_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    name: str
    phone: str | None = None
    address: str | None = None
    inventory_valuation_method: str = "weighted_average"


class CompanyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    phone: str | None
    address: str | None
    inventory_valuation_method: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BranchCreate(BaseModel):
    company_id: UUID
    name: str
    address: str | None = None


class BranchResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    name: str
    address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
