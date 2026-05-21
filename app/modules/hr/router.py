from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_tenant_id
from app.modules.hr.schemas import *
from app.modules.hr.service import HRService

router = APIRouter(prefix="/hr", tags=["hr"])

@router.post("/departments", response_model=DepartmentResponse)
async def create_department(data: DepartmentCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await HRService(db).create_department(tenant_id=tenant_id, **data.model_dump())

@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await HRService(db).get_departments(tenant_id)

@router.post("/employees", response_model=EmployeeResponse)
async def create_employee(data: EmployeeCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await HRService(db).create_employee(tenant_id=tenant_id, **data.model_dump())

@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await HRService(db).get_employees(tenant_id)

@router.post("/leaves", response_model=LeaveResponse)
async def create_leave(data: LeaveCreate, db: AsyncSession = Depends(get_db)):
    return await HRService(db).create_leave(**data.model_dump())

@router.post("/payroll", response_model=PayrollResponse)
async def create_payroll(data: PayrollCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await HRService(db).create_payroll(tenant_id=tenant_id, **data.model_dump())

@router.get("/payroll", response_model=list[PayrollResponse])
async def list_payroll(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await HRService(db).get_payrolls(tenant_id)
