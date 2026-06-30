"""Tests for device_helper.py, device.py, device_service.py.

Isolation: NO HA harness, NO real network.
Run with:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_device_layer.py -q \
    -o addopts= -p no:cacheprovider
"""
from __future__ import annotations

import types
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from boschshcpy.device import SHCDevice
from boschshcpy.device_helper import SHCDeviceHelper
from boschshcpy.device_service import SHCDeviceService
from boschshcpy.exceptions import SHCException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_api():
    """Minimal API stand-in — all calls raise if not explicitly set."""
    api = MagicMock(name="SHCAPI")
    return api


def _raw_device(
    device_id="dev-1",
    model="UNKNOWN_MODEL",
    name="Test Device",
    manufacturer="Bosch",
    status="AVAILABLE",
    **extras,
):
    """Return a minimal raw_device dict."""
    base = {
        "id": device_id,
        "rootDeviceId": "root-1",
        "deviceModel": model,
        "name": name,
        "manufacturer": manufacturer,
        "status": status,
        "deviceServiceIds": [],
    }
    base.update(extras)
    return base


def _raw_service(
    service_id="PowerSwitch",
    device_id="dev-1",
    path="/devices/dev-1/services/PowerSwitch",
    state=None,
):
    svc = {
        "@type": "DeviceServiceData",
        "id": service_id,
        "deviceId": device_id,
        "path": path,
    }
    if state is not None:
        svc["state"] = state
    return svc


def _make_device(raw=None, services=None, api=None):
    """Construct SHCDevice directly from raw dicts."""
    if raw is None:
        raw = _raw_device()
    if services is None:
        services = []
    if api is None:
        api = _fake_api()
    return SHCDevice(api=api, raw_device=raw, raw_device_services=services)


def _make_service(service_id="PowerSwitch", device_id="dev-1", state=None, api=None):
    if api is None:
        api = _fake_api()
    raw = _raw_service(service_id=service_id, device_id=device_id, state=state)
    return SHCDeviceService(api=api, raw_device_service=raw)


# ---------------------------------------------------------------------------
# SHCDevice — property accessors
# ---------------------------------------------------------------------------

class TestSHCDeviceProperties:
    def test_id(self):
        dev = _make_device(_raw_device(device_id="abc-123"))
        assert dev.id == "abc-123"

    def test_root_device_id(self):
        raw = _raw_device()
        raw["rootDeviceId"] = "root-xyz"
        dev = _make_device(raw)
        assert dev.root_device_id == "root-xyz"

    def test_manufacturer(self):
        dev = _make_device(_raw_device(manufacturer="Bosch"))
        assert dev.manufacturer == "Bosch"

    def test_device_model(self):
        dev = _make_device(_raw_device(model="SWD"))
        assert dev.device_model == "SWD"

    def test_name(self):
        dev = _make_device(_raw_device(name="Kitchen Sensor"))
        assert dev.name == "Kitchen Sensor"

    def test_status(self):
        dev = _make_device(_raw_device(status="AVAILABLE"))
        assert dev.status == "AVAILABLE"

    def test_room_id_present(self):
        raw = _raw_device()
        raw["roomId"] = "room-42"
        dev = _make_device(raw)
        assert dev.room_id == "room-42"

    def test_room_id_missing(self):
        dev = _make_device(_raw_device())
        assert dev.room_id is None

    def test_serial_present(self):
        raw = _raw_device()
        raw["serial"] = "SN001"
        dev = _make_device(raw)
        assert dev.serial == "SN001"

    def test_serial_missing(self):
        dev = _make_device(_raw_device())
        assert dev.serial is None

    def test_profile_present(self):
        raw = _raw_device()
        raw["profile"] = "OUTDOOR"
        dev = _make_device(raw)
        assert dev.profile == "OUTDOOR"

    def test_profile_missing(self):
        dev = _make_device(_raw_device())
        assert dev.profile is None

    def test_deleted_true(self):
        raw = _raw_device()
        raw["deleted"] = True
        dev = _make_device(raw)
        assert dev.deleted is True

    def test_deleted_false(self):
        dev = _make_device(_raw_device())
        assert dev.deleted is False

    def test_deleted_explicit_false(self):
        raw = _raw_device()
        raw["deleted"] = False
        dev = _make_device(raw)
        assert dev.deleted is False

    def test_child_device_ids_present(self):
        raw = _raw_device()
        raw["childDeviceIds"] = ["child-1", "child-2"]
        dev = _make_device(raw)
        assert dev.child_device_ids == ["child-1", "child-2"]

    def test_child_device_ids_missing(self):
        dev = _make_device(_raw_device())
        assert dev.child_device_ids is None

    def test_parent_device_id_present(self):
        raw = _raw_device()
        raw["parentDeviceId"] = "parent-7"
        dev = _make_device(raw)
        assert dev.parent_device_id == "parent-7"

    def test_parent_device_id_missing(self):
        dev = _make_device(_raw_device())
        assert dev.parent_device_id is None


# ---------------------------------------------------------------------------
# SHCDevice — installation profile write (set_profile / async_set_profile)
# ---------------------------------------------------------------------------

