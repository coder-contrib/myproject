from enum import StrEnum


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    POSTED = "posted"
    PAID = "paid"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    ARCHIVED = "archived"


class OrderStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PaymentMethod(StrEnum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    CREDIT_CARD = "credit_card"
    MOBILE_PAYMENT = "mobile_payment"


class PaymentType(StrEnum):
    CASH = "cash"
    CREDIT = "credit"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    MOBILE_PAYMENT = "mobile_payment"


class TransferStatus(StrEnum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ProductionOrderStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class OpportunityStage(StrEnum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ActivityType(StrEnum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    TASK = "task"
    NOTE = "note"


class ContractType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACTOR = "contractor"
    INTERN = "intern"


class LeaveStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PayrollStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    PAID = "paid"


class ChequeStatus(StrEnum):
    PENDING = "pending"
    CLEARED = "cleared"
    BOUNCED = "bounced"
    CANCELLED = "cancelled"


class ReturnStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSED = "processed"
    CANCELLED = "cancelled"


class ReturnType(StrEnum):
    SALES_RETURN = "sales_return"
    PURCHASE_RETURN = "purchase_return"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CreditNoteStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    APPLIED = "applied"
    CANCELLED = "cancelled"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class BackgroundJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WebhookDeliveryStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class InventoryReason(StrEnum):
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER = "transfer"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    PRODUCTION = "production"


class AccountType(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
    CONTRA = "contra"


class QuotationStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"


class POSSessionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
