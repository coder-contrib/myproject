"""Unit tests for webhook signature verification."""
import hashlib
import hmac
import time

import pytest


@pytest.mark.unit
class TestWebhookSignature:
    def test_sign_payload(self):
        from app.webhooks.signature import WebhookSignature

        signer = WebhookSignature()
        payload = b'{"event": "test"}'
        secret = "whsec_test123"
        signature = signer.sign(payload, secret)
        assert signature is not None
        assert "t=" in signature
        assert ",v1=" in signature

    def test_verify_valid_signature(self):
        from app.webhooks.signature import WebhookSignature

        signer = WebhookSignature()
        payload = b'{"event": "test"}'
        secret = "whsec_test123"
        signature = signer.sign(payload, secret)
        assert signer.verify(payload, signature, secret) is True

    def test_verify_invalid_signature(self):
        from app.webhooks.signature import WebhookSignature

        signer = WebhookSignature()
        payload = b'{"event": "test"}'
        secret = "whsec_test123"
        assert signer.verify(payload, "t=123,v1=invalid", secret) is False

    def test_verify_tampered_payload(self):
        from app.webhooks.signature import WebhookSignature

        signer = WebhookSignature()
        payload = b'{"event": "test"}'
        secret = "whsec_test123"
        signature = signer.sign(payload, secret)
        tampered = b'{"event": "hacked"}'
        assert signer.verify(tampered, signature, secret) is False

    def test_verify_wrong_secret(self):
        from app.webhooks.signature import WebhookSignature

        signer = WebhookSignature()
        payload = b'{"event": "test"}'
        signature = signer.sign(payload, "secret1")
        assert signer.verify(payload, signature, "secret2") is False

    def test_replay_protection(self):
        from app.webhooks.signature import WebhookSignature

        signer = WebhookSignature(tolerance_seconds=300)
        payload = b'{"event": "test"}'
        secret = "whsec_test123"
        old_timestamp = int(time.time()) - 600
        msg = f"{old_timestamp}.{payload.decode()}"
        sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
        old_signature = f"t={old_timestamp},v1={sig}"
        assert signer.verify(payload, old_signature, secret) is False

    def test_generate_secret(self):
        from app.webhooks.signature import WebhookSignature

        signer = WebhookSignature()
        secret = signer.generate_secret()
        assert secret.startswith("whsec_")
        assert len(secret) > 20