class TestSHCDeviceSetProfile:
    def test_set_profile_puts_full_body_and_updates_raw(self):
        raw = _raw_device(profile="GENERIC", supportedProfiles=["GENERIC", "OUTDOOR"])
        api = _fake_api()
        api.put_device.return_value = {}  # SHC answers empty 2xx → fall back to body
        dev = _make_device(raw, api=api)

        dev.set_profile("OUTDOOR")

        # PUT called with the full device body, profile swapped.
        api.put_device.assert_called_once()
        called_id, called_body = api.put_device.call_args[0]
        assert called_id == "dev-1"
        assert called_body["profile"] == "OUTDOOR"
        # supportedProfiles (and other fields) preserved in the body.
        assert called_body["supportedProfiles"] == ["GENERIC", "OUTDOOR"]
        # Local raw refreshed.
        assert dev.profile == "OUTDOOR"

    def test_set_profile_uses_server_response_when_returned(self):
        # When the SHC returns the canonical object, local state mirrors it.
        raw = _raw_device(profile="GENERIC", supportedProfiles=["GENERIC", "OUTDOOR"])
        api = _fake_api()
        server_body = _raw_device(
            profile="OUTDOOR", supportedProfiles=["GENERIC", "OUTDOOR"], name="Renamed"
        )
        api.put_device.return_value = server_body
        dev = _make_device(raw, api=api)

        dev.set_profile("OUTDOOR")
        assert dev.profile == "OUTDOOR"
        # Server normalization (here: a renamed device) is reflected locally.
        assert dev.name == "Renamed"

    def test_set_profile_rejects_unsupported(self):
        raw = _raw_device(profile="GENERIC", supportedProfiles=["GENERIC", "OUTDOOR"])
        api = _fake_api()
        dev = _make_device(raw, api=api)

        with pytest.raises(SHCException):
            dev.set_profile("LIGHT")
        api.put_device.assert_not_called()
        assert dev.profile == "GENERIC"

    def test_set_profile_allows_any_when_no_supported_list(self):
        # No supportedProfiles advertised → no validation, write proceeds.
        raw = _raw_device(profile="GENERIC")
        api = _fake_api()
        api.put_device.return_value = {}
        dev = _make_device(raw, api=api)

        dev.set_profile("OUTDOOR")
        api.put_device.assert_called_once()
        assert dev.profile == "OUTDOOR"

    def test_set_profile_fires_callbacks(self):
        raw = _raw_device(profile="GENERIC", supportedProfiles=["GENERIC", "OUTDOOR"])
        api = _fake_api()
        api.put_device.return_value = {}
        dev = _make_device(raw, api=api)
        cb = MagicMock()
        dev.subscribe_callback("ent", cb)

        dev.set_profile("OUTDOOR")
        cb.assert_called_once()

    def test_async_set_profile_awaits_put_and_updates_raw(self):
        import asyncio
        from unittest.mock import AsyncMock

        raw = _raw_device(profile="GENERIC", supportedProfiles=["GENERIC", "OUTDOOR"])
        api = _fake_api()
        api.put_device = AsyncMock(return_value={})
        dev = _make_device(raw, api=api)

        asyncio.run(dev.async_set_profile("OUTDOOR"))

        api.put_device.assert_awaited_once()
        called_id, called_body = api.put_device.call_args[0]
        assert called_id == "dev-1"
        assert called_body["profile"] == "OUTDOOR"
        assert dev.profile == "OUTDOOR"

    def test_async_set_profile_rejects_unsupported(self):
        import asyncio
        from unittest.mock import AsyncMock

        raw = _raw_device(profile="GENERIC", supportedProfiles=["GENERIC", "OUTDOOR"])
        api = _fake_api()
        api.put_device = AsyncMock()
        dev = _make_device(raw, api=api)

        with pytest.raises(SHCException):
            asyncio.run(dev.async_set_profile("LIGHT"))
        api.put_device.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCDevice — service wiring
# ---------------------------------------------------------------------------

class TestSHCDeviceServiceWiring:
    def test_device_services_empty_when_no_raw(self):
        dev = _make_device()
        assert dev.device_services == []

    def test_device_service_ids_empty(self):
        dev = _make_device()
        assert dev.device_service_ids == set()

    def test_device_service_lookup_missing(self):
        dev = _make_device()
        assert dev.device_service("PowerSwitch") is None

    def test_device_service_lookup_present(self):
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw_svc = _raw_service("PowerSwitch", state=state)
        dev = _make_device(services=[raw_svc])
        svc = dev.device_service("PowerSwitch")
        assert svc is not None
        assert svc.id == "PowerSwitch"

    def test_device_service_ids_populated(self):
        raw_svc = _raw_service("PowerSwitch", state={"@type": "powerSwitchState"})
        dev = _make_device(services=[raw_svc])
        assert "PowerSwitch" in dev.device_service_ids

    def test_device_services_list_length(self):
        svc1 = _raw_service("PowerSwitch", state={"@type": "powerSwitchState"})
        svc2 = _raw_service(
            "PowerMeter", path="/devices/dev-1/services/PowerMeter",
            state={"@type": "powerMeterState"}
        )
        dev = _make_device(services=[svc1, svc2])
        assert len(dev.device_services) == 2


# ---------------------------------------------------------------------------
# SHCDevice — callbacks
# ---------------------------------------------------------------------------

class TestSHCDeviceCallbacks:
    def test_subscribe_and_fire(self):
        dev = _make_device()
        fired = []
        dev.subscribe_callback("ent1", lambda: fired.append(1))
        dev.update_raw_information(_raw_device(device_id="dev-1"))
        assert fired == [1]

    def test_unsubscribe_callback(self):
        dev = _make_device()
        fired = []
        dev.subscribe_callback("ent1", lambda: fired.append(1))
        dev.unsubscribe_callback("ent1")
        dev.update_raw_information(_raw_device(device_id="dev-1"))
        assert fired == []

    def test_update_raw_mismatching_id_raises(self):
        dev = _make_device(_raw_device(device_id="dev-1"))
        with pytest.raises(SHCException):
            dev.update_raw_information(_raw_device(device_id="different-id"))

    def test_update_raw_updates_data(self):
        dev = _make_device(_raw_device(device_id="dev-1", name="Old Name"))
        new_raw = _raw_device(device_id="dev-1", name="New Name")
        dev.update_raw_information(new_raw)
        assert dev.name == "New Name"

    def test_multiple_callbacks_all_fired(self):
        dev = _make_device()
        results = []
        dev.subscribe_callback("ent1", lambda: results.append("a"))
        dev.subscribe_callback("ent2", lambda: results.append("b"))
        dev.update_raw_information(_raw_device(device_id="dev-1"))
        assert sorted(results) == ["a", "b"]


# ---------------------------------------------------------------------------
# SHCDevice — enumerate_services fallback
# ---------------------------------------------------------------------------

class TestSHCDeviceEnumerateServices:
    def test_enumerate_services_when_no_services_provided(self):
        """When raw_device_services=[] (falsy), _enumerate_services is called
        but only for known service IDs in deviceServiceIds — here none are
        in SUPPORTED_DEVICE_SERVICE_IDS so no API calls happen."""
        raw = _raw_device()
        raw["deviceServiceIds"] = ["UnknownService"]
        api = _fake_api()
        # Pass empty list → triggers _enumerate_services path
        dev = SHCDevice(api=api, raw_device=raw, raw_device_services=[])
        assert dev.device_services == []

    def test_enumerate_services_known_id_calls_api(self):
        raw = _raw_device()
        raw["deviceServiceIds"] = ["PowerSwitch"]
        api = _fake_api()
        svc_data = _raw_service("PowerSwitch", state={"@type": "powerSwitchState"})
        api.get_device_service.return_value = svc_data
        dev = SHCDevice(api=api, raw_device=raw, raw_device_services=[])
        api.get_device_service.assert_called_once_with("dev-1", "PowerSwitch")
        assert dev.device_service("PowerSwitch") is not None


