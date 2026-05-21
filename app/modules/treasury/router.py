from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_tenant_id
from app.modules.treasury.schemas import *
from app.modules.treasury.service import TreasuryService

router = APIRouter(prefix="/treasury", tags=["treasury"])

@router.post("/", response_model=TreasuryResponse)
async def create_treasury(data: TreasuryCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await TreasuryService(db).create_treasury(tenant_id=tenant_id, **data.model_dump())

@router.get("/", response_model=list[TreasuryResponse])
async def list_treasuries(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await TreasuryService(db).get_treasuries(tenant_id)

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(data: PaymentCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await TreasuryService(db).create_payment(tenant_id=tenant_id, **data.model_dump())

@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await TreasuryService(db).get_payments(tenant_id)

@router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(data: ExpenseCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await TreasuryService(db).create_expense(tenant_id=tenant_id, **data.model_dump())

@router.get("/expenses", response_model=list[ExpenseResponse])
async def list_expenses(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await TreasuryService(db).get_expenses(tenant_id)
