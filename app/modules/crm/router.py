from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.modules.crm.schemas import (
    CustomerCreate, CustomerUpdate, CustomerResponse,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    LeadCreate, LeadUpdate, LeadResponse,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
)
from app.modules.crm.service import CRMService

router = APIRouter(prefix="/crm", tags=["crm"])


def _svc(db: AsyncSession, ctx: TenantContext) -> CRMService:
    return CRMService(db, ctx)


# --- Customers ---

@router.post("/customers", response_model=CustomerResponse)
async def create_customer(data: CustomerCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_customer(**data.model_dump())


@router.get("/customers", response_model=list[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_customers(skip=skip, limit=limit)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_customer(customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: UUID, data: CustomerUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_customer(customer_id, **data.model_dump(exclude_unset=True))


@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    await _svc(db, ctx).delete_customer(customer_id)
    return {"message": "Customer deleted"}


# --- Suppliers ---

@router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(data: SupplierCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_supplier(**data.model_dump())


@router.get("/suppliers", response_model=list[SupplierResponse])
async def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_suppliers(skip=skip, limit=limit)


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(supplier_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_supplier(supplier_id)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: UUID, data: SupplierUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_supplier(supplier_id, **data.model_dump(exclude_unset=True))


# --- Leads ---

@router.post("/leads", response_model=LeadResponse)
async def create_lead(data: LeadCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_lead(**data.model_dump())


@router.get("/leads", response_model=list[LeadResponse])
async def list_leads(
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_leads(skip=skip, limit=limit, status=status)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_lead(lead_id)


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: UUID, data: LeadUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_lead(lead_id, **data.model_dump(exclude_unset=True))


@router.post("/leads/{lead_id}/convert", response_model=CustomerResponse)
async def convert_lead(lead_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).convert_lead(lead_id)


# --- Opportunities ---

@router.post("/opportunities", response_model=OpportunityResponse)
async def create_opportunity(data: OpportunityCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_opportunity(**data.model_dump())


@router.get("/opportunities", response_model=list[OpportunityResponse])
async def list_opportunities(
    stage: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_opportunities(skip=skip, limit=limit, stage=stage)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_opportunity(opportunity_id)


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(opportunity_id: UUID, data: OpportunityUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_opportunity(opportunity_id, **data.model_dump(exclude_unset=True))


# --- Activities ---

@router.post("/activities", response_model=ActivityResponse)
async def create_activity(data: ActivityCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_activity(**data.model_dump())


@router.get("/activities", response_model=list[ActivityResponse])
async def list_activities(
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_activities(entity_type=entity_type, entity_id=entity_id, skip=skip, limit=limit)


@router.post("/activities/{activity_id}/complete", response_model=ActivityResponse)
async def complete_activity(activity_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).complete_activity(activity_id)


# --- Pipeline ---

@router.get("/pipeline")
async def get_pipeline(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_pipeline_summary()
