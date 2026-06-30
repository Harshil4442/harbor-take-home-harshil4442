import functools
import importlib.util

import pytest

MODULE_PATH = "/app/src/your_module.py"


@functools.lru_cache(maxsize=1)
def _entry_point():
    spec = importlib.util.spec_from_file_location("solution", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.your_function


CASES = []


@pytest.mark.parametrize("given,expected", CASES)
def test_behavior(given, expected):
    """Assert observable behavior by running the agent's code."""
    assert _entry_point()(given) == expected
