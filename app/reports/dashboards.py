import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("reports.dashboards")


class KPIDashboard:
    """Real-time KPI dashboard data aggregation."""

    async def get_overview(
        self,
        db: AsyncSession,
        tenant_id: str,
        branch_id: Optional[str] = None,
    ) -> dict:
        branch_filter = f"AND branch_id = '{branch_id}'" if branch_id else ""
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)

        queries = {
            "today_revenue": f"""
                SELECT COALESCE(SUM(total), 0) as val FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND DATE(date) = '{today}'
                AND status NOT IN ('cancelled', 'draft') {branch_filter}
            """,
            "today_orders": f"""
                SELECT COUNT(*) as val FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND DATE(date) = '{today}'
                AND status NOT IN ('cancelled', 'draft') {branch_filter}
            """,
            "month_revenue": f"""
                SELECT COALESCE(SUM(total), 0) as val FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND date >= '{month_start}'
                AND status NOT IN ('cancelled', 'draft') {branch_filter}
            """,
            "month_orders": f"""
                SELECT COUNT(*) as val FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND date >= '{month_start}'
                AND status NOT IN ('cancelled', 'draft') {branch_filter}
            """,
            "pending_orders": f"""
                SELECT COUNT(*) as val FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND status = 'pending' {branch_filter}
            """,
            "low_stock_items": f"""
                SELECT COUNT(*) as val FROM products
                WHERE tenant_id = '{tenant_id}' AND stock_qty <= 10 AND status = 'active'
            """,
            "active_customers": f"""
                SELECT COUNT(DISTINCT customer_id) as val FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND date >= '{month_start}' {branch_filter}
            """,
            "accounts_receivable": f"""
                SELECT COALESCE(SUM(total - COALESCE(paid_amount, 0)), 0) as val
                FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND status = 'sent'
            """,
        }

        kpis = {}
        for key, sql in queries.items():
            try:
                result = await db.execute(text(sql))
                row = result.fetchone()
                kpis[key] = float(row.val) if row and row.val else 0
            except Exception as e:
                logger.warning("KPI query failed for %s: %s", key, str(e))
                kpis[key] = 0

        return {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "generated_at": datetime.utcnow().isoformat(),
            "kpis": kpis,
        }

    async def get_sales_trend(
        self,
        db: AsyncSession,
        tenant_id: str,
        days: int = 30,
        branch_id: Optional[str] = None,
    ) -> dict:
        branch_filter = f"AND branch_id = '{branch_id}'" if branch_id else ""
        start = datetime.utcnow() - timedelta(days=days)

        sql = f"""
            SELECT DATE(date) as day,
                   COUNT(*) as order_count,
                   COALESCE(SUM(total), 0) as revenue,
                   COALESCE(AVG(total), 0) as avg_order_value
            FROM sales_invoices
            WHERE tenant_id = '{tenant_id}'
              AND date >= '{start}'
              AND status NOT IN ('cancelled', 'draft') {branch_filter}
            GROUP BY DATE(date)
            ORDER BY day
        """

        result = await db.execute(text(sql))
        rows = result.fetchall()

        return {
            "period_days": days,
            "data": [
                {
                    "date": str(row.day),
                    "orders": row.order_count,
                    "revenue": float(row.revenue),
                    "avg_order_value": float(row.avg_order_value),
                }
                for row in rows
            ],
        }

    async def get_top_products(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 10,
        days: int = 30,
        branch_id: Optional[str] = None,
    ) -> list[dict]:
        branch_filter = f"AND si.branch_id = '{branch_id}'" if branch_id else ""
        start = datetime.utcnow() - timedelta(days=days)

        sql = f"""
            SELECT p.id, p.name, p.sku, p.category,
                   SUM(sii.quantity) as total_qty,
                   SUM(sii.total) as total_revenue,
                   COUNT(DISTINCT si.id) as order_count
            FROM sales_invoice_items sii
            JOIN sales_invoices si ON sii.invoice_id = si.id
            JOIN products p ON sii.product_id = p.id
            WHERE si.tenant_id = '{tenant_id}'
              AND si.date >= '{start}'
              AND si.status NOT IN ('cancelled', 'draft') {branch_filter}
            GROUP BY p.id, p.name, p.sku, p.category
            ORDER BY total_revenue DESC
            LIMIT {limit}
        """

        result = await db.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def get_top_customers(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 10,
        days: int = 30,
    ) -> list[dict]:
        start = datetime.utcnow() - timedelta(days=days)

        sql = f"""
            SELECT c.id, c.name, c.email, c.type,
                   COUNT(si.id) as order_count,
                   COALESCE(SUM(si.total), 0) as total_spent,
                   MAX(si.date) as last_order
            FROM customers c
            JOIN sales_invoices si ON si.customer_id = c.id
            WHERE si.tenant_id = '{tenant_id}'
              AND si.date >= '{start}'
              AND si.status NOT IN ('cancelled', 'draft')
            GROUP BY c.id, c.name, c.email, c.type
            ORDER BY total_spent DESC
            LIMIT {limit}
        """

        result = await db.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]

    async def get_inventory_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> dict:
        sql = f"""
            SELECT
                COUNT(*) as total_products,
                COUNT(CASE WHEN stock_qty <= 0 THEN 1 END) as out_of_stock,
                COUNT(CASE WHEN stock_qty > 0 AND stock_qty <= 10 THEN 1 END) as low_stock,
                COUNT(CASE WHEN stock_qty > 10 THEN 1 END) as in_stock,
                COALESCE(SUM(stock_qty * cost), 0) as total_value,
                COALESCE(AVG(stock_qty), 0) as avg_stock_level
            FROM products
            WHERE tenant_id = '{tenant_id}' AND status = 'active'
        """

        result = await db.execute(text(sql))
        row = result.fetchone()

        if not row:
            return {"total_products": 0}

        return {
            "total_products": row.total_products,
            "out_of_stock": row.out_of_stock,
            "low_stock": row.low_stock,
            "in_stock": row.in_stock,
            "total_value": float(row.total_value),
            "avg_stock_level": float(row.avg_stock_level),
        }

    async def get_hourly_sales(
        self,
        db: AsyncSession,
        tenant_id: str,
        date: Optional[str] = None,
        branch_id: Optional[str] = None,
    ) -> list[dict]:
        target_date = date or str(datetime.utcnow().date())
        branch_filter = f"AND branch_id = '{branch_id}'" if branch_id else ""

        sql = f"""
            SELECT EXTRACT(HOUR FROM date) as hour,
                   COUNT(*) as orders,
                   COALESCE(SUM(total), 0) as revenue
            FROM sales_invoices
            WHERE tenant_id = '{tenant_id}'
              AND DATE(date) = '{target_date}'
              AND status NOT IN ('cancelled', 'draft') {branch_filter}
            GROUP BY EXTRACT(HOUR FROM date)
            ORDER BY hour
        """

        result = await db.execute(text(sql))
        rows = result.fetchall()

        return [
            {"hour": int(row.hour), "orders": row.orders, "revenue": float(row.revenue)}
            for row in rows
        ]


dashboard_service = KPIDashboard()
