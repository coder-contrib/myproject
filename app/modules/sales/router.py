from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.modules.sales.schemas import (
    QuotationCreate, QuotationResponse, QuotationStatusUpdate, ConvertQuotationRequest,
    InvoiceCreate, InvoiceResponse, InvoiceStatusUpdate,
    PaymentCreate, PaymentResponse, ReturnCreate, ReturnResponse,
)
from app.modules.sales.service import SalesService

router = APIRouter(prefix="/sales", tags=["sales"])


def _svc(db: AsyncSession, ctx: TenantContext) -> SalesService:
    return SalesService(db, ctx)


# --- Quotations ---
@router.post("/quotations", response_model=QuotationResponse)
async def create_quotation(data: QuotationCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_quotation(items=[i.model_dump() for i in data.items], customer_id=data.customer_id, valid_until=data.valid_until, discount_amount=data.discount_amount, notes=data.notes, terms=data.terms)

@router.get("/quotations", response_model=list[QuotationResponse])
async def list_quotations(status: str | None = None, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_quotations(status=status, skip=skip, limit=limit)

@router.get("/quotations/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(quotation_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_quotation(quotation_id)

@router.patch("/quotations/{quotation_id}/status", response_model=QuotationResponse)
async def update_quotation_status(quotation_id: UUID, data: QuotationStatusUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_quotation_status(quotation_id, data.status)

@router.post("/quotations/{quotation_id}/convert", response_model=InvoiceResponse)
async def convert_quotation(quotation_id: UUID, data: ConvertQuotationRequest, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).convert_quotation_to_invoice(quotation_id, warehouse_id=data.warehouse_id)

# --- Invoices ---
@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(data: InvoiceCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_invoice(items=[i.model_dump() for i in data.items], customer_id=data.customer_id, warehouse_id=data.warehouse_id, issue_date=data.issue_date, due_date=data.due_date, payment_terms=data.payment_terms, discount_amount=data.discount_amount, notes=data.notes)

@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(status: str | None = None, customer_id: UUID | None = None, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_invoices(status=status, customer_id=customer_id, skip=skip, limit=limit)

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_invoice(invoice_id)

@router.patch("/invoices/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(invoice_id: UUID, data: InvoiceStatusUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_invoice_status(invoice_id, data.status)

# --- Payments ---
@router.post("/invoices/{invoice_id}/payments", response_model=PaymentResponse)
async def record_payment(invoice_id: UUID, data: PaymentCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).record_payment(invoice_id, amount=data.amount, payment_method=data.payment_method, payment_date=data.payment_date, reference=data.reference)

@router.get("/invoices/{invoice_id}/payments", response_model=list[PaymentResponse])
async def list_payments(invoice_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_payments(invoice_id)

# --- Returns ---
@router.post("/returns", response_model=ReturnResponse)
async def create_return(data: ReturnCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_return(invoice_id=data.invoice_id, items=[i.model_dump() for i in data.items], reason=data.reason, restock=data.restock)

@router.get("/returns", response_model=list[ReturnResponse])
async def list_returns(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_returns(skip=skip, limit=limit)

@router.post("/returns/{return_id}/approve", response_model=ReturnResponse)
async def approve_return(return_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).approve_return(return_id)
