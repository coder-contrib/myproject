from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant.context import TenantContext
from app.core.tenant.isolation import TenantIsolatedRepository
from app.core.exceptions.handlers import AppException, NotFoundException
from app.modules.inventory.models import (
    Product, ProductCategory, Warehouse, Inventory,
    InventoryMovement, Batch, StockTransfer, StockTransferItem, StockAlert,
)


class InventoryService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx
        self.products = TenantIsolatedRepository(Product, db, ctx)
        self.categories = TenantIsolatedRepository(ProductCategory, db, ctx)
        self.warehouses = TenantIsolatedRepository(Warehouse, db, ctx)
        self.inventory = TenantIsolatedRepository(Inventory, db, ctx)
        self.movements = TenantIsolatedRepository(InventoryMovement, db, ctx)
        self.batches = TenantIsolatedRepository(Batch, db, ctx)
        self.transfers = TenantIsolatedRepository(StockTransfer, db, ctx)
        self.alerts = TenantIsolatedRepository(StockAlert, db, ctx)

    # --- Categories ---

    async def create_category(self, **kwargs) -> ProductCategory:
        return await self.categories.create(**kwargs)

    async def get_categories(self) -> list:
        return await self.categories.get_all(limit=500)

    async def update_category(self, category_id: UUID, **kwargs) -> ProductCategory:
        return await self.categories.update_strict(category_id, **kwargs)

    # --- Products ---

    async def create_product(self, **kwargs) -> Product:
        if kwargs.get("sku"):
            existing = await self.products.find_one(sku=kwargs["sku"])
            if existing:
                raise AppException("Product with this SKU already exists", status_code=409)

        if kwargs.get("barcode"):
            existing = await self.products.find_one(barcode=kwargs["barcode"])
            if existing:
                raise AppException("Product with this barcode already exists", status_code=409)

        return await self.products.create(**kwargs)

    async def get_products(self, skip: int = 0, limit: int = 50, category_id: UUID | None = None, is_active: bool | None = None) -> list:
        filters = {}
        if category_id:
            filters["category_id"] = category_id
        if is_active is not None:
            filters["is_active"] = is_active
        return await self.products.get_all(skip=skip, limit=limit, **filters)

    async def get_product(self, product_id: UUID) -> Product:
        return await self.products.get_by_id_strict(product_id)

    async def get_product_by_barcode(self, barcode: str) -> Product | None:
        return await self.products.find_one(barcode=barcode)

    async def get_product_by_sku(self, sku: str) -> Product | None:
        return await self.products.find_one(sku=sku)

    async def update_product(self, product_id: UUID, **kwargs) -> Product:
        version = kwargs.pop("version", None)
        return await self.products.update_strict(product_id, expected_version=version, **kwargs)

    async def delete_product(self, product_id: UUID) -> bool:
        return await self.products.soft_delete(product_id)

    # --- Warehouses ---

    async def create_warehouse(self, **kwargs) -> Warehouse:
        return await self.warehouses.create(**kwargs)

    async def get_warehouses(self) -> list:
        return await self.warehouses.get_all(limit=200)

    async def get_warehouse(self, warehouse_id: UUID) -> Warehouse:
        return await self.warehouses.get_by_id_strict(warehouse_id)

    async def update_warehouse(self, warehouse_id: UUID, **kwargs) -> Warehouse:
        version = kwargs.pop("version", None)
        return await self.warehouses.update_strict(warehouse_id, expected_version=version, **kwargs)

    # --- Inventory / Stock Levels ---

    async def get_stock(self, product_id: UUID | None = None, warehouse_id: UUID | None = None) -> list:
        filters = {}
        if product_id:
            filters["product_id"] = product_id
        if warehouse_id:
            filters["warehouse_id"] = warehouse_id
        return await self.inventory.get_all(limit=1000, **filters)

    async def get_stock_level(self, product_id: UUID, warehouse_id: UUID) -> Inventory | None:
        return await self.inventory.find_one(product_id=product_id, warehouse_id=warehouse_id)

    async def adjust_stock(self, product_id: UUID, warehouse_id: UUID, quantity: int, reason: str, notes: str | None = None) -> Inventory:
        stock = await self.get_stock_level(product_id, warehouse_id)

        if not stock:
            if quantity < 0:
                raise AppException("Cannot reduce stock below zero for non-existent inventory", status_code=400)
            stock = await self.inventory.create(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
            )
        else:
            new_qty = stock.quantity + quantity
            if new_qty < 0:
                raise AppException(
                    f"Insufficient stock. Available: {stock.quantity}, Requested: {abs(quantity)}",
                    status_code=400,
                )
            stock.quantity = new_qty
            stock.updated_at = datetime.now(timezone.utc)
            await self.db.flush()

        movement_type = "adjustment_in" if quantity > 0 else "adjustment_out"
        await self.movements.create(
            product_id=product_id,
            to_warehouse_id=warehouse_id if quantity > 0 else None,
            from_warehouse_id=warehouse_id if quantity < 0 else None,
            quantity=abs(quantity),
            movement_type=movement_type,
            reason=reason,
            notes=notes,
        )

        await self._check_stock_alerts(product_id, warehouse_id, stock.quantity)
        return stock

    # --- Batch Tracking ---

    async def create_batch(self, **kwargs) -> Batch:
        product = await self.products.get_by_id_strict(kwargs["product_id"])
        if not product.is_batch_tracked:
            raise AppException("Product does not support batch tracking", status_code=400)

        batch = await self.batches.create(**kwargs)

        await self.adjust_stock(
            product_id=kwargs["product_id"],
            warehouse_id=kwargs["warehouse_id"],
            quantity=kwargs["quantity"],
            reason=f"Batch receipt: {kwargs['batch_number']}",
        )

        return batch

    async def get_batches(self, product_id: UUID | None = None, warehouse_id: UUID | None = None) -> list:
        filters = {}
        if product_id:
            filters["product_id"] = product_id
        if warehouse_id:
            filters["warehouse_id"] = warehouse_id
        return await self.batches.get_all(limit=500, **filters)

    async def get_batch(self, batch_id: UUID) -> Batch:
        return await self.batches.get_by_id_strict(batch_id)

    # --- Stock Movements ---

    async def record_movement(self, **kwargs) -> InventoryMovement:
        product_id = kwargs["product_id"]
        quantity = kwargs["quantity"]
        from_wh = kwargs.get("from_warehouse_id")
        to_wh = kwargs.get("to_warehouse_id")

        if from_wh:
            stock = await self.get_stock_level(product_id, from_wh)
            if not stock or stock.available_quantity < quantity:
                available = stock.available_quantity if stock else 0
                raise AppException(
                    f"Insufficient stock. Available: {available}, Requested: {quantity}",
                    status_code=400,
                )
            stock.quantity -= quantity
            stock.updated_at = datetime.now(timezone.utc)

        if to_wh:
            stock = await self.get_stock_level(product_id, to_wh)
            if not stock:
                stock = await self.inventory.create(
                    product_id=product_id, warehouse_id=to_wh, quantity=quantity,
                )
            else:
                stock.quantity += quantity
                stock.updated_at = datetime.now(timezone.utc)

        await self.db.flush()

        movement = await self.movements.create(**kwargs)

        if from_wh:
            from_stock = await self.get_stock_level(product_id, from_wh)
            await self._check_stock_alerts(product_id, from_wh, from_stock.quantity if from_stock else 0)

        return movement

    async def get_movements(self, product_id: UUID | None = None, warehouse_id: UUID | None = None, skip: int = 0, limit: int = 50) -> list:
        filters = {}
        if product_id:
            filters["product_id"] = product_id
        return await self.movements.get_all(skip=skip, limit=limit, **filters)

    # --- Stock Transfers ---

    async def create_transfer(self, from_warehouse_id: UUID, to_warehouse_id: UUID, items: list[dict], notes: str | None = None) -> StockTransfer:
        if from_warehouse_id == to_warehouse_id:
            raise AppException("Source and destination warehouse cannot be the same", status_code=400)

        await self.warehouses.get_by_id_strict(from_warehouse_id)
        await self.warehouses.get_by_id_strict(to_warehouse_id)

        transfer_number = await self._generate_transfer_number()

        transfer = await self.transfers.create(
            transfer_number=transfer_number,
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=to_warehouse_id,
            notes=notes,
            requested_by=self.ctx.user_id,
            status="draft",
        )

        for item in items:
            transfer_item = StockTransferItem(
                transfer_id=transfer.id,
                product_id=item["product_id"],
                batch_id=item.get("batch_id"),
                requested_quantity=item["requested_quantity"],
            )
            self.db.add(transfer_item)

        await self.db.flush()
        await self.db.refresh(transfer)
        return transfer

    async def get_transfers(self, status: str | None = None, skip: int = 0, limit: int = 50) -> list:
        filters = {}
        if status:
            filters["status"] = status
        return await self.transfers.get_all(skip=skip, limit=limit, **filters)

    async def get_transfer(self, transfer_id: UUID) -> StockTransfer:
        return await self.transfers.get_by_id_strict(transfer_id)

    async def update_transfer_status(self, transfer_id: UUID, status: str, items_data: list[dict] | None = None) -> StockTransfer:
        transfer = await self.transfers.get_by_id_strict(transfer_id)

        valid_transitions = {
            "draft": ["approved", "cancelled"],
            "approved": ["shipped", "cancelled"],
            "shipped": ["in_transit"],
            "in_transit": ["received"],
        }

        allowed = valid_transitions.get(transfer.status, [])
        if status not in allowed:
            raise AppException(
                f"Cannot transition from '{transfer.status}' to '{status}'. Allowed: {allowed}",
                status_code=400,
            )

        if status == "shipped":
            transfer.shipped_at = datetime.now(timezone.utc)
            for item in transfer.items:
                item.shipped_quantity = item.requested_quantity
                stock = await self.get_stock_level(item.product_id, transfer.from_warehouse_id)
                if not stock or stock.available_quantity < item.shipped_quantity:
                    raise AppException(
                        f"Insufficient stock for product {item.product_id}",
                        status_code=400,
                    )
                stock.quantity -= item.shipped_quantity
                stock.in_transit_quantity = (stock.in_transit_quantity or 0) + item.shipped_quantity

                await self.movements.create(
                    product_id=item.product_id,
                    from_warehouse_id=transfer.from_warehouse_id,
                    quantity=item.shipped_quantity,
                    movement_type="transfer_out",
                    reason=f"Transfer {transfer.transfer_number}",
                    reference_type="stock_transfer",
                    reference_id=transfer.id,
                    batch_id=item.batch_id,
                )

        elif status == "received":
            transfer.received_at = datetime.now(timezone.utc)
            for item in transfer.items:
                received_qty = item.shipped_quantity
                if items_data:
                    match = next((d for d in items_data if d.get("product_id") == str(item.product_id)), None)
                    if match and "received_quantity" in match:
                        received_qty = match["received_quantity"]
                item.received_quantity = received_qty

                to_stock = await self.get_stock_level(item.product_id, transfer.to_warehouse_id)
                if not to_stock:
                    await self.inventory.create(
                        product_id=item.product_id,
                        warehouse_id=transfer.to_warehouse_id,
                        quantity=received_qty,
                    )
                else:
                    to_stock.quantity += received_qty
                    to_stock.updated_at = datetime.now(timezone.utc)

                from_stock = await self.get_stock_level(item.product_id, transfer.from_warehouse_id)
                if from_stock:
                    from_stock.in_transit_quantity = max(0, (from_stock.in_transit_quantity or 0) - item.shipped_quantity)

                await self.movements.create(
                    product_id=item.product_id,
                    to_warehouse_id=transfer.to_warehouse_id,
                    quantity=received_qty,
                    movement_type="transfer_in",
                    reason=f"Transfer {transfer.transfer_number}",
                    reference_type="stock_transfer",
                    reference_id=transfer.id,
                    batch_id=item.batch_id,
                )

        elif status == "approved":
            transfer.approved_by = self.ctx.user_id

        transfer.status = status
        await self.db.flush()
        await self.db.refresh(transfer)
        return transfer

    # --- Stock Alerts ---

    async def get_alerts(self, is_resolved: bool = False) -> list:
        return await self.alerts.get_all(limit=200, is_resolved=is_resolved)

    async def resolve_alert(self, alert_id: UUID) -> StockAlert:
        alert = await self.alerts.get_by_id_strict(alert_id)
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(alert)
        return alert

    async def check_low_stock_all(self) -> list[StockAlert]:
        products = await self.products.get_all(limit=10000, is_active=True)
        new_alerts = []

        for product in products:
            stocks = await self.inventory.get_all(limit=100, product_id=product.id)
            total_qty = sum(s.quantity for s in stocks)

            if total_qty <= product.reorder_point:
                for stock in stocks:
                    existing = await self.alerts.find_one(
                        product_id=product.id,
                        warehouse_id=stock.warehouse_id,
                        is_resolved=False,
                    )
                    if not existing:
                        alert = await self.alerts.create(
                            product_id=product.id,
                            warehouse_id=stock.warehouse_id,
                            alert_type="low_stock",
                            current_quantity=stock.quantity,
                            threshold=product.reorder_point,
                        )
                        new_alerts.append(alert)

        return new_alerts

    # --- Private helpers ---

    async def _check_stock_alerts(self, product_id: UUID, warehouse_id: UUID, current_qty: int) -> None:
        product = await self.products.get_by_id(product_id)
        if not product:
            return

        if current_qty <= product.reorder_point:
            existing = await self.alerts.find_one(
                product_id=product_id,
                warehouse_id=warehouse_id,
                is_resolved=False,
            )
            if not existing:
                await self.alerts.create(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    alert_type="low_stock",
                    current_quantity=current_qty,
                    threshold=product.reorder_point,
                )
        else:
            existing = await self.alerts.find_one(
                product_id=product_id,
                warehouse_id=warehouse_id,
                is_resolved=False,
            )
            if existing:
                existing.is_resolved = True
                existing.resolved_at = datetime.now(timezone.utc)
                await self.db.flush()

    async def _generate_transfer_number(self) -> str:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(StockTransfer.id)).where(StockTransfer.tenant_id == self.ctx.tenant_id)
        )
        count = (result.scalar() or 0) + 1
        return f"TRF-{count:06d}"
