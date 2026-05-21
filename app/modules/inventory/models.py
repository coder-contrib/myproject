import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Integer, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import BaseModel, TimestampMixin, TenantMixin, SoftDeleteMixin, VersionMixin, CompanyMixin, BranchMixin


class ProductCategory(BaseModel, TimestampMixin, TenantMixin):
    __tablename__ = "product_categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent: Mapped["ProductCategory | None"] = relationship(remote_side="ProductCategory.id", lazy="selectin")


class Product(BaseModel, TimestampMixin, TenantMixin, CompanyMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(50), index=True)
    barcode: Mapped[str | None] = mapped_column(String(100), index=True)
    barcode_type: Mapped[str | None] = mapped_column(String(20))
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
    unit: Mapped[str] = mapped_column(String(20), default="pcs")
    description: Mapped[str | None] = mapped_column(Text)
    sale_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    purchase_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    average_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0)
    max_stock_level: Mapped[int] = mapped_column(Integer, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=10)
    is_batch_tracked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False)
    weight: Mapped[float | None] = mapped_column(Numeric(10, 3))
    dimensions: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    category: Mapped["ProductCategory | None"] = relationship(lazy="selectin")

    __table_args__ = (
        Index("ix_products_tenant_sku", "tenant_id", "sku", unique=True),
        Index("ix_products_tenant_barcode", "tenant_id", "barcode", unique=True),
    )


class Warehouse(BaseModel, TimestampMixin, TenantMixin, CompanyMixin, BranchMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "warehouses"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    capacity: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class Inventory(BaseModel, TenantMixin):
    __tablename__ = "inventory"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    damaged_quantity: Mapped[int] = mapped_column(Integer, default=0)
    in_transit_quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product: Mapped["Product"] = relationship(lazy="selectin")
    warehouse: Mapped["Warehouse"] = relationship(lazy="selectin")

    __table_args__ = (
        Index("ix_inventory_product_warehouse", "product_id", "warehouse_id", unique=True),
    )

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity - self.damaged_quantity


class Batch(BaseModel, TimestampMixin, TenantMixin):
    __tablename__ = "batches"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    lot_number: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    manufacturing_date: Mapped[datetime | None] = mapped_column(DateTime)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    purchase_price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(20), default="active")
    notes: Mapped[str | None] = mapped_column(Text)

    product: Mapped["Product"] = relationship(lazy="selectin")

    __table_args__ = (
        Index("ix_batches_tenant_batch_number", "tenant_id", "batch_number"),
    )


class InventoryMovement(BaseModel, TenantMixin):
    __tablename__ = "inventory_movements"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    from_warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"))
    to_warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"))
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("batches.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    unit_cost: Mapped[float | None] = mapped_column(Numeric(14, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    product: Mapped["Product"] = relationship(lazy="selectin")
    batch: Mapped["Batch | None"] = relationship(lazy="selectin")

    __table_args__ = (
        Index("ix_movements_product_date", "product_id", "created_at"),
        Index("ix_movements_reference", "reference_type", "reference_id"),
    )


class StockTransfer(BaseModel, TimestampMixin, TenantMixin):
    __tablename__ = "stock_transfers"

    transfer_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    from_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    requested_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime)
    received_at: Mapped[datetime | None] = mapped_column(DateTime)

    items: Mapped[list["StockTransferItem"]] = relationship(back_populates="transfer", lazy="selectin")
    from_warehouse: Mapped["Warehouse"] = relationship(foreign_keys=[from_warehouse_id], lazy="selectin")
    to_warehouse: Mapped["Warehouse"] = relationship(foreign_keys=[to_warehouse_id], lazy="selectin")


class StockTransferItem(BaseModel):
    __tablename__ = "stock_transfer_items"

    transfer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stock_transfers.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("batches.id"))
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    shipped_quantity: Mapped[int] = mapped_column(Integer, default=0)
    received_quantity: Mapped[int] = mapped_column(Integer, default=0)

    transfer: Mapped["StockTransfer"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(lazy="selectin")


class StockAlert(BaseModel, TenantMixin):
    __tablename__ = "stock_alerts"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    product: Mapped["Product"] = relationship(lazy="selectin")
    warehouse: Mapped["Warehouse"] = relationship(lazy="selectin")
