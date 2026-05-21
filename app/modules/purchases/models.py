import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin, VersionMixin


class PurchaseInvoice(BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "purchase_invoices"
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("branches.id"))
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class PurchaseItem(BaseModel):
    __tablename__ = "purchase_items"
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    tax_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)


class PurchaseOrder(BaseModel, TenantMixin):
    __tablename__ = "purchase_orders"
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class DebitNote(BaseModel, TenantMixin):
    __tablename__ = "debit_notes"
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    note_number: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    purchase_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"))
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
