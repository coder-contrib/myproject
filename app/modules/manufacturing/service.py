from uuid import UUID
from datetime import datetime, date, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant.context import TenantContext
from app.core.tenant.isolation import TenantIsolatedRepository
from app.core.exceptions.handlers import AppException
from app.modules.manufacturing.models import (
    BillOfMaterials, BOMItem, ProductionOrder, MaterialConsumption,
)


class ManufacturingService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx
        self.boms = TenantIsolatedRepository(BillOfMaterials, db, ctx)
        self.orders = TenantIsolatedRepository(ProductionOrder, db, ctx)
        self.consumptions = TenantIsolatedRepository(MaterialConsumption, db, ctx)

    # --- Bill of Materials ---

    async def create_bom(self, product_id: UUID, name: str, items: list[dict], **kwargs) -> BillOfMaterials:
        bom = await self.boms.create(
            product_id=product_id,
            name=name,
            created_by=self.ctx.user_id,
            **kwargs,
        )

        for item_data in items:
            bom_item = BOMItem(bom_id=bom.id, **item_data)
            self.db.add(bom_item)

        await self.db.flush()
        await self.db.refresh(bom)
        return bom

    async def get_boms(self, product_id: UUID | None = None) -> list:
        filters = {}
        if product_id:
            filters["product_id"] = product_id
        return await self.boms.get_all(limit=500, **filters)

    async def get_bom(self, bom_id: UUID) -> BillOfMaterials:
        return await self.boms.get_by_id_strict(bom_id)

    # --- Production Orders ---

    async def create_production_order(self, product_id: UUID, quantity: float, **kwargs) -> ProductionOrder:
        order_number = await self._generate_number("PRD", ProductionOrder, "order_number")

        order = await self.orders.create(
            order_number=order_number,
            product_id=product_id,
            quantity=quantity,
            created_by=self.ctx.user_id,
            **kwargs,
        )

        if kwargs.get("bom_id"):
            bom = await self.boms.get_by_id_strict(kwargs["bom_id"])
            for bom_item in bom.items:
                planned_qty = bom_item.quantity * quantity * (1 + bom_item.waste_percent / 100)
                consumption = MaterialConsumption(
                    production_order_id=order.id,
                    material_id=bom_item.material_id,
                    warehouse_id=kwargs.get("warehouse_id"),
                    planned_quantity=round(planned_qty, 4),
                    tenant_id=self.ctx.tenant_id,
                )
                self.db.add(consumption)

        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_production_orders(self, skip: int = 0, limit: int = 50, status: str | None = None) -> list:
        filters = {}
        if status:
            filters["status"] = status
        return await self.orders.get_all(skip=skip, limit=limit, **filters)

    async def get_production_order(self, order_id: UUID) -> ProductionOrder:
        return await self.orders.get_by_id_strict(order_id)

    async def update_order_status(self, order_id: UUID, status: str, produced_quantity: float | None = None) -> ProductionOrder:
        order = await self.orders.get_by_id_strict(order_id)

        valid_transitions = {
            "pending": ["in_progress", "cancelled"],
            "in_progress": ["completed", "cancelled"],
        }

        allowed = valid_transitions.get(order.status, [])
        if status not in allowed:
            raise AppException(
                f"Cannot transition from '{order.status}' to '{status}'. Allowed: {allowed}",
                status_code=400,
            )

        if status == "in_progress":
            order.actual_start_date = date.today()
        elif status == "completed":
            order.actual_end_date = date.today()
            if produced_quantity is not None:
                order.produced_quantity = produced_quantity
            else:
                order.produced_quantity = order.quantity

        order.status = status
        await self.db.flush()
        await self.db.refresh(order)
        return order

    # --- Material Consumption ---

    async def consume_material(self, order_id: UUID, material_id: UUID, quantity: float, warehouse_id: UUID | None = None) -> MaterialConsumption:
        order = await self.orders.get_by_id_strict(order_id)
        if order.status != "in_progress":
            raise AppException("Can only consume materials for in-progress orders", status_code=400)

        existing = None
        for c in order.consumptions:
            if c.material_id == material_id:
                existing = c
                break

        if existing:
            existing.actual_quantity += quantity
            existing.status = "consumed"
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        else:
            consumption = await self.consumptions.create(
                production_order_id=order_id,
                material_id=material_id,
                warehouse_id=warehouse_id,
                planned_quantity=quantity,
                actual_quantity=quantity,
                status="consumed",
            )
            return consumption

    # --- Helpers ---

    async def _generate_number(self, prefix: str, model, field: str) -> str:
        result = await self.db.execute(
            select(func.count(model.id)).where(model.tenant_id == self.ctx.tenant_id)
        )
        count = (result.scalar() or 0) + 1
        return f"{prefix}-{count:06d}"
