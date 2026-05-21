import uuid
from datetime import datetime, date
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Text, Boolean, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import BaseModel, TimestampMixin, TenantMixin, CompanyMixin, BranchMixin, SoftDeleteMixin, VersionMixin


class PurchaseOrder(BaseModel, TimestampMixin, TenantMixin, CompanyMixin, BranchMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "purchase_orders"
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"))
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="order", lazy="selectin", cascade="all, delete-orphan")

class PurchaseOrderItem(BaseModel):
    __tablename__ = "purchase_order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    tax_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    received_quantity: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    order: Mapped["PurchaseOrder"] = relationship(back_populates="items")

class PurchaseInvoice(BaseModel, TimestampMixin, TenantMixin, CompanyMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "purchase_invoices"
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    amount_paid: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    balance_due: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    items: Mapped[list["PurchaseInvoiceItem"]] = relationship(back_populates="invoice", lazy="selectin", cascade="all, delete-orphan")

class PurchaseInvoiceItem(BaseModel):
    __tablename__ = "purchase_invoice_items"
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    tax_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    invoice: Mapped["PurchaseInvoice"] = relationship(back_populates="items")

class PurchaseReturn(BaseModel, TimestampMixin, TenantMixin, CompanyMixin):
    __tablename__ = "purchase_returns"
    return_number: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    return_date: Mapped[date] = mapped_column(Date, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    items: Mapped[list["PurchaseReturnItem"]] = relationship(back_populates="purchase_return", lazy="selectin", cascade="all, delete-orphan")

class PurchaseReturnItem(BaseModel):
    __tablename__ = "purchase_return_items"
    return_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_returns.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    purchase_return: Mapped["PurchaseReturn"] = relationship(back_populates="items")
