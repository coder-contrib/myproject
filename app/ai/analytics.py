import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ai_client
from app.ai.templates import prompt_registry

logger = logging.getLogger("ai.analytics")


class AIAnalytics:
    """AI-powered business analytics."""

    async def detect_trends(
        self,
        db: AsyncSession,
        tenant_id: str,
        metric: str = "revenue",
        period_days: int = 30,
    ) -> dict:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        if metric == "revenue":
            sql = """
                SELECT DATE(date) as day, SUM(total) as value
                FROM sales_invoices
                WHERE tenant_id = :tenant_id AND date >= :start AND date <= :end AND status != 'cancelled'
                GROUP BY DATE(date) ORDER BY day
            """
        elif metric == "orders":
            sql = """
                SELECT DATE(date) as day, COUNT(*) as value
                FROM sales_invoices
                WHERE tenant_id = :tenant_id AND date >= :start AND date <= :end AND status != 'cancelled'
                GROUP BY DATE(date) ORDER BY day
            """
        elif metric == "inventory_movement":
            sql = """
                SELECT DATE(date) as day, SUM(ABS(quantity)) as value
                FROM inventory_movements
                WHERE tenant_id = :tenant_id AND date >= :start AND date <= :end
                GROUP BY DATE(date) ORDER BY day
            """
        else:
            return {"error": f"Unknown metric: {metric}"}

        result = await db.execute(text(sql), {
            "tenant_id": tenant_id,
            "start": start_date,
            "end": end_date,
        })
        rows = result.fetchall()
        data_points = [{"date": str(row.day), "value": float(row.value)} for row in rows]

        if not data_points:
            return {"trends": [], "summary": "No data available for the selected period."}

        analysis = await self._analyze_trends(metric, data_points, period_days)
        return analysis

    async def detect_anomalies(
        self,
        db: AsyncSession,
        tenant_id: str,
        entity_type: str = "sales",
    ) -> dict:
        if entity_type == "sales":
            sql = """
                SELECT si.id, si.invoice_number, si.total, si.date, c.name as customer_name
                FROM sales_invoices si
                LEFT JOIN customers c ON si.customer_id = c.id
                WHERE si.tenant_id = :tenant_id AND si.date >= NOW() - INTERVAL '30 days'
                    AND si.status != 'cancelled'
                ORDER BY si.total DESC LIMIT 50
            """
        elif entity_type == "inventory":
            sql = """
                SELECT p.name, p.stock_qty, p.sku,
                    COALESCE(SUM(CASE WHEN im.type = 'out' THEN im.quantity ELSE 0 END), 0) as total_out
                FROM products p
                LEFT JOIN inventory_movements im ON p.id = im.product_id
                    AND im.date >= NOW() - INTERVAL '30 days'
                WHERE p.tenant_id = :tenant_id AND p.status = 'active'
                GROUP BY p.id, p.name, p.stock_qty, p.sku
                ORDER BY p.stock_qty ASC LIMIT 50
            """
        else:
            return {"error": f"Unknown entity type: {entity_type}"}

        result = await db.execute(text(sql), {"tenant_id": tenant_id})
        rows = result.fetchall()
        columns = list(result.keys())
        data = [dict(zip(columns, row)) for row in rows]

        return await self._detect_anomalies_ai(entity_type, data)

    async def forecast(
        self,
        db: AsyncSession,
        tenant_id: str,
        metric: str = "revenue",
        forecast_days: int = 7,
    ) -> dict:
        sql = """
            SELECT DATE(date) as day, SUM(total) as value
            FROM sales_invoices
            WHERE tenant_id = :tenant_id AND date >= NOW() - INTERVAL '90 days' AND status != 'cancelled'
            GROUP BY DATE(date) ORDER BY day
        """
        result = await db.execute(text(sql), {"tenant_id": tenant_id})
        rows = result.fetchall()
        history = [{"date": str(row.day), "value": float(row.value)} for row in rows]

        if len(history) < 7:
            return {"error": "Insufficient data for forecasting (need at least 7 days)."}

        return await self._generate_forecast(metric, history, forecast_days)

    async def product_recommendations(
        self,
        db: AsyncSession,
        tenant_id: str,
        customer_id: Optional[str] = None,
    ) -> dict:
        if customer_id:
            sql = """
                SELECT p.name, p.category, SUM(sii.quantity) as qty_bought, COUNT(*) as times_bought
                FROM sales_invoice_items sii
                JOIN sales_invoices si ON sii.invoice_id = si.id
                JOIN products p ON sii.product_id = p.id
                WHERE si.tenant_id = :tenant_id AND si.customer_id = :customer_id
                GROUP BY p.name, p.category
                ORDER BY qty_bought DESC LIMIT 20
            """
            params = {"tenant_id": tenant_id, "customer_id": customer_id}
        else:
            sql = """
                SELECT p.name, p.category, SUM(sii.quantity) as qty_sold, COUNT(DISTINCT si.customer_id) as unique_buyers
                FROM sales_invoice_items sii
                JOIN sales_invoices si ON sii.invoice_id = si.id
                JOIN products p ON sii.product_id = p.id
                WHERE si.tenant_id = :tenant_id AND si.date >= NOW() - INTERVAL '30 days'
                GROUP BY p.name, p.category
                ORDER BY qty_sold DESC LIMIT 30
            """
            params = {"tenant_id": tenant_id}

        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        columns = list(result.keys())
        data = [dict(zip(columns, row)) for row in rows]

        return await self._generate_recommendations(data, customer_id)

    async def _analyze_trends(self, metric: str, data_points: list[dict], period_days: int) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a business analytics AI. Analyze the time series data and identify trends. "
                    "Return JSON with: trends (array of {direction, strength, period, description}), "
                    "summary (string), insights (array of strings), recommendations (array of strings)."
                ),
            },
            {
                "role": "user",
                "content": f"Metric: {metric}\nPeriod: last {period_days} days\nData: {json.dumps(data_points)}",
            },
        ]

        response = await ai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
        )
        result = ai_client.extract_json(response)
        result["data_points"] = data_points
        return result

    async def _detect_anomalies_ai(self, entity_type: str, data: list[dict]) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an anomaly detection AI for business data. Analyze the data and identify "
                    "unusual patterns, outliers, or concerning values. Return JSON with: "
                    "anomalies (array of {item, reason, severity: low|medium|high|critical}), "
                    "summary (string), risk_score (0-100)."
                ),
            },
            {
                "role": "user",
                "content": f"Entity type: {entity_type}\nData: {json.dumps(data, default=str)}",
            },
        ]

        response = await ai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
        )
        return ai_client.extract_json(response)

    async def _generate_forecast(self, metric: str, history: list[dict], forecast_days: int) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a business forecasting AI. Based on historical data, predict future values. "
                    "Return JSON with: forecast (array of {date, predicted_value, confidence_lower, confidence_upper}), "
                    "summary (string), confidence_level (low|medium|high), methodology (string)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Metric: {metric}\nForecast days: {forecast_days}\n"
                    f"Historical data ({len(history)} days): {json.dumps(history[-30:])}"
                ),
            },
        ]

        response = await ai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
        )
        return ai_client.extract_json(response)

    async def _generate_recommendations(self, data: list[dict], customer_id: Optional[str]) -> dict:
        context = f"for customer {customer_id}" if customer_id else "across all customers"
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a product recommendation AI for an ERP system. Based on purchase data, "
                    "suggest products and strategies. Return JSON with: "
                    "recommendations (array of {product, reason, confidence}), "
                    "cross_sell (array of strings), upsell (array of strings), summary (string)."
                ),
            },
            {
                "role": "user",
                "content": f"Purchase data {context}: {json.dumps(data, default=str)}",
            },
        ]

        response = await ai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
        )
        return ai_client.extract_json(response)
