from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: str | None = None

class NotificationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    title: str
    message: str
    type: str | None
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
