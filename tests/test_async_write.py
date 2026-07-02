"""Tests for async write methods across boschshcpy models.

Coverage targets (all new async_* methods added for the async write path):
  device_service.py  async_put_state / async_put_state_element
  models_impl.py     all async_set_* / async_stop* / async_trigger* methods
  domain_impl.py     async_arm* / async_disarm / async_mute
  scenario.py        async_trigger
  userdefinedstate.py async_set_state

Strategy:
  - No pytest-asyncio dependency — use asyncio.run() inside plain sync tests.
  - Mock the async API with unittest.mock.AsyncMock.
  - Each test asserts the awaited call was made with the correct arguments.
  - Build devices/objects via __new__ + attribute injection (same pattern as
    test_models_impl.py) so no real network or HA harness is needed.
"""

import asyncio
from unittest.mock import AsyncMock


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _fake_raw_device(model="PSM", device_id="device-1"):
    return {
        "id": device_id,
        "rootDeviceId": "root-1",
        "manufacturer": "BOSCH",
        "roomId": "room-1",
        "deviceModel": model,
        "serial": "SER-001",
        "profile": model,
        "name": "Test Device",
        "status": "AVAILABLE",
        "deviceServiceIds": [],
    }


def _make_async_api(api_root="https://192.168.0.1:8444/smarthome"):
    """Return an AsyncMock that mimics SHCAPIAsync for write operations."""
    api = AsyncMock()
    api._api_root = api_root
    api.put_device_service_state = AsyncMock()
    api.post_domain_action = AsyncMock()
    api._put_api_or_fail = AsyncMock()
    return api


def _fake_async_service(cls, svc_id, state, api):
    """Build a service instance wired to an async API."""
    from boschshcpy.device_service import SHCDeviceService
    svc = SHCDeviceService.__new__(SHCDeviceService)
    svc._api = api
    svc._raw_device_service = {
        "id": svc_id,
        "deviceId": "device-1",
        "path": f"/devices/device-1/services/{svc_id}",
        "state": state,
    }
    svc._raw_state = state
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


def _inject(obj, api, **service_attrs):
    """Wire an async api and named service attributes onto a device."""
    obj._api = api
    obj._callbacks = {}
    obj._device_services_by_id = {}
    for attr, svc in service_attrs.items():
        setattr(obj, attr, svc)


# ---------------------------------------------------------------------------
# device_service.py — async_put_state / async_put_state_element
# ---------------------------------------------------------------------------

class TestDeviceServiceAsyncWrite:
    def _make_svc(self, state_type="roomClimateControlState"):
        api = _make_async_api()
        state = {"@type": state_type, "setpointTemperature": 20.0}
        from boschshcpy.device_service import SHCDeviceService
        svc = SHCDeviceService.__new__(SHCDeviceService)
        svc._api = api
        svc._raw_device_service = {
            "id": "RoomClimateControl",
            "deviceId": "dev-1",
            "path": "/devices/dev-1/services/RoomClimateControl",
            "state": state,
        }
        svc._raw_state = state
        svc._last_update = None
        svc._callbacks = {}
        svc._event_callbacks = {}
        return svc, api

    def test_async_put_state(self):
        svc, api = self._make_svc()
        asyncio.run(svc.async_put_state({"setpointTemperature": 22.0}))
        api.put_device_service_state.assert_awaited_once_with(
            "dev-1",
            "RoomClimateControl",
            {"@type": "roomClimateControlState", "setpointTemperature": 22.0},
        )

    def test_async_put_state_element(self):
        svc, api = self._make_svc()
        asyncio.run(svc.async_put_state_element("setpointTemperature", 19.0))
        api.put_device_service_state.assert_awaited_once_with(
            "dev-1",
            "RoomClimateControl",
            {"@type": "roomClimateControlState", "setpointTemperature": 19.0},
        )

    def test_async_put_state_encodes_hash_in_device_id(self):
        """device_id containing '#' must be percent-encoded to '%23'."""
        api = _make_async_api()
        from boschshcpy.device_service import SHCDeviceService
        svc = SHCDeviceService.__new__(SHCDeviceService)
        svc._api = api
        svc._raw_device_service = {
            "id": "ShutterControl",
            "deviceId": "dev#1",
            "path": "/x",
            "state": {"@type": "shutterControlState"},
        }
        svc._raw_state = {"@type": "shutterControlState"}
        svc._last_update = None
        svc._callbacks = {}
        svc._event_callbacks = {}
        asyncio.run(svc.async_put_state_element("operationState", "STOPPED"))
        api.put_device_service_state.assert_awaited_once_with(
            "dev%231",  # '#' encoded
            "ShutterControl",
            {"@type": "shutterControlState", "operationState": "STOPPED"},
        )


# ---------------------------------------------------------------------------
# SHCChildProtection (_ChildProtection mixin)
# ---------------------------------------------------------------------------

