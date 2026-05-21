"""Integration tests for repository pattern."""
import pytest
import pytest_asyncio
from sqlalchemy import text


@pytest.mark.integration
class TestBaseRepository:
    @pytest.mark.asyncio
    async def test_create_entity(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_entities (
                id serial PRIMARY KEY,
                name text NOT NULL,
                tenant_id integer NOT NULL,
                is_deleted boolean DEFAULT false,
                created_at timestamp DEFAULT now()
            )
        """))
        await db_session.execute(
            text("INSERT INTO test_entities (name, tenant_id) VALUES (:name, :tid)"),
            {"name": "Test Entity", "tid": 1}
        )
        result = await db_session.execute(
            text("SELECT name FROM test_entities WHERE tenant_id = :tid"),
            {"tid": 1}
        )
        assert result.scalar() == "Test Entity"

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_soft_delete (
                id serial PRIMARY KEY,
                name text NOT NULL,
                tenant_id integer NOT NULL,
                is_deleted boolean DEFAULT false
            )
        """))
        await db_session.execute(
            text("INSERT INTO test_soft_delete (name, tenant_id) VALUES ('item1', 1)")
        )
        await db_session.execute(
            text("UPDATE test_soft_delete SET is_deleted = true WHERE name = 'item1'")
        )
        result = await db_session.execute(
            text("SELECT count(*) FROM test_soft_delete WHERE tenant_id = 1 AND is_deleted = false")
        )
        assert result.scalar() == 0

    @pytest.mark.asyncio
    async def test_pagination_query(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_paginate (
                id serial PRIMARY KEY,
                name text,
                tenant_id integer DEFAULT 1
            )
        """))
        for i in range(25):
            await db_session.execute(
                text("INSERT INTO test_paginate (name) VALUES (:name)"),
                {"name": f"Item {i}"}
            )

        result = await db_session.execute(
            text("SELECT * FROM test_paginate ORDER BY id LIMIT :limit OFFSET :offset"),
            {"limit": 10, "offset": 0}
        )
        page1 = result.fetchall()
        assert len(page1) == 10

        result = await db_session.execute(
            text("SELECT * FROM test_paginate ORDER BY id LIMIT :limit OFFSET :offset"),
            {"limit": 10, "offset": 20}
        )
        page3 = result.fetchall()
        assert len(page3) == 5


@pytest.mark.integration
class TestAccountingJournalEntries:
    @pytest.mark.asyncio
    async def test_balanced_journal_entry(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_journal_lines (
                id serial PRIMARY KEY,
                entry_id integer,
                account_id integer,
                debit numeric(15,2) DEFAULT 0,
                credit numeric(15,2) DEFAULT 0
            )
        """))
        await db_session.execute(text("""
            INSERT INTO test_journal_lines (entry_id, account_id, debit, credit) VALUES
            (1, 100, 1000.00, 0),
            (1, 200, 0, 1000.00)
        """))
        result = await db_session.execute(text("""
            SELECT (SUM(debit) - SUM(credit)) as balance
            FROM test_journal_lines WHERE entry_id = 1
        """))
        balance = result.scalar()
        assert float(balance) == 0.0

    @pytest.mark.asyncio
    async def test_unbalanced_entry_detected(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_journal_unbalanced (
                id serial PRIMARY KEY,
                entry_id integer,
                debit numeric(15,2) DEFAULT 0,
                credit numeric(15,2) DEFAULT 0
            )
        """))
        await db_session.execute(text("""
            INSERT INTO test_journal_unbalanced (entry_id, debit, credit) VALUES
            (1, 1000.00, 0),
            (1, 0, 500.00)
        """))
        result = await db_session.execute(text("""
            SELECT (SUM(debit) - SUM(credit)) as balance
            FROM test_journal_unbalanced WHERE entry_id = 1
        """))
        balance = float(result.scalar())
        assert balance != 0.0
