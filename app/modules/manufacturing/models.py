import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import BaseModel, TenantMixin


class BillOfMaterials(BaseModel, TenantMixin):
    __tablename__ = "bill_of_materials"
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    material_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class ProductionOrder(BaseModel, TenantMixin):
    __tablename__ = "production_orders"
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    planned_start_date: Mapped[datetime | None] = mapped_column(Date)
    planned_end_date: Mapped[datetime | None] = mapped_column(Date)
    actual_start_date: Mapped[datetime | None] = mapped_column(Date)
    actual_end_date: Mapped[datetime | None] = mapped_column(Date)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