# ---------------------------------------------------------------------------
# SHCDevice — long polling dispatch
# ---------------------------------------------------------------------------

class TestSHCDeviceLongPolling:
    def _device_with_power_service(self):
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw_svc = _raw_service("PowerSwitch", state=state)
        dev = _make_device(services=[raw_svc])
        return dev

    def test_dispatch_known_service(self):
        dev = self._device_with_power_service()
        poll_result = {
            "@type": "DeviceServiceData",
            "id": "PowerSwitch",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/PowerSwitch",
            "state": {"@type": "powerSwitchState", "switchState": "OFF"},
        }
        dev.process_long_polling_poll_result(poll_result)
        svc = dev.device_service("PowerSwitch")
        assert svc.state["switchState"] == "OFF"

    def test_dispatch_unknown_service_logs_debug(self, caplog):
        dev = self._device_with_power_service()
        poll_result = {
            "@type": "DeviceServiceData",
            "id": "NoSuchService",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/NoSuchService",
        }
        import logging
        with caplog.at_level(logging.DEBUG, logger="boschshcpy"):
            dev.process_long_polling_poll_result(poll_result)
        assert "NoSuchService" in caplog.text

    def test_dispatch_wrong_type_ignored(self):
        dev = self._device_with_power_service()
        # wrong @type is silently skipped instead of raising
        dev.process_long_polling_poll_result({"@type": "WrongType", "id": "X"})


# ---------------------------------------------------------------------------
# SHCDevice — summary (smoke test)
# ---------------------------------------------------------------------------

class TestSHCDeviceSummary:
    def test_summary_runs_without_error(self, capsys):
        raw = _raw_device()
        raw["deviceServiceIds"] = []
        dev = _make_device(raw)
        dev.summary()  # should not raise
        out = capsys.readouterr().out
        assert "dev-1" in out


# ---------------------------------------------------------------------------
# SHCDevice — update() short-polls all services
# ---------------------------------------------------------------------------

class TestSHCDeviceUpdate:
    def test_update_short_polls_each_service(self):
        api = _fake_api()
        svc_data = _raw_service("PowerSwitch", state={"@type": "powerSwitchState"})
        # short_poll will call api.get_device_service
        api.get_device_service.return_value = svc_data
        dev = _make_device(services=[svc_data], api=api)
        dev.update()
        # short_poll throttles within 1s, but _last_update starts None → first call fires
        api.get_device_service.assert_called()

    def test_async_update_awaits_async_short_poll(self):
        import asyncio
        from unittest.mock import AsyncMock
        svc_data = _raw_service("PowerSwitch", state={"@type": "powerSwitchState"})
        api = _fake_api()
        # async api: get_device_service is a coroutine returning the raw service
        api.get_device_service = AsyncMock(return_value=svc_data)
        dev = _make_device(services=[svc_data], api=api)
        asyncio.run(dev.async_update())
        api.get_device_service.assert_awaited()
        # the refreshed state must be a dict (not a left-over coroutine — #335)
        assert isinstance(dev.device_services[0].state, dict)


# ---------------------------------------------------------------------------
# SHCDeviceService — basic properties
# ---------------------------------------------------------------------------

class TestSHCDeviceServiceProperties:
    def test_id(self):
        svc = _make_service("BatteryLevel")
        assert svc.id == "BatteryLevel"

    def test_device_id(self):
        svc = _make_service(device_id="my-device")
        assert svc.device_id == "my-device"

    def test_path(self):
        raw = _raw_service("BatteryLevel", path="/devices/d/services/BatteryLevel")
        api = _fake_api()
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        assert svc.path == "/devices/d/services/BatteryLevel"

    def test_state_empty_when_not_in_raw(self):
        svc = _make_service()
        assert svc.state == {}

    def test_state_returned_when_present(self):
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        svc = _make_service(state=state)
        assert svc.state["switchState"] == "ON"


# ---------------------------------------------------------------------------
# SHCDeviceService — callbacks
# ---------------------------------------------------------------------------

class TestSHCDeviceServiceCallbacks:
    def test_subscribe_and_fire_via_long_poll(self):
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        svc = _make_service("PowerSwitch", state=state)
        fired = []
        svc.subscribe_callback("ent1", lambda: fired.append("fired"))
        poll = {
            "@type": "DeviceServiceData",
            "id": "PowerSwitch",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/PowerSwitch",
            "state": {"@type": "powerSwitchState", "switchState": "OFF"},
        }
        svc.process_long_polling_poll_result(poll)
        assert fired == ["fired"]

    def test_unsubscribe_callback(self):
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        svc = _make_service("PowerSwitch", state=state)
        fired = []
        svc.subscribe_callback("ent1", lambda: fired.append("fired"))
        svc.unsubscribe_callback("ent1")
        poll = {
            "@type": "DeviceServiceData",
            "id": "PowerSwitch",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/PowerSwitch",
            "state": {"@type": "powerSwitchState", "switchState": "OFF"},
        }
        svc.process_long_polling_poll_result(poll)
        assert fired == []

    def test_register_event_keypad(self):
        state = {"@type": "keypadState", "keyName": "KEY1"}
        svc = _make_service("Keypad", state=state)
        fired = []
        svc.register_event("KEY1", lambda: fired.append("key1"))
        poll = {
            "@type": "DeviceServiceData",
            "id": "Keypad",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/Keypad",
            "state": {"@type": "keypadState", "keyName": "KEY1"},
        }
        svc.process_long_polling_poll_result(poll)
        assert fired == ["key1"]

    def test_register_event_keypad_wrong_key_not_fired(self):
        state = {"@type": "keypadState", "keyName": "KEY2"}
        svc = _make_service("Keypad", state=state)
        fired = []
        svc.register_event("KEY1", lambda: fired.append("key1"))
        poll = {
            "@type": "DeviceServiceData",
            "id": "Keypad",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/Keypad",
            "state": {"@type": "keypadState", "keyName": "KEY2"},
        }
        svc.process_long_polling_poll_result(poll)
        assert fired == []

    def test_register_event_latest_motion(self):
        state = {"@type": "latestMotionState", "latestMotionDetected": "2024-01-01T00:00:00Z"}
        svc = _make_service("LatestMotion", device_id="motion-dev", state=state)
        fired = []
        svc.register_event("motion-dev", lambda: fired.append("motion"))
        poll = {
            "@type": "DeviceServiceData",
            "id": "LatestMotion",
            "deviceId": "motion-dev",
            "path": "/devices/motion-dev/services/LatestMotion",
            "state": {"@type": "latestMotionState", "latestMotionDetected": "2024-01-01T00:00:01Z"},
        }
        svc.process_long_polling_poll_result(poll)
        assert fired == ["motion"]


