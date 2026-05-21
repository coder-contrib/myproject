from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.modules.accounting.schemas import (
    AccountCreate, AccountUpdate, AccountResponse,
    FiscalYearCreate, FiscalYearResponse,
    CostCenterCreate, CostCenterResponse,
    JournalEntryCreate, JournalEntryResponse,
    LedgerEntryResponse, TrialBalanceRow,
)
from app.modules.accounting.service import AccountingService

router = APIRouter(prefix="/accounting", tags=["accounting"])


def _svc(db: AsyncSession, ctx: TenantContext) -> AccountingService:
    return AccountingService(db, ctx)


# --- Chart of Accounts ---

@router.post("/accounts", response_model=AccountResponse)
async def create_account(data: AccountCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_account(**data.model_dump())


@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(
    account_type: str | None = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_accounts(account_type=account_type)


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_account(account_id)


@router.patch("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(account_id: UUID, data: AccountUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_account(account_id, **data.model_dump(exclude_unset=True))


# --- Fiscal Years ---

@router.post("/fiscal-years", response_model=FiscalYearResponse)
async def create_fiscal_year(data: FiscalYearCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_fiscal_year(**data.model_dump())


@router.get("/fiscal-years", response_model=list[FiscalYearResponse])
async def list_fiscal_years(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_fiscal_years()


@router.post("/fiscal-years/{fiscal_year_id}/close", response_model=FiscalYearResponse)
async def close_fiscal_year(fiscal_year_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).close_fiscal_year(fiscal_year_id)


# --- Cost Centers ---

@router.post("/cost-centers", response_model=CostCenterResponse)
async def create_cost_center(data: CostCenterCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_cost_center(**data.model_dump())


@router.get("/cost-centers", response_model=list[CostCenterResponse])
async def list_cost_centers(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_cost_centers()


# --- Journal Entries ---

@router.post("/journal-entries", response_model=JournalEntryResponse)
async def create_journal_entry(data: JournalEntryCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    lines = [line.model_dump() for line in data.lines]
    return await _svc(db, ctx).create_journal_entry(
        entry_date=data.entry_date,
        lines=lines,
        fiscal_year_id=data.fiscal_year_id,
        cost_center_id=data.cost_center_id,
        reference_type=data.reference_type,
        reference_id=data.reference_id,
        description=data.description,
    )


@router.get("/journal-entries", response_model=list[JournalEntryResponse])
async def list_journal_entries(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_journal_entries(skip=skip, limit=limit, status=status)


@router.get("/journal-entries/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(entry_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_journal_entry(entry_id)


@router.post("/journal-entries/{entry_id}/post", response_model=JournalEntryResponse)
async def post_journal_entry(entry_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).post_journal_entry(entry_id)


@router.post("/journal-entries/{entry_id}/reverse", response_model=JournalEntryResponse)
async def reverse_journal_entry(entry_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).reverse_journal_entry(entry_id)


# --- Ledger & Reports ---

@router.get("/ledger/{account_id}", response_model=list[LedgerEntryResponse])
async def get_ledger(
    account_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_ledger(account_id, start_date=start_date, end_date=end_date)


@router.get("/trial-balance", response_model=list[TrialBalanceRow])
async def get_trial_balance(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_trial_balance()
