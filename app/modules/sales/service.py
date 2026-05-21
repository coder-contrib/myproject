from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.sales.models import SalesInvoice, SalesItem, Quotation, CreditNote


class SalesService:
    def __init__(self, db: AsyncSession):
        self.invoice_repo = BaseRepository(SalesInvoice, db)
        self.item_repo = BaseRepository(SalesItem, db)
        self.quotation_repo = BaseRepository(Quotation, db)
        self.credit_note_repo = BaseRepository(CreditNote, db)
        self.db = db

    async def create_invoice(self, tenant_id: UUID, **kwargs) -> SalesInvoice:
        return await self.invoice_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_invoices(self, tenant_id: UUID) -> list:
        return await self.invoice_repo.get_all(tenant_id=tenant_id)

    async def get_invoice(self, invoice_id: UUID) -> SalesInvoice | None:
        return await self.invoice_repo.get_by_id(invoice_id)

    async def add_item(self, invoice_id: UUID, **kwargs) -> SalesItem:
        tax_amount = kwargs.get("quantity", 0) * kwargs.get("unit_price", 0) * kwargs.get("tax_percent", 0) / 100
        total = kwargs.get("quantity", 0) * kwargs.get("unit_price", 0) - kwargs.get("discount", 0) + tax_amount
        return await self.item_repo.create(invoice_id=invoice_id, tax_amount=tax_amount, total=total, **kwargs)

    async def create_quotation(self, tenant_id: UUID, **kwargs) -> Quotation:
        return await self.quotation_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_quotations(self, tenant_id: UUID) -> list:
        return await self.quotation_repo.get_all(tenant_id=tenant_id)

    async def create_credit_note(self, tenant_id: UUID, **kwargs) -> CreditNote:
        return await self.credit_note_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_credit_notes(self, tenant_id: UUID) -> list:
        return await self.credit_note_repo.get_all(tenant_id=tenant_id)
