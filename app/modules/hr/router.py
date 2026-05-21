from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.tenant import TenantContext, get_tenant_context
from app.modules.hr.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    AttendanceCreate, AttendanceResponse,
    LeaveCreate, LeaveActionRequest, LeaveResponse,
    PayrollCreate, PayrollResponse, PayrollStatusUpdate,
)
from app.modules.hr.service import HRService

router = APIRouter(prefix="/hr", tags=["hr"])


def _svc(db: AsyncSession, ctx: TenantContext) -> HRService:
    return HRService(db, ctx)


# --- Departments ---

@router.post("/departments", response_model=DepartmentResponse)
async def create_department(data: DepartmentCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_department(**data.model_dump())


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_departments()


@router.patch("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(dept_id: UUID, data: DepartmentUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_department(dept_id, **data.model_dump(exclude_unset=True))


# --- Employees ---

@router.post("/employees", response_model=EmployeeResponse)
async def create_employee(data: EmployeeCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_employee(**data.model_dump())


@router.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(
    department_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_employees(skip=skip, limit=limit, department_id=department_id)


@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).get_employee(employee_id)


@router.patch("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: UUID, data: EmployeeUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_employee(employee_id, **data.model_dump(exclude_unset=True))


# --- Attendance ---

@router.post("/attendance", response_model=AttendanceResponse)
async def record_attendance(data: AttendanceCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).record_attendance(
        employee_id=data.employee_id,
        date=data.date,
        check_in=data.check_in,
        check_out=data.check_out,
    )


@router.get("/attendance", response_model=list[AttendanceResponse])
async def list_attendance(
    employee_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_attendance(employee_id=employee_id, skip=skip, limit=limit)


# --- Leave ---

@router.post("/leaves", response_model=LeaveResponse)
async def create_leave(data: LeaveCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_leave(
        employee_id=data.employee_id,
        leave_type=data.leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
    )


@router.get("/leaves", response_model=list[LeaveResponse])
async def list_leaves(
    employee_id: UUID | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_leaves(employee_id=employee_id, status=status, skip=skip, limit=limit)


@router.post("/leaves/{leave_id}/approve", response_model=LeaveResponse)
async def approve_leave(leave_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).approve_leave(leave_id)


@router.post("/leaves/{leave_id}/reject", response_model=LeaveResponse)
async def reject_leave(leave_id: UUID, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).reject_leave(leave_id)


# --- Payroll ---

@router.post("/payroll", response_model=PayrollResponse)
async def create_payroll(data: PayrollCreate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).create_payroll(
        employee_id=data.employee_id,
        period_start=data.period_start,
        period_end=data.period_end,
        base_salary=data.base_salary,
        deductions=data.deductions,
        bonuses=data.bonuses,
    )


@router.get("/payroll", response_model=list[PayrollResponse])
async def list_payroll(
    employee_id: UUID | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db, ctx).get_payrolls(employee_id=employee_id, status=status, skip=skip, limit=limit)


@router.patch("/payroll/{payroll_id}/status", response_model=PayrollResponse)
async def update_payroll_status(payroll_id: UUID, data: PayrollStatusUpdate, ctx: TenantContext = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    return await _svc(db, ctx).update_payroll_status(payroll_id, data.status)
