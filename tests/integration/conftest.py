"""Integration test fixtures requiring external services."""
import os
import pytest
import pytest_asyncio


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if DATABASE_URL is not set."""
    skip_integration = pytest.mark.skip(reason="DATABASE_URL not configured")
    for item in items:
        if "integration" in item.keywords:
            if not os.environ.get("DATABASE_URL"):
                item.add_marker(skip_integration)
