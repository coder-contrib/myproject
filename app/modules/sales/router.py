from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_tenant_id
from app.modules.sales.schemas import *
from app.modules.sales.service import SalesService

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/invoices", response_model=SalesInvoiceResponse)
async def create_invoice(data: SalesInvoiceCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await SalesService(db).create_invoice(tenant_id=tenant_id, **data.model_dump())

@router.get("/invoices", response_model=list[SalesInvoiceResponse])
async def list_invoices(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await SalesService(db).get_invoices(tenant_id)

@router.get("/invoices/{invoice_id}", response_model=SalesInvoiceResponse)
async def get_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db)):
    return await SalesService(db).get_invoice(invoice_id)

@router.post("/invoices/{invoice_id}/items", response_model=SalesItemResponse)
async def add_item(invoice_id: UUID, data: SalesItemCreate, db: AsyncSession = Depends(get_db)):
    return await SalesService(db).add_item(invoice_id=invoice_id, **data.model_dump())

@router.post("/quotations", response_model=QuotationResponse)
async def create_quotation(data: QuotationCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await SalesService(db).create_quotation(tenant_id=tenant_id, **data.model_dump())

@router.get("/quotations", response_model=list[QuotationResponse])
async def list_quotations(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await SalesService(db).get_quotations(tenant_id)

@router.post("/credit-notes", response_model=CreditNoteResponse)
async def create_credit_note(data: CreditNoteCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await SalesService(db).create_credit_note(tenant_id=tenant_id, **data.model_dump())

@router.get("/credit-notes", response_model=list[CreditNoteResponse])
async def list_credit_notes(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await SalesService(db).get_credit_notes(tenant_id)