class TestChildProtectionAsync:
    def _make(self, as_thermostat=False):
        from boschshcpy.services_impl import ChildProtectionService, ThermostatService
        api = _make_async_api()
        if as_thermostat:
            svc_cls = ThermostatService
            svc_id = "Thermostat"
            state = {"@type": "thermostatServiceState", "childLock": "OFF"}
        else:
            svc_cls = ChildProtectionService
            svc_id = "ChildProtection"
            state = {"@type": "ChildProtectionState", "childLockActive": False}
        svc = _fake_async_service(svc_cls, svc_id, state, api)

        if as_thermostat:
            from boschshcpy.models_impl import SHCThermostat
            obj = SHCThermostat.__new__(SHCThermostat)
            _inject(obj, api, _thermostat_service=svc)
        else:
            from boschshcpy.models_impl import SHCLightSwitch
            obj = SHCLightSwitch.__new__(SHCLightSwitch)
            _inject(obj, api, _childprotection_service=svc)
        obj._raw_device = _fake_raw_device()
        return obj, api

    def test_child_protection_async_set_child_lock_true(self):
        obj, api = self._make(as_thermostat=False)
        asyncio.run(obj.async_set_child_lock(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "ChildProtection",
            {"@type": "ChildProtectionState", "childLockActive": True},
        )

    def test_child_protection_async_set_child_lock_false(self):
        obj, api = self._make(as_thermostat=False)
        asyncio.run(obj.async_set_child_lock(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "ChildProtection",
            {"@type": "ChildProtectionState", "childLockActive": False},
        )

    def test_thermostat_async_set_child_lock_on(self):
        obj, api = self._make(as_thermostat=True)
        asyncio.run(obj.async_set_child_lock(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Thermostat",
            {"@type": "thermostatServiceState", "childLock": "ON"},
        )

    def test_thermostat_async_set_child_lock_off(self):
        obj, api = self._make(as_thermostat=True)
        asyncio.run(obj.async_set_child_lock(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Thermostat",
            {"@type": "thermostatServiceState", "childLock": "OFF"},
        )


# ---------------------------------------------------------------------------
# _PowerSwitch mixin — async_set_switchstate
# ---------------------------------------------------------------------------

class TestPowerSwitchAsync:
    def _make(self):
        from boschshcpy.services_impl import PowerSwitchService
        from boschshcpy.models_impl import SHCSmartPlug
        api = _make_async_api()
        state = {"@type": "powerSwitchState", "switchState": "OFF"}
        svc = _fake_async_service(PowerSwitchService, "PowerSwitch", state, api)
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        _inject(obj, api, _powerswitch_service=svc)
        obj._raw_device = _fake_raw_device()
        return obj, api

    def test_async_set_switchstate_on(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_switchstate(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PowerSwitch",
            {"@type": "powerSwitchState", "switchState": "ON"},
        )

    def test_async_set_switchstate_off(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_switchstate(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PowerSwitch",
            {"@type": "powerSwitchState", "switchState": "OFF"},
        )


# ---------------------------------------------------------------------------
# _TemperatureOffset mixin — async_set_offset
# ---------------------------------------------------------------------------

class TestTemperatureOffsetAsync:
    def _make(self):
        from boschshcpy.services_impl import TemperatureOffsetService
        from boschshcpy.models_impl import SHCThermostat
        api = _make_async_api()
        state = {"@type": "temperatureOffsetState", "offset": 0.0}
        svc = _fake_async_service(TemperatureOffsetService, "TemperatureOffset", state, api)
        obj = SHCThermostat.__new__(SHCThermostat)
        _inject(obj, api, _temperatureoffset_service=svc)
        obj._raw_device = _fake_raw_device()
        return obj, api

    def test_async_set_offset(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_offset(1.5))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "TemperatureOffset",
            {"@type": "temperatureOffsetState", "offset": 1.5},
        )


# ---------------------------------------------------------------------------
# _SilentMode mixin — async_set_silentmode
# ---------------------------------------------------------------------------

class TestSilentModeAsync:
    def _make(self, has_service=True):
        from boschshcpy.services_impl import SilentModeService
        from boschshcpy.models_impl import SHCThermostat
        api = _make_async_api()
        if has_service:
            state = {"@type": "SilentModeServiceState", "mode": "MODE_NORMAL"}
            svc = _fake_async_service(SilentModeService, "SilentMode", state, api)
        else:
            svc = None
        obj = SHCThermostat.__new__(SHCThermostat)
        _inject(obj, api, _silentmode_service=svc)
        obj._raw_device = _fake_raw_device()
        return obj, api

    def test_async_set_silentmode_on(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_silentmode(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "SilentMode",
            {"@type": "SilentModeServiceState", "mode": "MODE_SILENT"},
        )

    def test_async_set_silentmode_off(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_silentmode(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "SilentMode",
            {"@type": "SilentModeServiceState", "mode": "MODE_NORMAL"},
        )

    def test_async_set_silentmode_no_service_is_noop(self):
        """When silentmode service is None, async_set_silentmode must not raise."""
        obj, api = self._make(has_service=False)
        asyncio.run(obj.async_set_silentmode(True))
        api.put_device_service_state.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCSmokeDetector — async_set_alarmstate, async_smoketest_requested
# ---------------------------------------------------------------------------

class TestSmokeDetectorAsync:
    def _make(self):
        from boschshcpy.services_impl import AlarmService, SmokeDetectorCheckService
        from boschshcpy.models_impl import SHCSmokeDetector
        api = _make_async_api()
        alarm_state = {"@type": "alarmState", "value": "IDLE_OFF"}
        check_state = {"@type": "smokeDetectorCheckState", "value": "SMOKE_TEST_OK"}
        alarm_svc = _fake_async_service(AlarmService, "Alarm", alarm_state, api)
        check_svc = _fake_async_service(SmokeDetectorCheckService, "SmokeDetectorCheck", check_state, api)
        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        _inject(obj, api, _alarm_service=alarm_svc, _smokedetectorcheck_service=check_svc)
        obj._raw_device = _fake_raw_device(model="SD")
        return obj, api

    def test_async_set_alarmstate(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_alarmstate("MUTE_ALARM"))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Alarm",
            {"@type": "alarmState", "value": "MUTE_ALARM"},
        )

    def test_async_smoketest_requested(self):
        obj, api = self._make()
        asyncio.run(obj.async_smoketest_requested())
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "SmokeDetectorCheck",
            {"@type": "smokeDetectorCheckState", "value": "SMOKE_TEST_REQUESTED"},
        )


# ---------------------------------------------------------------------------
# SHCSmartPlug — async_set_routing
# ---------------------------------------------------------------------------

class TestSmartPlugRoutingAsync:
    def _make(self):
        from boschshcpy.services_impl import RoutingService
        from boschshcpy.models_impl import SHCSmartPlug
        api = _make_async_api()
        state = {"@type": "routingState", "value": "DISABLED"}
        svc = _fake_async_service(RoutingService, "Routing", state, api)
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        _inject(obj, api, _powerswitch_service=None, _routing_service=svc)
        obj._raw_device = _fake_raw_device()
        return obj, api

    def test_async_set_routing_enabled(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_routing(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Routing",
            {"@type": "routingState", "value": "ENABLED"},
        )

    def test_async_set_routing_disabled(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_routing(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Routing",
            {"@type": "routingState", "value": "DISABLED"},
        )


# ---------------------------------------------------------------------------
# SHCShutterControl — async_set_level, async_stop
# ---------------------------------------------------------------------------

class TestShutterControlAsync:
    def _make(self):
        from boschshcpy.services_impl import ShutterControlService
        from boschshcpy.models_impl import SHCShutterControl
        api = _make_async_api()
        state = {"@type": "shutterControlServiceState", "level": 0.5, "operationState": "STOPPED"}
        svc = _fake_async_service(ShutterControlService, "ShutterControl", state, api)
        obj = SHCShutterControl.__new__(SHCShutterControl)
        _inject(obj, api, _service=svc)
        obj._raw_device = _fake_raw_device(model="BBL")
        return obj, api

    def test_async_set_level(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_level(0.75))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "ShutterControl",
            {"@type": "shutterControlServiceState", "level": 0.75},
        )

    def test_async_stop(self):
        obj, api = self._make()
        asyncio.run(obj.async_stop())
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "ShutterControl",
            {"@type": "shutterControlServiceState", "operationState": "STOPPED"},
        )


# ---------------------------------------------------------------------------
# SHCMicromoduleBlinds — async_set_target_angle, async_stop_blinds,
#                         async_set_blinds_level
# ---------------------------------------------------------------------------

class TestMicromoduleBlindsAsync:
    def _make(self):
        from boschshcpy.services_impl import (
            ShutterControlService, BlindsControlService, BlindsSceneControlService,
        )
        from boschshcpy.models_impl import SHCMicromoduleBlinds
        api = _make_async_api()

        shutter_state = {
            "@type": "shutterControlServiceState",
            "level": 0.5,
            "operationState": "STOPPED",
        }
        blinds_state = {
            "@type": "BlindsControlServiceState",
            "currentAngle": 0.0,
            "targetAngle": 0.5,
            "blindsType": "SLAT_BLIND",
        }
        scene_state = {
            "@type": "BlindsSceneControlServiceState",
            "level": 0.6,
            "angle": 0.3,
        }
        shutter_svc = _fake_async_service(ShutterControlService, "ShutterControl", shutter_state, api)
        blinds_svc = _fake_async_service(BlindsControlService, "BlindsControl", blinds_state, api)
        # Build BlindsSceneControlService instance (not plain SHCDeviceService) so
        # the .angle property is available for async_set_blinds_level.
        scene_svc = BlindsSceneControlService.__new__(BlindsSceneControlService)
        scene_svc._api = api
        scene_svc._raw_device_service = {
            "id": "BlindsSceneControl",
            "deviceId": "device-1",
            "path": "/devices/device-1/services/BlindsSceneControl",
            "state": scene_state,
        }
        scene_svc._raw_state = scene_state
        scene_svc._last_update = None
        scene_svc._callbacks = {}
        scene_svc._event_callbacks = {}

        obj = SHCMicromoduleBlinds.__new__(SHCMicromoduleBlinds)
        _inject(
            obj,
            api,
            _service=shutter_svc,
            _blindscontrol_service=blinds_svc,
            _blindsscenecontrol_service=scene_svc,
            _keypad_service=None,
        )
        obj._raw_device = _fake_raw_device(model="MICROMODULE_BLINDS")
        return obj, api

    def test_async_set_target_angle(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_target_angle(0.25))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "BlindsControl",
            {"@type": "BlindsControlServiceState", "targetAngle": 0.25},
        )

    def test_async_stop_blinds(self):
        obj, api = self._make()
        asyncio.run(obj.async_stop_blinds())
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "ShutterControl",
            {"@type": "shutterControlServiceState", "operationState": "STOPPED"},
        )

    def test_async_set_blinds_level(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_blinds_level(0.8))
        # BlindsSceneControl PUT must include both level AND current angle
        # (spec requirement — angle is read from current state: 0.3)
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "BlindsSceneControl",
            {"@type": "BlindsSceneControlServiceState", "level": 0.8, "angle": 0.3},
        )


# ---------------------------------------------------------------------------
# SHCShutterContact2 — async_set_bypass
# ---------------------------------------------------------------------------

class TestShutterContactBypassAsync:
    def _make(self):
        from boschshcpy.services_impl import BypassService
        from boschshcpy.models_impl import SHCShutterContact2
        api = _make_async_api()
        state = {"@type": "BypassState", "state": "BYPASS_INACTIVE"}
        svc = _fake_async_service(BypassService, "Bypass", state, api)
        obj = SHCShutterContact2.__new__(SHCShutterContact2)
        _inject(obj, api, _bypass_service=svc)
        obj._raw_device = _fake_raw_device(model="SWD2")
        return obj, api

    def test_async_set_bypass_active(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_bypass(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Bypass",
            {"@type": "BypassState", "state": "BYPASS_ACTIVE"},
        )

    def test_async_set_bypass_inactive(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_bypass(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Bypass",
            {"@type": "BypassState", "state": "BYPASS_INACTIVE"},
        )


# ---------------------------------------------------------------------------
# BypassService / SHCShutterContact2 — async_set_bypass_configuration
#
# rawscan-database.md (SWD2/SWD2_PLUS, hass#245/#78): bypassState carries a
# nested configuration{enabled, timeout, infinite} block (timed/auto-expiring
# bypass) that was previously never read or written at all.
# ---------------------------------------------------------------------------

class TestBypassConfigurationAsync:
    def _fake_bypass_service(self, state, api):
        # _fake_async_service() always builds a bare SHCDeviceService (it
        # ignores its cls arg), which lacks BypassService's config-specific
        # properties/methods — build the real subclass instance here.
        from boschshcpy.services_impl import BypassService
        svc = BypassService.__new__(BypassService)
        svc._api = api
        svc._raw_device_service = {
            "id": "Bypass",
            "deviceId": "device-1",
            "path": "/devices/device-1/services/Bypass",
            "state": state,
        }
        svc._raw_state = state
        svc._last_update = None
        svc._callbacks = {}
        svc._event_callbacks = {}
        return svc

    def _make(self):
        from boschshcpy.models_impl import SHCShutterContact2
        api = _make_async_api()
        state = {
            "@type": "BypassState",
            "state": "BYPASS_INACTIVE",
            "configuration": {"enabled": True, "timeout": 5, "infinite": False},
        }
        svc = self._fake_bypass_service(state, api)
        obj = SHCShutterContact2.__new__(SHCShutterContact2)
        _inject(obj, api, _bypass_service=svc)
        obj._raw_device = _fake_raw_device(model="SWD2")
        return obj, svc, api

    def test_service_config_put_merges_full_block(self):
        # Changing only timeout must still PUT the whole configuration block
        # (mirrors OutdoorSirenService._merged_config — Bosch requires it).
        # Only the `configuration` key is sent, matching the existing
        # single-key PUT pattern (async_set_bypass sends only `state`).
        obj, svc, api = self._make()
        asyncio.run(svc.async_set_bypass_configuration(timeout=30))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Bypass",
            {
                "@type": "BypassState",
                "configuration": {"enabled": True, "timeout": 30, "infinite": False},
            },
        )

    def test_service_config_put_override_multiple(self):
        obj, svc, api = self._make()
        asyncio.run(svc.async_set_bypass_configuration(enabled=False, infinite=True))
        body = api.put_device_service_state.call_args.args[2]
        cfg = body["configuration"]
        assert cfg == {"enabled": False, "timeout": 5, "infinite": True}

    def test_service_config_put_skipped_when_unknown(self):
        """No configuration block yet (e.g. partial state push) -> skip the
        write rather than PUT a block of zeros that wipes user settings."""
        api = _make_async_api()
        state = {"@type": "BypassState", "state": "BYPASS_INACTIVE"}
        svc = self._fake_bypass_service(state, api)
        asyncio.run(svc.async_set_bypass_configuration(timeout=10))
        api.put_device_service_state.assert_not_awaited()

    def test_model_delegates_to_service(self):
        obj, svc, api = self._make()
        asyncio.run(obj.async_set_bypass_configuration(timeout=60, infinite=False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "Bypass",
            {
                "@type": "BypassState",
                "configuration": {"enabled": True, "timeout": 60, "infinite": False},
            },
        )

    def test_model_read_props_delegate_to_service(self):
        obj, svc, api = self._make()
        assert obj.bypass_configuration_enabled is True
        assert obj.bypass_timeout == 5
        assert obj.bypass_infinite is False


# ---------------------------------------------------------------------------
# SHCShutterContact2Plus — async_set_vibration_enabled, async_set_sensitivity
# ---------------------------------------------------------------------------

class TestVibrationSensorAsync:
    def _make(self):
        from boschshcpy.services_impl import VibrationSensorService
        from boschshcpy.models_impl import SHCShutterContact2Plus
        api = _make_async_api()
        state = {
            "@type": "VibrationSensorServiceState",
            "value": "NO_VIBRATION",
            "enabled": False,
            "sensitivity": "LOW",
        }
        svc = _fake_async_service(VibrationSensorService, "VibrationSensor", state, api)
        obj = SHCShutterContact2Plus.__new__(SHCShutterContact2Plus)
        _inject(obj, api, _vibrationsensor_service=svc)
        obj._raw_device = _fake_raw_device(model="SWD2_PLUS")
        return obj, api

    def test_async_set_vibration_enabled_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_vibration_enabled(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "VibrationSensor",
            {"@type": "VibrationSensorServiceState", "enabled": True},
        )

    def test_async_set_sensitivity(self):
        from boschshcpy.services_impl import VibrationSensorService
        obj, api = self._make()
        asyncio.run(obj.async_set_sensitivity(VibrationSensorService.SensitivityState.HIGH))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "VibrationSensor",
            {"@type": "VibrationSensorServiceState", "sensitivity": "HIGH"},
        )


# ---------------------------------------------------------------------------
# SHCCamera360 — async_set_privacymode, async_set_cameranotification
# ---------------------------------------------------------------------------

class TestCamera360Async:
    def _make(self, has_notification=True):
        from boschshcpy.services_impl import PrivacyModeService, CameraNotificationService
        from boschshcpy.models_impl import SHCCamera360
        api = _make_async_api()
        privacy_state = {"@type": "PrivacyModeState", "value": "ENABLED"}
        privacy_svc = _fake_async_service(PrivacyModeService, "PrivacyMode", privacy_state, api)
        if has_notification:
            notif_state = {"@type": "CameraNotificationState", "value": "DISABLED"}
            notif_svc = _fake_async_service(CameraNotificationService, "CameraNotification", notif_state, api)
        else:
            notif_svc = None
        obj = SHCCamera360.__new__(SHCCamera360)
        _inject(obj, api, _privacymode_service=privacy_svc, _cameranotification_service=notif_svc)
        obj._raw_device = _fake_raw_device(model="CAMERA_360")
        return obj, api

    def test_async_set_privacymode_on(self):
        """True = camera on = DISABLED privacy mode."""
        obj, api = self._make()
        asyncio.run(obj.async_set_privacymode(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PrivacyMode",
            {"@type": "PrivacyModeState", "value": "DISABLED"},
        )

    def test_async_set_privacymode_off(self):
        """False = camera off = ENABLED privacy mode."""
        obj, api = self._make()
        asyncio.run(obj.async_set_privacymode(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PrivacyMode",
            {"@type": "PrivacyModeState", "value": "ENABLED"},
        )

    def test_async_set_cameranotification_enabled(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cameranotification(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "CameraNotification",
            {"@type": "CameraNotificationState", "value": "ENABLED"},
        )

    def test_async_set_cameranotification_disabled(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cameranotification(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "CameraNotification",
            {"@type": "CameraNotificationState", "value": "DISABLED"},
        )

    def test_async_set_cameranotification_no_service_is_noop(self):
        obj, api = self._make(has_notification=False)
        asyncio.run(obj.async_set_cameranotification(True))
        api.put_device_service_state.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCCameraEyes — async_set_cameralight
# ---------------------------------------------------------------------------

class TestCameraEyesAsync:
    def _make(self, has_light=True):
        from boschshcpy.services_impl import PrivacyModeService, CameraLightService
        from boschshcpy.models_impl import SHCCameraEyes
        api = _make_async_api()
        privacy_svc = _fake_async_service(
            PrivacyModeService, "PrivacyMode",
            {"@type": "PrivacyModeState", "value": "ENABLED"}, api
        )
        if has_light:
            light_state = {"@type": "CameraLightState", "value": "OFF"}
            light_svc = _fake_async_service(CameraLightService, "CameraLight", light_state, api)
        else:
            light_svc = None
        obj = SHCCameraEyes.__new__(SHCCameraEyes)
        _inject(obj, api,
                _privacymode_service=privacy_svc,
                _cameranotification_service=None,
                _cameralight_service=light_svc)
        obj._raw_device = _fake_raw_device(model="CAMERA_EYES")
        return obj, api

    def test_async_set_cameralight_on(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cameralight(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "CameraLight",
            {"@type": "CameraLightState", "value": "ON"},
        )

    def test_async_set_cameralight_off(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cameralight(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "CameraLight",
            {"@type": "CameraLightState", "value": "OFF"},
        )

    def test_async_set_cameralight_no_service_is_noop(self):
        obj, api = self._make(has_light=False)
        asyncio.run(obj.async_set_cameralight(True))
        api.put_device_service_state.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCCameraOutdoorGen2 — async_set_cameraambientlight, async_set_camerafrontlight
# ---------------------------------------------------------------------------

class TestCameraOutdoorGen2Async:
    def _make(self, has_ambient=True, has_front=True):
        from boschshcpy.services_impl import (
            PrivacyModeService, CameraAmbientLightService, CameraFrontLightService,
        )
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        api = _make_async_api()
        privacy_svc = _fake_async_service(
            PrivacyModeService, "PrivacyMode",
            {"@type": "PrivacyModeState", "value": "ENABLED"}, api
        )
        ambient_svc = _fake_async_service(
            CameraAmbientLightService, "CameraAmbientLight",
            {"@type": "CameraAmbientLightState", "value": "OFF"}, api
        ) if has_ambient else None
        front_svc = _fake_async_service(
            CameraFrontLightService, "CameraFrontLight",
            {"@type": "CameraFrontLightState", "value": "OFF"}, api
        ) if has_front else None
        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        _inject(obj, api,
                _privacymode_service=privacy_svc,
                _cameranotification_service=None,
                _cameraambientlight_service=ambient_svc,
                _camerafrontlight_service=front_svc)
        obj._raw_device = _fake_raw_device(model="CAMERA_OUTDOOR_GEN2")
        return obj, api

    def test_async_set_cameraambientlight_on(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cameraambientlight(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "CameraAmbientLight",
            {"@type": "CameraAmbientLightState", "value": "ON"},
        )

    def test_async_set_cameraambientlight_off(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cameraambientlight(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "CameraAmbientLight",
            {"@type": "CameraAmbientLightState", "value": "OFF"},
        )

    def test_async_set_cameraambientlight_no_service_is_noop(self):
        obj, api = self._make(has_ambient=False)
        asyncio.run(obj.async_set_cameraambientlight(True))
        api.put_device_service_state.assert_not_awaited()

    def test_async_set_camerafrontlight_on(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_camerafrontlight(True))
        api.put_device_service_state.assert_awaited_with(
            "device-1",
            "CameraFrontLight",
            {"@type": "CameraFrontLightState", "value": "ON"},
        )

    def test_async_set_camerafrontlight_off(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_camerafrontlight(False))
        api.put_device_service_state.assert_awaited_with(
            "device-1",
            "CameraFrontLight",
            {"@type": "CameraFrontLightState", "value": "OFF"},
        )

    def test_async_set_camerafrontlight_no_service_is_noop(self):
        obj, api = self._make(has_front=False)
        asyncio.run(obj.async_set_camerafrontlight(True))
        api.put_device_service_state.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCClimateControl — all async setters
# ---------------------------------------------------------------------------

class TestClimateControlAsync:
    def _make(self):
        from boschshcpy.services_impl import RoomClimateControlService
        from boschshcpy.models_impl import SHCClimateControl
        api = _make_async_api()
        state = {
            "@type": "climateControlState",
            "setpointTemperature": 20.0,
            "operationMode": "AUTOMATIC",
            "boostMode": False,
            "low": False,
            "summerMode": False,
            "roomControlMode": "HEATING",
            "supportsBoostMode": True,
            "supportsCooling": False,
            "hasDemand": False,
        }
        svc = _fake_async_service(RoomClimateControlService, "RoomClimateControl", state, api)
        obj = SHCClimateControl.__new__(SHCClimateControl)
        _inject(obj, api, _roomclimatecontrol_service=svc)
        obj._raw_device = _fake_raw_device(model="ROOM_CLIMATE_CONTROL")
        return obj, api

    def test_async_set_setpoint_temperature(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_setpoint_temperature(22.5))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "setpointTemperature": 22.5},
        )

    def test_async_set_operation_mode(self):
        from boschshcpy.services_impl import RoomClimateControlService
        obj, api = self._make()
        asyncio.run(obj.async_set_operation_mode(
            RoomClimateControlService.OperationMode.MANUAL
        ))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "operationMode": "MANUAL"},
        )

    def test_async_set_boost_mode_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_boost_mode(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "boostMode": True},
        )

    def test_async_set_low_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_low(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "low": True},
        )

    def test_async_set_summer_mode_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_summer_mode(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "summerMode": True},
        )

    def test_async_set_room_control_mode(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_room_control_mode("COOLING"))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "roomControlMode": "COOLING"},
        )

    def test_async_set_cooling_mode_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cooling_mode(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "roomControlMode": "COOLING"},
        )

    def test_async_set_cooling_mode_false(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_cooling_mode(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "RoomClimateControl",
            {"@type": "climateControlState", "roomControlMode": "HEATING"},
        )


# ---------------------------------------------------------------------------
# SHCHeatingCircuit — async_set_setpoint_temperature, async_set_operation_mode
# ---------------------------------------------------------------------------

class TestHeatingCircuitAsync:
    def _make(self):
        from boschshcpy.services_impl import HeatingCircuitService
        from boschshcpy.models_impl import SHCHeatingCircuit
        api = _make_async_api()
        state = {
            "@type": "HeatingCircuitServiceState",
            "setpointTemperature": 20.0,
            "operationMode": "AUTOMATIC",
            "on": True,
            "setpointTemperatureForLevelEco": 16.0,
            "setpointTemperatureForLevelComfort": 21.0,
            "temperatureOverrideModeActive": False,
            "temperatureOverrideFeatureEnabled": False,
            "energySavingFeatureEnabled": False,
        }
        svc = _fake_async_service(HeatingCircuitService, "HeatingCircuit", state, api)
        obj = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
        _inject(obj, api, _heating_circuit_service=svc)
        obj._raw_device = _fake_raw_device(model="HEATING_CIRCUIT")
        return obj, api

    def test_async_set_setpoint_temperature(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_setpoint_temperature(19.0))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "HeatingCircuit",
            {"@type": "HeatingCircuitServiceState", "setpointTemperature": 19.0},
        )

    def test_async_set_operation_mode(self):
        from boschshcpy.services_impl import HeatingCircuitService
        obj, api = self._make()
        asyncio.run(obj.async_set_operation_mode(
            HeatingCircuitService.OperationMode.MANUAL
        ))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "HeatingCircuit",
            {"@type": "HeatingCircuitServiceState", "operationMode": "MANUAL"},
        )

    def test_async_set_setpoint_temperature_eco(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_setpoint_temperature_eco(15.0))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "HeatingCircuit",
            {"@type": "HeatingCircuitServiceState", "setpointTemperatureForLevelEco": 15.0},
        )

    def test_async_set_setpoint_temperature_comfort(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_setpoint_temperature_comfort(23.0))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "HeatingCircuit",
            {"@type": "HeatingCircuitServiceState", "setpointTemperatureForLevelComfort": 23.0},
        )


