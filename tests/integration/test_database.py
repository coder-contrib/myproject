"""Integration tests for database operations."""
import pytest
import pytest_asyncio
from sqlalchemy import text


@pytest.mark.integration
class TestDatabaseConnection:
    @pytest.mark.asyncio
    async def test_database_connectivity(self, db_session):
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_pgvector_extension(self, db_session):
        result = await db_session.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        assert result.scalar() is True

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session):
        await db_session.execute(
            text("CREATE TEMP TABLE test_rollback (id serial PRIMARY KEY, name text)")
        )
        await db_session.execute(
            text("INSERT INTO test_rollback (name) VALUES ('test')")
        )
        result = await db_session.execute(text("SELECT count(*) FROM test_rollback"))
        assert result.scalar() == 1
        await db_session.rollback()


@pytest.mark.integration
class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_tenant_scoped_query(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_products (
                id serial PRIMARY KEY,
                name text,
                tenant_id integer
            )
        """))
        await db_session.execute(text("""
            INSERT INTO test_products (name, tenant_id) VALUES
            ('Product A', 1), ('Product B', 1), ('Product C', 2)
        """))
        result = await db_session.execute(
            text("SELECT count(*) FROM test_products WHERE tenant_id = :tid"),
            {"tid": 1}
        )
        assert result.scalar() == 2

    @pytest.mark.asyncio
    async def test_tenant_cannot_access_other_data(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_invoices (
                id serial PRIMARY KEY,
                invoice_number text,
                tenant_id integer
            )
        """))
        await db_session.execute(text("""
            INSERT INTO test_invoices (invoice_number, tenant_id) VALUES
            ('INV-001', 1), ('INV-002', 2)
        """))
        result = await db_session.execute(
            text("SELECT invoice_number FROM test_invoices WHERE tenant_id = :tid"),
            {"tid": 1}
        )
        invoices = result.scalars().all()
        assert "INV-001" in invoices
        assert "INV-002" not in invoices
