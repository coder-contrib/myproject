import uuid
from datetime import datetime, date
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Text, Date, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin, VersionMixin, CompanyMixin


class Account(BaseModel, TimestampMixin, TenantMixin, CompanyMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "accounts"

    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    account_code: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    parent: Mapped["Account | None"] = relationship(remote_side="Account.id", lazy="selectin")

    __table_args__ = (
        Index("ix_accounts_tenant_code", "tenant_id", "account_code", unique=True),
    )


class FiscalYear(BaseModel, TimestampMixin, TenantMixin, CompanyMixin):
    __tablename__ = "fiscal_years"

    year_name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class CostCenter(BaseModel, TimestampMixin, TenantMixin, CompanyMixin):
    __tablename__ = "cost_centers"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index("ix_cost_centers_tenant_code", "tenant_id", "code", unique=True),
    )


class JournalEntry(BaseModel, TimestampMixin, TenantMixin, CompanyMixin):
    __tablename__ = "journal_entries"

    entry_number: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("fiscal_years.id"))
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"))
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    description: Mapped[str | None] = mapped_column(Text)
    total_debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    total_credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime)

    lines: Mapped[list["JournalEntryLine"]] = relationship(back_populates="journal_entry", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_journal_entries_tenant_number", "tenant_id", "entry_number", unique=True),
        Index("ix_journal_entries_reference", "reference_type", "reference_id"),
    )


class JournalEntryLine(BaseModel):
    __tablename__ = "journal_entry_lines"

    journal_entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    debit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    description: Mapped[str | None] = mapped_column(String(255))
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cost_centers.id"))

    journal_entry: Mapped["JournalEntry"] = relationship(back_populates="lines")
    account: Mapped["Account"] = relationship(lazy="selectin")
