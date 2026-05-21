import hmac
import hashlib
import time
import logging
from typing import Optional

from app.webhooks.config import webhook_config

logger = logging.getLogger("webhooks.signature")


class WebhookSignature:
    """HMAC-based webhook signature generation and verification."""

    @staticmethod
    def sign(payload: str, secret: str, timestamp: Optional[int] = None) -> tuple[str, int]:
        """Generate HMAC signature for a webhook payload.

        Returns (signature, timestamp) tuple.
        """
        ts = timestamp or int(time.time())
        message = f"{ts}.{payload}"

        if webhook_config.signature_algorithm == "sha256":
            signature = hmac.new(
                secret.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        elif webhook_config.signature_algorithm == "sha512":
            signature = hmac.new(
                secret.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha512,
            ).hexdigest()
        else:
            signature = hmac.new(
                secret.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

        return f"v1={signature}", ts

    @staticmethod
    def verify(
        payload: str,
        secret: str,
        signature: str,
        timestamp: int,
        tolerance: Optional[int] = None,
    ) -> bool:
        """Verify a webhook signature.

        Checks HMAC validity and timestamp freshness to prevent replay attacks.
        """
        tolerance = tolerance or webhook_config.timestamp_tolerance

        # Check timestamp freshness
        current_time = int(time.time())
        if abs(current_time - timestamp) > tolerance:
            logger.warning(
                "Webhook signature timestamp too old: %d (current: %d, tolerance: %d)",
                timestamp, current_time, tolerance,
            )
            return False

        # Compute expected signature
        expected_sig, _ = WebhookSignature.sign(payload, secret, timestamp)

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_sig, signature)

    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """Generate a cryptographically secure webhook secret."""
        import secrets
        return secrets.token_hex(length)
