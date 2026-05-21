import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("reports.analytics")


class AnalyticsEngine:
    """Advanced analytics queries for business intelligence."""

    async def revenue_breakdown(
        self,
        db: AsyncSession,
        tenant_id: str,
        period_days: int = 30,
        group_by: str = "category",
    ) -> dict:
        start = datetime.utcnow() - timedelta(days=period_days)

        if group_by == "category":
            sql = f"""
                SELECT p.category as group_key,
                       COUNT(DISTINCT si.id) as orders,
                       SUM(sii.quantity) as units_sold,
                       SUM(sii.total) as revenue,
                       SUM(sii.total) / NULLIF(SUM(SUM(sii.total)) OVER(), 0) * 100 as percentage
                FROM sales_invoice_items sii
                JOIN sales_invoices si ON sii.invoice_id = si.id
                JOIN products p ON sii.product_id = p.id
                WHERE si.tenant_id = '{tenant_id}' AND si.date >= '{start}'
                  AND si.status NOT IN ('cancelled', 'draft')
                GROUP BY p.category ORDER BY revenue DESC
            """
        elif group_by == "branch":
            sql = f"""
                SELECT b.name as group_key,
                       COUNT(*) as orders,
                       SUM(si.total) as revenue,
                       SUM(si.total) / NULLIF(SUM(SUM(si.total)) OVER(), 0) * 100 as percentage
                FROM sales_invoices si
                JOIN branches b ON si.branch_id = b.id
                WHERE si.tenant_id = '{tenant_id}' AND si.date >= '{start}'
                  AND si.status NOT IN ('cancelled', 'draft')
                GROUP BY b.name ORDER BY revenue DESC
            """
        elif group_by == "customer_type":
            sql = f"""
                SELECT c.type as group_key,
                       COUNT(*) as orders,
                       SUM(si.total) as revenue,
                       COUNT(DISTINCT si.customer_id) as unique_customers
                FROM sales_invoices si
                JOIN customers c ON si.customer_id = c.id
                WHERE si.tenant_id = '{tenant_id}' AND si.date >= '{start}'
                  AND si.status NOT IN ('cancelled', 'draft')
                GROUP BY c.type ORDER BY revenue DESC
            """
        elif group_by == "payment_method":
            sql = f"""
                SELECT payment_method as group_key,
                       COUNT(*) as orders,
                       SUM(amount) as revenue
                FROM payments
                WHERE tenant_id = '{tenant_id}' AND date >= '{start}'
                  AND status = 'completed'
                GROUP BY payment_method ORDER BY revenue DESC
            """
        else:
            return {"error": f"Invalid group_by: {group_by}"}

        result = await db.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())

        return {
            "group_by": group_by,
            "period_days": period_days,
            "data": [dict(zip(columns, row)) for row in rows],
        }

    async def customer_analytics(
        self,
        db: AsyncSession,
        tenant_id: str,
        period_days: int = 90,
    ) -> dict:
        start = datetime.utcnow() - timedelta(days=period_days)

        # Customer acquisition
        acquisition_sql = f"""
            SELECT DATE_TRUNC('week', created_at) as week,
                   COUNT(*) as new_customers
            FROM customers
            WHERE tenant_id = '{tenant_id}' AND created_at >= '{start}'
            GROUP BY DATE_TRUNC('week', created_at)
            ORDER BY week
        """

        # Customer retention (repeat buyers)
        retention_sql = f"""
            SELECT
                COUNT(DISTINCT customer_id) as total_buyers,
                COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END) as repeat_buyers
            FROM (
                SELECT customer_id, COUNT(*) as order_count
                FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND date >= '{start}'
                  AND status NOT IN ('cancelled', 'draft')
                GROUP BY customer_id
            ) sub
        """

        # Revenue per customer segment
        segment_sql = f"""
            SELECT
                CASE
                    WHEN total_spent >= 10000 THEN 'VIP'
                    WHEN total_spent >= 5000 THEN 'High Value'
                    WHEN total_spent >= 1000 THEN 'Regular'
                    ELSE 'Low Value'
                END as segment,
                COUNT(*) as customer_count,
                SUM(total_spent) as segment_revenue
            FROM (
                SELECT customer_id, SUM(total) as total_spent
                FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND date >= '{start}'
                  AND status NOT IN ('cancelled', 'draft')
                GROUP BY customer_id
            ) sub
            GROUP BY segment
            ORDER BY segment_revenue DESC
        """

        data = {}
        for key, sql in [("acquisition", acquisition_sql), ("retention", retention_sql), ("segments", segment_sql)]:
            try:
                result = await db.execute(text(sql))
                rows = result.fetchall()
                columns = list(result.keys())
                data[key] = [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                logger.warning("Analytics query %s failed: %s", key, str(e))
                data[key] = []

        return {"period_days": period_days, **data}

    async def inventory_analytics(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> dict:
        # Stock turnover
        turnover_sql = f"""
            SELECT p.id, p.name, p.sku, p.stock_qty, p.cost,
                   COALESCE(SUM(CASE WHEN im.type = 'out' THEN im.quantity ELSE 0 END), 0) as total_sold_30d,
                   CASE
                       WHEN p.stock_qty > 0 THEN
                           ROUND(p.stock_qty::numeric / NULLIF(
                               COALESCE(SUM(CASE WHEN im.type = 'out' THEN im.quantity ELSE 0 END), 0) / 30.0, 0
                           ), 1)
                       ELSE 0
                   END as days_of_supply
            FROM products p
            LEFT JOIN inventory_movements im ON p.id = im.product_id
                AND im.date >= NOW() - INTERVAL '30 days'
            WHERE p.tenant_id = '{tenant_id}' AND p.status = 'active'
            GROUP BY p.id, p.name, p.sku, p.stock_qty, p.cost
            ORDER BY days_of_supply ASC
            LIMIT 50
        """

        # Dead stock (no movement in 60 days)
        dead_stock_sql = f"""
            SELECT p.id, p.name, p.sku, p.stock_qty, p.cost,
                   (p.stock_qty * p.cost) as value_tied
            FROM products p
            WHERE p.tenant_id = '{tenant_id}' AND p.status = 'active' AND p.stock_qty > 0
              AND p.id NOT IN (
                  SELECT DISTINCT product_id FROM inventory_movements
                  WHERE tenant_id = '{tenant_id}' AND date >= NOW() - INTERVAL '60 days'
              )
            ORDER BY value_tied DESC
            LIMIT 20
        """

        data = {}
        for key, sql in [("turnover", turnover_sql), ("dead_stock", dead_stock_sql)]:
            try:
                result = await db.execute(text(sql))
                rows = result.fetchall()
                columns = list(result.keys())
                data[key] = [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                logger.warning("Inventory analytics %s failed: %s", key, str(e))
                data[key] = []

        return data

    async def sales_comparison(
        self,
        db: AsyncSession,
        tenant_id: str,
        period_days: int = 30,
    ) -> dict:
        """Compare current period vs previous period."""
        end = datetime.utcnow()
        current_start = end - timedelta(days=period_days)
        previous_start = current_start - timedelta(days=period_days)

        sql = f"""
            SELECT
                'current' as period,
                COUNT(*) as orders,
                COALESCE(SUM(total), 0) as revenue,
                COALESCE(AVG(total), 0) as avg_order,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales_invoices
            WHERE tenant_id = '{tenant_id}' AND date >= '{current_start}'
              AND status NOT IN ('cancelled', 'draft')
            UNION ALL
            SELECT
                'previous' as period,
                COUNT(*) as orders,
                COALESCE(SUM(total), 0) as revenue,
                COALESCE(AVG(total), 0) as avg_order,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales_invoices
            WHERE tenant_id = '{tenant_id}' AND date >= '{previous_start}' AND date < '{current_start}'
              AND status NOT IN ('cancelled', 'draft')
        """

        result = await db.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
        periods = {row[0]: dict(zip(columns, row)) for row in rows}

        current = periods.get("current", {})
        previous = periods.get("previous", {})

        def calc_change(current_val, previous_val):
            if not previous_val:
                return None
            return round((current_val - previous_val) / previous_val * 100, 1)

        return {
            "period_days": period_days,
            "current": current,
            "previous": previous,
            "changes": {
                "revenue_change_pct": calc_change(
                    float(current.get("revenue", 0)), float(previous.get("revenue", 0))
                ),
                "orders_change_pct": calc_change(
                    float(current.get("orders", 0)), float(previous.get("orders", 0))
                ),
                "avg_order_change_pct": calc_change(
                    float(current.get("avg_order", 0)), float(previous.get("avg_order", 0))
                ),
            },
        }

    async def cohort_analysis(
        self,
        db: AsyncSession,
        tenant_id: str,
        months: int = 6,
    ) -> dict:
        sql = f"""
            WITH customer_cohorts AS (
                SELECT customer_id,
                       DATE_TRUNC('month', MIN(date)) as cohort_month
                FROM sales_invoices
                WHERE tenant_id = '{tenant_id}' AND status NOT IN ('cancelled', 'draft')
                GROUP BY customer_id
            ),
            monthly_activity AS (
                SELECT si.customer_id,
                       cc.cohort_month,
                       DATE_TRUNC('month', si.date) as activity_month,
                       SUM(si.total) as revenue
                FROM sales_invoices si
                JOIN customer_cohorts cc ON si.customer_id = cc.customer_id
                WHERE si.tenant_id = '{tenant_id}'
                  AND si.date >= NOW() - INTERVAL '{months} months'
                  AND si.status NOT IN ('cancelled', 'draft')
                GROUP BY si.customer_id, cc.cohort_month, DATE_TRUNC('month', si.date)
            )
            SELECT cohort_month,
                   activity_month,
                   COUNT(DISTINCT customer_id) as active_customers,
                   SUM(revenue) as total_revenue
            FROM monthly_activity
            GROUP BY cohort_month, activity_month
            ORDER BY cohort_month, activity_month
        """

        try:
            result = await db.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())
            return {"months": months, "cohorts": [dict(zip(columns, row)) for row in rows]}
        except Exception as e:
            logger.warning("Cohort analysis failed: %s", str(e))
            return {"months": months, "cohorts": [], "error": str(e)}


analytics_engine = AnalyticsEngine()
