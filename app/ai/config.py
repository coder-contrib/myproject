import os
from dataclasses import dataclass


@dataclass
class AIConfig:
    api_base_url: str = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
    api_key: str = os.getenv("AI_API_KEY", "")
    chat_model: str = os.getenv("AI_CHAT_MODEL", "gpt-4o")
    embedding_model: str = os.getenv("AI_EMBEDDING_MODEL", "text-embedding-3-small")
    embedding_dimensions: int = int(os.getenv("AI_EMBEDDING_DIMENSIONS", "1536"))
    max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "4096"))
    temperature: float = float(os.getenv("AI_TEMPERATURE", "0.1"))
    request_timeout: int = int(os.getenv("AI_REQUEST_TIMEOUT", "60"))
    max_retries: int = int(os.getenv("AI_MAX_RETRIES", "3"))


ai_config = AIConfig()
