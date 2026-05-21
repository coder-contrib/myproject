import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("reports.views")


MATERIALIZED_VIEWS = {
    "mv_daily_sales": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_sales AS
        SELECT
            tenant_id,
            branch_id,
            DATE(date) as sale_date,
            COUNT(*) as order_count,
            SUM(total) as total_revenue,
            SUM(tax) as total_tax,
            AVG(total) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM sales_invoices
        WHERE status NOT IN ('cancelled', 'draft')
        GROUP BY tenant_id, branch_id, DATE(date)
        WITH DATA;
    """,
    "mv_product_performance": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_product_performance AS
        SELECT
            si.tenant_id,
            p.id as product_id,
            p.name as product_name,
            p.sku,
            p.category,
            SUM(sii.quantity) as total_qty_sold,
            SUM(sii.total) as total_revenue,
            COUNT(DISTINCT si.id) as order_appearances,
            COUNT(DISTINCT si.customer_id) as unique_buyers,
            AVG(sii.unit_price) as avg_selling_price,
            MAX(si.date) as last_sold_date
        FROM sales_invoice_items sii
        JOIN sales_invoices si ON sii.invoice_id = si.id
        JOIN products p ON sii.product_id = p.id
        WHERE si.status NOT IN ('cancelled', 'draft')
        GROUP BY si.tenant_id, p.id, p.name, p.sku, p.category
        WITH DATA;
    """,
    "mv_customer_lifetime": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_customer_lifetime AS
        SELECT
            si.tenant_id,
            c.id as customer_id,
            c.name as customer_name,
            c.type as customer_type,
            COUNT(si.id) as total_orders,
            SUM(si.total) as lifetime_value,
            AVG(si.total) as avg_order_value,
            MIN(si.date) as first_order,
            MAX(si.date) as last_order,
            EXTRACT(DAY FROM MAX(si.date) - MIN(si.date)) as customer_age_days
        FROM customers c
        JOIN sales_invoices si ON si.customer_id = c.id
        WHERE si.status NOT IN ('cancelled', 'draft')
        GROUP BY si.tenant_id, c.id, c.name, c.type
        WITH DATA;
    """,
    "mv_inventory_status": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_inventory_status AS
        SELECT
            p.tenant_id,
            p.id as product_id,
            p.name,
            p.sku,
            p.category,
            p.stock_qty,
            p.cost,
            p.price,
            (p.stock_qty * p.cost) as stock_value,
            (p.price - p.cost) as margin_per_unit,
            CASE
                WHEN p.stock_qty <= 0 THEN 'out_of_stock'
                WHEN p.stock_qty <= 10 THEN 'low_stock'
                WHEN p.stock_qty <= 50 THEN 'normal'
                ELSE 'overstock'
            END as stock_status
        FROM products p
        WHERE p.status = 'active'
        WITH DATA;
    """,
    "mv_monthly_financials": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_financials AS
        SELECT
            tenant_id,
            DATE_TRUNC('month', date) as month,
            SUM(CASE WHEN type = 'income' THEN total ELSE 0 END) as income,
            SUM(CASE WHEN type = 'expense' THEN total ELSE 0 END) as expenses,
            SUM(CASE WHEN type = 'income' THEN total ELSE -total END) as net_income
        FROM (
            SELECT tenant_id, date, total, 'income' as type
            FROM sales_invoices WHERE status NOT IN ('cancelled', 'draft')
            UNION ALL
            SELECT tenant_id, date, total, 'expense' as type
            FROM purchase_orders WHERE status NOT IN ('cancelled', 'draft')
        ) combined
        GROUP BY tenant_id, DATE_TRUNC('month', date)
        WITH DATA;
    """,
}

VIEW_INDEXES = {
    "mv_daily_sales": [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_sales ON mv_daily_sales(tenant_id, branch_id, sale_date);",
    ],
    "mv_product_performance": [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_product_perf ON mv_product_performance(tenant_id, product_id);",
    ],
    "mv_customer_lifetime": [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_customer_lt ON mv_customer_lifetime(tenant_id, customer_id);",
    ],
    "mv_inventory_status": [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_inventory ON mv_inventory_status(tenant_id, product_id);",
    ],
    "mv_monthly_financials": [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_monthly_fin ON mv_monthly_financials(tenant_id, month);",
    ],
}


class MaterializedViewManager:
    """Manages PostgreSQL materialized views for reporting performance."""

    async def create_all(self, db: AsyncSession):
        for name, sql in MATERIALIZED_VIEWS.items():
            try:
                await db.execute(text(sql))
                for idx_sql in VIEW_INDEXES.get(name, []):
                    await db.execute(text(idx_sql))
                logger.info("Materialized view created: %s", name)
            except Exception as e:
                logger.warning("Error creating view %s: %s", name, str(e))
        await db.commit()

    async def refresh(self, db: AsyncSession, view_name: Optional[str] = None, concurrently: bool = True):
        concurrent_clause = "CONCURRENTLY" if concurrently else ""

        if view_name:
            if view_name not in MATERIALIZED_VIEWS:
                raise ValueError(f"Unknown materialized view: {view_name}")
            await db.execute(text(f"REFRESH MATERIALIZED VIEW {concurrent_clause} {view_name}"))
            await db.commit()
            logger.info("Refreshed view: %s", view_name)
        else:
            for name in MATERIALIZED_VIEWS:
                try:
                    await db.execute(text(f"REFRESH MATERIALIZED VIEW {concurrent_clause} {name}"))
                    logger.info("Refreshed view: %s", name)
                except Exception as e:
                    logger.warning("Failed to refresh %s: %s", name, str(e))
            await db.commit()

    async def drop(self, db: AsyncSession, view_name: str):
        if view_name not in MATERIALIZED_VIEWS:
            raise ValueError(f"Unknown materialized view: {view_name}")
        await db.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {view_name}"))
        await db.commit()
        logger.info("Dropped view: %s", view_name)

    async def get_status(self, db: AsyncSession) -> list[dict]:
        sql = """
            SELECT schemaname, matviewname, ispopulated
            FROM pg_matviews
            WHERE matviewname LIKE 'mv_%'
            ORDER BY matviewname
        """
        try:
            result = await db.execute(text(sql))
            rows = result.fetchall()
            return [
                {
                    "name": row.matviewname,
                    "schema": row.schemaname,
                    "populated": row.ispopulated,
                }
                for row in rows
            ]
        except Exception:
            return []

    async def query_view(
        self,
        db: AsyncSession,
        view_name: str,
        tenant_id: str,
        filters: Optional[dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        if view_name not in MATERIALIZED_VIEWS:
            raise ValueError(f"Unknown materialized view: {view_name}")

        sql = f"SELECT * FROM {view_name} WHERE tenant_id = :tenant_id"
        params = {"tenant_id": tenant_id}

        if filters:
            for key, value in filters.items():
                sql += f" AND {key} = :{key}"
                params[key] = value

        sql += f" LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]


view_manager = MaterializedViewManager()
