import os
import io
import csv
import logging
from datetime import datetime, timezone

from app.jobs.celery_app import celery_app
from app.jobs.base import BaseTask

logger = logging.getLogger("jobs.reports")


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.reports.process_scheduled_reports",
)
def process_scheduled_reports(self):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT sr.id, sr.tenant_id, sr.report_name, sr.frequency "
                "FROM scheduled_reports sr "
                "WHERE sr.id IS NOT NULL"
            )
        )
        reports = result.fetchall()

    processed = 0
    for report in reports:
        try:
            generate_report.delay(
                report_id=str(report[0]),
                tenant_id=str(report[1]),
                report_name=report[2],
            )
            processed += 1
        except Exception as e:
            logger.error("Failed to queue report %s: %s", report[0], e)

    logger.info("Scheduled %d reports for generation", processed)
    return {"scheduled": processed, "total": len(reports)}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="app.jobs.tasks.reports.generate_report",
    soft_time_limit=120,
    time_limit=300,
)
def generate_report(
    self,
    report_id: str,
    tenant_id: str,
    report_name: str,
):
    from app.core.database import get_sync_engine
    from sqlalchemy import text

    engine = get_sync_engine()

    report_generators = {
        "monthly_sales": _generate_sales_report,
        "monthly_purchases": _generate_purchases_report,
        "inventory_status": _generate_inventory_report,
        "profit_loss": _generate_pl_report,
        "accounts_receivable": _generate_ar_report,
        "accounts_payable": _generate_ap_report,
    }

    generator = report_generators.get(report_name, _generate_generic_report)
    report_data = generator(engine, tenant_id)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT email FROM scheduled_report_recipients WHERE report_id = :report_id"
            ),
            {"report_id": report_id},
        )
        recipients = [row[0] for row in result.fetchall()]

    if recipients:
        from app.jobs.tasks.email import send_email
        csv_content = _to_csv(report_data)
        for email in recipients:
            send_email.delay(
                to=email,
                subject=f"Scheduled Report: {report_name} - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                body=f"Please find attached the {report_name} report.\n\nData:\n{csv_content[:2000]}",
            )

    logger.info("Report '%s' generated for tenant %s, sent to %d recipients", report_name, tenant_id, len(recipients))
    return {"report": report_name, "rows": len(report_data), "recipients": len(recipients)}


def _generate_sales_report(engine, tenant_id: str) -> list[dict]:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT invoice_number, total, amount_paid, status, created_at "
                "FROM sales_invoices WHERE tenant_id = :tid AND deleted_at IS NULL "
                "ORDER BY created_at DESC LIMIT 500"
            ),
            {"tid": tenant_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]


def _generate_purchases_report(engine, tenant_id: str) -> list[dict]:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT invoice_number, total, amount_paid, status, created_at "
                "FROM purchase_invoices WHERE tenant_id = :tid AND deleted_at IS NULL "
                "ORDER BY created_at DESC LIMIT 500"
            ),
            {"tid": tenant_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]


def _generate_inventory_report(engine, tenant_id: str) -> list[dict]:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT p.name, p.sku, i.quantity, i.reserved_quantity, "
                "(i.quantity - i.reserved_quantity - i.damaged_quantity) as available "
                "FROM inventory i JOIN products p ON p.id = i.product_id "
                "JOIN warehouses w ON w.id = i.warehouse_id "
                "WHERE w.tenant_id = :tid ORDER BY p.name"
            ),
            {"tid": tenant_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]


def _generate_pl_report(engine, tenant_id: str) -> list[dict]:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT a.account_code, a.account_name, a.account_type, "
                "COALESCE(SUM(jel.debit), 0) as total_debit, "
                "COALESCE(SUM(jel.credit), 0) as total_credit "
                "FROM accounts a LEFT JOIN journal_entry_lines jel ON jel.account_id = a.id "
                "WHERE a.tenant_id = :tid AND a.account_type IN ('revenue', 'expense') "
                "AND a.deleted_at IS NULL GROUP BY a.id ORDER BY a.account_code"
            ),
            {"tid": tenant_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]


def _generate_ar_report(engine, tenant_id: str) -> list[dict]:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT invoice_number, customer_id, total, amount_paid, "
                "(total - amount_paid) as balance, due_date, status "
                "FROM sales_invoices WHERE tenant_id = :tid "
                "AND status IN ('approved', 'posted', 'partial') AND deleted_at IS NULL "
                "ORDER BY due_date"
            ),
            {"tid": tenant_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]


def _generate_ap_report(engine, tenant_id: str) -> list[dict]:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT invoice_number, supplier_id, total, amount_paid, "
                "(total - amount_paid) as balance, due_date, status "
                "FROM purchase_invoices WHERE tenant_id = :tid "
                "AND status IN ('approved', 'posted', 'partial') AND deleted_at IS NULL "
                "ORDER BY due_date"
            ),
            {"tid": tenant_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]


def _generate_generic_report(engine, tenant_id: str) -> list[dict]:
    return [{"message": "No specific generator for this report type"}]


def _to_csv(data: list[dict]) -> str:
    if not data:
        return "No data"
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    for row in data:
        writer.writerow({k: str(v) for k, v in row.items()})
    return output.getvalue()
