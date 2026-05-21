from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, field_validator


# --- Account (Chart of Accounts) ---

class AccountCreate(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    parent_id: UUID | None = None
    currency: str = "USD"
    description: str | None = None

    @field_validator("account_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        allowed = {"asset", "liability", "equity", "revenue", "expense"}
        if v not in allowed:
            raise ValueError(f"Account type must be one of: {', '.join(allowed)}")
        return v

class AccountUpdate(BaseModel):
    account_name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    version: int | None = None

class AccountResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    account_code: str
    account_name: str
    account_type: str
    parent_id: UUID | None
    currency: str
    description: str | None
    is_active: bool
    balance: float
    version: int
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Fiscal Year ---

class FiscalYearCreate(BaseModel):
    year_name: str
    start_date: date
    end_date: date

class FiscalYearResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    year_name: str
    start_date: date
    end_date: date
    is_closed: bool
    closed_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Cost Center ---

class CostCenterCreate(BaseModel):
    name: str
    code: str
    parent_id: UUID | None = None

class CostCenterResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    code: str
    parent_id: UUID | None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Journal Entry ---

class JournalLineCreate(BaseModel):
    account_id: UUID
    debit: float = 0
    credit: float = 0
    description: str | None = None
    cost_center_id: UUID | None = None

    @field_validator("debit", "credit")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Debit and credit must be non-negative")
        return v

class JournalEntryCreate(BaseModel):
    entry_date: date
    fiscal_year_id: UUID | None = None
    cost_center_id: UUID | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    description: str | None = None
    lines: list[JournalLineCreate]

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: list) -> list:
        if len(v) < 2:
            raise ValueError("Journal entry must have at least 2 lines")
        total_debit = sum(line.debit for line in v)
        total_credit = sum(line.credit for line in v)
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(
                f"Journal entry must balance: total debit ({total_debit}) must equal total credit ({total_credit})"
            )
        return v

class JournalLineResponse(BaseModel):
    id: UUID
    account_id: UUID
    debit: float
    credit: float
    description: str | None
    cost_center_id: UUID | None
    model_config = {"from_attributes": True}

class JournalEntryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    entry_number: str
    entry_date: date
    fiscal_year_id: UUID | None
    cost_center_id: UUID | None
    reference_type: str | None
    reference_id: UUID | None
    description: str | None
    total_debit: float
    total_credit: float
    status: str
    is_reversed: bool
    lines: list[JournalLineResponse] = []
    created_at: datetime
    posted_at: datetime | None
    model_config = {"from_attributes": True}


# --- Ledger ---

class LedgerEntryResponse(BaseModel):
    entry_date: date
    entry_number: str
    description: str | None
    debit: float
    credit: float
    running_balance: float


# --- Trial Balance ---

class TrialBalanceRow(BaseModel):
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    debit_total: float
    credit_total: float
