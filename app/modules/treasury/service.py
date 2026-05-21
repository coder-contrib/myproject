from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.treasury.models import Treasury, Payment, Expense


class TreasuryService:
    def __init__(self, db: AsyncSession):
        self.treasury_repo = BaseRepository(Treasury, db)
        self.payment_repo = BaseRepository(Payment, db)
        self.expense_repo = BaseRepository(Expense, db)
        self.db = db

    async def create_treasury(self, tenant_id: UUID, **kwargs) -> Treasury:
        return await self.treasury_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_treasuries(self, tenant_id: UUID) -> list:
        return await self.treasury_repo.get_all(tenant_id=tenant_id)

    async def create_payment(self, tenant_id: UUID, **kwargs) -> Payment:
        return await self.payment_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_payments(self, tenant_id: UUID) -> list:
        return await self.payment_repo.get_all(tenant_id=tenant_id)

    async def create_expense(self, tenant_id: UUID, **kwargs) -> Expense:
        return await self.expense_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_expenses(self, tenant_id: UUID) -> list:
        return await self.expense_repo.get_all(tenant_id=tenant_id)
