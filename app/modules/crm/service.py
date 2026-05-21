from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tenant.context import TenantContext
from app.core.tenant.isolation import TenantIsolatedRepository
from app.core.exceptions.handlers import AppException
from app.modules.crm.models import Customer, Supplier, Lead, Opportunity, Activity


class CRMService:
    def __init__(self, db: AsyncSession, ctx: TenantContext):
        self.db = db
        self.ctx = ctx
        self.customers = TenantIsolatedRepository(Customer, db, ctx)
        self.suppliers = TenantIsolatedRepository(Supplier, db, ctx)
        self.leads = TenantIsolatedRepository(Lead, db, ctx)
        self.opportunities = TenantIsolatedRepository(Opportunity, db, ctx)
        self.activities = TenantIsolatedRepository(Activity, db, ctx)

    # --- Customers ---

    async def create_customer(self, **kwargs) -> Customer:
        return await self.customers.create(created_by=self.ctx.user_id, **kwargs)

    async def get_customers(self, skip: int = 0, limit: int = 50) -> list:
        return await self.customers.get_all(skip=skip, limit=limit)

    async def get_customer(self, customer_id: UUID) -> Customer:
        return await self.customers.get_by_id_strict(customer_id)

    async def update_customer(self, customer_id: UUID, **kwargs) -> Customer:
        version = kwargs.pop("version", None)
        return await self.customers.update_strict(customer_id, expected_version=version, **kwargs)

    async def delete_customer(self, customer_id: UUID) -> bool:
        return await self.customers.soft_delete(customer_id)

    # --- Suppliers ---

    async def create_supplier(self, **kwargs) -> Supplier:
        return await self.suppliers.create(created_by=self.ctx.user_id, **kwargs)

    async def get_suppliers(self, skip: int = 0, limit: int = 50) -> list:
        return await self.suppliers.get_all(skip=skip, limit=limit)

    async def get_supplier(self, supplier_id: UUID) -> Supplier:
        return await self.suppliers.get_by_id_strict(supplier_id)

    async def update_supplier(self, supplier_id: UUID, **kwargs) -> Supplier:
        version = kwargs.pop("version", None)
        return await self.suppliers.update_strict(supplier_id, expected_version=version, **kwargs)

    # --- Leads ---

    async def create_lead(self, **kwargs) -> Lead:
        return await self.leads.create(**kwargs)

    async def get_leads(self, skip: int = 0, limit: int = 50, status: str | None = None) -> list:
        filters = {}
        if status:
            filters["status"] = status
        return await self.leads.get_all(skip=skip, limit=limit, **filters)

    async def get_lead(self, lead_id: UUID) -> Lead:
        return await self.leads.get_by_id_strict(lead_id)

    async def update_lead(self, lead_id: UUID, **kwargs) -> Lead:
        lead = await self.leads.get_by_id_strict(lead_id)
        for key, value in kwargs.items():
            setattr(lead, key, value)
        await self.db.flush()
        await self.db.refresh(lead)
        return lead

    async def convert_lead(self, lead_id: UUID) -> Customer:
        lead = await self.leads.get_by_id_strict(lead_id)
        if lead.status == "converted":
            raise AppException("Lead is already converted", status_code=400)

        customer = await self.customers.create(
            full_name=lead.full_name,
            phone=lead.phone,
            created_by=self.ctx.user_id,
        )

        lead.status = "converted"
        await self.db.flush()
        return customer

    # --- Opportunities ---

    async def create_opportunity(self, **kwargs) -> Opportunity:
        return await self.opportunities.create(**kwargs)

    async def get_opportunities(self, skip: int = 0, limit: int = 50, stage: str | None = None) -> list:
        filters = {}
        if stage:
            filters["stage"] = stage
        return await self.opportunities.get_all(skip=skip, limit=limit, **filters)

    async def get_opportunity(self, opportunity_id: UUID) -> Opportunity:
        return await self.opportunities.get_by_id_strict(opportunity_id)

    async def update_opportunity(self, opportunity_id: UUID, **kwargs) -> Opportunity:
        opp = await self.opportunities.get_by_id_strict(opportunity_id)
        for key, value in kwargs.items():
            setattr(opp, key, value)
        await self.db.flush()
        await self.db.refresh(opp)
        return opp

    # --- Activities ---

    async def create_activity(self, **kwargs) -> Activity:
        return await self.activities.create(**kwargs)

    async def get_activities(self, entity_type: str | None = None, entity_id: UUID | None = None, skip: int = 0, limit: int = 50) -> list:
        filters = {}
        if entity_type:
            filters["entity_type"] = entity_type
        if entity_id:
            filters["entity_id"] = entity_id
        return await self.activities.get_all(skip=skip, limit=limit, **filters)

    async def complete_activity(self, activity_id: UUID) -> Activity:
        activity = await self.activities.get_by_id_strict(activity_id)
        activity.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(activity)
        return activity

    # --- Pipeline ---

    async def get_pipeline_summary(self) -> list[dict]:
        stages = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
        summary = []
        for stage in stages:
            opps = await self.opportunities.get_all(limit=10000, stage=stage)
            total_value = sum(o.expected_value or 0 for o in opps)
            summary.append({
                "stage": stage,
                "count": len(opps),
                "total_value": total_value,
            })
        return summary
