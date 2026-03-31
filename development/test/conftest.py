from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):
    for item in items:
        test_path = Path(str(item.fspath))
        parts = test_path.parts
        if "integration" in parts or "integration" in item.keywords:
            item.add_marker(pytest.mark.integration)
        elif "unit" in parts and "integration" not in item.keywords:
            item.add_marker(pytest.mark.unit)
