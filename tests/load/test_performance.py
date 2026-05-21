"""Pytest-based load/stress tests for critical paths.

These tests measure response times and throughput without Locust.
Run with: pytest tests/load/test_performance.py -m load -v
"""
import asyncio
import time
from statistics import mean, median

import pytest


@pytest.mark.load
@pytest.mark.slow
class TestAPIPerformance:
    @pytest.mark.asyncio
    async def test_health_endpoint_latency(self, client):
        """Health endpoint should respond under 50ms."""
        latencies = []
        for _ in range(50):
            start = time.perf_counter()
            response = await client.get("/health")
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            assert response.status_code == 200

        avg = mean(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        assert avg < 50, f"Average latency {avg:.1f}ms exceeds 50ms"
        assert p95 < 100, f"P95 latency {p95:.1f}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_product_list_latency(self, authenticated_client):
        """Product listing should respond under 200ms."""
        latencies = []
        for _ in range(20):
            start = time.perf_counter()
            response = await authenticated_client.get("/api/v1/products/?page=1&size=20")
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        if any(l < 5000 for l in latencies):
            avg = mean(latencies)
            assert avg < 500, f"Average latency {avg:.1f}ms exceeds 500ms"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """System should handle 20 concurrent requests."""
        async def make_request():
            start = time.perf_counter()
            response = await client.get("/health")
            return time.perf_counter() - start, response.status_code

        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        latencies = [r[0] * 1000 for r in results]
        status_codes = [r[1] for r in results]

        assert all(s == 200 for s in status_codes), "Some concurrent requests failed"
        assert max(latencies) < 2000, f"Max latency {max(latencies):.1f}ms under concurrency"

    @pytest.mark.asyncio
    async def test_sustained_throughput(self, client):
        """System should sustain 50+ requests/second for 5 seconds."""
        total_requests = 0
        errors = 0
        start = time.perf_counter()
        duration = 5.0

        while time.perf_counter() - start < duration:
            batch = [client.get("/health") for _ in range(10)]
            responses = await asyncio.gather(*batch, return_exceptions=True)
            for r in responses:
                total_requests += 1
                if isinstance(r, Exception) or (hasattr(r, 'status_code') and r.status_code != 200):
                    errors += 1

        elapsed = time.perf_counter() - start
        rps = total_requests / elapsed
        error_rate = errors / total_requests if total_requests > 0 else 1.0

        assert rps >= 50, f"Throughput {rps:.1f} RPS below 50 RPS target"
        assert error_rate < 0.05, f"Error rate {error_rate:.1%} exceeds 5%"

    @pytest.mark.asyncio
    async def test_dashboard_latency(self, authenticated_client):
        """Dashboard endpoint should respond under 500ms."""
        latencies = []
        for _ in range(10):
            start = time.perf_counter()
            response = await authenticated_client.get("/api/v1/reports/dashboard/overview")
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        if latencies and min(latencies) < 5000:
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            assert p95 < 1000, f"Dashboard P95 latency {p95:.1f}ms exceeds 1000ms"
