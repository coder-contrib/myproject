from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class ConversationCreate(BaseModel):
    title: str | None = None

class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    title: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class AIQueryRequest(BaseModel):
    query: str
    conversation_id: UUID | None = None

class AIQueryResponse(BaseModel):
    id: UUID
    user_query: str | None
    ai_response: str | None
    detected_intent: str | None
    confidence_score: float | None
    execution_time_ms: int | None
    created_at: datetime
    model_config = {"from_attributes": True}

class PromptTemplateCreate(BaseModel):
    name: str
    template: str
    category: str | None = None

class PromptTemplateResponse(BaseModel):
    id: UUID
    name: str
    template: str
    category: str | None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
