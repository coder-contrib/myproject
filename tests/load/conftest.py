"""Load test configuration."""
import pytest


def pytest_collection_modifyitems(config, items):
    """Skip load tests by default (run with -m load)."""
    skip_load = pytest.mark.skip(reason="Load tests not selected (use -m load)")
    for item in items:
        if "load" in item.keywords:
            if "load" not in (config.getoption("-m", default="") or ""):
                item.add_marker(skip_load)