# ---------------------------------------------------------------------------
# SHCMotionDetector2 — async_set_multi_level_switch, async_set_binaryswitch,
#                      async_set_motion_sensitivity, async_set_pet_immunity_enabled
# ---------------------------------------------------------------------------

class TestMotionDetector2Async:
    def _make(self):
        from boschshcpy.services_impl import (
            MultiLevelSwitchService, BinarySwitchService,
            PirSensorConfigurationService, PetImmunityService,
        )
        from boschshcpy.models_impl import SHCMotionDetector2
        api = _make_async_api()
        mls_svc = _fake_async_service(
            MultiLevelSwitchService, "MultiLevelSwitch",
            {"@type": "MultiLevelSwitchState", "level": 50}, api
        )
        bs_svc = _fake_async_service(
            BinarySwitchService, "BinarySwitch",
            {"@type": "BinarySwitchState", "on": False}, api
        )
        pir_svc = _fake_async_service(
            PirSensorConfigurationService, "PirSensorConfiguration",
            {"@type": "PirSensorConfigurationState", "motionSensitivity": "NORMAL"}, api
        )
        pet_svc = _fake_async_service(
            PetImmunityService, "PetImmunity",
            {"@type": "PetImmunityState", "enabled": False}, api
        )
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        _inject(obj, api,
                _multi_level_switch_service=mls_svc,
                _binaryswitch_service=bs_svc,
                _pirsensorconfiguration_service=pir_svc,
                _petimmunity_service=pet_svc)
        obj._raw_device = _fake_raw_device(model="MD2")
        return obj, api

    def test_async_set_multi_level_switch(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_multi_level_switch(75))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "MultiLevelSwitch",
            {"@type": "MultiLevelSwitchState", "level": 75},
        )

    def test_async_set_binaryswitch_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_binaryswitch(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "BinarySwitch",
            {"@type": "BinarySwitchState", "on": True},
        )

    def test_async_set_motion_sensitivity(self):
        from boschshcpy.services_impl import PirSensorConfigurationService
        obj, api = self._make()
        asyncio.run(obj.async_set_motion_sensitivity(
            PirSensorConfigurationService.MotionSensitivity.HIGH
        ))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PirSensorConfiguration",
            {"@type": "PirSensorConfigurationState", "motionSensitivity": "HIGH"},
        )

    def test_async_set_pet_immunity_enabled_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_pet_immunity_enabled(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PetImmunity",
            {"@type": "PetImmunityState", "enabled": True},
        )


