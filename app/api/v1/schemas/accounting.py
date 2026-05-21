from uuid import UUID
from datetime import datetime
from pydantic import field_validator, model_validator
from typing import Self

from app.core.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, TenantResponseSchema
from app.core.schemas.decimal_type import Money, Decimal2
from app.core.schemas.enums import AccountType


# --- Account ---

class AccountCreate(CreateSchema):
    account_code: str
    account_name: str
    account_type: AccountType
    parent_id: UUID | None = None

    @field_validator("account_code")
    @classmethod
    def code_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Account code cannot be empty")
        return v.strip()


class AccountUpdate(UpdateSchema):
    account_name: str | None = None
    account_type: AccountType | None = None
    parent_id: UUID | None = None


class AccountResponse(TenantResponseSchema):
    account_code: str
    account_name: str
    account_type: AccountType
    parent_id: UUID | None
    version: int


# --- Journal Entry ---

class JournalEntryLineCreate(CreateSchema):
    account_id: UUID
    debit: Money = Money(0)
    credit: Money = Money(0)

    @model_validator(mode="after")
    def one_side_only(self) -> Self:
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A line can have debit OR credit, not both")
        if self.debit == 0 and self.credit == 0:
            raise ValueError("Either debit or credit must be positive")
        return self


class JournalEntryCreate(CreateSchema):
    description: str | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    fiscal_year_id: UUID | None = None
    cost_center_id: UUID | None = None
    lines: list[JournalEntryLineCreate]

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: list) -> list:
        if len(v) < 2:
            raise ValueError("Journal entry must have at least 2 lines")
        total_debit = sum(float(line.debit) for line in v)
        total_credit = sum(float(line.credit) for line in v)
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(
                f"Journal entry must balance: debit={total_debit:.2f}, credit={total_credit:.2f}"
            )
        return v


class JournalEntryLineResponse(ResponseSchema):
    account_id: UUID
    debit: Decimal2
    credit: Decimal2


class JournalEntryResponse(TenantResponseSchema):
    description: str | None
    reference_type: str | None
    reference_id: UUID | None
    lines: list[JournalEntryLineResponse] = []
    total_debit: Decimal2 | None = None
    total_credit: Decimal2 | None = None


# --- Trial Balance ---

class TrialBalanceRow(CreateSchema):
    account_id: UUID
    account_code: str
    account_name: str
    account_type: AccountType
    total_debit: Decimal2
    total_credit: Decimal2
    balance: Decimal2


class TrialBalanceResponse(CreateSchema):
    accounts: list[TrialBalanceRow]
    total_debit: Decimal2
    total_credit: Decimal2
    is_balanced: bool
