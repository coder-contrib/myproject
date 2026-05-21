from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_tenant_id
from app.modules.accounting.schemas import *
from app.modules.accounting.service import AccountingService

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.post("/accounts", response_model=AccountResponse)
async def create_account(data: AccountCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await AccountingService(db).create_account(tenant_id=tenant_id, **data.model_dump())

@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await AccountingService(db).get_accounts(tenant_id)

@router.post("/journal-entries", response_model=JournalEntryResponse)
async def create_journal_entry(data: JournalEntryCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await AccountingService(db).create_journal_entry(
        tenant_id=tenant_id,
        description=data.description,
        lines=[l.model_dump() for l in data.lines],
        reference_type=data.reference_type,
        reference_id=data.reference_id,
    )

@router.get("/journal-entries", response_model=list[JournalEntryResponse])
async def list_journal_entries(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await AccountingService(db).get_journal_entries(tenant_id)

@router.post("/fiscal-years", response_model=FiscalYearResponse)
async def create_fiscal_year(data: FiscalYearCreate, db: AsyncSession = Depends(get_db)):
    return await AccountingService(db).create_fiscal_year(**data.model_dump())