# ---------------------------------------------------------------------------
# SHCDeviceService — long poll state assertion
# ---------------------------------------------------------------------------

class TestSHCDeviceServiceLongPoll:
    def test_wrong_inner_at_type_is_skipped(self):
        # A mismatched inner state @type is now defensively skipped (no crash,
        # no state corruption) rather than raising AssertionError.
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        svc = _make_service("PowerSwitch", state=state)
        poll = {
            "@type": "DeviceServiceData",  # outer type correct
            "id": "PowerSwitch",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/PowerSwitch",
            "state": {"@type": "WRONG_TYPE", "switchState": "OFF"},
        }
        svc.process_long_polling_poll_result(poll)  # must not raise
        # original state preserved (not overwritten by the wrong-typed payload)
        assert svc.state["switchState"] == "ON"

    def test_no_state_in_poll_skips_callback(self):
        """When poll result has no 'state' key, callbacks must NOT fire."""
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        svc = _make_service("PowerSwitch", state=state)
        fired = []
        svc.subscribe_callback("ent", lambda: fired.append(1))
        poll = {
            "@type": "DeviceServiceData",
            "id": "PowerSwitch",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/PowerSwitch",
            # no "state" key
        }
        svc.process_long_polling_poll_result(poll)
        assert fired == []

    def test_process_long_polling_wrong_outer_type_is_skipped(self):
        # Wrong outer @type is now defensively skipped instead of asserting.
        svc = _make_service()
        svc.process_long_polling_poll_result({"@type": "WRONG"})  # no raise


# ---------------------------------------------------------------------------
# SHCDeviceService — put_state / put_state_element
# ---------------------------------------------------------------------------

class TestSHCDeviceServicePutState:
    def test_put_state_calls_api(self):
        api = _fake_api()
        raw = _raw_service("PowerSwitch", device_id="dev-1",
                           state={"@type": "powerSwitchState"})
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        svc.put_state({"switchState": "OFF"})
        api.put_device_service_state.assert_called_once_with(
            "dev-1",
            "PowerSwitch",
            {"@type": "powerSwitchState", "switchState": "OFF"},
        )

    def test_put_state_encodes_hash_in_device_id(self):
        """Device IDs containing '#' must be percent-encoded to '%23'."""
        api = _fake_api()
        raw = _raw_service("PowerSwitch", device_id="dev#1",
                           state={"@type": "powerSwitchState"})
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        svc.put_state({"switchState": "ON"})
        args = api.put_device_service_state.call_args[0]
        assert args[0] == "dev%231"

    def test_put_state_element_calls_put_state(self):
        api = _fake_api()
        raw = _raw_service("PowerSwitch", device_id="dev-1",
                           state={"@type": "powerSwitchState"})
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        svc.put_state_element("switchState", "OFF")
        api.put_device_service_state.assert_called_once_with(
            "dev-1",
            "PowerSwitch",
            {"@type": "powerSwitchState", "switchState": "OFF"},
        )


# ---------------------------------------------------------------------------
# SHCDeviceService — short_poll
# ---------------------------------------------------------------------------