# ---------------------------------------------------------------------------
# SHCPresenceSimulationSystem — async_set_enabled
# ---------------------------------------------------------------------------

class TestPresenceSimulationAsync:
    def _make(self):
        from boschshcpy.services_impl import PresenceSimulationConfigurationService
        from boschshcpy.models_impl import SHCPresenceSimulationSystem
        api = _make_async_api()
        state = {"@type": "PresenceSimulationConfigurationState", "enabled": False}
        svc = _fake_async_service(PresenceSimulationConfigurationService,
                                  "PresenceSimulationConfiguration", state, api)
        obj = SHCPresenceSimulationSystem.__new__(SHCPresenceSimulationSystem)
        _inject(obj, api, _presencesimulationconfiguration_service=svc)
        obj._raw_device = _fake_raw_device(model="PRESENCE_SIMULATION_SERVICE")
        return obj, api

    def test_async_set_enabled_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_enabled(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PresenceSimulationConfiguration",
            {"@type": "PresenceSimulationConfigurationState", "enabled": True},
        )

    def test_async_set_enabled_false(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_enabled(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PresenceSimulationConfiguration",
            {"@type": "PresenceSimulationConfigurationState", "enabled": False},
        )


# ---------------------------------------------------------------------------
# SHCLight — async_set_binarystate, async_set_brightness, async_set_color,
#             async_set_rgb
# ---------------------------------------------------------------------------

class TestLightAsync:
    def _make(self, has_brightness=True, has_color_temp=True, has_color_hsb=True):
        from boschshcpy.services_impl import (
            BinarySwitchService, MultiLevelSwitchService,
            HueColorTemperatureService, HSBColorActuatorService,
        )
        from boschshcpy.models_impl import SHCLight
        api = _make_async_api()
        bs_svc = _fake_async_service(
            BinarySwitchService, "BinarySwitch",
            {"@type": "BinarySwitchState", "on": False}, api
        )
        mls_svc = _fake_async_service(
            MultiLevelSwitchService, "MultiLevelSwitch",
            {"@type": "MultiLevelSwitchState", "level": 50}, api
        ) if has_brightness else None
        hct_svc = _fake_async_service(
            HueColorTemperatureService, "HueColorTemperature",
            {"@type": "HueColorTemperatureState", "colorTemperature": 3000, "minValue": 2000, "maxValue": 6500}, api
        ) if has_color_temp else None
        hsb_svc = _fake_async_service(
            HSBColorActuatorService, "HSBColorActuator",
            {"@type": "HSBColorActuatorState", "rgb": 0xFF0000, "minValue": 0, "maxValue": 16777215}, api
        ) if has_color_hsb else None

        obj = SHCLight.__new__(SHCLight)
        _inject(obj, api,
                _binaryswitch_service=bs_svc,
                _multilevelswitch_service=mls_svc,
                _huecolortemperature_service=hct_svc,
                _hsbcoloractuator_service=hsb_svc)
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities(0)
        if has_brightness:
            obj._capabilities |= _L.Capabilities.BRIGHTNESS
        if has_color_temp:
            obj._capabilities |= _L.Capabilities.COLOR_TEMP
        if has_color_hsb:
            obj._capabilities |= _L.Capabilities.COLOR_HSB
        obj._raw_device = _fake_raw_device(model="LEDVANCE_LIGHT")
        return obj, api

    def test_async_set_binarystate_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_binarystate(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "BinarySwitch",
            {"@type": "BinarySwitchState", "on": True},
        )

    def test_async_set_binarystate_false(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_binarystate(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "BinarySwitch",
            {"@type": "BinarySwitchState", "on": False},
        )

    def test_async_set_brightness(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_brightness(80))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "MultiLevelSwitch",
            {"@type": "MultiLevelSwitchState", "level": 80},
        )

    def test_async_set_brightness_no_service_is_noop(self):
        obj, api = self._make(has_brightness=False)
        asyncio.run(obj.async_set_brightness(80))
        api.put_device_service_state.assert_not_awaited()

    def test_async_set_color(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_color(4000))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "HueColorTemperature",
            {"@type": "HueColorTemperatureState", "colorTemperature": 4000},
        )

    def test_async_set_color_no_service_is_noop(self):
        obj, api = self._make(has_color_temp=False, has_color_hsb=False)
        asyncio.run(obj.async_set_color(4000))
        api.put_device_service_state.assert_not_awaited()

    def test_async_set_rgb(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_rgb(0x00FF00))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "HSBColorActuator",
            {"@type": "HSBColorActuatorState", "rgb": 0x00FF00},
        )

    def test_async_set_rgb_no_service_is_noop(self):
        obj, api = self._make(has_color_hsb=False, has_color_temp=False)
        asyncio.run(obj.async_set_rgb(0x00FF00))
        api.put_device_service_state.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCMicromoduleDimmer — async_set_binarystate (overrides SHCLight version)
