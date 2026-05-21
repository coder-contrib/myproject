from uuid import UUID
from datetime import datetime, date, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant.context import TenantContext
from app.core.tenant.isolation import TenantIsolatedRepository
from app.core.exceptions.handlers import AppException, NotFoundException
from app.modules.sales.models import (
    Quotation, QuotationItem, SalesInvoice, SalesItem,
    SalesPayment, SalesReturn, SalesReturnItem,
)


class SalesService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx
        self.quotations = TenantIsolatedRepository(Quotation, db, ctx)
        self.invoices = TenantIsolatedRepository(SalesInvoice, db, ctx)
        self.payments = TenantIsolatedRepository(SalesPayment, db, ctx)
        self.returns = TenantIsolatedRepository(SalesReturn, db, ctx)

    async def create_quotation(self, items: list[dict], **kwargs) -> Quotation:
        number = await self._generate_number("QTN", Quotation)
        quotation = await self.quotations.create(quotation_number=number, **kwargs)
        subtotal, tax_total = 0, 0
        for item_data in items:
            line_total = self._calc_line_total(item_data)
            tax = line_total * item_data.get("tax_percent", 0) / 100
            self.db.add(QuotationItem(
                quotation_id=quotation.id, product_id=item_data["product_id"],
                description=item_data.get("description"), quantity=item_data["quantity"],
                unit_price=item_data["unit_price"], discount_percent=item_data.get("discount_percent", 0),
                tax_percent=item_data.get("tax_percent", 0), total=line_total + tax,
            ))
            subtotal += line_total
            tax_total += tax
        quotation.subtotal = subtotal
        quotation.tax_amount = tax_total
        quotation.total = subtotal + tax_total - (quotation.discount_amount or 0)
        await self.db.flush()
        await self.db.refresh(quotation)
        return quotation

    async def get_quotations(self, status: str | None = None, skip: int = 0, limit: int = 50) -> list:
        filters = {"status": status} if status else {}
        return await self.quotations.get_all(skip=skip, limit=limit, **filters)

    async def get_quotation(self, quotation_id: UUID) -> Quotation:
        return await self.quotations.get_by_id_strict(quotation_id)

    async def update_quotation_status(self, quotation_id: UUID, status: str) -> Quotation:
        quotation = await self.quotations.get_by_id_strict(quotation_id)
        valid = {"draft": ["sent", "cancelled"], "sent": ["accepted", "rejected", "expired"]}
        if status not in valid.get(quotation.status, []):
            raise AppException(f"Cannot transition from '{quotation.status}' to '{status}'", status_code=400)
        return await self.quotations.update_strict(quotation_id, status=status)

    async def convert_quotation_to_invoice(self, quotation_id: UUID, warehouse_id: UUID | None = None) -> SalesInvoice:
        quotation = await self.quotations.get_by_id_strict(quotation_id)
        if quotation.status != "accepted":
            raise AppException("Only accepted quotations can be converted", status_code=400)
        if quotation.converted_to_invoice_id:
            raise AppException("Quotation already converted", status_code=400)
        items = [{"product_id": i.product_id, "description": i.description, "quantity": i.quantity,
                  "unit_price": i.unit_price, "discount_percent": i.discount_percent, "tax_percent": i.tax_percent}
                 for i in quotation.items]
        invoice = await self.create_invoice(items=items, customer_id=quotation.customer_id, quotation_id=quotation.id, warehouse_id=warehouse_id)
        quotation.converted_to_invoice_id = invoice.id
        quotation.status = "converted"
        await self.db.flush()
        return invoice

    async def create_invoice(self, items: list[dict], **kwargs) -> SalesInvoice:
        number = await self._generate_number("INV", SalesInvoice)
        kwargs.setdefault("issue_date", date.today())
        invoice = await self.invoices.create(invoice_number=number, **kwargs)
        subtotal, tax_total = 0, 0
        for item_data in items:
            line_total = self._calc_line_total(item_data)
            tax = line_total * item_data.get("tax_percent", 0) / 100
            self.db.add(SalesItem(
                invoice_id=invoice.id, product_id=item_data["product_id"],
                description=item_data.get("description"), quantity=item_data["quantity"],
                unit_price=item_data["unit_price"], discount_percent=item_data.get("discount_percent", 0),
                tax_percent=item_data.get("tax_percent", 0), tax_amount=tax,
                total=line_total + tax, cost_price=item_data.get("cost_price", 0),
            ))
            subtotal += line_total
            tax_total += tax
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_total
        invoice.discount_amount = kwargs.get("discount_amount", 0)
        invoice.total = subtotal + tax_total - invoice.discount_amount
        invoice.balance_due = invoice.total
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def get_invoices(self, status: str | None = None, customer_id: UUID | None = None, skip: int = 0, limit: int = 50) -> list:
        filters = {}
        if status: filters["status"] = status
        if customer_id: filters["customer_id"] = customer_id
        return await self.invoices.get_all(skip=skip, limit=limit, **filters)

    async def get_invoice(self, invoice_id: UUID) -> SalesInvoice:
        return await self.invoices.get_by_id_strict(invoice_id)

    async def update_invoice_status(self, invoice_id: UUID, status: str) -> SalesInvoice:
        invoice = await self.invoices.get_by_id_strict(invoice_id)
        valid = {"draft": ["confirmed", "cancelled"], "confirmed": ["delivered", "cancelled"], "delivered": ["paid", "partial", "overdue"], "partial": ["paid", "overdue"]}
        if status not in valid.get(invoice.status, []):
            raise AppException(f"Cannot transition from '{invoice.status}' to '{status}'", status_code=400)
        return await self.invoices.update_strict(invoice_id, status=status)

    async def record_payment(self, invoice_id: UUID, amount: float, payment_method: str, payment_date: date | None = None, reference: str | None = None) -> SalesPayment:
        invoice = await self.invoices.get_by_id_strict(invoice_id)
        if invoice.status in ("cancelled", "draft"):
            raise AppException("Cannot record payment on this invoice", status_code=400)
        if amount <= 0:
            raise AppException("Payment amount must be positive", status_code=400)
        if amount > invoice.balance_due:
            raise AppException(f"Payment exceeds balance due ({invoice.balance_due})", status_code=400)
        payment = await self.payments.create(invoice_id=invoice_id, amount=amount, payment_method=payment_method, payment_date=payment_date or date.today(), reference=reference)
        invoice.amount_paid += amount
        invoice.balance_due = invoice.total - invoice.amount_paid
        if invoice.balance_due <= 0: invoice.status = "paid"
        elif invoice.amount_paid > 0: invoice.status = "partial"
        await self.db.flush()
        return payment

    async def create_return(self, invoice_id: UUID, items: list[dict], reason: str | None = None, restock: bool = True) -> SalesReturn:
        invoice = await self.invoices.get_by_id_strict(invoice_id)
        number = await self._generate_number("RET", SalesReturn)
        subtotal, tax_total = 0, 0
        return_items = []
        for item_data in items:
            line_total = item_data["quantity"] * item_data["unit_price"]
            tax = line_total * item_data.get("tax_percent", 0) / 100
            return_items.append(SalesReturnItem(product_id=item_data["product_id"], quantity=item_data["quantity"], unit_price=item_data["unit_price"], tax_percent=item_data.get("tax_percent", 0), total=line_total + tax))
            subtotal += line_total
            tax_total += tax
        sales_return = await self.returns.create(return_number=number, invoice_id=invoice_id, customer_id=invoice.customer_id, return_date=date.today(), subtotal=subtotal, tax_amount=tax_total, total=subtotal + tax_total, reason=reason, restock=restock)
        for item in return_items:
            item.return_id = sales_return.id
            self.db.add(item)
        await self.db.flush()
        await self.db.refresh(sales_return)
        return sales_return

    async def get_returns(self, skip: int = 0, limit: int = 50) -> list:
        return await self.returns.get_all(skip=skip, limit=limit)

    def _calc_line_total(self, item: dict) -> float:
        return item["quantity"] * item["unit_price"] * (1 - item.get("discount_percent", 0) / 100)

    async def _generate_number(self, prefix: str, model) -> str:
        result = await self.db.execute(select(func.count(model.id)).where(model.tenant_id == self.ctx.tenant_id))
        return f"{prefix}-{(result.scalar() or 0) + 1:06d}"
