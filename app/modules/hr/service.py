from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant.context import TenantContext
from app.core.tenant.isolation import TenantIsolatedRepository
from app.core.exceptions.handlers import AppException
from app.modules.hr.models import Department, Employee, Attendance, Leave, Payroll


class HRService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx
        self.departments = TenantIsolatedRepository(Department, db, ctx)
        self.employees = TenantIsolatedRepository(Employee, db, ctx)
        self.payrolls = TenantIsolatedRepository(Payroll, db, ctx)

    # --- Departments ---

    async def create_department(self, **kwargs) -> Department:
        return await self.departments.create(**kwargs)

    async def get_departments(self) -> list:
        return await self.departments.get_all(limit=200)

    async def update_department(self, dept_id: UUID, **kwargs) -> Department:
        dept = await self.departments.get_by_id_strict(dept_id)
        for key, value in kwargs.items():
            setattr(dept, key, value)
        await self.db.flush()
        await self.db.refresh(dept)
        return dept

    # --- Employees ---

    async def create_employee(self, **kwargs) -> Employee:
        return await self.employees.create(**kwargs)

    async def get_employees(self, skip: int = 0, limit: int = 50, department_id: UUID | None = None) -> list:
        filters = {}
        if department_id:
            filters["department_id"] = department_id
        return await self.employees.get_all(skip=skip, limit=limit, **filters)

    async def get_employee(self, employee_id: UUID) -> Employee:
        return await self.employees.get_by_id_strict(employee_id)

    async def update_employee(self, employee_id: UUID, **kwargs) -> Employee:
        emp = await self.employees.get_by_id_strict(employee_id)
        for key, value in kwargs.items():
            setattr(emp, key, value)
        await self.db.flush()
        await self.db.refresh(emp)
        return emp

    # --- Attendance ---

    async def record_attendance(self, employee_id: UUID, date, check_in=None, check_out=None) -> Attendance:
        await self.employees.get_by_id_strict(employee_id)
        attendance = Attendance(
            employee_id=employee_id,
            date=date,
            check_in=check_in,
            check_out=check_out,
        )
        self.db.add(attendance)
        await self.db.flush()
        await self.db.refresh(attendance)
        return attendance

    async def get_attendance(self, employee_id: UUID | None = None, skip: int = 0, limit: int = 50) -> list:
        from sqlalchemy import select
        query = select(Attendance).offset(skip).limit(limit)
        if employee_id:
            query = query.where(Attendance.employee_id == employee_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # --- Leave Management ---

    async def create_leave(self, employee_id: UUID, leave_type: str, start_date, end_date) -> Leave:
        await self.employees.get_by_id_strict(employee_id)
        leave = Leave(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            status="pending",
        )
        self.db.add(leave)
        await self.db.flush()
        await self.db.refresh(leave)
        return leave

    async def get_leaves(self, employee_id: UUID | None = None, status: str | None = None, skip: int = 0, limit: int = 50) -> list:
        from sqlalchemy import select
        query = select(Leave).offset(skip).limit(limit)
        if employee_id:
            query = query.where(Leave.employee_id == employee_id)
        if status:
            query = query.where(Leave.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def approve_leave(self, leave_id: UUID) -> Leave:
        from sqlalchemy import select
        result = await self.db.execute(select(Leave).where(Leave.id == leave_id))
        leave = result.scalar_one_or_none()
        if not leave:
            raise AppException("Leave not found", status_code=404)
        if leave.status != "pending":
            raise AppException(f"Cannot approve leave with status '{leave.status}'", status_code=400)
        leave.status = "approved"
        leave.approved_by = self.ctx.user_id
        leave.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(leave)
        return leave

    async def reject_leave(self, leave_id: UUID, reason: str | None = None) -> Leave:
        from sqlalchemy import select
        result = await self.db.execute(select(Leave).where(Leave.id == leave_id))
        leave = result.scalar_one_or_none()
        if not leave:
            raise AppException("Leave not found", status_code=404)
        if leave.status != "pending":
            raise AppException(f"Cannot reject leave with status '{leave.status}'", status_code=400)
        leave.status = "rejected"
        leave.approved_by = self.ctx.user_id
        leave.rejection_reason = reason
        await self.db.flush()
        await self.db.refresh(leave)
        return leave

    # --- Payroll ---

    async def create_payroll(self, employee_id: UUID, period_start, period_end, base_salary: float, deductions: float = 0, bonuses: float = 0) -> Payroll:
        await self.employees.get_by_id_strict(employee_id)
        net_salary = base_salary - deductions + bonuses
        return await self.payrolls.create(
            employee_id=employee_id,
            period_start=period_start,
            period_end=period_end,
            base_salary=base_salary,
            deductions=deductions,
            bonuses=bonuses,
            net_salary=round(net_salary, 2),
            status="draft",
        )

    async def get_payrolls(self, employee_id: UUID | None = None, status: str | None = None, skip: int = 0, limit: int = 50) -> list:
        filters = {}
        if employee_id:
            filters["employee_id"] = employee_id
        if status:
            filters["status"] = status
        return await self.payrolls.get_all(skip=skip, limit=limit, **filters)

    async def update_payroll_status(self, payroll_id: UUID, status: str) -> Payroll:
        payroll = await self.payrolls.get_by_id_strict(payroll_id)

        valid_transitions = {
            "draft": ["approved", "cancelled"],
            "approved": ["paid", "cancelled"],
        }
        allowed = valid_transitions.get(payroll.status, [])
        if status not in allowed:
            raise AppException(
                f"Cannot transition payroll from '{payroll.status}' to '{status}'. Allowed: {allowed}",
                status_code=400,
            )
        payroll.status = status
        await self.db.flush()
        await self.db.refresh(payroll)
        return payroll