class TestSHCDeviceServiceShortPoll:
    def test_short_poll_first_call_hits_api(self):
        api = _fake_api()
        new_raw = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"})
        api.get_device_service.return_value = new_raw
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw = _raw_service("PowerSwitch", state=state)
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        svc.short_poll()
        api.get_device_service.assert_called_once_with("dev-1", "PowerSwitch")
        assert svc.state["switchState"] == "OFF"

    def test_short_poll_second_call_within_1s_skipped(self):
        api = _fake_api()
        new_raw = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"})
        api.get_device_service.return_value = new_raw
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw = _raw_service("PowerSwitch", state=state)
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        svc.short_poll()
        svc.short_poll()  # second call within 1 second — throttled
        assert api.get_device_service.call_count == 1

    def test_short_poll_no_state_key_sets_empty(self):
        api = _fake_api()
        new_raw = _raw_service("PowerSwitch")  # no state key
        api.get_device_service.return_value = new_raw
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw = _raw_service("PowerSwitch", state=state)
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        svc.short_poll()
        assert svc.state == {}

    def test_short_poll_last_update_is_timezone_aware(self):
        """Regression: short_poll must stamp _last_update with a timezone-AWARE datetime
        (datetime.now(timezone.utc)), not the deprecated naive datetime.utcnow()."""
        api = _fake_api()
        api.get_device_service.return_value = _raw_service(
            "PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"}
        )
        raw = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "ON"})
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        svc.short_poll()
        assert svc._last_update is not None
        assert svc._last_update.tzinfo is not None  # aware, not naive utcnow()

    # --- #183: short_poll(fire_callbacks=True) notifies HA on the resubscribe path ---

    def test_short_poll_fires_callbacks_when_opted_in(self):
        """#183: short_poll(fire_callbacks=True) must invoke all registered
        callbacks after updating _raw_state.

        This is the core of the resubscribe-refresh fix: session.py calls
        device.update(fire_callbacks=True) → service.short_poll(fire_callbacks=
        True) after a poll-id resubscribe.  Without firing callbacks the HA
        entity closures are never invoked and the device stays visually stale.
        """
        api = _fake_api()
        new_raw = _raw_service(
            "PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"}
        )
        api.get_device_service.return_value = new_raw
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw = _raw_service("PowerSwitch", state=state)
        svc = SHCDeviceService(api=api, raw_device_service=raw)

        fired = []
        svc.subscribe_callback("entity-a", lambda: fired.append("a"))
        svc.subscribe_callback("entity-b", lambda: fired.append("b"))

        svc.short_poll(fire_callbacks=True)

        assert set(fired) == {"a", "b"}, "Both callbacks must fire when opted in"
        # State was updated first, then callbacks fired
        assert svc.state["switchState"] == "OFF"

    def test_short_poll_default_does_not_fire_callbacks(self):
        """REGRESSION (bug-hunt): the ordinary HA poll path calls short_poll()
        with the default fire_callbacks=False — it must update _raw_state but
        NOT fire callbacks.  Firing on every ~30 s poll of a should_poll=True
        camera switch would fan out redundant schedule_update_ha_state() calls
        to every co-registered entity on the device."""
        api = _fake_api()
        new_raw = _raw_service(
            "PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"}
        )
        api.get_device_service.return_value = new_raw
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw = _raw_service("PowerSwitch", state=state)
        svc = SHCDeviceService(api=api, raw_device_service=raw)

        fired = []
        svc.subscribe_callback("entity-a", lambda: fired.append("a"))

        svc.short_poll()  # default fire_callbacks=False

        assert fired == [], "Default short_poll must NOT fire callbacks"
        # but state IS refreshed so HA's own poll write picks up the new value
        assert svc.state["switchState"] == "OFF"

    def test_short_poll_no_callbacks_registered_is_noop(self):
        """At initial setup _callbacks is empty; short_poll(fire_callbacks=True)
        must not raise."""
        api = _fake_api()
        api.get_device_service.return_value = _raw_service(
            "PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"}
        )
        raw = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "ON"})
        svc = SHCDeviceService(api=api, raw_device_service=raw)
        assert svc._callbacks == {}

        svc.short_poll(fire_callbacks=True)  # must not raise

        assert svc.state["switchState"] == "OFF"

    def test_short_poll_throttled_does_not_fire_callbacks(self):
        """A throttled short_poll (within 1 s) must NOT fire callbacks even when
        opted in (no API call, no state change)."""
        api = _fake_api()
        new_raw = _raw_service(
            "PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"}
        )
        api.get_device_service.return_value = new_raw
        state = {"@type": "powerSwitchState", "switchState": "ON"}
        raw = _raw_service("PowerSwitch", state=state)
        svc = SHCDeviceService(api=api, raw_device_service=raw)

        fired = []
        svc.subscribe_callback("entity-a", lambda: fired.append("a"))

        svc.short_poll(fire_callbacks=True)  # first call — fires
        assert fired == ["a"]

        # Second call within 1 s — throttled; no API call, no callback
        fired.clear()
        svc.short_poll(fire_callbacks=True)
        assert fired == [], "Throttled short_poll must not fire callbacks"

    def test_short_poll_callback_unsubscribe_during_iteration_is_safe(self):
        """Unsubscribing a callback from within another callback during short_poll
        must not raise RuntimeError (list() snapshot semantics)."""
        api = _fake_api()
        api.get_device_service.return_value = _raw_service(
            "PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"}
        )
        raw = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "ON"})
        svc = SHCDeviceService(api=api, raw_device_service=raw)

        calls = []

        def cb_a():
            calls.append("a")
            svc.unsubscribe_callback("entity-b")  # mutate dict while iterating

        def cb_b():
            calls.append("b")

        svc.subscribe_callback("entity-a", cb_a)
        svc.subscribe_callback("entity-b", cb_b)

        svc.short_poll(fire_callbacks=True)  # must not raise RuntimeError

        assert "a" in calls  # cb_a always fires

    def test_device_update_fire_callbacks_propagates_to_services(self):
        """Via SHCDevice.update(fire_callbacks=True): every service fires its own
        callbacks; with the default it stays quiet."""
        api = _fake_api()
        svc1_raw = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "ON"})
        svc2_raw = _raw_service("PowerMeter", device_id="dev-1",
                                state={"@type": "powerMeterState", "powerConsumption": 0.0})
        svc1_updated = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"})
        svc2_updated = _raw_service("PowerMeter", device_id="dev-1",
                                    state={"@type": "powerMeterState", "powerConsumption": 10.5})

        def get_device_service_side_effect(device_id, service_id):
            return svc1_updated if service_id == "PowerSwitch" else svc2_updated

        api.get_device_service.side_effect = get_device_service_side_effect

        dev = _make_device(services=[svc1_raw, svc2_raw], api=api)

        fired = []
        dev.device_service("PowerSwitch").subscribe_callback("e1", lambda: fired.append("switch"))
        dev.device_service("PowerMeter").subscribe_callback("e2", lambda: fired.append("meter"))

        dev.update(fire_callbacks=True)

        assert "switch" in fired
        assert "meter" in fired

    def test_device_update_default_quiet(self):
        """REGRESSION: SHCDevice.update() with the default must NOT fire any
        callbacks (the ordinary HA poll path)."""
        api = _fake_api()
        svc_raw = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "ON"})
        svc_updated = _raw_service("PowerSwitch", state={"@type": "powerSwitchState", "switchState": "OFF"})
        api.get_device_service.return_value = svc_updated

        dev = _make_device(services=[svc_raw], api=api)

        fired = []
        dev.device_service("PowerSwitch").subscribe_callback("e1", lambda: fired.append("switch"))

        dev.update()  # default fire_callbacks=False

        assert fired == [], "Default device.update() must stay quiet"
        # state still refreshed
        assert dev.device_service("PowerSwitch").state["switchState"] == "OFF"


# ---------------------------------------------------------------------------
# SHCDeviceService — summary smoke test
# ---------------------------------------------------------------------------

class TestSHCDeviceServiceSummary:
    def test_summary_runs(self, capsys):
        state = {"@type": "powerSwitchState"}
        svc = _make_service("PowerSwitch", state=state)
        svc.summary()
        out = capsys.readouterr().out
        assert "PowerSwitch" in out


# ---------------------------------------------------------------------------
# SHCDeviceHelper — construction
# ---------------------------------------------------------------------------

class TestSHCDeviceHelperConstruction:
    def test_init_creates_empty_buckets(self):
        from boschshcpy.models_impl import SUPPORTED_MODELS
        api = _fake_api()
        helper = SHCDeviceHelper.__new__(SHCDeviceHelper)
        helper._api = api
        helper._devices_by_model = {}
        for model in SUPPORTED_MODELS:
            helper._devices_by_model[model] = {}
        # All buckets empty
        assert helper.thermostats == []
        assert helper.smoke_detectors == []
        assert helper.motion_detectors == []

    def test_full_init(self):
        api = _fake_api()
        helper = SHCDeviceHelper(api)
        assert helper.thermostats == []


