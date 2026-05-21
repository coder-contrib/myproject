"""API tests for AI endpoints."""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.api
class TestAIAPI:
    @pytest.mark.asyncio
    async def test_query_assistant(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/ai/query", json={
            "question": "What are total sales this month?",
        })
        assert response.status_code in (200, 401, 503)

    @pytest.mark.asyncio
    async def test_query_assistant_empty_question(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/ai/query", json={
            "question": "",
        })
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_semantic_search(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/ai/search", json={
            "query": "red widgets with high margin",
            "entity_type": "product",
            "limit": 5,
        })
        assert response.status_code in (200, 401, 503)
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)

    @pytest.mark.asyncio
    async def test_analytics_trends(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/ai/analytics/trends", json={
            "metric": "revenue",
            "period": "30d",
        })
        assert response.status_code in (200, 401, 503)

    @pytest.mark.asyncio
    async def test_generate_report(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/ai/reports/generate", json={
            "report_type": "executive_summary",
        })
        assert response.status_code in (200, 401, 503)

    @pytest.mark.asyncio
    async def test_submit_feedback(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/ai/feedback", json={
            "query_id": "test-query-123",
            "rating": 4,
            "comment": "Good response but could be more detailed",
        })
        assert response.status_code in (200, 201, 401)

    @pytest.mark.asyncio
    async def test_get_feedback_stats(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/ai/feedback/stats")
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert "average_rating" in data or "total" in data

    @pytest.mark.asyncio
    async def test_list_prompt_templates(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/ai/templates")
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "templates" in data
