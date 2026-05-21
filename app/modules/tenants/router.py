from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, get_current_tenant_id
from app.modules.tenants.schemas import (
    TenantCreate, TenantResponse,
    CompanyCreate, CompanyResponse,
    BranchCreate, BranchResponse,
)
from app.modules.tenants.service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/", response_model=TenantResponse)
async def create_tenant(data: TenantCreate, db: AsyncSession = Depends(get_db)):
    service = TenantService(db)
    return await service.create_tenant(name=data.name)


@router.get("/me", response_model=TenantResponse)
async def get_my_tenant(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = TenantService(db)
    return await service.get_tenant(tenant_id)


@router.post("/companies", response_model=CompanyResponse)
async def create_company(
    data: CompanyCreate,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = TenantService(db)
    return await service.create_company(tenant_id=tenant_id, **data.model_dump())


@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = TenantService(db)
    return await service.get_companies(tenant_id)


@router.post("/branches", response_model=BranchResponse)
async def create_branch(
    data: BranchCreate,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = TenantService(db)
    return await service.create_branch(tenant_id=tenant_id, **data.model_dump())


@router.get("/branches", response_model=list[BranchResponse])
async def list_branches(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    service = TenantService(db)
    return await service.get_branches(tenant_id)
