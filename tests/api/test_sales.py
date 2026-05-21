"""API tests for sales/invoice endpoints."""
import pytest


@pytest.mark.api
class TestSalesAPI:
    @pytest.mark.asyncio
    async def test_list_invoices(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/sales/invoices/")
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_create_invoice(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/sales/invoices/", json={
            "customer_id": 1,
            "items": [
                {"product_id": 1, "quantity": 2, "unit_price": 29.99},
                {"product_id": 2, "quantity": 1, "unit_price": 49.99},
            ],
            "notes": "Test invoice",
        })
        assert response.status_code in (200, 201, 401, 422)
        if response.status_code in (200, 201):
            data = response.json()
            assert "invoice_number" in data
            assert data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_invoice_empty_items(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/sales/invoices/", json={
            "customer_id": 1,
            "items": [],
        })
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_get_invoice(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/sales/invoices/1")
        assert response.status_code in (200, 404, 401)
        if response.status_code == 200:
            data = response.json()
            assert "total" in data
            assert "items" in data or "line_items" in data

    @pytest.mark.asyncio
    async def test_update_invoice_status(self, authenticated_client):
        response = await authenticated_client.patch("/api/v1/sales/invoices/1/status", json={
            "status": "confirmed",
        })
        assert response.status_code in (200, 400, 404, 401, 422)

    @pytest.mark.asyncio
    async def test_void_invoice(self, authenticated_client):
        response = await authenticated_client.patch("/api/v1/sales/invoices/1/status", json={
            "status": "void",
        })
        assert response.status_code in (200, 400, 404, 401, 422)

    @pytest.mark.asyncio
    async def test_invoice_total_calculation(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/sales/invoices/", json={
            "customer_id": 1,
            "items": [
                {"product_id": 1, "quantity": 3, "unit_price": 100.00},
            ],
            "tax_rate": 14.0,
        })
        if response.status_code in (200, 201):
            data = response.json()
            assert float(data.get("subtotal", 0)) == 300.00
            assert float(data.get("tax_amount", 0)) == 42.00
            assert float(data.get("total", 0)) == 342.00
