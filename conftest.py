from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    run_integration = os.getenv("RUN_INTEGRATION_TESTS", "").lower() == "true"
    skip_mark = pytest.mark.skip(reason="Set RUN_INTEGRATION_TESTS=true to run integration tests")
    for item in items:
        if "integration" in item.keywords and not run_integration:
            item.add_marker(skip_mark)


@pytest.fixture
def cmc_api_key() -> str:
    key = os.getenv("CMC_API_KEY", "")
    if not key:
        pytest.skip("CMC_API_KEY environment variable not set")
    return key
