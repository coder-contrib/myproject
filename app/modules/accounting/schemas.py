from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel


class AccountCreate(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    company_id: UUID | None = None
    parent_id: UUID | None = None

class AccountResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    account_code: str
    account_name: str
    account_type: str
    parent_id: UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}

class JournalEntryLineCreate(BaseModel):
    account_id: UUID
    debit: float = 0
    credit: float = 0

class JournalEntryCreate(BaseModel):
    description: str | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    lines: list[JournalEntryLineCreate]

class JournalEntryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    description: str | None
    reference_type: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class FiscalYearCreate(BaseModel):
    company_id: UUID
    year_name: str
    start_date: date
    end_date: date

class FiscalYearResponse(BaseModel):
    id: UUID
    company_id: UUID | None
    year_name: str
    start_date: date
    end_date: date
    is_closed: bool
    created_at: datetime
    model_config = {"from_attributes": True}
