import json
import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import ai_client
from app.ai.templates import prompt_registry
from app.ai.feedback import feedback_collector

logger = logging.getLogger("ai.query_assistant")

DB_SCHEMA_CONTEXT = """
Available tables and key columns:
- products (id, name, sku, category, price, cost, stock_qty, status, tenant_id)
- sales_invoices (id, invoice_number, customer_id, total, tax, status, date, branch_id, tenant_id)
- sales_invoice_items (id, invoice_id, product_id, quantity, unit_price, total)
- customers (id, name, email, phone, type, credit_limit, tenant_id)
- purchase_orders (id, supplier_id, total, status, date, tenant_id)
- inventory_movements (id, product_id, warehouse_id, quantity, type, date, tenant_id)
- accounts (id, name, code, type, balance, tenant_id)
- journal_entries (id, date, reference, total_debit, total_credit, status, tenant_id)
- branches (id, name, code, tenant_id)
- users (id, name, email, role, branch_id, tenant_id)
"""


class QueryAssistant:
    """Natural language to SQL query assistant."""

    async def process_question(
        self,
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        question: str,
        context: Optional[dict] = None,
    ) -> dict:
        template = prompt_registry.get("query_assistant")
        system_prompt = template.render(
            schema=DB_SCHEMA_CONTEXT,
            tenant_id=tenant_id,
            context=json.dumps(context or {}),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        response = await ai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
        )

        result = ai_client.extract_json(response)
        sql_query = result.get("sql")
        explanation = result.get("explanation", "")
        confidence = result.get("confidence", 0.5)

        if not sql_query:
            return {
                "success": False,
                "answer": result.get("answer", "I couldn't generate a query for that question."),
                "explanation": explanation,
            }

        # Safety: only allow SELECT statements
        normalized = sql_query.strip().upper()
        if not normalized.startswith("SELECT"):
            return {
                "success": False,
                "answer": "Only read queries are supported for safety.",
                "explanation": "The AI attempted to generate a non-SELECT statement.",
            }

        # Inject tenant isolation
        safe_sql = self._inject_tenant_filter(sql_query, tenant_id)

        try:
            query_result = await db.execute(text(safe_sql))
            rows = query_result.fetchall()
            columns = list(query_result.keys()) if rows else []

            data = [dict(zip(columns, row)) for row in rows[:100]]

            # Generate natural language answer from results
            answer = await self._generate_answer(question, data, explanation)

            return {
                "success": True,
                "answer": answer,
                "sql": safe_sql,
                "data": data,
                "row_count": len(rows),
                "confidence": confidence,
                "explanation": explanation,
            }
        except Exception as e:
            logger.error("Query execution failed: %s | SQL: %s", str(e), safe_sql)
            return {
                "success": False,
                "answer": "The generated query could not be executed.",
                "sql": safe_sql,
                "error": str(e),
            }

    async def _generate_answer(self, question: str, data: list[dict], explanation: str) -> str:
        if not data:
            return "No results found for your query."

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful data analyst. Given a user's question and query results, "
                    "provide a clear, concise natural language answer. Use specific numbers. "
                    "Keep the answer under 3 sentences unless the data requires more detail."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nResults ({len(data)} rows): {json.dumps(data[:20], default=str)}",
            },
        ]

        response = await ai_client.chat_completion(messages=messages, max_tokens=500)
        return ai_client.extract_content(response)

    def _inject_tenant_filter(self, sql: str, tenant_id: str) -> str:
        if "tenant_id" not in sql.lower():
            if "WHERE" in sql.upper():
                sql = sql.replace("WHERE", f"WHERE tenant_id = '{tenant_id}' AND", 1)
            else:
                parts = sql.rsplit("GROUP BY", 1)
                if len(parts) == 2:
                    sql = parts[0] + f" WHERE tenant_id = '{tenant_id}' GROUP BY" + parts[1]
                else:
                    parts = sql.rsplit("ORDER BY", 1)
                    if len(parts) == 2:
                        sql = parts[0] + f" WHERE tenant_id = '{tenant_id}' ORDER BY" + parts[1]
                    else:
                        sql += f" WHERE tenant_id = '{tenant_id}'"
        return sql

    async def suggest_questions(self, tenant_id: str, context: Optional[str] = None) -> list[str]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an ERP analytics assistant. Suggest 5 useful business questions "
                    "the user could ask about their data. Return JSON array of strings."
                ),
            },
            {
                "role": "user",
                "content": f"Context: {context or 'General ERP dashboard'}. Suggest analytical questions.",
            },
        ]

        response = await ai_client.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
            max_tokens=500,
        )
        result = ai_client.extract_json(response)
        return result.get("questions", [])
