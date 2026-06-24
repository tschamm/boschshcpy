"""Tests for the APK-driven additions (#120 OutdoorSiren, #174 SD II intrusion
alarm, #186 controller software-update info).

Strategy mirrors test_async_write.py: build services/devices via __new__ +
attribute injection, mock the (async) API, and assert the awaited write/POST
calls carry the correct field/value — including the Bosch *_REQUESTED quirk.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_svc(cls, state, api=None):
    svc = cls.__new__(cls)
    svc._api = api if api is not None else MagicMock()
    svc._raw_device_service = {
        "id": cls.__name__,
        "deviceId": "device-1",
        "path": "/devices/device-1/services/X",
        "state": {"@type": "testState", **state},
    }
    svc._raw_state = svc._raw_device_service["state"]
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


# ---------------------------------------------------------------------------
# #120 OutdoorSirenService
# ---------------------------------------------------------------------------

class TestOutdoorSirenService:
    def _svc(self, api=None, **state):
        from boschshcpy.services_impl import OutdoorSirenService
        base = {
            "acousticAlarmOn": False,
            "visualAlarmOn": False,
            "tamperActivated": False,
            "outdoorSirenConfiguration": {
                "alarmDuration": 3,
                "flashDuration": 5,
                "soundLevel": "MEDIUM",
                "alarmDelay": 0,
                "flashDelay": 10,
            },
        }
        base.update(state)
        return _make_svc(OutdoorSirenService, base, api)

    def test_read_props(self):
        from boschshcpy.services_impl import OutdoorSirenService
        s = self._svc(acousticAlarmOn=True, tamperActivated=True)
        assert s.acoustic_alarm_on is True
        assert s.visual_alarm_on is False
        assert s.tamper_activated is True
        assert s.alarm_duration == 3
        assert s.flash_duration == 5
        assert s.alarm_delay == 0
        assert s.flash_delay == 10
        assert s.sound_level == OutdoorSirenService.SoundLevel.MEDIUM

    def test_sound_level_bad_value_falls_back(self):
        from boschshcpy.services_impl import OutdoorSirenService
        s = self._svc()
        s._raw_state["outdoorSirenConfiguration"]["soundLevel"] = "BOGUS"
        assert s.sound_level == OutdoorSirenService.SoundLevel.MEDIUM

    def test_config_put_merges_full_block(self):
        from boschshcpy.services_impl import OutdoorSirenService
        api = AsyncMock()
        s = self._svc(api=api)
        # change only the sound level -> all 5 fields must still be sent
        asyncio.run(
            s.async_set_configuration(sound_level=OutdoorSirenService.SoundLevel.HIGH)
        )
        args = api.put_device_service_state.call_args
        body = args.args[2]
        cfg = body["outdoorSirenConfiguration"]
        assert cfg == {
            "alarmDuration": 3,
            "flashDuration": 5,
            "soundLevel": "HIGH",
            "alarmDelay": 0,
            "flashDelay": 10,
        }

    def test_config_put_override_multiple(self):
        s = self._svc(api=AsyncMock())
        asyncio.run(s.async_set_configuration(alarm_duration=9, flash_delay=42))
        body = s._api.put_device_service_state.call_args.args[2]
        cfg = body["outdoorSirenConfiguration"]
        assert cfg["alarmDuration"] == 9
        assert cfg["flashDelay"] == 42
        # untouched fields preserved
        assert cfg["flashDuration"] == 5

    def test_trigger_test_alarm_posts_operation(self):
        from boschshcpy.services_impl import OutdoorSirenService
        api = AsyncMock()
        s = self._svc(api=api)
        asyncio.run(
            s.async_trigger_test_alarm(OutdoorSirenService.SoundLevel.LOW)
        )
        call = api.post_device_service_operation.call_args
        # device_id, service_id, operation, data
        assert call.args[2] == "triggerTestAlarm"
        assert call.args[3] == {"soundLevel": "LOW"}

    def test_trigger_test_alarm_defaults_to_configured_level(self):
        s = self._svc(api=AsyncMock())
        asyncio.run(s.async_trigger_test_alarm())
        call = s._api.post_device_service_operation.call_args
        assert call.args[3] == {"soundLevel": "MEDIUM"}


class TestOutdoorSirenPowerSupplyService:
    def _svc(self, **state):
        from boschshcpy.services_impl import OutdoorSirenPowerSupplyService
        return _make_svc(OutdoorSirenPowerSupplyService, state)

    def test_read_props(self):
        from boschshcpy.services_impl import OutdoorSirenPowerSupplyService as P
        s = self._svc(
            batteryPercentageRemaining=87,
            mainPowerSupply="SOLAR",
            solarChargingScore="GOOD",
            configuredPowerSupply="DC",
            batteryDefect=True,
        )
        assert s.battery_percentage_remaining == 87
        assert s.main_power_supply == P.MainPowerSupply.SOLAR
        assert s.solar_charging_score == P.SolarChargingScore.GOOD
        assert s.configured_power_supply == P.ConfiguredPowerSupply.DC
        assert s.battery_defect is True

    def test_unknown_enum_falls_back(self):
        from boschshcpy.services_impl import OutdoorSirenPowerSupplyService as P
        s = self._svc(mainPowerSupply="WEIRD")
        assert s.main_power_supply == P.MainPowerSupply.UNKNOWN


class TestSHCOutdoorSirenDevice:
    def test_registered_in_model_mapping(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCOutdoorSiren
        assert MODEL_MAPPING["OUTDOOR_SIREN"] is SHCOutdoorSiren

    def test_device_test_alarm_delegates(self):
        from boschshcpy.models_impl import SHCOutdoorSiren
        siren_svc = MagicMock()
        siren_svc.async_trigger_test_alarm = AsyncMock()
        dev = SHCOutdoorSiren.__new__(SHCOutdoorSiren)
        dev._siren_service = siren_svc
        dev._powersupply_service = None
        assert dev.supports_power_supply is False
        asyncio.run(dev.async_trigger_test_alarm())
        siren_svc.async_trigger_test_alarm.assert_awaited_once()


# ---------------------------------------------------------------------------
# #174 SD II intrusion alarm trigger
# ---------------------------------------------------------------------------

class TestSmokeDetectorIntrusionAlarm:
    def _detector(self, model="SMOKE_DETECTOR2", alarm_value="IDLE_OFF", api=None):
        from boschshcpy.models_impl import SHCSmokeDetector
        from boschshcpy.services_impl import AlarmService
        alarm = AlarmService.__new__(AlarmService)
        alarm._api = api if api is not None else AsyncMock()
        alarm._raw_device_service = {
            "id": "Alarm", "deviceId": "d1", "path": "/x",
            "state": {"@type": "alarmState", "value": alarm_value},
        }
        alarm._raw_state = alarm._raw_device_service["state"]
        alarm._last_update = None
        alarm._callbacks = {}
        alarm._event_callbacks = {}

        dev = SHCSmokeDetector.__new__(SHCSmokeDetector)
        dev._raw_device = {"deviceModel": model, "id": "d1"}
        dev._device_services_by_id = {"Alarm": alarm}
        dev._callbacks = {}
        dev._api = alarm._api
        dev._alarm_service = alarm
        dev._smokedetectorcheck_service = None
        dev._smoke_sensitivity_service = None
        return dev, alarm

    def test_sd2_supports_intrusion_alarm(self):
        dev, _ = self._detector(model="SMOKE_DETECTOR2")
        assert dev.supports_intrusion_alarm is True

    def test_gen1_does_not_support_intrusion_alarm(self):
        dev, _ = self._detector(model="SD")
        assert dev.supports_intrusion_alarm is False

    def test_set_intrusion_alarm_on_uses_requested_value(self):
        api = AsyncMock()
        dev, _ = self._detector(api=api)
        asyncio.run(dev.async_set_intrusion_alarm(True))
        body = api.put_device_service_state.call_args.args[2]
        assert body["value"] == "INTRUSION_ALARM_ON_REQUESTED"

    def test_set_intrusion_alarm_off_uses_requested_value(self):
        api = AsyncMock()
        dev, _ = self._detector(api=api)
        asyncio.run(dev.async_set_intrusion_alarm(False))
        body = api.put_device_service_state.call_args.args[2]
        assert body["value"] == "INTRUSION_ALARM_OFF_REQUESTED"

    def test_intrusion_alarm_reflects_state(self):
        # Real SD II read-back values (spec AlarmState enum) must not raise and
        # must map to the right bool.
        dev_off, _ = self._detector(alarm_value="IDLE_OFF")
        assert dev_off.intrusion_alarm is False
        dev_on, _ = self._detector(alarm_value="INTRUSION_ALARM_ON_REQUESTED")
        assert dev_on.intrusion_alarm is True
        dev_off2, _ = self._detector(alarm_value="INTRUSION_ALARM_OFF_REQUESTED")
        assert dev_off2.intrusion_alarm is False

    def test_alarm_service_value_does_not_raise_on_requested_states(self):
        # #174 BLOCKER regression guard: the *_REQUESTED read-back values must be
        # valid AlarmService.State members.
        _, alarm = self._detector(alarm_value="INTRUSION_ALARM_ON_REQUESTED")
        assert alarm.value.value == "INTRUSION_ALARM_ON_REQUESTED"


# ---------------------------------------------------------------------------
# #186 controller software-update info
# ---------------------------------------------------------------------------

class TestSHCInformationSoftwareUpdate:
    def _info(self, **sw):
        from boschshcpy.information import SHCInformation
        info = SHCInformation.__new__(SHCInformation)
        info._pub_info = {"softwareUpdateState": sw}
        return info

    def test_available_version(self):
        info = self._info(
            swInstalledVersion="10.20.1234",
            swUpdateAvailableVersion="10.25.5678",
            automaticUpdatesEnabled=True,
            swUpdateState="UPDATE_AVAILABLE",
        )
        assert info.version == "10.20.1234"
        assert info.available_version == "10.25.5678"
        assert info.automatic_updates_enabled is True
        assert info.updateState == info.UpdateState.UPDATE_AVAILABLE

    def test_missing_fields_return_none(self):
        info = self._info()
        assert info.available_version is None
        assert info.automatic_updates_enabled is None
