"""Unit tests for AI client and utilities."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.unit
class TestAIClient:
    @pytest.mark.asyncio
    async def test_chat_completion(self):
        from app.ai.client import AIClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, how can I help?"}}]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            client = AIClient()
            result = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )
            assert result == "Hello, how can I help?"

    @pytest.mark.asyncio
    async def test_create_embedding(self):
        from app.ai.client import AIClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3] * 512}]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            client = AIClient()
            result = await client.create_embedding("test text")
            assert len(result) == 1536
            assert result[0] == 0.1

    @pytest.mark.asyncio
    async def test_extract_json_from_response(self):
        from app.ai.client import AIClient

        client = AIClient()
        text = 'Here is the result: ```json\n{"key": "value", "count": 42}\n```'
        result = client.extract_json(text)
        assert result == {"key": "value", "count": 42}

    @pytest.mark.asyncio
    async def test_extract_json_plain(self):
        from app.ai.client import AIClient

        client = AIClient()
        text = '{"key": "value"}'
        result = client.extract_json(text)
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_extract_json_invalid(self):
        from app.ai.client import AIClient

        client = AIClient()
        text = "This is not JSON at all"
        result = client.extract_json(text)
        assert result is None


@pytest.mark.unit
class TestPromptTemplates:
    def test_get_template(self):
        from app.ai.templates import PromptTemplateRegistry

        registry = PromptTemplateRegistry()
        template = registry.get("query_assistant")
        assert template is not None
        assert "{{question}}" in template or "{question}" in template

    def test_render_template(self):
        from app.ai.templates import PromptTemplateRegistry

        registry = PromptTemplateRegistry()
        rendered = registry.render("query_assistant", question="What are total sales?")
        assert "What are total sales?" in rendered

    def test_list_templates(self):
        from app.ai.templates import PromptTemplateRegistry

        registry = PromptTemplateRegistry()
        templates = registry.list_templates()
        assert len(templates) >= 4
        assert "query_assistant" in templates

    def test_register_custom_template(self):
        from app.ai.templates import PromptTemplateRegistry

        registry = PromptTemplateRegistry()
        registry.register("custom", "Hello {name}, welcome!")
        rendered = registry.render("custom", name="World")
        assert rendered == "Hello World, welcome!"

    def test_get_nonexistent_template(self):
        from app.ai.templates import PromptTemplateRegistry

        registry = PromptTemplateRegistry()
        template = registry.get("nonexistent")
        assert template is None
