from uuid import UUID
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.repository import BaseRepository
from app.modules.ai.models import AIConversation, AILog, PromptTemplate


class AIService:
    def __init__(self, db: AsyncSession):
        self.conversation_repo = BaseRepository(AIConversation, db)
        self.log_repo = BaseRepository(AILog, db)
        self.template_repo = BaseRepository(PromptTemplate, db)
        self.db = db

    async def create_conversation(self, user_id: UUID, title: str | None = None) -> AIConversation:
        return await self.conversation_repo.create(user_id=user_id, title=title)

    async def get_conversations(self, user_id: UUID) -> list:
        return await self.conversation_repo.get_all()

    async def query(self, user_id: UUID, query: str, conversation_id: UUID | None = None) -> AILog:
        start = time.time()
        # Placeholder: actual AI integration would go here
        response = f"AI response to: {query}"
        execution_time = int((time.time() - start) * 1000)

        return await self.log_repo.create(
            user_id=user_id,
            conversation_id=conversation_id,
            user_query=query,
            ai_response=response,
            detected_intent="general_query",
            confidence_score=0.85,
            execution_time_ms=execution_time,
        )

    async def get_templates(self) -> list:
        return await self.template_repo.get_all()

    async def create_template(self, **kwargs) -> PromptTemplate:
        return await self.template_repo.create(**kwargs)
