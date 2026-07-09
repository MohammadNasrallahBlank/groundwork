"""Test-slot adapters must not leak between tests."""
import pytest

from groundwork.tools.verify import adapters


@pytest.fixture(autouse=True)
def _clear_test_slots():
    yield
    adapters._TEST_SLOTS.clear()
