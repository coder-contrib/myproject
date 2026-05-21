from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.core.api import (
    PaginationParams, get_pagination,
    FilterParams, get_filters,
    SortParams, get_sorting,
    SearchParams, get_search,
)
from app.core.api.response import paginated_response, success_response
from app.modules.accounting.models import Account, JournalEntry, JournalEntryLine

router = APIRouter(prefix="/accounting", tags=["accounting"])


class AccountCreate(BaseModel):
    account_code: str
    account_name: str
    account_type: str
    parent_id: UUID | None = None

    @field_validator("account_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        allowed = {"asset", "liability", "equity", "revenue", "expense", "contra"}
        if v not in allowed:
            raise ValueError(f"account_type must be one of: {', '.join(allowed)}")
        return v


class JournalEntryLineCreate(BaseModel):
    account_id: UUID
    debit: float = 0
    credit: float = 0

    @field_validator("debit", "credit")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v


class JournalEntryCreate(BaseModel):
    description: str | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    lines: list[JournalEntryLineCreate]

    @field_validator("lines")
    @classmethod
    def balanced(cls, v: list) -> list:
        if len(v) < 2:
            raise ValueError("Journal entry must have at least 2 lines")
        total_debit = sum(line.debit for line in v)
        total_credit = sum(line.credit for line in v)
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Entry must balance: debit={total_debit}, credit={total_credit}")
        return v


@router.get("/accounts")
async def list_accounts(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    search: SearchParams = Depends(get_search),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(Account).where(
        Account.tenant_id == ctx.tenant_id,
        Account.deleted_at == None,
    )

    base = search.apply_to_query(base, Account, searchable_fields=["account_code", "account_name"])
    base = filters.apply_to_query(base, Account)
    base = sorting.apply_to_query(base, Account)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    accounts = result.scalars().all()

    data = [
        {
            "id": str(a.id),
            "account_code": a.account_code,
            "account_name": a.account_name,
            "account_type": a.account_type,
            "parent_id": str(a.parent_id) if a.parent_id else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in accounts
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("/accounts")
async def create_account(
    data: AccountCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Account).where(
            Account.tenant_id == ctx.tenant_id,
            Account.account_code == data.account_code,
            Account.deleted_at == None,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Account code already exists")

    account = Account(
        tenant_id=ctx.tenant_id,
        company_id=ctx.company_id,
        account_code=data.account_code,
        account_name=data.account_name,
        account_type=data.account_type,
        parent_id=data.parent_id,
        created_by=ctx.user_id,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)

    return success_response(
        data={"id": str(account.id), "account_code": account.account_code, "account_name": account.account_name},
        message="Account created",
    )


@router.get("/accounts/{account_id}")
async def get_account(
    account_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.tenant_id == ctx.tenant_id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return success_response(data={
        "id": str(account.id),
        "account_code": account.account_code,
        "account_name": account.account_name,
        "account_type": account.account_type,
        "parent_id": str(account.parent_id) if account.parent_id else None,
        "version": account.version,
        "created_at": account.created_at.isoformat() if account.created_at else None,
    })


@router.get("/journal-entries")
async def list_journal_entries(
    pagination: PaginationParams = Depends(get_pagination),
    filters: FilterParams = Depends(get_filters),
    sorting: SortParams = Depends(get_sorting),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    base = select(JournalEntry).where(JournalEntry.tenant_id == ctx.tenant_id)
    base = filters.apply_to_query(base, JournalEntry)
    base = sorting.apply_to_query(base, JournalEntry)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.offset(pagination.skip).limit(pagination.limit)
    result = await db.execute(stmt)
    entries = result.scalars().all()

    data = [
        {
            "id": str(e.id),
            "description": e.description,
            "reference_type": e.reference_type,
            "reference_id": str(e.reference_id) if e.reference_id else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]

    return paginated_response(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("/journal-entries")
async def create_journal_entry(
    data: JournalEntryCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone

    entry = JournalEntry(
        tenant_id=ctx.tenant_id,
        description=data.description,
        reference_type=data.reference_type,
        reference_id=data.reference_id,
        created_by=ctx.user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()

    for line_data in data.lines:
        line = JournalEntryLine(
            journal_entry_id=entry.id,
            journal_entry_created_at=entry.created_at,
            account_id=line_data.account_id,
            debit=line_data.debit,
            credit=line_data.credit,
        )
        db.add(line)

    await db.flush()
    await db.refresh(entry)

    return success_response(
        data={
            "id": str(entry.id),
            "description": entry.description,
            "lines_count": len(data.lines),
            "total_debit": sum(l.debit for l in data.lines),
        },
        message="Journal entry created",
    )


@router.get("/journal-entries/{entry_id}")
async def get_journal_entry(
    entry_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.tenant_id == ctx.tenant_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    lines_result = await db.execute(
        select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry_id)
    )
    lines = lines_result.scalars().all()

    return success_response(data={
        "id": str(entry.id),
        "description": entry.description,
        "reference_type": entry.reference_type,
        "reference_id": str(entry.reference_id) if entry.reference_id else None,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "lines": [
            {
                "id": str(line.id),
                "account_id": str(line.account_id),
                "debit": float(line.debit),
                "credit": float(line.credit),
            }
            for line in lines
        ],
        "total_debit": sum(float(l.debit) for l in lines),
        "total_credit": sum(float(l.credit) for l in lines),
    })


@router.get("/trial-balance")
async def trial_balance(
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            Account.id,
            Account.account_code,
            Account.account_name,
            Account.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        )
        .outerjoin(JournalEntryLine, JournalEntryLine.account_id == Account.id)
        .where(Account.tenant_id == ctx.tenant_id, Account.deleted_at == None)
        .group_by(Account.id, Account.account_code, Account.account_name, Account.account_type)
        .order_by(Account.account_code)
    )

    result = await db.execute(stmt)
    rows = result.all()

    data = [
        {
            "account_id": str(row.id),
            "account_code": row.account_code,
            "account_name": row.account_name,
            "account_type": row.account_type,
            "total_debit": float(row.total_debit),
            "total_credit": float(row.total_credit),
            "balance": float(row.total_debit - row.total_credit),
        }
        for row in rows
    ]

    total_debit = sum(r["total_debit"] for r in data)
    total_credit = sum(r["total_credit"] for r in data)

    return success_response(data={
        "accounts": data,
        "totals": {
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01,
        },
    })
