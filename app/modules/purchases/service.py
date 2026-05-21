from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.purchases.models import PurchaseInvoice, PurchaseItem, PurchaseOrder, DebitNote


class PurchaseService:
    def __init__(self, db: AsyncSession):
        self.invoice_repo = BaseRepository(PurchaseInvoice, db)
        self.item_repo = BaseRepository(PurchaseItem, db)
        self.order_repo = BaseRepository(PurchaseOrder, db)
        self.debit_note_repo = BaseRepository(DebitNote, db)
        self.db = db

    async def create_invoice(self, tenant_id: UUID, **kwargs) -> PurchaseInvoice:
        return await self.invoice_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_invoices(self, tenant_id: UUID) -> list:
        return await self.invoice_repo.get_all(tenant_id=tenant_id)

    async def get_invoice(self, invoice_id: UUID) -> PurchaseInvoice | None:
        return await self.invoice_repo.get_by_id(invoice_id)

    async def create_order(self, tenant_id: UUID, **kwargs) -> PurchaseOrder:
        return await self.order_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_orders(self, tenant_id: UUID) -> list:
        return await self.order_repo.get_all(tenant_id=tenant_id)

    async def create_debit_note(self, tenant_id: UUID, **kwargs) -> DebitNote:
        return await self.debit_note_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_debit_notes(self, tenant_id: UUID) -> list:
        return await self.debit_note_repo.get_all(tenant_id=tenant_id)
