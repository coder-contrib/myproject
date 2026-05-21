import time
import logging
from typing import Optional
from collections import defaultdict
from datetime import datetime, timezone

from app.monitoring.config import monitoring_config

logger = logging.getLogger("monitoring.metrics")


class Counter:
    """Prometheus-compatible counter metric."""

    def __init__(self, name: str, description: str, labels: Optional[list[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: dict[tuple, float] = defaultdict(float)

    def inc(self, value: float = 1.0, **label_values):
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] += value

    def get(self, **label_values) -> float:
        key = tuple(label_values.get(l, "") for l in self.labels)
        return self._values[key]

    def collect(self) -> list[dict]:
        results = []
        for key, value in self._values.items():
            labels = dict(zip(self.labels, key))
            results.append({"labels": labels, "value": value})
        return results


class Gauge:
    """Prometheus-compatible gauge metric."""

    def __init__(self, name: str, description: str, labels: Optional[list[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: dict[tuple, float] = defaultdict(float)

    def set(self, value: float, **label_values):
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] = value

    def inc(self, value: float = 1.0, **label_values):
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] += value

    def dec(self, value: float = 1.0, **label_values):
        key = tuple(label_values.get(l, "") for l in self.labels)
        self._values[key] -= value

    def get(self, **label_values) -> float:
        key = tuple(label_values.get(l, "") for l in self.labels)
        return self._values[key]

    def collect(self) -> list[dict]:
        results = []
        for key, value in self._values.items():
            labels = dict(zip(self.labels, key))
            results.append({"labels": labels, "value": value})
        return results


class Histogram:
    """Prometheus-compatible histogram metric with fixed buckets."""

    DEFAULT_BUCKETS = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

    def __init__(self, name: str, description: str, labels: Optional[list[str]] = None, buckets: Optional[list[float]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)
        self._counts: dict[tuple, dict[str, float]] = defaultdict(lambda: {
            "sum": 0.0, "count": 0, **{str(b): 0 for b in self.buckets}, "+Inf": 0
        })

    def observe(self, value: float, **label_values):
        key = tuple(label_values.get(l, "") for l in self.labels)
        data = self._counts[key]
        data["sum"] += value
        data["count"] += 1
        data["+Inf"] += 1
        for bucket in self.buckets:
            if value <= bucket:
                data[str(bucket)] += 1

    def collect(self) -> list[dict]:
        results = []
        for key, data in self._counts.items():
            labels = dict(zip(self.labels, key))
            results.append({
                "labels": labels,
                "count": data["count"],
                "sum": data["sum"],
                "buckets": {k: v for k, v in data.items() if k not in ("sum", "count")},
            })
        return results


class MetricsCollector:
    """Central metrics registry compatible with Prometheus exposition format."""

    def __init__(self):
        self.prefix = monitoring_config.metrics_prefix
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}
        self._register_defaults()

    def counter(self, name: str, description: str, labels: Optional[list[str]] = None) -> Counter:
        full_name = f"{self.prefix}_{name}"
        if full_name not in self._metrics:
            self._metrics[full_name] = Counter(full_name, description, labels)
        return self._metrics[full_name]

    def gauge(self, name: str, description: str, labels: Optional[list[str]] = None) -> Gauge:
        full_name = f"{self.prefix}_{name}"
        if full_name not in self._metrics:
            self._metrics[full_name] = Gauge(full_name, description, labels)
        return self._metrics[full_name]

    def histogram(self, name: str, description: str, labels: Optional[list[str]] = None, buckets: Optional[list[float]] = None) -> Histogram:
        full_name = f"{self.prefix}_{name}"
        if full_name not in self._metrics:
            self._metrics[full_name] = Histogram(full_name, description, labels, buckets)
        return self._metrics[full_name]

    def expose_prometheus(self) -> str:
        """Generate Prometheus text exposition format."""
        lines = []

        for name, metric in self._metrics.items():
            if isinstance(metric, Counter):
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} counter")
                for entry in metric.collect():
                    label_str = self._format_labels(entry["labels"])
                    lines.append(f"{name}_total{label_str} {entry['value']}")

            elif isinstance(metric, Gauge):
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} gauge")
                for entry in metric.collect():
                    label_str = self._format_labels(entry["labels"])
                    lines.append(f"{name}{label_str} {entry['value']}")

            elif isinstance(metric, Histogram):
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} histogram")
                for entry in metric.collect():
                    label_str = self._format_labels(entry["labels"])
                    for bucket_le, count in entry["buckets"].items():
                        lines.append(f'{name}_bucket{{le="{bucket_le}"{self._append_labels(entry["labels"])}}} {count}')
                    lines.append(f"{name}_sum{label_str} {entry['sum']}")
                    lines.append(f"{name}_count{label_str} {entry['count']}")

            lines.append("")

        return "\n".join(lines)

    def get_all_metrics(self) -> dict:
        """Get all metrics as structured dict."""
        result = {}
        for name, metric in self._metrics.items():
            result[name] = {
                "type": type(metric).__name__.lower(),
                "description": metric.description,
                "data": metric.collect(),
            }
        return result

    def _format_labels(self, labels: dict) -> str:
        if not labels or all(v == "" for v in labels.values()):
            return ""
        pairs = [f'{k}="{v}"' for k, v in labels.items() if v]
        return "{" + ",".join(pairs) + "}" if pairs else ""

    def _append_labels(self, labels: dict) -> str:
        pairs = [f',{k}="{v}"' for k, v in labels.items() if v]
        return "".join(pairs)

    def _register_defaults(self):
        # HTTP metrics
        self.counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
        self.histogram("http_request_duration_ms", "HTTP request duration in ms", ["method", "path"])
        self.gauge("http_requests_in_progress", "In-flight HTTP requests", ["method"])

        # Business metrics
        self.counter("sales_total", "Total sales transactions", ["tenant_id", "branch_id"])
        self.counter("sales_revenue_total", "Total sales revenue", ["tenant_id", "currency"])
        self.counter("orders_created_total", "Total orders created", ["tenant_id", "type"])

        # System metrics
        self.gauge("active_websocket_connections", "Active WebSocket connections", ["tenant_id"])
        self.counter("webhook_deliveries_total", "Total webhook deliveries", ["status", "event_type"])
        self.counter("background_jobs_total", "Total background jobs executed", ["queue", "status"])
        self.histogram("background_job_duration_ms", "Background job duration in ms", ["queue"])

        # Error metrics
        self.counter("errors_total", "Total application errors", ["type", "module"])

        # Database metrics
        self.histogram("db_query_duration_ms", "Database query duration in ms", ["operation"])
        self.gauge("db_pool_active", "Active database connections")
        self.gauge("db_pool_idle", "Idle database connections")


metrics_collector = MetricsCollector()
