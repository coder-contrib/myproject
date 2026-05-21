import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AI_API_KEY", "test-key")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "testpassword123",
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.publish = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def sample_tenant():
    return {"id": 1, "name": "Test Tenant", "slug": "test-tenant", "is_active": True}


@pytest.fixture
def sample_user(sample_tenant):
    return {
        "id": 1,
        "email": "admin@test.com",
        "full_name": "Test Admin",
        "tenant_id": sample_tenant["id"],
        "is_active": True,
        "role": "admin",
    }


@pytest.fixture
def sample_product(sample_tenant):
    return {
        "id": 1,
        "name": "Test Product",
        "sku": "TST-001",
        "price": 29.99,
        "cost": 15.00,
        "quantity": 100,
        "tenant_id": sample_tenant["id"],
        "category_id": 1,
        "is_active": True,
    }


@pytest.fixture
def sample_invoice(sample_tenant, sample_user):
    return {
        "id": 1,
        "invoice_number": "INV-2026-0001",
        "customer_id": 1,
        "tenant_id": sample_tenant["id"],
        "created_by": sample_user["id"],
        "subtotal": 100.00,
        "tax_amount": 14.00,
        "total": 114.00,
        "status": "draft",
    }


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-jwt-token"}
