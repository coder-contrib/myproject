from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, get_current_tenant_id
from app.modules.crm.schemas import *
from app.modules.crm.service import CRMService

router = APIRouter(prefix="/crm", tags=["crm"])


@router.post("/customers", response_model=CustomerResponse)
async def create_customer(data: CustomerCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.create_customer(tenant_id=tenant_id, **data.model_dump())


@router.get("/customers", response_model=list[CustomerResponse])
async def list_customers(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.get_customers(tenant_id)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.get_customer(customer_id)


@router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(data: SupplierCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.create_supplier(tenant_id=tenant_id, **data.model_dump())


@router.get("/suppliers", response_model=list[SupplierResponse])
async def list_suppliers(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.get_suppliers(tenant_id)


@router.post("/leads", response_model=LeadResponse)
async def create_lead(data: LeadCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.create_lead(tenant_id=tenant_id, **data.model_dump())


@router.get("/leads", response_model=list[LeadResponse])
async def list_leads(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.get_leads(tenant_id)


@router.post("/opportunities", response_model=OpportunityResponse)
async def create_opportunity(data: OpportunityCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.create_opportunity(tenant_id=tenant_id, **data.model_dump())


@router.get("/opportunities", response_model=list[OpportunityResponse])
async def list_opportunities(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    service = CRMService(db)
    return await service.get_opportunities(tenant_id)
