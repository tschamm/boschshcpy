"""conftest.py — project-wide pytest config for boschshcpy tests.

Overrides the async autouse fixture from pytest-homeassistant-custom-component
that breaks sync tests under pytest-asyncio strict mode.
"""

import pytest


@pytest.fixture(autouse=True)
def enable_event_loop_debug():
    """Sync no-op override of the async fixture from pytest_homeassistant_custom_component.

    The upstream fixture calls asyncio.get_running_loop().set_debug(True), which
    only works inside an async test. Overriding it here as a plain sync fixture
    lets sync tests collect and run without error.
    """
