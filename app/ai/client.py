import json
import logging
from typing import Optional

import httpx

from app.ai.config import ai_config

logger = logging.getLogger("ai.client")


class AIClient:
    """OpenAI-compatible API client supporting any provider."""

    def __init__(self):
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=ai_config.api_base_url,
                headers={
                    "Authorization": f"Bearer {ai_config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=ai_config.request_timeout,
            )
        return self._http

    async def chat_completion(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> dict:
        payload = {
            "model": model or ai_config.chat_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else ai_config.temperature,
            "max_tokens": max_tokens or ai_config.max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        for attempt in range(ai_config.max_retries):
            try:
                resp = await self.http.post("/chat/completions", json=payload)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.warning("AI API error (attempt %d): %s", attempt + 1, e.response.text)
                if attempt == ai_config.max_retries - 1:
                    raise
            except httpx.RequestError as e:
                logger.warning("AI API request failed (attempt %d): %s", attempt + 1, str(e))
                if attempt == ai_config.max_retries - 1:
                    raise

    async def create_embedding(self, text: str, model: Optional[str] = None) -> list[float]:
        payload = {
            "model": model or ai_config.embedding_model,
            "input": text,
        }

        for attempt in range(ai_config.max_retries):
            try:
                resp = await self.http.post("/embeddings", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["data"][0]["embedding"]
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning("Embedding API error (attempt %d): %s", attempt + 1, str(e))
                if attempt == ai_config.max_retries - 1:
                    raise

    async def create_embeddings_batch(self, texts: list[str], model: Optional[str] = None) -> list[list[float]]:
        payload = {
            "model": model or ai_config.embedding_model,
            "input": texts,
        }

        for attempt in range(ai_config.max_retries):
            try:
                resp = await self.http.post("/embeddings", json=payload)
                resp.raise_for_status()
                data = resp.json()
                sorted_data = sorted(data["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_data]
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                logger.warning("Batch embedding error (attempt %d): %s", attempt + 1, str(e))
                if attempt == ai_config.max_retries - 1:
                    raise

    def extract_content(self, response: dict) -> str:
        return response["choices"][0]["message"]["content"]

    def extract_json(self, response: dict) -> dict:
        content = self.extract_content(response)
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())

    async def close(self):
        if self._http and not self._http.is_closed:
            await self._http.aclose()


ai_client = AIClient()
