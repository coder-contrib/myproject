import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import BaseModel, TenantMixin


class ScheduledReport(BaseModel, TenantMixin):
    __tablename__ = "scheduled_reports"
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)


class KPIDefinition(BaseModel, TenantMixin):
    __tablename__ = "kpi_definitions"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(30))
    target_value: Mapped[float | None] = mapped_column(Numeric(14, 2))


class DashboardWidget(BaseModel, TenantMixin):
    __tablename__ = "dashboard_widgets"
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    kpi_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("kpi_definitions.id"))
    widget_type: Mapped[str | None] = mapped_column(String(50))
    position: Mapped[int | None] = mapped_column(Integer)
    config: Mapped[dict | None] = mapped_column(JSONB)
