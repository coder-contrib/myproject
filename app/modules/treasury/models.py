import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import BaseModel, TenantMixin


class Treasury(BaseModel, TenantMixin):
    __tablename__ = "treasury"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class Payment(BaseModel, TenantMixin):
    __tablename__ = "payments"
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    sales_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    purchase_invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    treasury_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treasury.id"), nullable=False)
    currency_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class Expense(BaseModel, TenantMixin):
    __tablename__ = "expenses"
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"))
    treasury_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treasury.id"), nullable=False)
    currency_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))


class Cheque(BaseModel):
    __tablename__ = "cheques"
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    cheque_number: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(100))
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
