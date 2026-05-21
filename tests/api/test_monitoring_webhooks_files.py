"""API tests for monitoring and health endpoints."""
import pytest


@pytest.mark.api
class TestMonitoringAPI:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "ok")

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        response = await client.get("/api/v1/monitoring/metrics")
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            content = response.text
            assert "# HELP" in content or "# TYPE" in content

    @pytest.mark.asyncio
    async def test_performance_stats(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/monitoring/performance")
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert "endpoints" in data or "stats" in data

    @pytest.mark.asyncio
    async def test_error_list(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/monitoring/errors")
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_audit_log(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/monitoring/audit")
        assert response.status_code in (200, 401, 403)


@pytest.mark.api
class TestWebhooksAPI:
    @pytest.mark.asyncio
    async def test_list_webhooks(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/webhooks/")
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_create_webhook(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/webhooks/", json={
            "url": "https://example.com/webhook",
            "events": ["invoice.created", "invoice.paid"],
            "is_active": True,
        })
        assert response.status_code in (200, 201, 401, 422)
        if response.status_code in (200, 201):
            data = response.json()
            assert "id" in data
            assert "secret" in data

    @pytest.mark.asyncio
    async def test_create_webhook_invalid_url(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/webhooks/", json={
            "url": "not-a-valid-url",
            "events": ["invoice.created"],
        })
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_test_webhook(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/webhooks/1/test")
        assert response.status_code in (200, 404, 401)

    @pytest.mark.asyncio
    async def test_webhook_deliveries(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/webhooks/1/deliveries")
        assert response.status_code in (200, 404, 401)


@pytest.mark.api
class TestFilesAPI:
    @pytest.mark.asyncio
    async def test_upload_file(self, authenticated_client):
        import io
        file_content = b"test file content for upload"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        response = await authenticated_client.post("/api/v1/files/upload", files=files)
        assert response.status_code in (200, 201, 401, 413)

    @pytest.mark.asyncio
    async def test_upload_oversized_file(self, authenticated_client):
        import io
        large_content = b"x" * (50 * 1024 * 1024)
        files = {"file": ("large.bin", io.BytesIO(large_content), "application/octet-stream")}
        response = await authenticated_client.post("/api/v1/files/upload", files=files)
        assert response.status_code in (400, 413, 422)

    @pytest.mark.asyncio
    async def test_upload_forbidden_extension(self, authenticated_client):
        import io
        files = {"file": ("malware.exe", io.BytesIO(b"MZ"), "application/x-executable")}
        response = await authenticated_client.post("/api/v1/files/upload", files=files)
        assert response.status_code in (400, 415, 422)
