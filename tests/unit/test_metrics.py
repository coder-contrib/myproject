"""Unit tests for monitoring metrics."""
import pytest


@pytest.mark.unit
class TestMetricsCollector:
    def test_counter_increment(self):
        from app.monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.register_counter("test_requests", "Test counter")
        collector.increment("test_requests")
        collector.increment("test_requests")
        assert collector.get_value("test_requests") == 2

    def test_counter_increment_with_labels(self):
        from app.monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.register_counter("http_requests", "HTTP requests", labels=["method", "path"])
        collector.increment("http_requests", labels={"method": "GET", "path": "/api/v1/users"})
        collector.increment("http_requests", labels={"method": "POST", "path": "/api/v1/users"})
        collector.increment("http_requests", labels={"method": "GET", "path": "/api/v1/users"})
        assert collector.get_value("http_requests", labels={"method": "GET", "path": "/api/v1/users"}) == 2

    def test_gauge_set(self):
        from app.monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.register_gauge("active_connections", "Active WS connections")
        collector.set_gauge("active_connections", 42)
        assert collector.get_value("active_connections") == 42

    def test_gauge_increment_decrement(self):
        from app.monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.register_gauge("active_users", "Active users")
        collector.set_gauge("active_users", 10)
        collector.increment_gauge("active_users")
        assert collector.get_value("active_users") == 11
        collector.decrement_gauge("active_users", 3)
        assert collector.get_value("active_users") == 8

    def test_histogram_observe(self):
        from app.monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.register_histogram("response_time", "Response time in seconds")
        collector.observe("response_time", 0.15)
        collector.observe("response_time", 0.25)
        collector.observe("response_time", 0.35)
        stats = collector.get_histogram_stats("response_time")
        assert stats["count"] == 3
        assert stats["sum"] == pytest.approx(0.75)

    def test_prometheus_exposition(self):
        from app.monitoring.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.register_counter("test_total", "A test counter")
        collector.increment("test_total")
        output = collector.expose_prometheus()
        assert "# HELP test_total A test counter" in output
        assert "# TYPE test_total counter" in output
        assert "test_total 1" in output
