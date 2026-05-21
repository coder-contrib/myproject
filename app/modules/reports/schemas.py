from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class ScheduledReportCreate(BaseModel):
    report_name: str
    frequency: str

class ScheduledReportResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    report_name: str
    frequency: str
    created_at: datetime
    model_config = {"from_attributes": True}

class KPICreate(BaseModel):
    name: str
    query: str
    unit: str | None = None
    target_value: float | None = None

class KPIResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    unit: str | None
    target_value: float | None
    created_at: datetime
    model_config = {"from_attributes": True}

class DashboardWidgetCreate(BaseModel):
    kpi_id: UUID | None = None
    widget_type: str | None = None
    position: int | None = None
    config: dict | None = None

class DashboardWidgetResponse(BaseModel):
    id: UUID
    widget_type: str | None
    position: int | None
    config: dict | None
    created_at: datetime
    model_config = {"from_attributes": True}