# ---------------------------------------------------------------------------
# SHCDeviceHelper — device_init with unknown model
# ---------------------------------------------------------------------------

class TestSHCDeviceHelperDeviceInit:
    def _helper(self):
        api = _fake_api()
        return SHCDeviceHelper(api), api

    def test_device_init_unknown_model_returns_base_device(self):
        helper, api = self._helper()
        raw = _raw_device(model="COMPLETELY_UNKNOWN_MODEL")
        dev = helper.device_init(raw, [])
        assert isinstance(dev, SHCDevice)

    def test_device_init_known_model_registers_in_bucket(self):
        helper, api = self._helper()
        raw = _raw_device(device_id="shutter-1", model="BBL")
        dev = helper.device_init(raw, [])
        assert "shutter-1" in helper._devices_by_model["BBL"]

    def test_device_init_known_model_appears_in_shutter_controls(self):
        helper, api = self._helper()
        raw = _raw_device(device_id="bbl-1", model="BBL")
        helper.device_init(raw, [])
        controls = helper.shutter_controls
        assert len(controls) == 1

    def test_device_init_two_devices_same_model(self):
        helper, api = self._helper()
        helper.device_init(_raw_device(device_id="bbl-1", model="BBL"), [])
        helper.device_init(_raw_device(device_id="bbl-2", model="BBL"), [])
        assert len(helper.shutter_controls) == 2


# ---------------------------------------------------------------------------
# SHCDeviceHelper — per-model accessor properties
# ---------------------------------------------------------------------------

def _inject_fake_device(helper, model, device_id="dev-x"):
    """Inject a bare SHCDevice stand-in into the helper's model bucket."""
    fake = _make_device(_raw_device(device_id=device_id, model=model))
    helper._devices_by_model[model][device_id] = fake
    return fake