# ---------------------------------------------------------------------------

class TestMicromoduleDimmerAsync:
    def _make(self, has_powerswitch=True):
        from boschshcpy.services_impl import PowerSwitchService
        from boschshcpy.models_impl import SHCMicromoduleDimmer
        api = _make_async_api()
        if has_powerswitch:
            ps_svc = _fake_async_service(
                PowerSwitchService, "PowerSwitch",
                {"@type": "powerSwitchState", "switchState": "OFF"}, api
            )
        else:
            ps_svc = None
        obj = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
        _inject(obj, api,
                _powerswitch_service=ps_svc,
                _binaryswitch_service=None,
                _multilevelswitch_service=None,
                _huecolortemperature_service=None,
                _hsbcoloractuator_service=None)
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities(0)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_DIMMER")
        return obj, api

    def test_async_set_binarystate_on(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_binarystate(True))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PowerSwitch",
            {"@type": "powerSwitchState", "switchState": "ON"},
        )

    def test_async_set_binarystate_off(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_binarystate(False))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "PowerSwitch",
            {"@type": "powerSwitchState", "switchState": "OFF"},
        )

    def test_async_set_binarystate_no_powerswitch_is_noop(self):
        obj, api = self._make(has_powerswitch=False)
        asyncio.run(obj.async_set_binarystate(True))
        api.put_device_service_state.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCMicromoduleRelay — async_trigger_impulse_state, async_set_impulse_length
