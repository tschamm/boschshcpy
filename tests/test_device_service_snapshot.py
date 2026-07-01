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


def _make_alarm_service(service_id: str, initial_value: str):
    raw_svc = {
        "id": service_id,
        "deviceId": "dev-1",
        "path": f"/devices/dev-1/services/{service_id}",
        "state": {"@type": "alarmState", "value": initial_value},
    }
    api = MagicMock(name="SHCAPI")
    return SHCDeviceService(api=api, raw_device_service=raw_svc)


def _poll(svc, service_id, value):
    svc.process_long_polling_poll_result(
        {
            "@type": "DeviceServiceData",
            "id": service_id,
            "deviceId": "dev-1",
            "path": f"/devices/dev-1/services/{service_id}",
            "state": {"@type": "alarmState", "value": value},
        }
    )


def test_alarm_register_event_fires_on_value_change():
    """Alarm/SurveillanceAlarm register_event callbacks must fire — they were
    previously never dispatched (_process_events had no branch for them)."""
    for service_id in ("Alarm", "SurveillanceAlarm"):
        svc = _make_alarm_service(service_id, "IDLE_OFF")
        calls = []
        svc.register_event("dev-1", lambda: calls.append(1))

        _poll(svc, service_id, "PRIMARY_ALARM")
        assert calls == [1], f"{service_id} did not fire"


def test_alarm_register_event_suppresses_replayed_unchanged_value():
    """A (re)subscribe/restart re-delivering the same current value must not
    be dispatched as a fresh event."""
    for service_id in ("Alarm", "SurveillanceAlarm"):
        svc = _make_alarm_service(service_id, "IDLE_OFF")
        calls = []
        svc.register_event("dev-1", lambda: calls.append(1))

        # Same value as construction snapshot -> replay, must be suppressed
        _poll(svc, service_id, "IDLE_OFF")
        assert calls == [], f"{service_id} replayed an unchanged value"

        # Real transition still fires
        _poll(svc, service_id, "PRIMARY_ALARM")
        assert calls == [1], f"{service_id} did not fire on a real transition"

        # Repeating the new value again must not re-fire
        _poll(svc, service_id, "PRIMARY_ALARM")
        assert calls == [1], f"{service_id} re-fired an unchanged value"
