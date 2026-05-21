from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.ai.schemas import *
from app.modules.ai.service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(data: ConversationCreate, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AIService(db).create_conversation(user_id=current_user.id, title=data.title)

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AIService(db).get_conversations(user_id=current_user.id)

@router.post("/query", response_model=AIQueryResponse)
async def ai_query(data: AIQueryRequest, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AIService(db).query(user_id=current_user.id, query=data.query, conversation_id=data.conversation_id)

@router.post("/templates", response_model=PromptTemplateResponse)
async def create_template(data: PromptTemplateCreate, db: AsyncSession = Depends(get_db)):
    return await AIService(db).create_template(**data.model_dump())

@router.get("/templates", response_model=list[PromptTemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    return await AIService(db).get_templates()
