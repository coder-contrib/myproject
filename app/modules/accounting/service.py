from uuid import UUID
from datetime import datetime, date, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant.context import TenantContext
from app.core.tenant.isolation import TenantIsolatedRepository
from app.core.exceptions.handlers import AppException
from app.modules.accounting.models import (
    Account, JournalEntry, JournalEntryLine, FiscalYear, CostCenter,
)


class AccountingService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx
        self.accounts = TenantIsolatedRepository(Account, db, ctx)
        self.journals = TenantIsolatedRepository(JournalEntry, db, ctx)
        self.fiscal_years = TenantIsolatedRepository(FiscalYear, db, ctx)
        self.cost_centers = TenantIsolatedRepository(CostCenter, db, ctx)

    # --- Chart of Accounts ---

    async def create_account(self, **kwargs) -> Account:
        existing = await self.accounts.find_one(account_code=kwargs["account_code"])
        if existing:
            raise AppException("Account with this code already exists", status_code=409)
        return await self.accounts.create(created_by=self.ctx.user_id, **kwargs)

    async def get_accounts(self, account_type: str | None = None) -> list:
        filters = {}
        if account_type:
            filters["account_type"] = account_type
        return await self.accounts.get_all(limit=1000, **filters)

    async def get_account(self, account_id: UUID) -> Account:
        return await self.accounts.get_by_id_strict(account_id)

    async def update_account(self, account_id: UUID, **kwargs) -> Account:
        version = kwargs.pop("version", None)
        return await self.accounts.update_strict(account_id, expected_version=version, **kwargs)

    # --- Fiscal Years ---

    async def create_fiscal_year(self, **kwargs) -> FiscalYear:
        return await self.fiscal_years.create(**kwargs)

    async def get_fiscal_years(self) -> list:
        return await self.fiscal_years.get_all(limit=50)

    async def close_fiscal_year(self, fiscal_year_id: UUID) -> FiscalYear:
        fy = await self.fiscal_years.get_by_id_strict(fiscal_year_id)
        if fy.is_closed:
            raise AppException("Fiscal year is already closed", status_code=400)
        fy.is_closed = True
        fy.closed_at = datetime.now(timezone.utc)
        fy.closed_by = self.ctx.user_id
        await self.db.flush()
        await self.db.refresh(fy)
        return fy

    # --- Cost Centers ---

    async def create_cost_center(self, **kwargs) -> CostCenter:
        return await self.cost_centers.create(**kwargs)

    async def get_cost_centers(self) -> list:
        return await self.cost_centers.get_all(limit=500)

    # --- Journal Entries (Double-Entry Accounting) ---

    async def create_journal_entry(self, entry_date: date, lines: list[dict], **kwargs) -> JournalEntry:
        total_debit = sum(line.get("debit", 0) for line in lines)
        total_credit = sum(line.get("credit", 0) for line in lines)

        if abs(total_debit - total_credit) > 0.01:
            raise AppException(
                f"Journal entry must balance: debit ({total_debit}) != credit ({total_credit})",
                status_code=400,
            )

        if kwargs.get("fiscal_year_id"):
            fy = await self.fiscal_years.get_by_id_strict(kwargs["fiscal_year_id"])
            if fy.is_closed:
                raise AppException("Cannot post to a closed fiscal year", status_code=400)

        entry_number = await self._generate_number("JE", JournalEntry, "entry_number")

        entry = await self.journals.create(
            entry_number=entry_number,
            entry_date=entry_date,
            total_debit=round(total_debit, 2),
            total_credit=round(total_credit, 2),
            created_by=self.ctx.user_id,
            **kwargs,
        )

        for line_data in lines:
            jel = JournalEntryLine(journal_entry_id=entry.id, **line_data)
            self.db.add(jel)

        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def get_journal_entries(self, skip: int = 0, limit: int = 50, status: str | None = None) -> list:
        filters = {}
        if status:
            filters["status"] = status
        return await self.journals.get_all(skip=skip, limit=limit, **filters)

    async def get_journal_entry(self, entry_id: UUID) -> JournalEntry:
        return await self.journals.get_by_id_strict(entry_id)

    async def post_journal_entry(self, entry_id: UUID) -> JournalEntry:
        entry = await self.journals.get_by_id_strict(entry_id)
        if entry.status != "draft":
            raise AppException(f"Cannot post entry with status '{entry.status}'", status_code=400)

        for line in entry.lines:
            account = await self.accounts.get_by_id_strict(line.account_id)
            if account.account_type in ("asset", "expense"):
                account.balance += line.debit - line.credit
            else:
                account.balance += line.credit - line.debit

        entry.status = "posted"
        entry.posted_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def reverse_journal_entry(self, entry_id: UUID) -> JournalEntry:
        original = await self.journals.get_by_id_strict(entry_id)
        if original.status != "posted":
            raise AppException("Only posted entries can be reversed", status_code=400)
        if original.is_reversed:
            raise AppException("Entry has already been reversed", status_code=400)

        reversal_lines = []
        for line in original.lines:
            reversal_lines.append({
                "account_id": line.account_id,
                "debit": line.credit,
                "credit": line.debit,
                "description": f"Reversal of {original.entry_number}",
                "cost_center_id": line.cost_center_id,
            })

        reversal = await self.create_journal_entry(
            entry_date=date.today(),
            lines=reversal_lines,
            description=f"Reversal of {original.entry_number}",
            reference_type="reversal",
            reference_id=original.id,
        )

        await self.post_journal_entry(reversal.id)

        original.is_reversed = True
        original.reversed_by_id = reversal.id
        await self.db.flush()
        await self.db.refresh(original)
        return original

    # --- Ledger ---

    async def get_ledger(self, account_id: UUID, start_date: date | None = None, end_date: date | None = None) -> list[dict]:
        await self.accounts.get_by_id_strict(account_id)

        query = (
            select(JournalEntryLine, JournalEntry)
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(
                and_(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.tenant_id == self.ctx.tenant_id,
                    JournalEntry.status == "posted",
                )
            )
            .order_by(JournalEntry.entry_date)
        )

        if start_date:
            query = query.where(JournalEntry.entry_date >= start_date)
        if end_date:
            query = query.where(JournalEntry.entry_date <= end_date)

        result = await self.db.execute(query)
        rows = result.all()

        ledger = []
        running_balance = 0.0
        for line, entry in rows:
            running_balance += line.debit - line.credit
            ledger.append({
                "entry_date": entry.entry_date,
                "entry_number": entry.entry_number,
                "description": line.description or entry.description,
                "debit": line.debit,
                "credit": line.credit,
                "running_balance": round(running_balance, 2),
            })
        return ledger

    # --- Trial Balance ---

    async def get_trial_balance(self) -> list[dict]:
        accounts = await self.accounts.get_all(limit=10000, is_active=True)

        trial_balance = []
        for account in accounts:
            query = (
                select(
                    func.coalesce(func.sum(JournalEntryLine.debit), 0),
                    func.coalesce(func.sum(JournalEntryLine.credit), 0),
                )
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    and_(
                        JournalEntryLine.account_id == account.id,
                        JournalEntry.status == "posted",
                    )
                )
            )
            result = await self.db.execute(query)
            row = result.one()
            debit_total, credit_total = float(row[0]), float(row[1])

            if debit_total > 0 or credit_total > 0:
                trial_balance.append({
                    "account_id": account.id,
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "debit_total": debit_total,
                    "credit_total": credit_total,
                })
        return trial_balance

    # --- Helpers ---

    async def _generate_number(self, prefix: str, model, field: str) -> str:
        result = await self.db.execute(
            select(func.count(model.id)).where(model.tenant_id == self.ctx.tenant_id)
        )
        count = (result.scalar() or 0) + 1
        return f"{prefix}-{count:06d}"
