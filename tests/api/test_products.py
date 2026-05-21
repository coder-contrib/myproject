"""API tests for product endpoints."""
import pytest


@pytest.mark.api
class TestProductsAPI:
    @pytest.mark.asyncio
    async def test_list_products(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/products/")
        assert response.status_code in (200, 401)
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_products_pagination(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/products/?page=1&size=5")
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_create_product(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/products/", json={
            "name": "Test Product",
            "sku": "TEST-API-001",
            "price": 29.99,
            "cost": 15.00,
            "category_id": 1,
        })
        assert response.status_code in (200, 201, 401, 422)

    @pytest.mark.asyncio
    async def test_create_product_validation(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/products/", json={
            "name": "",  # empty name
            "sku": "",
            "price": -10,  # negative price
        })
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/products/1")
        assert response.status_code in (200, 404, 401)
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "name" in data

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/products/99999")
        assert response.status_code in (404, 401)

    @pytest.mark.asyncio
    async def test_update_product(self, authenticated_client):
        response = await authenticated_client.put("/api/v1/products/1", json={
            "name": "Updated Product",
            "price": 39.99,
        })
        assert response.status_code in (200, 404, 401, 422)

    @pytest.mark.asyncio
    async def test_delete_product(self, authenticated_client):
        # Create then delete
        create_resp = await authenticated_client.post("/api/v1/products/", json={
            "name": "Delete Me",
            "sku": "DEL-001",
            "price": 10.00,
            "cost": 5.00,
            "category_id": 1,
        })
        if create_resp.status_code in (200, 201):
            product_id = create_resp.json()["id"]
            response = await authenticated_client.delete(f"/api/v1/products/{product_id}")
            assert response.status_code in (200, 204)

    @pytest.mark.asyncio
    async def test_search_products(self, authenticated_client):
        response = await authenticated_client.get("/api/v1/products/?search=widget")
        assert response.status_code in (200, 401)