# ---------------------------------------------------------------------------

class TestMicromoduleRelayAsync:
    def _make(self, has_impulse=True):
        from boschshcpy.services_impl import PowerSwitchService, ImpulseSwitchService
        from boschshcpy.models_impl import SHCMicromoduleRelay
        api = _make_async_api()
        ps_svc = _fake_async_service(
            PowerSwitchService, "PowerSwitch",
            {"@type": "powerSwitchState", "switchState": "OFF"}, api
        )
        if has_impulse:
            impulse_svc = _fake_async_service(
                ImpulseSwitchService, "ImpulseSwitch",
                {"@type": "ImpulseSwitchState", "impulseState": False, "impulseLength": 10,
                 "instantOfLastImpulse": "2024-01-01T00:00:00.000Z"}, api
            )
        else:
            impulse_svc = None
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        _inject(obj, api, _powerswitch_service=ps_svc, _impulseswitch_service=impulse_svc,
                _childprotection_service=None)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_RELAY")
        return obj, api

    def test_async_trigger_impulse_state(self):
        obj, api = self._make()
        asyncio.run(obj.async_trigger_impulse_state())
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "ImpulseSwitch",
            {"@type": "ImpulseSwitchState", "impulseState": True},
        )

    def test_async_trigger_impulse_state_no_service_is_noop(self):
        obj, api = self._make(has_impulse=False)
        asyncio.run(obj.async_trigger_impulse_state())
        api.put_device_service_state.assert_not_awaited()

    def test_async_set_impulse_length(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_impulse_length(20))
        api.put_device_service_state.assert_awaited_once_with(
            "device-1",
            "ImpulseSwitch",
            {"@type": "ImpulseSwitchState", "impulseLength": 20},
        )

    def test_async_set_impulse_length_no_service_is_noop(self):
        obj, api = self._make(has_impulse=False)
        asyncio.run(obj.async_set_impulse_length(20))
        api.put_device_service_state.assert_not_awaited()


