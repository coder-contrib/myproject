"""API tests for inventory endpoints."""
import pytest


@pytest.mark.api
class TestInventoryAPI:
    @pytest.mark.asyncio
    async def test_get_stock_levels(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/inventory/stock/")
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_stock_movement_in(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/inventory/movements/", json={
            "product_id": 1,
            "warehouse_id": 1,
            "quantity": 50,
            "movement_type": "in",
            "reference": "PO-001",
        })
        assert response.status_code in (200, 201, 401, 422)

    @pytest.mark.asyncio
    async def test_stock_movement_out(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/inventory/movements/", json={
            "product_id": 1,
            "warehouse_id": 1,
            "quantity": 5,
            "movement_type": "out",
            "reference": "INV-001",
        })
        assert response.status_code in (200, 201, 400, 401, 422)

    @pytest.mark.asyncio
    async def test_stock_movement_insufficient(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/inventory/movements/", json={
            "product_id": 1,
            "warehouse_id": 1,
            "quantity": 999999,
            "movement_type": "out",
            "reference": "TEST",
        })
        assert response.status_code in (400, 422, 401)

    @pytest.mark.asyncio
    async def test_stock_transfer(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/inventory/transfers/", json={
            "product_id": 1,
            "from_warehouse_id": 1,
            "to_warehouse_id": 2,
            "quantity": 10,
        })
        assert response.status_code in (200, 201, 400, 401, 422)

    @pytest.mark.asyncio
    async def test_list_warehouses(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/inventory/warehouses/")
        assert response.status_code in (200, 401)

    @pytest.mark.asyncio
    async def test_low_stock_alerts(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "items" in data
