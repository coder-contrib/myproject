"""Unit tests for webhook retry mechanism."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.unit
class TestRetryPolicy:
    def test_default_retry_policy(self):
        from app.webhooks.retry import RetryPolicy

        policy = RetryPolicy()
        assert policy.max_retries == 5
        assert policy.base_delay == 60

    def test_calculate_delay_exponential(self):
        from app.webhooks.retry import RetryPolicy

        policy = RetryPolicy(base_delay=60, max_delay=3600)
        delay1 = policy.calculate_delay(attempt=1)
        delay2 = policy.calculate_delay(attempt=2)
        delay3 = policy.calculate_delay(attempt=3)
        assert delay1 >= 60
        assert delay2 > delay1
        assert delay3 > delay2

    def test_calculate_delay_capped(self):
        from app.webhooks.retry import RetryPolicy

        policy = RetryPolicy(base_delay=60, max_delay=3600)
        delay = policy.calculate_delay(attempt=10)
        assert delay <= 3600 * 1.5  # account for jitter

    def test_should_retry_within_limit(self):
        from app.webhooks.retry import RetryPolicy

        policy = RetryPolicy(max_retries=5)
        assert policy.should_retry(attempt=3) is True
        assert policy.should_retry(attempt=5) is False
        assert policy.should_retry(attempt=6) is False

    def test_jitter_adds_randomness(self):
        from app.webhooks.retry import RetryPolicy

        policy = RetryPolicy(base_delay=60)
        delays = [policy.calculate_delay(attempt=2) for _ in range(10)]
        assert len(set(delays)) > 1  # should not all be identical


@pytest.mark.unit
class TestWebhookRetryManager:
    @pytest.mark.asyncio
    async def test_record_failure(self):
        from app.webhooks.retry import WebhookRetryManager

        manager = WebhookRetryManager()
        manager.record_failure(
            webhook_id=1,
            event_id="evt_123",
            attempt=1,
            status_code=500,
            error="Internal Server Error",
        )
        pending = manager.get_pending_retries()
        assert len(pending) >= 1

    @pytest.mark.asyncio
    async def test_record_success_clears_retries(self):
        from app.webhooks.retry import WebhookRetryManager

        manager = WebhookRetryManager()
        manager.record_failure(webhook_id=1, event_id="evt_123", attempt=1, status_code=500, error="err")
        manager.record_success(webhook_id=1, event_id="evt_123")
        pending = manager.get_pending_retries()
        matching = [p for p in pending if p["event_id"] == "evt_123"]
        assert len(matching) == 0

    @pytest.mark.asyncio
    async def test_get_delivery_stats(self):
        from app.webhooks.retry import WebhookRetryManager

        manager = WebhookRetryManager()
        manager.record_success(webhook_id=1, event_id="evt_1")
        manager.record_success(webhook_id=1, event_id="evt_2")
        manager.record_failure(webhook_id=1, event_id="evt_3", attempt=1, status_code=500, error="err")
        stats = manager.get_stats(webhook_id=1)
        assert stats["successes"] == 2
        assert stats["failures"] == 1
