"""API test fixtures."""
import pytest
import pytest_asyncio


def pytest_collection_modifyitems(config, items):
    """Mark API tests that require a running server."""
    for item in items:
        if "api" in item.keywords:
            item.add_marker(pytest.mark.timeout(30))
