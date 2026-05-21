from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_tenant_id
from app.modules.purchases.schemas import *
from app.modules.purchases.service import PurchaseService

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/invoices", response_model=PurchaseInvoiceResponse)
async def create_invoice(data: PurchaseInvoiceCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await PurchaseService(db).create_invoice(tenant_id=tenant_id, **data.model_dump())

@router.get("/invoices", response_model=list[PurchaseInvoiceResponse])
async def list_invoices(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await PurchaseService(db).get_invoices(tenant_id)

@router.post("/orders", response_model=PurchaseOrderResponse)
async def create_order(data: PurchaseOrderCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await PurchaseService(db).create_order(tenant_id=tenant_id, **data.model_dump())

@router.get("/orders", response_model=list[PurchaseOrderResponse])
async def list_orders(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await PurchaseService(db).get_orders(tenant_id)

@router.post("/debit-notes", response_model=DebitNoteResponse)
async def create_debit_note(data: DebitNoteCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await PurchaseService(db).create_debit_note(tenant_id=tenant_id, **data.model_dump())

@router.get("/debit-notes", response_model=list[DebitNoteResponse])
async def list_debit_notes(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await PurchaseService(db).get_debit_notes(tenant_id)
