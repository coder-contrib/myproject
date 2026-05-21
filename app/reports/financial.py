import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.reports.config import report_config

logger = logging.getLogger("reports.financial")


class FinancialReports:
    """Standard financial report generation."""

    async def profit_and_loss(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        # Revenue
        revenue_sql = f"""
            SELECT
                COALESCE(SUM(total), 0) as gross_revenue,
                COALESCE(SUM(tax), 0) as tax_collected,
                COALESCE(SUM(discount), 0) as discounts_given,
                COUNT(*) as invoice_count
            FROM sales_invoices
            WHERE tenant_id = '{tenant_id}'
              AND date >= '{start_date}' AND date <= '{end_date}'
              AND status NOT IN ('cancelled', 'draft')
        """

        # Cost of Goods Sold
        cogs_sql = f"""
            SELECT COALESCE(SUM(sii.quantity * p.cost), 0) as cogs
            FROM sales_invoice_items sii
            JOIN sales_invoices si ON sii.invoice_id = si.id
            JOIN products p ON sii.product_id = p.id
            WHERE si.tenant_id = '{tenant_id}'
              AND si.date >= '{start_date}' AND si.date <= '{end_date}'
              AND si.status NOT IN ('cancelled', 'draft')
        """

        # Operating Expenses
        expenses_sql = f"""
            SELECT
                COALESCE(SUM(total), 0) as total_expenses,
                COUNT(*) as expense_count
            FROM purchase_orders
            WHERE tenant_id = '{tenant_id}'
              AND date >= '{start_date}' AND date <= '{end_date}'
              AND status NOT IN ('cancelled', 'draft')
        """

        revenue_data = {}
        cogs_data = {}
        expense_data = {}

        try:
            result = await db.execute(text(revenue_sql))
            row = result.fetchone()
            revenue_data = {
                "gross_revenue": float(row.gross_revenue) if row else 0,
                "tax_collected": float(row.tax_collected) if row else 0,
                "discounts_given": float(row.discounts_given) if row else 0,
                "invoice_count": row.invoice_count if row else 0,
            }
        except Exception as e:
            logger.warning("Revenue query failed: %s", str(e))

        try:
            result = await db.execute(text(cogs_sql))
            row = result.fetchone()
            cogs_data = {"cogs": float(row.cogs) if row else 0}
        except Exception as e:
            logger.warning("COGS query failed: %s", str(e))

        try:
            result = await db.execute(text(expenses_sql))
            row = result.fetchone()
            expense_data = {
                "total_expenses": float(row.total_expenses) if row else 0,
                "expense_count": row.expense_count if row else 0,
            }
        except Exception as e:
            logger.warning("Expenses query failed: %s", str(e))

        gross_revenue = revenue_data.get("gross_revenue", 0)
        cogs = cogs_data.get("cogs", 0)
        total_expenses = expense_data.get("total_expenses", 0)
        gross_profit = gross_revenue - cogs
        net_income = gross_profit - total_expenses
        gross_margin = (gross_profit / gross_revenue * 100) if gross_revenue else 0
        net_margin = (net_income / gross_revenue * 100) if gross_revenue else 0

        return {
            "report_type": "profit_and_loss",
            "period": {"start": start_date, "end": end_date},
            "revenue": revenue_data,
            "cost_of_goods_sold": cogs,
            "gross_profit": gross_profit,
            "gross_margin_percent": round(gross_margin, 2),
            "operating_expenses": total_expenses,
            "net_income": net_income,
            "net_margin_percent": round(net_margin, 2),
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def balance_sheet(
        self,
        db: AsyncSession,
        tenant_id: str,
        as_of_date: Optional[str] = None,
    ) -> dict:
        date = as_of_date or str(datetime.utcnow().date())

        # Assets
        assets_sql = f"""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'asset' AND subtype = 'current' THEN balance ELSE 0 END), 0) as current_assets,
                COALESCE(SUM(CASE WHEN type = 'asset' AND subtype = 'fixed' THEN balance ELSE 0 END), 0) as fixed_assets,
                COALESCE(SUM(CASE WHEN type = 'asset' THEN balance ELSE 0 END), 0) as total_assets
            FROM accounts
            WHERE tenant_id = '{tenant_id}'
        """

        # Liabilities
        liabilities_sql = f"""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'liability' AND subtype = 'current' THEN balance ELSE 0 END), 0) as current_liabilities,
                COALESCE(SUM(CASE WHEN type = 'liability' AND subtype = 'long_term' THEN balance ELSE 0 END), 0) as long_term_liabilities,
                COALESCE(SUM(CASE WHEN type = 'liability' THEN balance ELSE 0 END), 0) as total_liabilities
            FROM accounts
            WHERE tenant_id = '{tenant_id}'
        """

        # Equity
        equity_sql = f"""
            SELECT COALESCE(SUM(balance), 0) as total_equity
            FROM accounts
            WHERE tenant_id = '{tenant_id}' AND type = 'equity'
        """

        assets = {}
        liabilities = {}
        equity = {}

        try:
            result = await db.execute(text(assets_sql))
            row = result.fetchone()
            assets = {
                "current_assets": float(row.current_assets),
                "fixed_assets": float(row.fixed_assets),
                "total_assets": float(row.total_assets),
            }
        except Exception:
            pass

        try:
            result = await db.execute(text(liabilities_sql))
            row = result.fetchone()
            liabilities = {
                "current_liabilities": float(row.current_liabilities),
                "long_term_liabilities": float(row.long_term_liabilities),
                "total_liabilities": float(row.total_liabilities),
            }
        except Exception:
            pass

        try:
            result = await db.execute(text(equity_sql))
            row = result.fetchone()
            equity = {"total_equity": float(row.total_equity)}
        except Exception:
            pass

        return {
            "report_type": "balance_sheet",
            "as_of_date": date,
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "balance_check": {
                "assets_total": assets.get("total_assets", 0),
                "liabilities_plus_equity": liabilities.get("total_liabilities", 0) + equity.get("total_equity", 0),
                "balanced": abs(assets.get("total_assets", 0) - (liabilities.get("total_liabilities", 0) + equity.get("total_equity", 0))) < 0.01,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def cash_flow(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        # Cash inflows (payments received)
        inflows_sql = f"""
            SELECT
                COALESCE(SUM(amount), 0) as total_inflows,
                COUNT(*) as payment_count
            FROM payments
            WHERE tenant_id = '{tenant_id}'
              AND date >= '{start_date}' AND date <= '{end_date}'
              AND status = 'completed' AND type = 'received'
        """

        # Cash outflows (payments made)
        outflows_sql = f"""
            SELECT
                COALESCE(SUM(amount), 0) as total_outflows,
                COUNT(*) as payment_count
            FROM payments
            WHERE tenant_id = '{tenant_id}'
              AND date >= '{start_date}' AND date <= '{end_date}'
              AND status = 'completed' AND type = 'made'
        """

        inflows = {}
        outflows = {}

        try:
            result = await db.execute(text(inflows_sql))
            row = result.fetchone()
            inflows = {"total": float(row.total_inflows), "count": row.payment_count}
        except Exception:
            inflows = {"total": 0, "count": 0}

        try:
            result = await db.execute(text(outflows_sql))
            row = result.fetchone()
            outflows = {"total": float(row.total_outflows), "count": row.payment_count}
        except Exception:
            outflows = {"total": 0, "count": 0}

        net_cash_flow = inflows["total"] - outflows["total"]

        return {
            "report_type": "cash_flow",
            "period": {"start": start_date, "end": end_date},
            "inflows": inflows,
            "outflows": outflows,
            "net_cash_flow": net_cash_flow,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def accounts_receivable_aging(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> dict:
        sql = f"""
            SELECT
                c.name as customer_name,
                si.invoice_number,
                si.total,
                COALESCE(si.paid_amount, 0) as paid,
                (si.total - COALESCE(si.paid_amount, 0)) as outstanding,
                si.date as invoice_date,
                si.due_date,
                EXTRACT(DAY FROM NOW() - si.due_date) as days_overdue,
                CASE
                    WHEN NOW() <= si.due_date THEN 'current'
                    WHEN EXTRACT(DAY FROM NOW() - si.due_date) <= 30 THEN '1-30 days'
                    WHEN EXTRACT(DAY FROM NOW() - si.due_date) <= 60 THEN '31-60 days'
                    WHEN EXTRACT(DAY FROM NOW() - si.due_date) <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket
            FROM sales_invoices si
            JOIN customers c ON si.customer_id = c.id
            WHERE si.tenant_id = '{tenant_id}'
              AND si.status = 'sent'
              AND si.total > COALESCE(si.paid_amount, 0)
            ORDER BY days_overdue DESC
        """

        try:
            result = await db.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())
            items = [dict(zip(columns, row)) for row in rows]

            # Summarize by bucket
            buckets = {}
            for item in items:
                bucket = item["aging_bucket"]
                if bucket not in buckets:
                    buckets[bucket] = {"count": 0, "total": 0}
                buckets[bucket]["count"] += 1
                buckets[bucket]["total"] += float(item["outstanding"])

            return {
                "report_type": "accounts_receivable_aging",
                "summary": buckets,
                "total_outstanding": sum(b["total"] for b in buckets.values()),
                "items": items[:50],
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"report_type": "accounts_receivable_aging", "error": str(e)}

    async def tax_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        sales_tax_sql = f"""
            SELECT
                COALESCE(SUM(tax), 0) as tax_collected,
                COALESCE(SUM(total), 0) as taxable_revenue,
                COUNT(*) as invoice_count
            FROM sales_invoices
            WHERE tenant_id = '{tenant_id}'
              AND date >= '{start_date}' AND date <= '{end_date}'
              AND status NOT IN ('cancelled', 'draft')
        """

        purchase_tax_sql = f"""
            SELECT
                COALESCE(SUM(tax), 0) as tax_paid,
                COALESCE(SUM(total), 0) as total_purchases
            FROM purchase_orders
            WHERE tenant_id = '{tenant_id}'
              AND date >= '{start_date}' AND date <= '{end_date}'
              AND status NOT IN ('cancelled', 'draft')
        """

        sales_tax = {}
        purchase_tax = {}

        try:
            result = await db.execute(text(sales_tax_sql))
            row = result.fetchone()
            sales_tax = {
                "collected": float(row.tax_collected),
                "taxable_revenue": float(row.taxable_revenue),
                "invoices": row.invoice_count,
            }
        except Exception:
            sales_tax = {"collected": 0, "taxable_revenue": 0, "invoices": 0}

        try:
            result = await db.execute(text(purchase_tax_sql))
            row = result.fetchone()
            purchase_tax = {
                "paid": float(row.tax_paid),
                "total_purchases": float(row.total_purchases),
            }
        except Exception:
            purchase_tax = {"paid": 0, "total_purchases": 0}

        net_tax = sales_tax["collected"] - purchase_tax["paid"]

        return {
            "report_type": "tax_summary",
            "period": {"start": start_date, "end": end_date},
            "sales_tax": sales_tax,
            "purchase_tax": purchase_tax,
            "net_tax_liability": net_tax,
            "generated_at": datetime.utcnow().isoformat(),
        }


financial_reports = FinancialReports()