# ---------------------------------------------------------------------------
# SHCIntrusionSystem — arm variants, disarm, mute
# ---------------------------------------------------------------------------

class TestIntrusionSystemAsync:
    def _make(self):
        from boschshcpy.domain_impl import SHCIntrusionSystem
        api = _make_async_api()
        raw_domain_state = {
            "systemAvailability": {"available": True},
            "armingState": {"state": "SYSTEM_DISARMED"},
            "alarmState": {"value": "ALARM_OFF", "incidents": []},
            "activeConfigurationProfile": {"profileId": "0"},
            "securityGapState": {"securityGaps": []},
        }
        obj = SHCIntrusionSystem(api=api, raw_domain_state=raw_domain_state,
                                 root_device_id="root-1")
        return obj, api

    def test_async_arm(self):
        obj, api = self._make()
        asyncio.run(obj.async_arm())
        api.post_domain_action.assert_awaited_once_with("intrusion/actions/arm")

    def test_async_arm_full_protection(self):
        obj, api = self._make()
        asyncio.run(obj.async_arm_full_protection())
        api.post_domain_action.assert_awaited_once_with(
            "intrusion/actions/arm",
            {"@type": "armRequest", "profileId": "0"},
        )

    def test_async_arm_partial_protection(self):
        obj, api = self._make()
        asyncio.run(obj.async_arm_partial_protection())
        api.post_domain_action.assert_awaited_once_with(
            "intrusion/actions/arm",
            {"@type": "armRequest", "profileId": "1"},
        )

    def test_async_arm_individual_protection(self):
        obj, api = self._make()
        asyncio.run(obj.async_arm_individual_protection())
        api.post_domain_action.assert_awaited_once_with(
            "intrusion/actions/arm",
            {"@type": "armRequest", "profileId": "2"},
        )

    def test_async_disarm(self):
        obj, api = self._make()
        asyncio.run(obj.async_disarm())
        api.post_domain_action.assert_awaited_once_with("intrusion/actions/disarm")

    def test_async_mute(self):
        obj, api = self._make()
        asyncio.run(obj.async_mute())
        api.post_domain_action.assert_awaited_once_with("intrusion/actions/mute")


