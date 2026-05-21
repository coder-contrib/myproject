from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.hr.models import Department, Employee, Leave, Payroll, Attendance


class HRService:
    def __init__(self, db: AsyncSession):
        self.dept_repo = BaseRepository(Department, db)
        self.emp_repo = BaseRepository(Employee, db)
        self.leave_repo = BaseRepository(Leave, db)
        self.payroll_repo = BaseRepository(Payroll, db)
        self.db = db

    async def create_department(self, tenant_id: UUID, **kwargs) -> Department:
        return await self.dept_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_departments(self, tenant_id: UUID) -> list:
        return await self.dept_repo.get_all(tenant_id=tenant_id)

    async def create_employee(self, tenant_id: UUID, **kwargs) -> Employee:
        return await self.emp_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_employees(self, tenant_id: UUID) -> list:
        return await self.emp_repo.get_all(tenant_id=tenant_id)

    async def create_leave(self, **kwargs) -> Leave:
        return await self.leave_repo.create(**kwargs)

    async def get_leaves(self, tenant_id: UUID) -> list:
        return await self.leave_repo.get_all()

    async def create_payroll(self, tenant_id: UUID, **kwargs) -> Payroll:
        net = kwargs.get("base_salary", 0) - kwargs.get("deductions", 0) + kwargs.get("bonuses", 0)
        return await self.payroll_repo.create(tenant_id=tenant_id, net_salary=net, **kwargs)

    async def get_payrolls(self, tenant_id: UUID) -> list:
        return await self.payroll_repo.get_all(tenant_id=tenant_id)