class TestSHCDeviceHelperAccessors:
    def setup_method(self):
        self.helper = SHCDeviceHelper(_fake_api())

    # --- shutter contacts ---
    def test_shutter_contacts_empty(self):
        assert self.helper.shutter_contacts == []

    def test_shutter_contacts_populated(self):
        _inject_fake_device(self.helper, "SWD", "swd-1")
        assert len(self.helper.shutter_contacts) == 1

    def test_shutter_contacts2_swd2(self):
        _inject_fake_device(self.helper, "SWD2", "swd2-1")
        assert len(self.helper.shutter_contacts2) == 1

    def test_shutter_contacts2_plus(self):
        _inject_fake_device(self.helper, "SWD2_PLUS", "swd2p-1")
        assert len(self.helper.shutter_contacts2) == 1

    def test_shutter_contacts2_dual(self):
        _inject_fake_device(self.helper, "SWD2_DUAL", "swd2d-1")
        assert len(self.helper.shutter_contacts2) == 1

    def test_shutter_contacts2_multiple_models_aggregated(self):
        _inject_fake_device(self.helper, "SWD2", "a")
        _inject_fake_device(self.helper, "SWD2_PLUS", "b")
        _inject_fake_device(self.helper, "SWD2_DUAL", "c")
        assert len(self.helper.shutter_contacts2) == 3

    # --- shutter controls ---
    def test_shutter_controls_empty(self):
        assert self.helper.shutter_controls == []

    def test_shutter_controls_populated(self):
        _inject_fake_device(self.helper, "BBL", "bbl-1")
        assert len(self.helper.shutter_controls) == 1

    # --- micromodule shutter controls ---
    def test_micromodule_shutter_controls_empty(self):
        assert self.helper.micromodule_shutter_controls == []

    def test_micromodule_shutter_shutter(self):
        _inject_fake_device(self.helper, "MICROMODULE_SHUTTER", "ms-1")
        assert len(self.helper.micromodule_shutter_controls) == 1

    def test_micromodule_shutter_awning(self):
        _inject_fake_device(self.helper, "MICROMODULE_AWNING", "ma-1")
        assert len(self.helper.micromodule_shutter_controls) == 1

    def test_micromodule_shutter_both(self):
        _inject_fake_device(self.helper, "MICROMODULE_SHUTTER", "ms-1")
        _inject_fake_device(self.helper, "MICROMODULE_AWNING", "ma-1")
        assert len(self.helper.micromodule_shutter_controls) == 2

    # --- micromodule blinds ---
    def test_micromodule_blinds_empty(self):
        assert self.helper.micromodule_blinds == []

    def test_micromodule_blinds_populated(self):
        _inject_fake_device(self.helper, "MICROMODULE_BLINDS", "mb-1")
        assert len(self.helper.micromodule_blinds) == 1

    # --- smart plugs ---
    def test_smart_plugs_empty(self):
        assert self.helper.smart_plugs == []

    def test_smart_plugs_populated(self):
        _inject_fake_device(self.helper, "PSM", "psm-1")
        assert len(self.helper.smart_plugs) == 1

    # --- smart plugs compact ---
    def test_smart_plugs_compact_empty(self):
        assert self.helper.smart_plugs_compact == []

    def test_smart_plugs_compact_plug_compact(self):
        _inject_fake_device(self.helper, "PLUG_COMPACT", "pc-1")
        assert len(self.helper.smart_plugs_compact) == 1

    def test_smart_plugs_compact_dual(self):
        _inject_fake_device(self.helper, "PLUG_COMPACT_DUAL", "pcd-1")
        assert len(self.helper.smart_plugs_compact) == 1

    # --- smoke detectors ---
    def test_smoke_detectors_empty(self):
        assert self.helper.smoke_detectors == []

    def test_smoke_detectors_sd(self):
        _inject_fake_device(self.helper, "SD", "sd-1")
        assert len(self.helper.smoke_detectors) == 1

    def test_smoke_detectors_smoke_detector2(self):
        _inject_fake_device(self.helper, "SMOKE_DETECTOR2", "sd2-1")
        assert len(self.helper.smoke_detectors) == 1

    def test_smoke_detectors_both_aggregated(self):
        _inject_fake_device(self.helper, "SD", "sd-1")
        _inject_fake_device(self.helper, "SMOKE_DETECTOR2", "sd2-1")
        assert len(self.helper.smoke_detectors) == 2

    # --- climate controls ---
    def test_climate_controls_empty(self):
        assert self.helper.climate_controls == []

    def test_climate_controls_populated(self):
        _inject_fake_device(self.helper, "ROOM_CLIMATE_CONTROL", "rcc-1")
        assert len(self.helper.climate_controls) == 1

    # --- thermostats ---
    def test_thermostats_empty(self):
        assert self.helper.thermostats == []

    def test_thermostats_trv(self):
        _inject_fake_device(self.helper, "TRV", "trv-1")
        assert len(self.helper.thermostats) == 1

    def test_thermostats_trv_gen2(self):
        _inject_fake_device(self.helper, "TRV_GEN2", "trv2-1")
        assert len(self.helper.thermostats) == 1

    def test_thermostats_trv_gen2_dual(self):
        _inject_fake_device(self.helper, "TRV_GEN2_DUAL", "trv2d-1")
        assert len(self.helper.thermostats) == 1

    def test_thermostats_all_three_aggregated(self):
        _inject_fake_device(self.helper, "TRV", "a")
        _inject_fake_device(self.helper, "TRV_GEN2", "b")
        _inject_fake_device(self.helper, "TRV_GEN2_DUAL", "c")
        assert len(self.helper.thermostats) == 3

    # --- wall thermostats ---
    def test_wallthermostats_empty(self):
        assert self.helper.wallthermostats == []

    def test_wallthermostats_thb(self):
        _inject_fake_device(self.helper, "THB", "thb-1")
        assert len(self.helper.wallthermostats) == 1

    def test_wallthermostats_bwth(self):
        _inject_fake_device(self.helper, "BWTH", "bwth-1")
        assert len(self.helper.wallthermostats) == 1

    def test_wallthermostats_bwth24(self):
        _inject_fake_device(self.helper, "BWTH24", "bwth24-1")
        assert len(self.helper.wallthermostats) == 1

    # --- room thermostats ---
    def test_roomthermostats_empty(self):
        assert self.helper.roomthermostats == []

    def test_roomthermostats_bat(self):
        _inject_fake_device(self.helper, "RTH2_BAT", "rth-bat")
        assert len(self.helper.roomthermostats) == 1

    def test_roomthermostats_230(self):
        _inject_fake_device(self.helper, "RTH2_230", "rth-230")
        assert len(self.helper.roomthermostats) == 1

    # --- motion detectors ---
    def test_motion_detectors_empty(self):
        assert self.helper.motion_detectors == []

    def test_motion_detectors_populated(self):
        _inject_fake_device(self.helper, "MD", "md-1")
        assert len(self.helper.motion_detectors) == 1

    def test_motion_detectors2_empty(self):
        assert self.helper.motion_detectors2 == []

    def test_motion_detectors2_populated(self):
        _inject_fake_device(self.helper, "MD2", "md2-1")
        assert len(self.helper.motion_detectors2) == 1

    # --- twinguards ---
    def test_twinguards_empty(self):
        assert self.helper.twinguards == []

    def test_twinguards_populated(self):
        _inject_fake_device(self.helper, "TWINGUARD", "tg-1")
        assert len(self.helper.twinguards) == 1

    # --- universal switches ---
    def test_universal_switches_empty(self):
        assert self.helper.universal_switches == []

    def test_universal_switches_wrc2(self):
        _inject_fake_device(self.helper, "WRC2", "wrc2-1")
        assert len(self.helper.universal_switches) == 1

    def test_universal_switches_switch2(self):
        _inject_fake_device(self.helper, "SWITCH2", "sw2-1")
        assert len(self.helper.universal_switches) == 1

    # --- cameras ---
    def test_camera_eyes_empty(self):
        assert self.helper.camera_eyes == []

    def test_camera_eyes_populated(self):
        _inject_fake_device(self.helper, "CAMERA_EYES", "cam-eyes")
        assert len(self.helper.camera_eyes) == 1

    def test_camera_360_empty(self):
        assert self.helper.camera_360 == []

    def test_camera_360_populated(self):
        _inject_fake_device(self.helper, "CAMERA_360", "cam-360")
        assert len(self.helper.camera_360) == 1

    def test_camera_outdoor_gen2_empty(self):
        assert self.helper.camera_outdoor_gen2 == []

    def test_camera_outdoor_gen2_populated(self):
        _inject_fake_device(self.helper, "CAMERA_OUTDOOR_GEN2", "cam-gen2")
        assert len(self.helper.camera_outdoor_gen2) == 1

    # --- lights ---
    def test_ledvance_lights_empty(self):
        assert self.helper.ledvance_lights == []

    def test_ledvance_lights_populated(self):
        _inject_fake_device(self.helper, "LEDVANCE_LIGHT", "lv-1")
        assert len(self.helper.ledvance_lights) == 1

    def test_hue_lights_empty(self):
        assert self.helper.hue_lights == []

    def test_hue_lights_populated(self):
        _inject_fake_device(self.helper, "HUE_LIGHT", "hue-1")
        assert len(self.helper.hue_lights) == 1

    # --- water leakage ---
    def test_water_leakage_detectors_empty(self):
        assert self.helper.water_leakage_detectors == []

    def test_water_leakage_detectors_populated(self):
        _inject_fake_device(self.helper, "WLS", "wls-1")
        assert len(self.helper.water_leakage_detectors) == 1

    # --- light switches ---
    def test_light_switches_bsm_empty(self):
        assert self.helper.light_switches_bsm == []

    def test_light_switches_bsm_populated(self):
        _inject_fake_device(self.helper, "BSM", "bsm-1")
        assert len(self.helper.light_switches_bsm) == 1

    # --- micromodule light attached ---
    def test_micromodule_light_attached_empty(self):
        assert self.helper.micromodule_light_attached == []

    def test_micromodule_light_attached_populated(self):
        _inject_fake_device(self.helper, "MICROMODULE_LIGHT_ATTACHED", "mla-1")
        assert len(self.helper.micromodule_light_attached) == 1

    # --- micromodule light controls ---
    def test_micromodule_light_controls_empty(self):
        assert self.helper.micromodule_light_controls == []

    def test_micromodule_light_controls_populated(self):
        _inject_fake_device(self.helper, "MICROMODULE_LIGHT_CONTROL", "mlc-1")
        assert len(self.helper.micromodule_light_controls) == 1

    # --- heating circuits ---
    def test_heating_circuits_empty(self):
        assert self.helper.heating_circuits == []

    def test_heating_circuits_populated(self):
        _inject_fake_device(self.helper, "HEATING_CIRCUIT", "hc-1")
        assert len(self.helper.heating_circuits) == 1

    # --- micromodule dimmers ---
    def test_micromodule_dimmers_empty(self):
        assert self.helper.micromodule_dimmers == []

    def test_micromodule_dimmers_populated(self):
        _inject_fake_device(self.helper, "MICROMODULE_DIMMER", "mmd-1")
        assert len(self.helper.micromodule_dimmers) == 1


