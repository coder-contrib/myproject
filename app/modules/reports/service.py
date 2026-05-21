from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.reports.models import ScheduledReport, KPIDefinition, DashboardWidget


class ReportsService:
    def __init__(self, db: AsyncSession):
        self.report_repo = BaseRepository(ScheduledReport, db)
        self.kpi_repo = BaseRepository(KPIDefinition, db)
        self.widget_repo = BaseRepository(DashboardWidget, db)
        self.db = db

    async def create_report(self, tenant_id: UUID, **kwargs) -> ScheduledReport:
        return await self.report_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_reports(self, tenant_id: UUID) -> list:
        return await self.report_repo.get_all(tenant_id=tenant_id)

    async def create_kpi(self, tenant_id: UUID, **kwargs) -> KPIDefinition:
        return await self.kpi_repo.create(tenant_id=tenant_id, **kwargs)

    async def get_kpis(self, tenant_id: UUID) -> list:
        return await self.kpi_repo.get_all(tenant_id=tenant_id)

    async def create_widget(self, tenant_id: UUID, user_id: UUID, **kwargs) -> DashboardWidget:
        return await self.widget_repo.create(tenant_id=tenant_id, user_id=user_id, **kwargs)

    async def get_widgets(self, tenant_id: UUID) -> list:
        return await self.widget_repo.get_all(tenant_id=tenant_id)
