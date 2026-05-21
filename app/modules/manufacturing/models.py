import uuid
from datetime import datetime, date
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Text, Date, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import BaseModel, TimestampMixin, TenantMixin


class BillOfMaterials(BaseModel, TimestampMixin, TenantMixin):
    __tablename__ = "bill_of_materials"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    items: Mapped[list["BOMItem"]] = relationship(back_populates="bom", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_bom_tenant_product", "tenant_id", "product_id"),
    )


class BOMItem(BaseModel):
    __tablename__ = "bom_items"

    bom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bill_of_materials.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="pcs")
    waste_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    bom: Mapped["BillOfMaterials"] = relationship(back_populates="items")


class ProductionOrder(BaseModel, TimestampMixin, TenantMixin):
    __tablename__ = "production_orders"

    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    bom_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bill_of_materials.id"))
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    produced_quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    planned_start_date: Mapped[date | None] = mapped_column(Date)
    planned_end_date: Mapped[date | None] = mapped_column(Date)
    actual_start_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    consumptions: Mapped[list["MaterialConsumption"]] = relationship(back_populates="production_order", lazy="selectin")

    __table_args__ = (
        Index("ix_production_orders_tenant_number", "tenant_id", "order_number", unique=True),
    )


class MaterialConsumption(BaseModel, TimestampMixin, TenantMixin):
    __tablename__ = "material_consumptions"

    production_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"))
    planned_quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    actual_quantity: Mapped[float] = mapped_column(Numeric(12, 4), default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    production_order: Mapped["ProductionOrder"] = relationship(back_populates="consumptions")
