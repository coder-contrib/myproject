import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ai_client
from app.ai.templates import prompt_registry

logger = logging.getLogger("ai.reports")


class AIReportGenerator:
    """AI-powered report generation with natural language summaries."""

    async def generate_executive_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
        period_days: int = 30,
    ) -> dict:
        metrics = await self._gather_executive_metrics(db, tenant_id, period_days)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior business analyst generating an executive summary report. "
                    "Write professionally, be data-driven, highlight key achievements and concerns. "
                    "Return JSON with: title (string), period (string), "
                    "highlights (array of strings), concerns (array of strings), "
                    "kpis (array of {name, value, change_percent, trend: up|down|stable}), "
                    "narrative (string - 2-3 paragraph executive summary), "
                    "recommendations (array of strings)."
                ),
            },
            {
                "role": "user",
                "content": f"Generate executive summary for last {period_days} days.\nMetrics: {json.dumps(metrics, default=str)}",
            },
        ]

        response = await ai_client.chat_completion(messages=messages, response_format={"type": "json_object"})
        report = ai_client.extract_json(response)
        report["generated_at"] = datetime.utcnow().isoformat()
        report["raw_metrics"] = metrics
        return report

    async def generate_sales_report(
        self,
        db: AsyncSession,
        tenant_id: str,
        period_days: int = 30,
        branch_id: Optional[str] = None,
    ) -> dict:
        data = await self._gather_sales_data(db, tenant_id, period_days, branch_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a sales analytics expert. Analyze sales data and generate a comprehensive report. "
                    "Return JSON with: title, period, total_revenue, total_orders, average_order_value, "
                    "top_products (array), top_customers (array), "
                    "daily_breakdown (array of {date, revenue, orders}), "
                    "analysis (string - detailed narrative), "
                    "opportunities (array of strings), risks (array of strings)."
                ),
            },
            {
                "role": "user",
                "content": f"Generate sales report.\nData: {json.dumps(data, default=str)}",
            },
        ]

        response = await ai_client.chat_completion(messages=messages, response_format={"type": "json_object"})
        report = ai_client.extract_json(response)
        report["generated_at"] = datetime.utcnow().isoformat()
        return report

    async def generate_inventory_report(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> dict:
        data = await self._gather_inventory_data(db, tenant_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an inventory management expert. Analyze stock data and provide actionable insights. "
                    "Return JSON with: title, total_products, total_value, "
                    "low_stock_items (array of {name, qty, reorder_suggestion}), "
                    "overstock_items (array of {name, qty, days_supply}), "
                    "turnover_analysis (string), reorder_recommendations (array of strings), "
                    "summary (string - narrative overview)."
                ),
            },
            {
                "role": "user",
                "content": f"Generate inventory report.\nData: {json.dumps(data, default=str)}",
            },
        ]

        response = await ai_client.chat_completion(messages=messages, response_format={"type": "json_object"})
        report = ai_client.extract_json(response)
        report["generated_at"] = datetime.utcnow().isoformat()
        return report

    async def generate_financial_report(
        self,
        db: AsyncSession,
        tenant_id: str,
        period_days: int = 30,
    ) -> dict:
        data = await self._gather_financial_data(db, tenant_id, period_days)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a financial analyst. Generate a financial health report. "
                    "Return JSON with: title, period, revenue, expenses, net_income, "
                    "gross_margin_percent, accounts_receivable, accounts_payable, "
                    "cash_flow_summary (string), financial_ratios (array of {name, value, status: good|warning|critical}), "
                    "narrative (string), action_items (array of strings)."
                ),
            },
            {
                "role": "user",
                "content": f"Generate financial report for last {period_days} days.\nData: {json.dumps(data, default=str)}",
            },
        ]

        response = await ai_client.chat_completion(messages=messages, response_format={"type": "json_object"})
        report = ai_client.extract_json(response)
        report["generated_at"] = datetime.utcnow().isoformat()
        return report

    async def generate_custom_report(
        self,
        db: AsyncSession,
        tenant_id: str,
        description: str,
        data_queries: Optional[list[str]] = None,
    ) -> dict:
        gathered_data = {}
        if data_queries:
            for i, query in enumerate(data_queries):
                normalized = query.strip().upper()
                if not normalized.startswith("SELECT"):
                    continue
                try:
                    result = await db.execute(text(query))
                    rows = result.fetchall()
                    columns = list(result.keys())
                    gathered_data[f"dataset_{i}"] = [dict(zip(columns, row)) for row in rows[:100]]
                except Exception as e:
                    gathered_data[f"dataset_{i}_error"] = str(e)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a business intelligence report generator. Create a structured report based on "
                    "the user's description and provided data. Return JSON with: title, sections (array of "
                    "{heading, content, data_highlights}), summary, recommendations, generated_at."
                ),
            },
            {
                "role": "user",
                "content": f"Report description: {description}\nData: {json.dumps(gathered_data, default=str)}",
            },
        ]

        response = await ai_client.chat_completion(messages=messages, response_format={"type": "json_object"})
        report = ai_client.extract_json(response)
        report["generated_at"] = datetime.utcnow().isoformat()
        return report

    async def _gather_executive_metrics(self, db: AsyncSession, tenant_id: str, period_days: int) -> dict:
        end = datetime.utcnow()
        start = end - timedelta(days=period_days)
        prev_start = start - timedelta(days=period_days)

        queries = {
            "current_revenue": f"SELECT COALESCE(SUM(total), 0) as val FROM sales_invoices WHERE tenant_id = '{tenant_id}' AND date >= '{start}' AND status != 'cancelled'",
            "previous_revenue": f"SELECT COALESCE(SUM(total), 0) as val FROM sales_invoices WHERE tenant_id = '{tenant_id}' AND date >= '{prev_start}' AND date < '{start}' AND status != 'cancelled'",
            "current_orders": f"SELECT COUNT(*) as val FROM sales_invoices WHERE tenant_id = '{tenant_id}' AND date >= '{start}' AND status != 'cancelled'",
            "active_customers": f"SELECT COUNT(DISTINCT customer_id) as val FROM sales_invoices WHERE tenant_id = '{tenant_id}' AND date >= '{start}'",
            "low_stock_count": f"SELECT COUNT(*) as val FROM products WHERE tenant_id = '{tenant_id}' AND stock_qty < 10 AND status = 'active'",
            "total_products": f"SELECT COUNT(*) as val FROM products WHERE tenant_id = '{tenant_id}' AND status = 'active'",
        }

        metrics = {}
        for key, sql in queries.items():
            try:
                result = await db.execute(text(sql))
                row = result.fetchone()
                metrics[key] = float(row.val) if row else 0
            except Exception:
                metrics[key] = 0

        return metrics

    async def _gather_sales_data(self, db: AsyncSession, tenant_id: str, period_days: int, branch_id: Optional[str]) -> dict:
        start = datetime.utcnow() - timedelta(days=period_days)
        branch_filter = f"AND branch_id = '{branch_id}'" if branch_id else ""

        top_products_sql = f"""
            SELECT p.name, SUM(sii.quantity) as qty, SUM(sii.total) as revenue
            FROM sales_invoice_items sii
            JOIN sales_invoices si ON sii.invoice_id = si.id
            JOIN products p ON sii.product_id = p.id
            WHERE si.tenant_id = '{tenant_id}' AND si.date >= '{start}' AND si.status != 'cancelled' {branch_filter}
            GROUP BY p.name ORDER BY revenue DESC LIMIT 10
        """

        top_customers_sql = f"""
            SELECT c.name, COUNT(*) as orders, SUM(si.total) as revenue
            FROM sales_invoices si
            JOIN customers c ON si.customer_id = c.id
            WHERE si.tenant_id = '{tenant_id}' AND si.date >= '{start}' AND si.status != 'cancelled' {branch_filter}
            GROUP BY c.name ORDER BY revenue DESC LIMIT 10
        """

        data = {}
        for key, sql in [("top_products", top_products_sql), ("top_customers", top_customers_sql)]:
            try:
                result = await db.execute(text(sql))
                rows = result.fetchall()
                columns = list(result.keys())
                data[key] = [dict(zip(columns, row)) for row in rows]
            except Exception:
                data[key] = []

        return data

    async def _gather_inventory_data(self, db: AsyncSession, tenant_id: str) -> dict:
        sql = f"""
            SELECT name, sku, category, stock_qty, price, cost,
                   (stock_qty * cost) as stock_value
            FROM products
            WHERE tenant_id = '{tenant_id}' AND status = 'active'
            ORDER BY stock_qty ASC LIMIT 50
        """
        try:
            result = await db.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())
            return {"products": [dict(zip(columns, row)) for row in rows]}
        except Exception:
            return {"products": []}

    async def _gather_financial_data(self, db: AsyncSession, tenant_id: str, period_days: int) -> dict:
        start = datetime.utcnow() - timedelta(days=period_days)

        revenue_sql = f"SELECT COALESCE(SUM(total), 0) as val FROM sales_invoices WHERE tenant_id = '{tenant_id}' AND date >= '{start}' AND status != 'cancelled'"
        expenses_sql = f"SELECT COALESCE(SUM(total), 0) as val FROM purchase_orders WHERE tenant_id = '{tenant_id}' AND date >= '{start}' AND status != 'cancelled'"

        data = {}
        for key, sql in [("revenue", revenue_sql), ("expenses", expenses_sql)]:
            try:
                result = await db.execute(text(sql))
                row = result.fetchone()
                data[key] = float(row.val) if row else 0
            except Exception:
                data[key] = 0

        return data
