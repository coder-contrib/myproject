from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class WebhookEvent:
    event_type: str
    tenant_id: str
    payload: dict
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    actor_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


# All supported webhook event types
WEBHOOK_EVENTS = {
    # Sales events
    "sales.invoice.created": "Fired when a new sales invoice is created",
    "sales.invoice.updated": "Fired when a sales invoice is updated",
    "sales.invoice.paid": "Fired when a sales invoice is fully paid",
    "sales.invoice.cancelled": "Fired when a sales invoice is cancelled",
    "sales.invoice.overdue": "Fired when a sales invoice becomes overdue",
    "sales.payment.received": "Fired when a payment is received",
    "sales.quotation.created": "Fired when a quotation is created",
    "sales.quotation.accepted": "Fired when a quotation is accepted",

    # Purchase events
    "purchase.order.created": "Fired when a purchase order is created",
    "purchase.order.received": "Fired when goods from a PO are received",
    "purchase.order.cancelled": "Fired when a purchase order is cancelled",
    "purchase.invoice.created": "Fired when a purchase invoice is created",
    "purchase.payment.made": "Fired when a payment is made to supplier",

    # Inventory events
    "inventory.stock.low": "Fired when stock drops below reorder level",
    "inventory.stock.out": "Fired when a product goes out of stock",
    "inventory.adjustment.created": "Fired when a stock adjustment is made",
    "inventory.transfer.created": "Fired when a warehouse transfer is initiated",
    "inventory.transfer.completed": "Fired when a warehouse transfer is completed",

    # Product events
    "product.created": "Fired when a new product is created",
    "product.updated": "Fired when a product is updated",
    "product.deleted": "Fired when a product is soft-deleted",
    "product.price.changed": "Fired when a product price changes",

    # Customer events
    "customer.created": "Fired when a new customer is created",
    "customer.updated": "Fired when a customer is updated",
    "customer.credit.exceeded": "Fired when a customer exceeds credit limit",

    # User/Auth events
    "user.created": "Fired when a new user is created",
    "user.login": "Fired when a user logs in",
    "user.login.failed": "Fired when a login attempt fails",

    # Accounting events
    "accounting.journal.posted": "Fired when a journal entry is posted",
    "accounting.period.closed": "Fired when an accounting period is closed",

    # System events
    "system.backup.completed": "Fired when a backup completes",
    "system.backup.failed": "Fired when a backup fails",
    "system.report.generated": "Fired when a scheduled report is generated",
}
