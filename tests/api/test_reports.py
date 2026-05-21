"""API tests for reporting and analytics endpoints."""
import pytest


@pytest.mark.api
class TestReportsAPI:
    @pytest.mark.asyncio
    async def test_dashboard_overview(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/reports/dashboard/overview")
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert "total_revenue" in data or "revenue" in data
            assert "total_orders" in data or "orders" in data

    @pytest.mark.asyncio
    async def test_sales_trend(self, authenticated_client):
        response = await authenticated_client.get(
            "/api/v1/reports/dashboard/sales-trend?period=30d"
        )
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_top_products(self, authenticated_client):
        response = await authenticated_client.get(
            "/api/v1/reports/dashboard/top-products?limit=10"
        )
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "items" in data

    @pytest.mark.asyncio
    async def test_revenue_breakdown(self, authenticated_client):
        response = await authenticated_client.get(
            "/api/v1/reports/analytics/revenue-breakdown?group_by=category"
        )
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_financial_profit_loss(self, authenticated_client):
        response = await authenticated_client.get(
            "/api/v1/reports/financial/profit-loss?start_date=2026-01-01&end_date=2026-03-31"
        )
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert "revenue" in data or "income" in data
            assert "expenses" in data

    @pytest.mark.asyncio
    async def test_export_to_csv(self, authenticated_client):
        response = await authenticated_client.get(
            "/api/v1/reports/export/sales?format=csv&start_date=2026-01-01&end_date=2026-01-31"
        )
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_to_excel(self, authenticated_client):
        response = await authenticated_client.get(
            "/api/v1/reports/export/sales?format=xlsx&start_date=2026-01-01&end_date=2026-01-31"
        )
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            assert "spreadsheet" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_refresh_materialized_views(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/reports/views/refresh")
        assert response.status_code in (200, 202, 401, 403)
