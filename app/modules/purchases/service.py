from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant.context import TenantContext
from app.core.tenant.isolation import TenantIsolatedRepository
from app.core.exceptions.handlers import AppException
from app.modules.purchases.models import (
    PurchaseOrder, PurchaseOrderItem, PurchaseInvoice, PurchaseInvoiceItem,
    PurchaseReturn, PurchaseReturnItem,
)


class PurchaseService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx
        self.orders = TenantIsolatedRepository(PurchaseOrder, db, ctx)
        self.invoices = TenantIsolatedRepository(PurchaseInvoice, db, ctx)
        self.returns = TenantIsolatedRepository(PurchaseReturn, db, ctx)

    # --- Purchase Orders ---

    async def create_order(self, supplier_id: UUID, order_date, items: list[dict], **kwargs) -> PurchaseOrder:
        order_number = await self._generate_number("PO", PurchaseOrder, "order_number")

        subtotal = 0.0
        tax_amount = 0.0
        order_items = []

        for item in items:
            line_total = item["quantity"] * item["unit_price"]
            line_tax = line_total * item.get("tax_percent", 0) / 100
            subtotal += line_total
            tax_amount += line_tax
            order_items.append({**item, "total": line_total + line_tax})

        order = await self.orders.create(
            order_number=order_number,
            supplier_id=supplier_id,
            order_date=order_date,
            subtotal=round(subtotal, 2),
            tax_amount=round(tax_amount, 2),
            total=round(subtotal + tax_amount, 2),
            created_by=self.ctx.user_id,
            **kwargs,
        )

        for item_data in order_items:
            oi = PurchaseOrderItem(order_id=order.id, **item_data)
            self.db.add(oi)

        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_orders(self, skip: int = 0, limit: int = 50, status: str | None = None) -> list:
        filters = {}
        if status:
            filters["status"] = status
        return await self.orders.get_all(skip=skip, limit=limit, **filters)

    async def get_order(self, order_id: UUID) -> PurchaseOrder:
        return await self.orders.get_by_id_strict(order_id)

    async def update_order_status(self, order_id: UUID, status: str) -> PurchaseOrder:
        order = await self.orders.get_by_id_strict(order_id)

        valid_transitions = {
            "draft": ["confirmed", "cancelled"],
            "confirmed": ["sent", "cancelled"],
            "sent": ["partial", "received", "cancelled"],
            "partial": ["received"],
        }

        allowed = valid_transitions.get(order.status, [])
        if status not in allowed:
            raise AppException(
                f"Cannot transition from '{order.status}' to '{status}'. Allowed: {allowed}",
                status_code=400,
            )

        order.status = status
        order.updated_by = self.ctx.user_id
        await self.db.flush()
        await self.db.refresh(order)
        return order

    # --- Purchase Invoices ---

    async def create_invoice(self, supplier_id: UUID, issue_date, items: list[dict], **kwargs) -> PurchaseInvoice:
        invoice_number = await self._generate_number("PINV", PurchaseInvoice, "invoice_number")

        subtotal = 0.0
        tax_amount = 0.0
        invoice_items = []

        for item in items:
            line_total = item["quantity"] * item["unit_price"]
            line_tax = line_total * item.get("tax_percent", 0) / 100
            subtotal += line_total
            tax_amount += line_tax
            invoice_items.append({**item, "tax_amount": round(line_tax, 2), "total": round(line_total + line_tax, 2)})

        total = round(subtotal + tax_amount, 2)

        invoice = await self.invoices.create(
            invoice_number=invoice_number,
            supplier_id=supplier_id,
            issue_date=issue_date,
            subtotal=round(subtotal, 2),
            tax_amount=round(tax_amount, 2),
            total=total,
            balance_due=total,
            created_by=self.ctx.user_id,
            **kwargs,
        )

        for item_data in invoice_items:
            ii = PurchaseInvoiceItem(invoice_id=invoice.id, **item_data)
            self.db.add(ii)

        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def get_invoices(self, skip: int = 0, limit: int = 50, status: str | None = None) -> list:
        filters = {}
        if status:
            filters["status"] = status
        return await self.invoices.get_all(skip=skip, limit=limit, **filters)

    async def get_invoice(self, invoice_id: UUID) -> PurchaseInvoice:
        return await self.invoices.get_by_id_strict(invoice_id)

    async def record_payment(self, invoice_id: UUID, amount: float, payment_method: str, payment_date, **kwargs) -> PurchaseInvoice:
        invoice = await self.invoices.get_by_id_strict(invoice_id)

        if invoice.status in ("paid", "cancelled"):
            raise AppException(f"Cannot pay invoice with status '{invoice.status}'", status_code=400)

        if amount > invoice.balance_due:
            raise AppException(
                f"Payment amount {amount} exceeds balance due {invoice.balance_due}",
                status_code=400,
            )

        invoice.amount_paid = round(invoice.amount_paid + amount, 2)
        invoice.balance_due = round(invoice.total - invoice.amount_paid, 2)

        if invoice.balance_due <= 0:
            invoice.status = "paid"
        else:
            invoice.status = "partial"

        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    # --- Purchase Returns ---

    async def create_return(self, invoice_id: UUID, supplier_id: UUID, return_date, items: list[dict], **kwargs) -> PurchaseReturn:
        await self.invoices.get_by_id_strict(invoice_id)
        return_number = await self._generate_number("PRET", PurchaseReturn, "return_number")

        total = 0.0
        return_items = []
        for item in items:
            line_total = round(item["quantity"] * item["unit_price"], 2)
            total += line_total
            return_items.append({**item, "total": line_total})

        purchase_return = await self.returns.create(
            return_number=return_number,
            invoice_id=invoice_id,
            supplier_id=supplier_id,
            return_date=return_date,
            total=round(total, 2),
            created_by=self.ctx.user_id,
            **kwargs,
        )

        for item_data in return_items:
            ri = PurchaseReturnItem(return_id=purchase_return.id, **item_data)
            self.db.add(ri)

        await self.db.flush()
        await self.db.refresh(purchase_return)
        return purchase_return

    async def get_returns(self, skip: int = 0, limit: int = 50) -> list:
        return await self.returns.get_all(skip=skip, limit=limit)

    async def get_return(self, return_id: UUID) -> PurchaseReturn:
        return await self.returns.get_by_id_strict(return_id)

    # --- Helpers ---

    async def _generate_number(self, prefix: str, model, field: str) -> str:
        result = await self.db.execute(
            select(func.count(model.id)).where(model.tenant_id == self.ctx.tenant_id)
        )
        count = (result.scalar() or 0) + 1
        return f"{prefix}-{count:06d}"
