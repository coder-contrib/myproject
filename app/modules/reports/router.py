from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, get_current_tenant_id
from app.modules.reports.schemas import *
from app.modules.reports.service import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/scheduled", response_model=ScheduledReportResponse)
async def create_report(data: ScheduledReportCreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).create_report(tenant_id=tenant_id, **data.model_dump())

@router.get("/scheduled", response_model=list[ScheduledReportResponse])
async def list_reports(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).get_reports(tenant_id)

@router.post("/kpis", response_model=KPIResponse)
async def create_kpi(data: KPICreate, tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).create_kpi(tenant_id=tenant_id, **data.model_dump())

@router.get("/kpis", response_model=list[KPIResponse])
async def list_kpis(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).get_kpis(tenant_id)

@router.post("/widgets", response_model=DashboardWidgetResponse)
async def create_widget(data: DashboardWidgetCreate, current_user=Depends(get_current_user), tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).create_widget(tenant_id=tenant_id, user_id=current_user.id, **data.model_dump())

@router.get("/widgets", response_model=list[DashboardWidgetResponse])
async def list_widgets(tenant_id: UUID = Depends(get_current_tenant_id), db: AsyncSession = Depends(get_db)):
    return await ReportsService(db).get_widgets(tenant_id)
