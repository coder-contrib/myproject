from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.core.exceptions.handlers import ValidationException
from app.modules.accounting.models import Account, JournalEntry, JournalEntryLine, FiscalYear, CostCenter


class AccountingService:
    def __init__(self, db: AsyncSession):
        self.account_repo = BaseRepository(Account, db)
        self.journal_repo = BaseRepository(JournalEntry, db)
        self.line_repo = BaseRepository(JournalEntryLine, db)
        self.fiscal_repo = BaseRepository(FiscalYear, db)
        self.db = db

    async def create_account(self, tenant_id: UUID, **kwargs) -> Account:
        return await self.account_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_accounts(self, tenant_id: UUID) -> list:
        return await self.account_repo.get_all(tenant_id=tenant_id)

    async def create_journal_entry(self, tenant_id: UUID, description: str, lines: list, **kwargs) -> JournalEntry:
        total_debit = sum(l.get("debit", 0) if isinstance(l, dict) else l.debit for l in lines)
        total_credit = sum(l.get("credit", 0) if isinstance(l, dict) else l.credit for l in lines)
        if abs(total_debit - total_credit) > 0.01:
            raise ValidationException("Journal entry must balance: total debits must equal total credits")

        entry = await self.journal_repo.create(tenant_id=tenant_id, description=description, **kwargs)
        now = datetime.utcnow()
        for line in lines:
            line_data = line if isinstance(line, dict) else line.model_dump()
            await self.line_repo.create(
                journal_entry_id=entry.id,
                journal_entry_created_at=now,
                **line_data,
            )
        return entry

    async def get_journal_entries(self, tenant_id: UUID) -> list:
        return await self.journal_repo.get_all(tenant_id=tenant_id)

    async def create_fiscal_year(self, **kwargs) -> FiscalYear:
        return await self.fiscal_repo.create(**kwargs)

    async def get_fiscal_years(self, company_id: UUID) -> list:
        return await self.fiscal_repo.get_all()
