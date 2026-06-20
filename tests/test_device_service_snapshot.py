"""Tests for device_service.py — snapshot-safe callback iteration.

Isolation: NO HA harness, NO real network.
Run with:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_device_service_snapshot.py -q \
    -o addopts= -p no:cacheprovider
"""
from __future__ import annotations

from unittest.mock import MagicMock

from boschshcpy.device_service import SHCDeviceService


def _make_service():
    """Build a minimal SHCDeviceService without a real API."""
    raw_svc = {
        "id": "PowerSwitch",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/PowerSwitch",
        "state": {
            "@type": "powerSwitchState",
            "switchState": "ON",
        },
    }
    api = MagicMock(name="SHCAPI")
    return SHCDeviceService(api=api, raw_device_service=raw_svc)


def test_callback_fires_for_each_subscriber():
    """All registered callbacks are called on a poll result."""
    svc = _make_service()
    calls = []
    svc.subscribe_callback("entity-a", lambda: calls.append("a"))
    svc.subscribe_callback("entity-b", lambda: calls.append("b"))

    raw_result = {
        "@type": "DeviceServiceData",
        "id": "PowerSwitch",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/PowerSwitch",
        "state": {
            "@type": "powerSwitchState",
            "switchState": "OFF",
        },
    }
    svc.process_long_polling_poll_result(raw_result)

    assert set(calls) == {"a", "b"}


def test_callback_unsubscribe_during_iteration_is_safe():
    """Unsubscribing inside a callback must not raise RuntimeError.

    Without the list() snapshot this causes:
      RuntimeError: dictionary changed size during iteration
    """
    svc = _make_service()
    calls = []

    def callback_a():
        calls.append("a")
        # Unsubscribe another entity while the dict is being iterated
        svc.unsubscribe_callback("entity-b")

    def callback_b():
        calls.append("b")

    svc.subscribe_callback("entity-a", callback_a)
    svc.subscribe_callback("entity-b", callback_b)

    raw_result = {
        "@type": "DeviceServiceData",
        "id": "PowerSwitch",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/PowerSwitch",
        "state": {
            "@type": "powerSwitchState",
            "switchState": "OFF",
        },
    }
    # Must not raise RuntimeError
    svc.process_long_polling_poll_result(raw_result)
    assert "a" in calls  # callback_a always fires


def test_subscribe_during_iteration_does_not_affect_current_pass():
    """Subscribing a new callback mid-iteration must not raise and must not
    call the new callback in the current pass (list snapshot semantics)."""
    svc = _make_service()
    late_calls = []

    def callback_a():
        # Register a new subscriber while iterating — snapshot means this
        # new subscriber should NOT be called in the current poll result pass.
        svc.subscribe_callback("entity-late", lambda: late_calls.append("late"))

    svc.subscribe_callback("entity-a", callback_a)

    raw_result = {
        "@type": "DeviceServiceData",
        "id": "PowerSwitch",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/PowerSwitch",
        "state": {
            "@type": "powerSwitchState",
            "switchState": "OFF",
        },
    }
    svc.process_long_polling_poll_result(raw_result)
    assert late_calls == [], "Late-registered callback must not fire in the same pass"
