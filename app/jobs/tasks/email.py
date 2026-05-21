import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.jobs.celery_app import celery_app
from app.jobs.base import BaseTask

logger = logging.getLogger("jobs.email")

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@ceramix.ai")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


@celery_app.task(base=BaseTask, bind=True, name="app.jobs.tasks.email.send_email")
def send_email(
    self,
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: str | None = None,
):
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc)
    if reply_to:
        msg["Reply-To"] = reply_to

    msg.attach(MIMEText(body, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    recipients = [to]
    if cc:
        recipients.extend(cc)
    if bcc:
        recipients.extend(bcc)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, recipients, msg.as_string())

    logger.info("Email sent to %s: %s", to, subject)
    return {"status": "sent", "to": to, "subject": subject}


@celery_app.task(base=BaseTask, bind=True, name="app.jobs.tasks.email.send_template_email")
def send_template_email(
    self,
    to: str,
    template_name: str,
    context: dict,
    subject: str | None = None,
):
    templates = {
        "welcome": {
            "subject": "Welcome to Ceramix AI ERP",
            "body": "Hello {full_name},\n\nYour account has been created successfully.\n\nBest regards,\nCeramix AI Team",
        },
        "password_reset": {
            "subject": "Password Reset Request",
            "body": "Hello {full_name},\n\nClick the link to reset your password: {reset_link}\n\nThis link expires in 1 hour.",
        },
        "invoice_created": {
            "subject": "Invoice #{invoice_number} Created",
            "body": "Hello {customer_name},\n\nInvoice #{invoice_number} for {total} has been created.\n\nDue date: {due_date}",
        },
        "payment_received": {
            "subject": "Payment Received - Invoice #{invoice_number}",
            "body": "Hello {customer_name},\n\nWe received a payment of {amount} for invoice #{invoice_number}.\n\nRemaining balance: {balance}",
        },
        "order_shipped": {
            "subject": "Order #{order_number} Shipped",
            "body": "Hello {customer_name},\n\nYour order #{order_number} has been shipped.\n\nTracking: {tracking_info}",
        },
        "low_stock_alert": {
            "subject": "Low Stock Alert: {product_name}",
            "body": "Product '{product_name}' (SKU: {sku}) has fallen below threshold.\n\nCurrent: {current_qty} | Threshold: {threshold}",
        },
    }

    template = templates.get(template_name)
    if not template:
        raise ValueError(f"Unknown email template: {template_name}")

    final_subject = (subject or template["subject"]).format(**context)
    body = template["body"].format(**context)

    return send_email(to=to, subject=final_subject, body=body)


@celery_app.task(base=BaseTask, bind=True, name="app.jobs.tasks.email.send_bulk_email")
def send_bulk_email(
    self,
    recipients: list[str],
    subject: str,
    body: str,
    html_body: str | None = None,
):
    results = []
    for recipient in recipients:
        try:
            send_email.delay(to=recipient, subject=subject, body=body, html_body=html_body)
            results.append({"to": recipient, "status": "queued"})
        except Exception as e:
            results.append({"to": recipient, "status": "failed", "error": str(e)})

    logger.info("Bulk email queued for %d recipients", len(recipients))
    return {"total": len(recipients), "results": results}
