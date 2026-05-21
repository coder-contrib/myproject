import os
from dataclasses import dataclass, field


@dataclass
class WebhookConfig:
    max_retries: int = int(os.getenv("WEBHOOK_MAX_RETRIES", "5"))
    retry_base_delay: int = int(os.getenv("WEBHOOK_RETRY_BASE_DELAY", "60"))
    retry_max_delay: int = int(os.getenv("WEBHOOK_RETRY_MAX_DELAY", "3600"))
    request_timeout: int = int(os.getenv("WEBHOOK_TIMEOUT", "30"))
    signature_algorithm: str = os.getenv("WEBHOOK_SIG_ALGORITHM", "sha256")
    signature_header: str = os.getenv("WEBHOOK_SIG_HEADER", "X-Webhook-Signature")
    timestamp_header: str = os.getenv("WEBHOOK_TS_HEADER", "X-Webhook-Timestamp")
    event_header: str = os.getenv("WEBHOOK_EVENT_HEADER", "X-Webhook-Event")
    delivery_id_header: str = os.getenv("WEBHOOK_ID_HEADER", "X-Webhook-Delivery")
    timestamp_tolerance: int = int(os.getenv("WEBHOOK_TS_TOLERANCE", "300"))
    max_payload_size: int = int(os.getenv("WEBHOOK_MAX_PAYLOAD", str(256 * 1024)))
    concurrent_deliveries: int = int(os.getenv("WEBHOOK_CONCURRENCY", "10"))
    user_agent: str = os.getenv("WEBHOOK_USER_AGENT", "CeramixERP-Webhook/1.0")


webhook_config = WebhookConfig()