# ---------------------------------------------------------------------------
# SHCDeviceHelper — micromodule relay type filtering
# ---------------------------------------------------------------------------

class TestSHCDeviceHelperRelayTypeFiltering:
    """micromodule_relays vs micromodule_impulse_relays filter by relay_type."""

    def _helper_with_relay(self, has_impulse_service: bool, device_id: str):
        helper = SHCDeviceHelper(_fake_api())
        # Build a fake relay that has the correct relay_type
        fake = MagicMock()
        from boschshcpy.models_impl import SHCMicromoduleRelay
        if has_impulse_service:
            fake.relay_type = SHCMicromoduleRelay.RelayType.BUTTON
        else:
            fake.relay_type = SHCMicromoduleRelay.RelayType.SWITCH
        helper._devices_by_model["MICROMODULE_RELAY"][device_id] = fake
        return helper

    def test_switch_type_appears_in_relays(self):
        helper = self._helper_with_relay(has_impulse_service=False, device_id="r-sw")
        assert len(helper.micromodule_relays) == 1
        assert len(helper.micromodule_impulse_relays) == 0

    def test_button_type_appears_in_impulse_relays(self):
        helper = self._helper_with_relay(has_impulse_service=True, device_id="r-btn")
        assert len(helper.micromodule_relays) == 0
        assert len(helper.micromodule_impulse_relays) == 1

    def test_mixed_relays_split_correctly(self):
        helper = SHCDeviceHelper(_fake_api())
        from boschshcpy.models_impl import SHCMicromoduleRelay
        sw = MagicMock()
        sw.relay_type = SHCMicromoduleRelay.RelayType.SWITCH
        btn = MagicMock()
        btn.relay_type = SHCMicromoduleRelay.RelayType.BUTTON
        helper._devices_by_model["MICROMODULE_RELAY"]["sw-1"] = sw
        helper._devices_by_model["MICROMODULE_RELAY"]["btn-1"] = btn
        assert len(helper.micromodule_relays) == 1
        assert len(helper.micromodule_impulse_relays) == 1


# ---------------------------------------------------------------------------
# SHCDeviceHelper — presence_simulation_system / smoke_detection_system
# ---------------------------------------------------------------------------

class TestSHCDeviceHelperSingletonDevices:
    def test_presence_simulation_none_when_empty(self):
        helper = SHCDeviceHelper(_fake_api())
        assert helper.presence_simulation_system is None

    def test_presence_simulation_returned_when_registered(self):
        helper = SHCDeviceHelper(_fake_api())
        fake = MagicMock(name="PresenceSim")
        helper._devices_by_model["PRESENCE_SIMULATION_SERVICE"][
            "presenceSimulationService"
        ] = fake
        assert helper.presence_simulation_system is fake

    def test_smoke_detection_system_none_when_empty(self):
        helper = SHCDeviceHelper(_fake_api())
        assert helper.smoke_detection_system is None

    def test_smoke_detection_system_returned_when_registered(self):
        helper = SHCDeviceHelper(_fake_api())
        fake = MagicMock(name="SmokeDetSys")
        helper._devices_by_model["SMOKE_DETECTION_SYSTEM"]["smokeDetectionSystem"] = fake
        assert helper.smoke_detection_system is fake

    def test_presence_simulation_wrong_key_returns_none(self):
        helper = SHCDeviceHelper(_fake_api())
        fake = MagicMock()
        helper._devices_by_model["PRESENCE_SIMULATION_SERVICE"]["wrongKey"] = fake
        assert helper.presence_simulation_system is None

    def test_smoke_detection_system_wrong_key_returns_none(self):
        helper = SHCDeviceHelper(_fake_api())
        fake = MagicMock()
        helper._devices_by_model["SMOKE_DETECTION_SYSTEM"]["wrongKey"] = fake
        assert helper.smoke_detection_system is None


class TestKeypadEventReplaySuppression:
    """Restart-replay bug: the post-subscribe snapshot must not re-fire the last press."""

    def test_replayed_keypad_event_is_suppressed_then_new_one_fires(self):
        # Service constructed from the snapshot of the last press (ts=1000).
        state = {"@type": "keypadState", "keyName": "UPPER_BUTTON",
                 "eventType": "PRESS_SHORT", "eventTimestamp": 1000}
        svc = _make_service("Keypad", device_id="kp-1", state=state)
        fired = []
        svc.register_event("UPPER_BUTTON", lambda: fired.append("up"))

        # 1) Post-subscribe snapshot replays the SAME last press → must NOT fire.
        replay = {"@type": "DeviceServiceData", "id": "Keypad", "deviceId": "kp-1",
                  "path": "/devices/kp-1/services/Keypad",
                  "state": {"@type": "keypadState", "keyName": "UPPER_BUTTON",
                            "eventType": "PRESS_SHORT", "eventTimestamp": 1000}}
        svc.process_long_polling_poll_result(replay)
        assert fired == []

        # 2) A genuine new press (newer timestamp) → fires.
        new = {"@type": "DeviceServiceData", "id": "Keypad", "deviceId": "kp-1",
               "path": "/devices/kp-1/services/Keypad",
               "state": {"@type": "keypadState", "keyName": "UPPER_BUTTON",
                         "eventType": "PRESS_SHORT", "eventTimestamp": 2000}}
        svc.process_long_polling_poll_result(new)
        assert fired == ["up"]

    def test_motion_replay_suppressed(self):
        state = {"@type": "latestMotionState", "latestMotionDetected": "2026-06-21T10:00:00Z"}
        svc = _make_service("LatestMotion", device_id="md-1", state=state)
        fired = []
        svc.register_event("md-1", lambda: fired.append("m"))
        replay = {"@type": "DeviceServiceData", "id": "LatestMotion", "deviceId": "md-1",
                  "path": "/devices/md-1/services/LatestMotion",
                  "state": {"@type": "latestMotionState",
                            "latestMotionDetected": "2026-06-21T10:00:00Z"}}
        svc.process_long_polling_poll_result(replay)
        assert fired == []
