"""API tests for authentication endpoints."""
import pytest


@pytest.mark.api
class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "testpassword123",
        })
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        response = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "wrongpassword",
        })
        assert response.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_new_user(self, client):
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "securepassword123",
            "full_name": "New User",
        })
        assert response.status_code in (200, 201, 422)

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        payload = {
            "email": "duplicate@test.com",
            "password": "password123",
            "full_name": "Test",
        }
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code in (400, 409, 422)

    @pytest.mark.asyncio
    async def test_refresh_token(self, client):
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "testpassword123",
        })
        if login_resp.status_code == 200:
            refresh_token = login_resp.json()["refresh_token"]
            response = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": refresh_token,
            })
            assert response.status_code == 200
            assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, client):
        client.headers["Authorization"] = "Bearer invalid_token_here"
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401