# ---------------------------------------------------------------------------
# SHCScenario — async_trigger
# ---------------------------------------------------------------------------

class TestScenarioAsync:
    def _make(self):
        from boschshcpy.scenario import SHCScenario
        api = _make_async_api()
        raw_scenario = {
            "id": "scenario-1",
            "iconId": "icon-1",
            "name": "Test Scenario",
        }
        obj = SHCScenario(api=api, raw_scenario=raw_scenario)
        return obj, api

    def test_async_trigger(self):
        obj, api = self._make()
        asyncio.run(obj.async_trigger())
        api._post_api_or_fail.assert_awaited_once_with(
            f"{api._api_root}/scenarios/scenario-1/triggers", ""
        )


# ---------------------------------------------------------------------------
# SHCUserDefinedState — async_set_state
# ---------------------------------------------------------------------------

class TestUserDefinedStateAsync:
    def _make(self):
        from boschshcpy.userdefinedstate import SHCUserDefinedState
        api = _make_async_api()
        # SHCInformation is only used for macAddress; stub it.
        info = type("FakeInfo", (), {"macAddress": "AA:BB:CC:DD:EE:FF"})()
        raw_state = {
            "id": "uds-1",
            "name": "Vacation Mode",
            "state": False,
            "deleted": False,
        }
        obj = SHCUserDefinedState(api=api, info=info, raw_state=raw_state)
        return obj, api

    def test_async_set_state_true(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_state(True))
        api._put_api_or_fail.assert_awaited_once_with(
            f"{api._api_root}/userdefinedstates/uds-1/state", True
        )

    def test_async_set_state_false(self):
        obj, api = self._make()
        asyncio.run(obj.async_set_state(False))
        api._put_api_or_fail.assert_awaited_once_with(
            f"{api._api_root}/userdefinedstates/uds-1/state", False
        )
