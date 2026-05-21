"""Integration tests for materialized views."""
import pytest
from sqlalchemy import text


@pytest.mark.integration
class TestMaterializedViews:
    @pytest.mark.asyncio
    async def test_create_daily_sales_view(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_sales (
                id serial PRIMARY KEY,
                sale_date date NOT NULL,
                total numeric(15,2) NOT NULL,
                tenant_id integer NOT NULL
            )
        """))
        await db_session.execute(text("""
            INSERT INTO test_sales (sale_date, total, tenant_id) VALUES
            ('2026-01-01', 150.00, 1),
            ('2026-01-01', 200.00, 1),
            ('2026-01-02', 300.00, 1),
            ('2026-01-01', 500.00, 2)
        """))
        result = await db_session.execute(text("""
            SELECT sale_date, SUM(total) as daily_total, COUNT(*) as num_sales
            FROM test_sales
            WHERE tenant_id = 1
            GROUP BY sale_date
            ORDER BY sale_date
        """))
        rows = result.fetchall()
        assert len(rows) == 2
        assert float(rows[0].daily_total) == 350.00
        assert rows[0].num_sales == 2

    @pytest.mark.asyncio
    async def test_product_performance_aggregation(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_sale_items (
                id serial PRIMARY KEY,
                product_id integer,
                product_name text,
                quantity integer,
                unit_price numeric(15,2),
                tenant_id integer
            )
        """))
        await db_session.execute(text("""
            INSERT INTO test_sale_items (product_id, product_name, quantity, unit_price, tenant_id) VALUES
            (1, 'Widget A', 10, 25.00, 1),
            (1, 'Widget A', 5, 25.00, 1),
            (2, 'Widget B', 3, 50.00, 1),
            (1, 'Widget A', 2, 25.00, 2)
        """))
        result = await db_session.execute(text("""
            SELECT product_name, SUM(quantity) as total_qty,
                   SUM(quantity * unit_price) as total_revenue
            FROM test_sale_items
            WHERE tenant_id = 1
            GROUP BY product_id, product_name
            ORDER BY total_revenue DESC
        """))
        rows = result.fetchall()
        assert len(rows) == 2
        assert rows[0].product_name == "Widget A"
        assert rows[0].total_qty == 15
        assert float(rows[0].total_revenue) == 375.00

    @pytest.mark.asyncio
    async def test_customer_lifetime_value(self, db_session):
        await db_session.execute(text("""
            CREATE TEMP TABLE test_customer_sales (
                id serial PRIMARY KEY,
                customer_id integer,
                customer_name text,
                total numeric(15,2),
                sale_date date,
                tenant_id integer
            )
        """))
        await db_session.execute(text("""
            INSERT INTO test_customer_sales (customer_id, customer_name, total, sale_date, tenant_id) VALUES
            (1, 'Customer A', 500.00, '2026-01-01', 1),
            (1, 'Customer A', 750.00, '2026-02-01', 1),
            (1, 'Customer A', 300.00, '2026-03-01', 1),
            (2, 'Customer B', 1000.00, '2026-01-15', 1)
        """))
        result = await db_session.execute(text("""
            SELECT customer_name,
                   COUNT(*) as purchase_count,
                   SUM(total) as lifetime_value,
                   MIN(sale_date) as first_purchase,
                   MAX(sale_date) as last_purchase
            FROM test_customer_sales
            WHERE tenant_id = 1
            GROUP BY customer_id, customer_name
            ORDER BY lifetime_value DESC
        """))
        rows = result.fetchall()
        assert len(rows) == 2
        assert rows[0].customer_name == "Customer A"
        assert float(rows[0].lifetime_value) == 1550.00
        assert rows[0].purchase_count == 3
