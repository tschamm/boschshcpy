"""APK BATCHES 2-4 — new service class tests.

Batch 2: Smart Plug services (EnergySavingMode, LedBrightnessConfiguration,
         PowerSwitchConfiguration, PowerSwitchWarning)
Batch 3: Motion Detector II services (WalkTest, SmartSensitivityControl)
Batch 4: Twinguard / SmokeDetector services (SmokeSensitivity,
         TwinguardNightlyPromise)
"""

import asyncio


# ---------------------------------------------------------------------------
# Helpers (same pattern as test_apk_batch1.py)
# ---------------------------------------------------------------------------

def _make_svc(cls, state_dict):
    """Build a service via __new__ with injected fake state."""
    svc = cls.__new__(cls)
    raw = {
        "id": cls.__name__,
        "deviceId": "test-device",
        "path": "/test",
        "state": {"@type": "testType", **state_dict},
    }
    svc._api = None
    svc._raw_device_service = raw
    svc._raw_state = raw["state"]
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


def _fake_raw_device(model="PSM"):
    return {
        "@type": "device",
        "rootDeviceId": "root",
        "id": "test-device",
        "deviceServiceIds": [],
        "manufacturer": "BOSCH",
        "roomId": "hz_1",
        "deviceModel": model,
        "serial": "FAKE000000",
        "profile": "GENERIC",
        "name": "Test Device",
        "status": "AVAILABLE",
        "childDeviceIds": [],
    }


def _make_model(cls, service_map):
    """Build a device model via __new__ with injected service map."""
    obj = cls.__new__(cls)
    obj._raw_device = _fake_raw_device(model="PSM")
    obj._device_services_by_id = service_map
    obj._callbacks = {}
    obj._api = None
    # Manually wire service attributes (mirror __init__ pattern)
    for attr, svc_id in _SERVICE_ATTRS.get(cls.__name__, {}).items():
        setattr(obj, attr, service_map.get(svc_id))
    return obj


# Map model class name → {attr_name: service_id}
_SERVICE_ATTRS = {
    "SHCSmartPlug": {
        "_routing_service": "Routing",
        "_energy_saving_mode_service": "EnergySavingMode",
        "_led_brightness_configuration_service": "LedBrightnessConfiguration",
        "_power_switch_configuration_service": "PowerSwitchConfiguration",
        "_power_switch_warning_service": "PowerSwitchWarning",
        "_powermeter_service": "PowerMeter",
        "_powerswitch_service": "PowerSwitch",
        "_powerswitchprogram_service": "PowerSwitchProgram",
    },
    "SHCSmartPlugCompact": {
        "_energy_saving_mode_service": "EnergySavingMode",
        "_led_brightness_configuration_service": "LedBrightnessConfiguration",
        "_power_switch_configuration_service": "PowerSwitchConfiguration",
        "_power_switch_warning_service": "PowerSwitchWarning",
        "_powermeter_service": "PowerMeter",
        "_powerswitch_service": "PowerSwitch",
        "_powerswitchprogram_service": "PowerSwitchProgram",
        "_communicationquality_service": "CommunicationQuality",
    },
    "SHCMotionDetector2": {
        "_walktest_service": "WalkTest",
        "_smart_sensitivity_control_service": "SmartSensitivityControl",
        "_latestmotion_service": "LatestMotion",
        "_multi_level_sensor_service": "MultiLevelSensor",
        "_latesttamper_service": "LatestTamper",
        "_temperaturelevel_service": "TemperatureLevel",
        "_pollcontrol_service": "PollControl",
        "_pirsensorconfiguration_service": "PirSensorConfiguration",
        "_occupancydetection_service": "OccupancyDetection",
        "_communicationquality_service": "CommunicationQuality",
        "_petimmunity_service": "PetImmunity",
        "_multi_level_switch_service": "MultiLevelSwitch",
        "_binaryswitch_service": "BinarySwitch",
        "_detectiontest_service": "DetectionTest",
        "_batterylevel_service": "BatteryLevel",
    },
    "SHCTwinguard": {
        "_airqualitylevel_service": "AirQualityLevel",
        "_smokedetectorcheck_service": "SmokeDetectorCheck",
        "_smoke_sensitivity_service": "SmokeSensitivity",
        "_twinguard_nightly_promise_service": "TwinguardNightlyPromise",
        "_batterylevel_service": "BatteryLevel",
    },
    "SHCSmokeDetector": {
        "_alarm_service": "Alarm",
        "_smokedetectorcheck_service": "SmokeDetectorCheck",
        "_smoke_sensitivity_service": "SmokeSensitivity",
        "_batterylevel_service": "BatteryLevel",
    },
}


# ---------------------------------------------------------------------------
# BATCH 2: EnergySavingModeService
# ---------------------------------------------------------------------------

class TestEnergySavingModeService:
    def _svc(self, **state):
        from boschshcpy.services_impl import EnergySavingModeService
        return _make_svc(EnergySavingModeService, state)

    def test_energy_saving_mode_enabled_true(self):
        svc = self._svc(energySavingModeEnabled=True)
        assert svc.energy_saving_mode_enabled is True

    def test_energy_saving_mode_enabled_false(self):
        svc = self._svc(energySavingModeEnabled=False)
        assert svc.energy_saving_mode_enabled is False

    def test_energy_saving_mode_enabled_missing_defaults_false(self):
        svc = self._svc()
        assert svc.energy_saving_mode_enabled is False

    def test_power_threshold_value(self):
        svc = self._svc(powerThreshold=5.5)
        assert svc.power_threshold == 5.5

    def test_power_threshold_missing_returns_none(self):
        svc = self._svc()
        assert svc.power_threshold is None

    def test_enter_duration_seconds_value(self):
        svc = self._svc(enterDurationSeconds=300)
        assert svc.enter_duration_seconds == 300

    def test_enter_duration_seconds_missing_defaults_zero(self):
        svc = self._svc()
        assert svc.enter_duration_seconds == 0

    def test_async_setter_enabled(self):
        from unittest.mock import AsyncMock
        svc = self._svc(energySavingModeEnabled=False)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_energy_saving_mode_enabled(True))
        svc.async_put_state_element.assert_called_once_with("energySavingModeEnabled", True)

    def test_async_setter_power_threshold(self):
        from unittest.mock import AsyncMock
        svc = self._svc(powerThreshold=1.0)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_power_threshold(7.5))
        svc.async_put_state_element.assert_called_once_with("powerThreshold", 7.5)

    def test_async_setter_enter_duration(self):
        from unittest.mock import AsyncMock
        svc = self._svc(enterDurationSeconds=0)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_enter_duration_seconds(600))
        svc.async_put_state_element.assert_called_once_with("enterDurationSeconds", 600)

    def test_property_setter_enabled(self):
        from unittest.mock import MagicMock
        svc = self._svc(energySavingModeEnabled=False)
        svc.put_state_element = MagicMock()
        svc.energy_saving_mode_enabled = True
        svc.put_state_element.assert_called_once_with("energySavingModeEnabled", True)

    def test_property_setter_power_threshold(self):
        from unittest.mock import MagicMock
        svc = self._svc(powerThreshold=1.0)
        svc.put_state_element = MagicMock()
        svc.power_threshold = 3.0
        svc.put_state_element.assert_called_once_with("powerThreshold", 3.0)

    def test_property_setter_enter_duration(self):
        from unittest.mock import MagicMock
        svc = self._svc(enterDurationSeconds=0)
        svc.put_state_element = MagicMock()
        svc.enter_duration_seconds = 90
        svc.put_state_element.assert_called_once_with("enterDurationSeconds", 90)

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, EnergySavingModeService
        assert "EnergySavingMode" in SERVICE_MAPPING
        assert SERVICE_MAPPING["EnergySavingMode"] is EnergySavingModeService


# ---------------------------------------------------------------------------
# BATCH 2: LedBrightnessConfigurationService
# ---------------------------------------------------------------------------

class TestLedBrightnessConfigurationService:
    def _svc(self, **state):
        from boschshcpy.services_impl import LedBrightnessConfigurationService
        return _make_svc(LedBrightnessConfigurationService, state)

    def test_brightness_value(self):
        svc = self._svc(brightness=75)
        assert svc.brightness == 75

    def test_brightness_missing_returns_none(self):
        svc = self._svc()
        assert svc.brightness is None

    def test_max_brightness(self):
        svc = self._svc(maxBrightness=100)
        assert svc.max_brightness == 100

    def test_min_brightness(self):
        svc = self._svc(minBrightness=0)
        assert svc.min_brightness == 0

    def test_step_size(self):
        svc = self._svc(stepSize=5)
        assert svc.step_size == 5

    def test_max_brightness_missing_returns_none(self):
        svc = self._svc()
        assert svc.max_brightness is None

    def test_async_setter_brightness(self):
        from unittest.mock import AsyncMock
        svc = self._svc(brightness=50)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_brightness(90))
        svc.async_put_state_element.assert_called_once_with("brightness", 90)

    def test_property_setter_brightness(self):
        from unittest.mock import MagicMock
        svc = self._svc(brightness=50)
        svc.put_state_element = MagicMock()
        svc.brightness = 30
        svc.put_state_element.assert_called_once_with("brightness", 30)

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, LedBrightnessConfigurationService
        assert "LedBrightnessConfiguration" in SERVICE_MAPPING
        assert SERVICE_MAPPING["LedBrightnessConfiguration"] is LedBrightnessConfigurationService


# ---------------------------------------------------------------------------
# BATCH 2: PowerSwitchConfigurationService
# ---------------------------------------------------------------------------

class TestPowerSwitchConfigurationService:
    def _svc(self, **state):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        return _make_svc(PowerSwitchConfigurationService, state)

    def test_state_after_power_outage_off(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc(stateAfterPowerOutage="OFF")
        assert svc.state_after_power_outage == PowerSwitchConfigurationService.StateAfterPowerOutage.OFF

    def test_state_after_power_outage_on(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc(stateAfterPowerOutage="ON")
        assert svc.state_after_power_outage == PowerSwitchConfigurationService.StateAfterPowerOutage.ON

    def test_state_after_power_outage_last_state(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc(stateAfterPowerOutage="LAST_STATE")
        assert svc.state_after_power_outage == PowerSwitchConfigurationService.StateAfterPowerOutage.LAST_STATE

    def test_state_after_power_outage_unknown_explicit(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc(stateAfterPowerOutage="UNKNOWN")
        assert svc.state_after_power_outage == PowerSwitchConfigurationService.StateAfterPowerOutage.UNKNOWN

    def test_state_after_power_outage_missing_returns_none(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc()
        assert svc.state_after_power_outage is None

    def test_state_after_power_outage_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc(stateAfterPowerOutage="FUTURE_VALUE")
        assert svc.state_after_power_outage == PowerSwitchConfigurationService.StateAfterPowerOutage.UNKNOWN

    def test_supported_states_list(self):
        svc = self._svc(supportedStatesAfterPowerOutage=["OFF", "ON", "LAST_STATE"])
        assert svc.supported_states_after_power_outage == ["OFF", "ON", "LAST_STATE"]

    def test_supported_states_missing_returns_empty(self):
        svc = self._svc()
        assert svc.supported_states_after_power_outage == []

    def test_async_setter_state_after_power_outage(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc(stateAfterPowerOutage="OFF")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_state_after_power_outage(
            PowerSwitchConfigurationService.StateAfterPowerOutage.ON
        ))
        svc.async_put_state_element.assert_called_once_with("stateAfterPowerOutage", "ON")

    def test_property_setter_state_after_power_outage(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = self._svc(stateAfterPowerOutage="OFF")
        svc.put_state_element = MagicMock()
        svc.state_after_power_outage = (
            PowerSwitchConfigurationService.StateAfterPowerOutage.ON
        )
        svc.put_state_element.assert_called_once_with("stateAfterPowerOutage", "ON")

    def test_enum_values_are_strings(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        for member in PowerSwitchConfigurationService.StateAfterPowerOutage:
            assert member.value == member.name

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, PowerSwitchConfigurationService
        assert "PowerSwitchConfiguration" in SERVICE_MAPPING
        assert SERVICE_MAPPING["PowerSwitchConfiguration"] is PowerSwitchConfigurationService


# ---------------------------------------------------------------------------
# BATCH 2: PowerSwitchWarningService
# ---------------------------------------------------------------------------

class TestPowerSwitchWarningService:
    def _svc(self, **state):
        from boschshcpy.services_impl import PowerSwitchWarningService
        return _make_svc(PowerSwitchWarningService, state)

    def test_warning_suppressed_true(self):
        svc = self._svc(warningSuppressed=True)
        assert svc.warning_suppressed is True

    def test_warning_suppressed_false(self):
        svc = self._svc(warningSuppressed=False)
        assert svc.warning_suppressed is False

    def test_warning_suppressed_missing_defaults_false(self):
        svc = self._svc()
        assert svc.warning_suppressed is False

    def test_async_setter(self):
        from unittest.mock import AsyncMock
        svc = self._svc(warningSuppressed=False)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_warning_suppressed(True))
        svc.async_put_state_element.assert_called_once_with("warningSuppressed", True)

    def test_property_setter(self):
        from unittest.mock import MagicMock
        svc = self._svc(warningSuppressed=False)
        svc.put_state_element = MagicMock()
        svc.warning_suppressed = True
        svc.put_state_element.assert_called_once_with("warningSuppressed", True)

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, PowerSwitchWarningService
        assert "PowerSwitchWarning" in SERVICE_MAPPING
        assert SERVICE_MAPPING["PowerSwitchWarning"] is PowerSwitchWarningService


# ---------------------------------------------------------------------------
# BATCH 3: WalkTestService
# ---------------------------------------------------------------------------

class TestWalkTestService:
    def _svc(self, **state):
        from boschshcpy.services_impl import WalkTestService
        return _make_svc(WalkTestService, state)

    def test_walk_state_started(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkState="WALK_TEST_STARTED")
        assert svc.walk_state == WalkTestService.WalkState.WALK_TEST_STARTED

    def test_walk_state_stopped(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkState="WALK_TEST_STOPPED")
        assert svc.walk_state == WalkTestService.WalkState.WALK_TEST_STOPPED

    def test_walk_state_unknown_explicit(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkState="UNKNOWN")
        assert svc.walk_state == WalkTestService.WalkState.UNKNOWN

    def test_walk_state_missing_returns_unknown(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc()
        assert svc.walk_state == WalkTestService.WalkState.UNKNOWN

    def test_walk_state_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkState="FUTURE_VALUE")
        assert svc.walk_state == WalkTestService.WalkState.UNKNOWN

    def test_walk_state_request_start(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkStateRequest="WALK_STATE_START")
        assert svc.walk_state_request == WalkTestService.WalkStateRequest.WALK_STATE_START

    def test_walk_state_request_stop(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkStateRequest="WALK_STATE_STOP")
        assert svc.walk_state_request == WalkTestService.WalkStateRequest.WALK_STATE_STOP

    def test_walk_state_request_missing_returns_unknown(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc()
        assert svc.walk_state_request == WalkTestService.WalkStateRequest.UNKNOWN

    def test_walk_state_request_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkStateRequest="BOGUS")
        assert svc.walk_state_request == WalkTestService.WalkStateRequest.UNKNOWN

    def test_pet_immunity_state_enabled(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(petImmunityState="PET_IMMUNITY_ENABLED")
        assert svc.pet_immunity_state == WalkTestService.PetImmunityState.PET_IMMUNITY_ENABLED

    def test_pet_immunity_state_disabled(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(petImmunityState="PET_IMMUNITY_DISABLED")
        assert svc.pet_immunity_state == WalkTestService.PetImmunityState.PET_IMMUNITY_DISABLED

    def test_pet_immunity_state_missing_returns_unknown(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc()
        assert svc.pet_immunity_state == WalkTestService.PetImmunityState.UNKNOWN

    def test_pet_immunity_state_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(petImmunityState="FUTURE_STATE")
        assert svc.pet_immunity_state == WalkTestService.PetImmunityState.UNKNOWN

    def test_async_setter_walk_state_request(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkStateRequest="STOP")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_walk_state_request(WalkTestService.WalkStateRequest.WALK_STATE_START))
        svc.async_put_state_element.assert_called_once_with(
            "walkStateRequest", "WALK_STATE_START"
        )

    def test_property_setter_walk_state_request(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import WalkTestService
        svc = self._svc(walkStateRequest="STOP")
        svc.put_state_element = MagicMock()
        svc.walk_state_request = WalkTestService.WalkStateRequest.WALK_STATE_START
        svc.put_state_element.assert_called_once_with("walkStateRequest", "WALK_STATE_START")

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, WalkTestService
        assert "WalkTest" in SERVICE_MAPPING
        assert SERVICE_MAPPING["WalkTest"] is WalkTestService


# ---------------------------------------------------------------------------
# BATCH 3: SmartSensitivityControlService
# ---------------------------------------------------------------------------

class TestSmartSensitivityControlService:
    def _svc(self, **state):
        from boschshcpy.services_impl import SmartSensitivityControlService
        return _make_svc(SmartSensitivityControlService, state)

    def _sample_sensitivities(self):
        # APK: manualLevel + automaticLevel are MotionSensitivity enum strings
        return [
            {"context": "SECURITY", "automaticLevel": "HIGH", "manualLevel": "MIDDLE"},
            {"context": "COMFORT", "automaticLevel": "LOW", "manualLevel": "LOW"},
        ]

    def test_enabled_true(self):
        svc = self._svc(enabled=True, sensitivities=[])
        assert svc.enabled is True

    def test_enabled_false(self):
        svc = self._svc(enabled=False, sensitivities=[])
        assert svc.enabled is False

    def test_enabled_missing_defaults_false(self):
        svc = self._svc()
        assert svc.enabled is False

    def test_sensitivities_list(self):
        sens = self._sample_sensitivities()
        svc = self._svc(enabled=True, sensitivities=sens)
        assert svc.sensitivities == sens

    def test_sensitivities_missing_returns_empty(self):
        svc = self._svc(enabled=True)
        assert svc.sensitivities == []

    def test_get_sensitivity_security(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        sens = self._sample_sensitivities()
        svc = self._svc(enabled=True, sensitivities=sens)
        result = svc.get_sensitivity(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY
        )
        assert result is not None
        assert result["context"] == "SECURITY"
        assert result["manualLevel"] == "MIDDLE"  # MotionSensitivity enum string

    def test_get_sensitivity_comfort(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        sens = self._sample_sensitivities()
        svc = self._svc(enabled=True, sensitivities=sens)
        result = svc.get_sensitivity(
            SmartSensitivityControlService.SmartSensitivityContext.COMFORT
        )
        assert result is not None
        assert result["context"] == "COMFORT"

    def test_get_sensitivity_unknown_context_returns_none(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        sens = self._sample_sensitivities()
        svc = self._svc(enabled=True, sensitivities=sens)
        result = svc.get_sensitivity(
            SmartSensitivityControlService.SmartSensitivityContext.UNKNOWN
        )
        assert result is None

    def test_get_sensitivity_empty_list_returns_none(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        svc = self._svc(enabled=True, sensitivities=[])
        result = svc.get_sensitivity(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY
        )
        assert result is None

    def test_async_set_enabled(self):
        from unittest.mock import AsyncMock
        svc = self._svc(enabled=False, sensitivities=[])
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_enabled(True))
        svc.async_put_state_element.assert_called_once_with("enabled", True)

    def test_property_setter_enabled(self):
        from unittest.mock import MagicMock
        svc = self._svc(enabled=False, sensitivities=[])
        svc.put_state_element = MagicMock()
        svc.enabled = True
        svc.put_state_element.assert_called_once_with("enabled", True)

    def test_set_manual_level_builds_correct_payload(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import SmartSensitivityControlService
        sens = self._sample_sensitivities()
        svc = self._svc(enabled=True, sensitivities=sens)
        svc.put_state = MagicMock()
        svc.set_manual_level(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY,
            SmartSensitivityControlService.MotionSensitivity.HIGH,
        )
        call_args = svc.put_state.call_args[0][0]
        # enabled passes through
        assert call_args["enabled"] is True
        # SECURITY entry updated to HIGH
        security_entry = next(
            e for e in call_args["sensitivities"] if e["context"] == "SECURITY"
        )
        assert security_entry["manualLevel"] == "HIGH"
        # COMFORT entry unchanged (LOW)
        comfort_entry = next(
            e for e in call_args["sensitivities"] if e["context"] == "COMFORT"
        )
        assert comfort_entry["manualLevel"] == "LOW"

    def test_async_set_manual_level(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SmartSensitivityControlService
        sens = self._sample_sensitivities()
        svc = self._svc(enabled=True, sensitivities=sens)
        svc.async_put_state = AsyncMock()
        asyncio.run(svc.async_set_manual_level(
            SmartSensitivityControlService.SmartSensitivityContext.COMFORT,
            SmartSensitivityControlService.MotionSensitivity.MIDDLE,
        ))
        call_args = svc.async_put_state.call_args[0][0]
        comfort_entry = next(
            e for e in call_args["sensitivities"] if e["context"] == "COMFORT"
        )
        assert comfort_entry["manualLevel"] == "MIDDLE"

    def test_context_enum_values(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        assert SmartSensitivityControlService.SmartSensitivityContext.SECURITY.value == "SECURITY"
        assert SmartSensitivityControlService.SmartSensitivityContext.COMFORT.value == "COMFORT"
        assert SmartSensitivityControlService.SmartSensitivityContext.UNKNOWN.value == "UNKNOWN"

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, SmartSensitivityControlService
        assert "SmartSensitivityControl" in SERVICE_MAPPING
        assert SERVICE_MAPPING["SmartSensitivityControl"] is SmartSensitivityControlService


# ---------------------------------------------------------------------------
# BATCH 4: SmokeSensitivityService
# ---------------------------------------------------------------------------

class TestSmokeSensitivityService:
    def _svc(self, **state):
        from boschshcpy.services_impl import SmokeSensitivityService
        return _make_svc(SmokeSensitivityService, state)

    def test_smoke_sensitivity_high(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc(smokeSensitivity="HIGH")
        assert svc.smoke_sensitivity == SmokeSensitivityService.SmokeSensitivityLevel.HIGH

    def test_smoke_sensitivity_middle(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc(smokeSensitivity="MIDDLE")
        assert svc.smoke_sensitivity == SmokeSensitivityService.SmokeSensitivityLevel.MIDDLE

    def test_smoke_sensitivity_low(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc(smokeSensitivity="LOW")
        assert svc.smoke_sensitivity == SmokeSensitivityService.SmokeSensitivityLevel.LOW

    def test_smoke_sensitivity_unknown_explicit(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc(smokeSensitivity="UNKNOWN")
        assert svc.smoke_sensitivity == SmokeSensitivityService.SmokeSensitivityLevel.UNKNOWN

    def test_smoke_sensitivity_missing_returns_none(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc()
        assert svc.smoke_sensitivity is None

    def test_smoke_sensitivity_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc(smokeSensitivity="ULTRA")
        assert svc.smoke_sensitivity == SmokeSensitivityService.SmokeSensitivityLevel.UNKNOWN

    def test_pre_alarm_enabled_true(self):
        svc = self._svc(smokeSensitivity="HIGH", preAlarmEnabled=True)
        assert svc.pre_alarm_enabled is True

    def test_pre_alarm_enabled_false(self):
        svc = self._svc(smokeSensitivity="HIGH", preAlarmEnabled=False)
        assert svc.pre_alarm_enabled is False

    def test_pre_alarm_enabled_missing_defaults_false(self):
        svc = self._svc(smokeSensitivity="HIGH")
        assert svc.pre_alarm_enabled is False

    def test_async_setter_smoke_sensitivity(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc(smokeSensitivity="HIGH")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_smoke_sensitivity(SmokeSensitivityService.SmokeSensitivityLevel.MIDDLE))
        svc.async_put_state_element.assert_called_once_with("smokeSensitivity", "MIDDLE")

    def test_async_setter_pre_alarm(self):
        from unittest.mock import AsyncMock
        svc = self._svc(smokeSensitivity="HIGH", preAlarmEnabled=False)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_pre_alarm_enabled(True))
        svc.async_put_state_element.assert_called_once_with("preAlarmEnabled", True)

    def test_property_setter_smoke_sensitivity(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = self._svc(smokeSensitivity="HIGH")
        svc.put_state_element = MagicMock()
        svc.smoke_sensitivity = SmokeSensitivityService.SmokeSensitivityLevel.LOW
        svc.put_state_element.assert_called_once_with("smokeSensitivity", "LOW")

    def test_property_setter_pre_alarm(self):
        from unittest.mock import MagicMock
        svc = self._svc(smokeSensitivity="HIGH", preAlarmEnabled=False)
        svc.put_state_element = MagicMock()
        svc.pre_alarm_enabled = True
        svc.put_state_element.assert_called_once_with("preAlarmEnabled", True)

    def test_enum_values_are_strings(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        for member in SmokeSensitivityService.SmokeSensitivityLevel:
            assert member.value == member.name

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, SmokeSensitivityService
        assert "SmokeSensitivity" in SERVICE_MAPPING
        assert SERVICE_MAPPING["SmokeSensitivity"] is SmokeSensitivityService


# ---------------------------------------------------------------------------
# BATCH 4: TwinguardNightlyPromiseService
# ---------------------------------------------------------------------------

class TestTwinguardNightlyPromiseService:
    def _svc(self, **state):
        from boschshcpy.services_impl import TwinguardNightlyPromiseService
        return _make_svc(TwinguardNightlyPromiseService, state)

    def test_nightly_promise_enabled_true(self):
        svc = self._svc(nightlyPromiseEnabled=True)
        assert svc.nightly_promise_enabled is True

    def test_nightly_promise_enabled_false(self):
        svc = self._svc(nightlyPromiseEnabled=False)
        assert svc.nightly_promise_enabled is False

    def test_nightly_promise_enabled_missing_defaults_false(self):
        svc = self._svc()
        assert svc.nightly_promise_enabled is False

    def test_async_setter(self):
        from unittest.mock import AsyncMock
        svc = self._svc(nightlyPromiseEnabled=False)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_nightly_promise_enabled(True))
        svc.async_put_state_element.assert_called_once_with("nightlyPromiseEnabled", True)

    def test_property_setter(self):
        from unittest.mock import MagicMock
        svc = self._svc(nightlyPromiseEnabled=False)
        svc.put_state_element = MagicMock()
        svc.nightly_promise_enabled = True
        svc.put_state_element.assert_called_once_with("nightlyPromiseEnabled", True)

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, TwinguardNightlyPromiseService
        assert "TwinguardNightlyPromise" in SERVICE_MAPPING
        assert SERVICE_MAPPING["TwinguardNightlyPromise"] is TwinguardNightlyPromiseService


# ---------------------------------------------------------------------------
# Model bindings: SHCSmartPlug
# ---------------------------------------------------------------------------

class TestSHCSmartPlugBindings:
    def _make_plug(self, esm_state=None, led_state=None, psc_state=None, psw_state=None):
        from boschshcpy.services_impl import (
            EnergySavingModeService,
            LedBrightnessConfigurationService,
            PowerSwitchConfigurationService,
            PowerSwitchWarningService,
        )
        from boschshcpy.models_impl import SHCSmartPlug

        esm = _make_svc(EnergySavingModeService, esm_state or {})
        led = _make_svc(LedBrightnessConfigurationService, led_state or {})
        psc = _make_svc(PowerSwitchConfigurationService, psc_state or {})
        psw = _make_svc(PowerSwitchWarningService, psw_state or {})

        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device("PSM")
        obj._callbacks = {}
        obj._api = None
        obj._device_services_by_id = {
            "EnergySavingMode": esm,
            "LedBrightnessConfiguration": led,
            "PowerSwitchConfiguration": psc,
            "PowerSwitchWarning": psw,
        }
        obj._routing_service = None
        obj._energy_saving_mode_service = esm
        obj._led_brightness_configuration_service = led
        obj._power_switch_configuration_service = psc
        obj._power_switch_warning_service = psw
        obj._powermeter_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        return obj

    def test_energy_saving_mode_enabled_passthrough(self):
        plug = self._make_plug(esm_state={"energySavingModeEnabled": True})
        assert plug.energy_saving_mode_enabled is True

    def test_power_threshold_passthrough(self):
        plug = self._make_plug(esm_state={"powerThreshold": 5.0})
        assert plug.power_threshold == 5.0

    def test_enter_duration_seconds_passthrough(self):
        plug = self._make_plug(esm_state={"enterDurationSeconds": 120})
        assert plug.enter_duration_seconds == 120

    def test_led_brightness_passthrough(self):
        plug = self._make_plug(led_state={"brightness": 80})
        assert plug.led_brightness == 80

    def test_state_after_power_outage_passthrough(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        plug = self._make_plug(psc_state={"stateAfterPowerOutage": "OFF"})
        assert plug.state_after_power_outage == (
            PowerSwitchConfigurationService.StateAfterPowerOutage.OFF
        )

    def test_warning_suppressed_passthrough(self):
        plug = self._make_plug(psw_state={"warningSuppressed": True})
        assert plug.warning_suppressed is True

    def test_energy_saving_mode_absent_service_returns_false(self):
        from boschshcpy.models_impl import SHCSmartPlug
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device("PSM")
        obj._callbacks = {}
        obj._api = None
        obj._energy_saving_mode_service = None
        obj._led_brightness_configuration_service = None
        obj._power_switch_configuration_service = None
        obj._power_switch_warning_service = None
        obj._routing_service = None
        obj._powermeter_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        assert obj.energy_saving_mode_enabled is False
        assert obj.power_threshold is None
        assert obj.enter_duration_seconds == 0
        assert obj.led_brightness is None
        assert obj.state_after_power_outage is None
        assert obj.warning_suppressed is False

    def test_async_set_energy_saving_mode_enabled(self):
        from unittest.mock import AsyncMock
        plug = self._make_plug(esm_state={"energySavingModeEnabled": False})
        plug._energy_saving_mode_service.async_put_state_element = AsyncMock()
        asyncio.run(plug.async_set_energy_saving_mode_enabled(True))
        plug._energy_saving_mode_service.async_put_state_element.assert_called_once_with(
            "energySavingModeEnabled", True
        )

    def test_async_set_led_brightness(self):
        from unittest.mock import AsyncMock
        plug = self._make_plug(led_state={"brightness": 50})
        plug._led_brightness_configuration_service.async_put_state_element = AsyncMock()
        asyncio.run(plug.async_set_led_brightness(100))
        plug._led_brightness_configuration_service.async_put_state_element.assert_called_once_with(
            "brightness", 100
        )

    def test_async_set_warning_suppressed(self):
        from unittest.mock import AsyncMock
        plug = self._make_plug(psw_state={"warningSuppressed": False})
        plug._power_switch_warning_service.async_put_state_element = AsyncMock()
        asyncio.run(plug.async_set_warning_suppressed(True))
        plug._power_switch_warning_service.async_put_state_element.assert_called_once_with(
            "warningSuppressed", True
        )


# ---------------------------------------------------------------------------
# Model bindings: SHCMotionDetector2
# ---------------------------------------------------------------------------

class TestSHCMotionDetector2Bindings:
    def _make_md2(self, walktest_state=None, ssc_state=None):
        from boschshcpy.services_impl import WalkTestService, SmartSensitivityControlService
        from boschshcpy.models_impl import SHCMotionDetector2

        walktest = _make_svc(WalkTestService, walktest_state or {})
        ssc = _make_svc(SmartSensitivityControlService, ssc_state or {"sensitivities": []})

        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._raw_device = _fake_raw_device("MD2")
        obj._callbacks = {}
        obj._api = None
        obj._device_services_by_id = {
            "WalkTest": walktest,
            "SmartSensitivityControl": ssc,
        }
        obj._walktest_service = walktest
        obj._smart_sensitivity_control_service = ssc
        # Other services set to None
        for attr in (
            "_multi_level_switch_service", "_binaryswitch_service", "_detectiontest_service",
            "_latestmotion_service", "_multi_level_sensor_service", "_latesttamper_service",
            "_temperaturelevel_service", "_pollcontrol_service", "_pirsensorconfiguration_service",
            "_occupancydetection_service", "_communicationquality_service",
            "_petimmunity_service", "_batterylevel_service",
        ):
            setattr(obj, attr, None)
        return obj

    def test_walk_state_passthrough(self):
        from boschshcpy.services_impl import WalkTestService
        obj = self._make_md2(walktest_state={"walkState": "WALK_TEST_STARTED"})
        assert obj.walk_state == WalkTestService.WalkState.WALK_TEST_STARTED

    def test_walk_state_request_passthrough(self):
        from boschshcpy.services_impl import WalkTestService
        obj = self._make_md2(walktest_state={"walkStateRequest": "WALK_STATE_STOP"})
        assert obj.walk_state_request == WalkTestService.WalkStateRequest.WALK_STATE_STOP

    def test_pet_immunity_walk_state_passthrough(self):
        from boschshcpy.services_impl import WalkTestService
        obj = self._make_md2(walktest_state={"petImmunityState": "PET_IMMUNITY_ENABLED"})
        assert obj.pet_immunity_walk_state == WalkTestService.PetImmunityState.PET_IMMUNITY_ENABLED

    def test_smart_sensitivity_enabled_passthrough(self):
        obj = self._make_md2(ssc_state={"enabled": True, "sensitivities": []})
        assert obj.smart_sensitivity_enabled is True

    def test_get_smart_sensitivity_returns_dict(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        sens = [{"context": "SECURITY", "automaticLevel": 3, "manualLevel": 2}]
        obj = self._make_md2(ssc_state={"enabled": True, "sensitivities": sens})
        result = obj.get_smart_sensitivity(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY
        )
        assert result is not None
        assert result["context"] == "SECURITY"

    def test_walk_state_absent_service_returns_none(self):
        from boschshcpy.models_impl import SHCMotionDetector2
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._walktest_service = None
        obj._smart_sensitivity_control_service = None
        assert obj.walk_state is None
        assert obj.walk_state_request is None
        assert obj.pet_immunity_walk_state is None
        assert obj.smart_sensitivity_enabled is False
        assert obj.get_smart_sensitivity("anything") is None

    def test_async_set_walk_state_request(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import WalkTestService
        obj = self._make_md2(walktest_state={"walkStateRequest": "STOP"})
        obj._walktest_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_walk_state_request(WalkTestService.WalkStateRequest.WALK_STATE_START))
        obj._walktest_service.async_put_state_element.assert_called_once_with(
            "walkStateRequest", "WALK_STATE_START"
        )

    def test_async_set_smart_sensitivity_enabled(self):
        from unittest.mock import AsyncMock
        obj = self._make_md2(ssc_state={"enabled": False, "sensitivities": []})
        obj._smart_sensitivity_control_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_smart_sensitivity_enabled(True))
        obj._smart_sensitivity_control_service.async_put_state_element.assert_called_once_with(
            "enabled", True
        )


# ---------------------------------------------------------------------------
# Model bindings: SHCTwinguard
# ---------------------------------------------------------------------------

class TestSHCTwinguardBindings:
    def _make_twinguard(self, ss_state=None, np_state=None):
        from boschshcpy.services_impl import SmokeSensitivityService, TwinguardNightlyPromiseService
        from boschshcpy.models_impl import SHCTwinguard

        ss = _make_svc(SmokeSensitivityService, ss_state or {})
        np = _make_svc(TwinguardNightlyPromiseService, np_state or {})

        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._raw_device = _fake_raw_device("TWINGUARD")
        obj._callbacks = {}
        obj._api = None
        obj._device_services_by_id = {
            "SmokeSensitivity": ss,
            "TwinguardNightlyPromise": np,
        }
        obj._smoke_sensitivity_service = ss
        obj._twinguard_nightly_promise_service = np
        obj._airqualitylevel_service = None
        obj._smokedetectorcheck_service = None
        obj._batterylevel_service = None
        return obj

    def test_smoke_sensitivity_passthrough(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        obj = self._make_twinguard(ss_state={"smokeSensitivity": "HIGH"})
        assert obj.smoke_sensitivity == SmokeSensitivityService.SmokeSensitivityLevel.HIGH

    def test_pre_alarm_enabled_passthrough(self):
        obj = self._make_twinguard(ss_state={"smokeSensitivity": "HIGH", "preAlarmEnabled": True})
        assert obj.pre_alarm_enabled is True

    def test_nightly_promise_enabled_passthrough(self):
        obj = self._make_twinguard(np_state={"nightlyPromiseEnabled": True})
        assert obj.nightly_promise_enabled is True

    def test_smoke_sensitivity_absent_service_returns_none(self):
        from boschshcpy.models_impl import SHCTwinguard
        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._smoke_sensitivity_service = None
        obj._twinguard_nightly_promise_service = None
        assert obj.smoke_sensitivity is None
        assert obj.pre_alarm_enabled is False
        assert obj.nightly_promise_enabled is False

    def test_async_set_smoke_sensitivity(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SmokeSensitivityService
        obj = self._make_twinguard(ss_state={"smokeSensitivity": "HIGH"})
        obj._smoke_sensitivity_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_smoke_sensitivity(SmokeSensitivityService.SmokeSensitivityLevel.LOW))
        obj._smoke_sensitivity_service.async_put_state_element.assert_called_once_with(
            "smokeSensitivity", "LOW"
        )

    def test_async_set_nightly_promise_enabled(self):
        from unittest.mock import AsyncMock
        obj = self._make_twinguard(np_state={"nightlyPromiseEnabled": False})
        obj._twinguard_nightly_promise_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_nightly_promise_enabled(True))
        obj._twinguard_nightly_promise_service.async_put_state_element.assert_called_once_with(
            "nightlyPromiseEnabled", True
        )


# ---------------------------------------------------------------------------
# Model bindings: SHCSmokeDetector
# ---------------------------------------------------------------------------

class TestSHCSmokeDetectorBindings:
    def _make_sd(self, ss_state=None, has_ss=True):
        from boschshcpy.services_impl import SmokeSensitivityService
        from boschshcpy.models_impl import SHCSmokeDetector

        ss = _make_svc(SmokeSensitivityService, ss_state or {}) if has_ss else None

        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._raw_device = _fake_raw_device("SD")
        obj._callbacks = {}
        obj._api = None
        obj._smoke_sensitivity_service = ss
        obj._alarm_service = None
        obj._smokedetectorcheck_service = None
        obj._batterylevel_service = None
        return obj

    def test_has_smoke_sensitivity_service_true(self):
        obj = self._make_sd(ss_state={"smokeSensitivity": "HIGH"})
        assert obj.has_smoke_sensitivity_service is True

    def test_has_smoke_sensitivity_service_false(self):
        obj = self._make_sd(has_ss=False)
        assert obj.has_smoke_sensitivity_service is False

    def test_smoke_sensitivity_passthrough(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        obj = self._make_sd(ss_state={"smokeSensitivity": "MIDDLE"})
        assert obj.smoke_sensitivity == SmokeSensitivityService.SmokeSensitivityLevel.MIDDLE

    def test_smoke_sensitivity_absent_returns_none(self):
        obj = self._make_sd(has_ss=False)
        assert obj.smoke_sensitivity is None

    def test_pre_alarm_enabled_passthrough(self):
        obj = self._make_sd(ss_state={"smokeSensitivity": "HIGH", "preAlarmEnabled": True})
        assert obj.pre_alarm_enabled is True

    def test_pre_alarm_absent_service_returns_false(self):
        obj = self._make_sd(has_ss=False)
        assert obj.pre_alarm_enabled is False

    def test_async_set_smoke_sensitivity(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SmokeSensitivityService
        obj = self._make_sd(ss_state={"smokeSensitivity": "HIGH"})
        obj._smoke_sensitivity_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_smoke_sensitivity(SmokeSensitivityService.SmokeSensitivityLevel.LOW))
        obj._smoke_sensitivity_service.async_put_state_element.assert_called_once_with(
            "smokeSensitivity", "LOW"
        )

    def test_async_set_smoke_sensitivity_absent_service_no_error(self):
        obj = self._make_sd(has_ss=False)
        # Should not raise even when service is absent
        asyncio.run(obj.async_set_smoke_sensitivity(None))

    def test_async_set_pre_alarm_enabled(self):
        from unittest.mock import AsyncMock
        obj = self._make_sd(ss_state={"smokeSensitivity": "HIGH", "preAlarmEnabled": False})
        obj._smoke_sensitivity_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_pre_alarm_enabled(True))
        obj._smoke_sensitivity_service.async_put_state_element.assert_called_once_with(
            "preAlarmEnabled", True
        )


# ---------------------------------------------------------------------------
# Summary method coverage for new services
# ---------------------------------------------------------------------------

class TestNewServiceSummaries:
    """Ensure summary() runs without error (covers the print lines)."""

    def _capsvc(self, cls, state):
        return _make_svc(cls, state)

    def test_walk_test_summary(self, capsys):
        from boschshcpy.services_impl import WalkTestService
        svc = _make_svc(
            WalkTestService,
            {"walkState": "STOPPED", "walkStateRequest": "STOP", "petImmunityState": "DISABLED"},
        )
        svc.summary()
        out = capsys.readouterr().out
        assert "walkState" in out

    def test_smoke_sensitivity_summary(self, capsys):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = _make_svc(SmokeSensitivityService, {"smokeSensitivity": "HIGH", "preAlarmEnabled": False})
        svc.summary()
        out = capsys.readouterr().out
        assert "smokeSensitivity" in out

    def test_twinguard_nightly_promise_summary(self, capsys):
        from boschshcpy.services_impl import TwinguardNightlyPromiseService
        svc = _make_svc(TwinguardNightlyPromiseService, {"nightlyPromiseEnabled": True})
        svc.summary()
        out = capsys.readouterr().out
        assert "nightlyPromiseEnabled" in out

    def test_energy_saving_mode_summary(self, capsys):
        from boschshcpy.services_impl import EnergySavingModeService
        svc = _make_svc(
            EnergySavingModeService,
            {"energySavingModeEnabled": True, "powerThreshold": 5.0, "enterDurationSeconds": 300},
        )
        svc.summary()
        out = capsys.readouterr().out
        assert "energySavingModeEnabled" in out

    def test_led_brightness_summary(self, capsys):
        from boschshcpy.services_impl import LedBrightnessConfigurationService
        svc = _make_svc(
            LedBrightnessConfigurationService,
            {"brightness": 75, "maxBrightness": 100, "minBrightness": 0, "stepSize": 5},
        )
        svc.summary()
        out = capsys.readouterr().out
        assert "brightness" in out

    def test_power_switch_configuration_summary(self, capsys):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = _make_svc(
            PowerSwitchConfigurationService,
            {"stateAfterPowerOutage": "OFF", "supportedStatesAfterPowerOutage": ["OFF", "ON"]},
        )
        svc.summary()
        out = capsys.readouterr().out
        assert "stateAfterPowerOutage" in out

    def test_power_switch_warning_summary(self, capsys):
        from boschshcpy.services_impl import PowerSwitchWarningService
        svc = _make_svc(PowerSwitchWarningService, {"warningSuppressed": False})
        svc.summary()
        out = capsys.readouterr().out
        assert "warningSuppressed" in out


# ---------------------------------------------------------------------------
# Additional model async coverage for SHCSmartPlug
# ---------------------------------------------------------------------------

class TestSHCSmartPlugAsyncCoverage:
    """Cover async_set_power_threshold and async_set_enter_duration_seconds."""

    def _make_plug(self, esm_state=None):
        from boschshcpy.services_impl import EnergySavingModeService
        from boschshcpy.models_impl import SHCSmartPlug
        esm = _make_svc(EnergySavingModeService, esm_state or {})
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device("PSM")
        obj._callbacks = {}
        obj._api = None
        obj._energy_saving_mode_service = esm
        obj._led_brightness_configuration_service = None
        obj._power_switch_configuration_service = None
        obj._power_switch_warning_service = None
        obj._routing_service = None
        obj._powermeter_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        return obj, esm

    def test_async_set_power_threshold(self):
        from unittest.mock import AsyncMock
        plug, esm = self._make_plug({"powerThreshold": 1.0})
        esm.async_put_state_element = AsyncMock()
        asyncio.run(plug.async_set_power_threshold(8.0))
        esm.async_put_state_element.assert_called_once_with("powerThreshold", 8.0)

    def test_async_set_enter_duration_seconds(self):
        from unittest.mock import AsyncMock
        plug, esm = self._make_plug({"enterDurationSeconds": 60})
        esm.async_put_state_element = AsyncMock()
        asyncio.run(plug.async_set_enter_duration_seconds(300))
        esm.async_put_state_element.assert_called_once_with("enterDurationSeconds", 300)

    def test_async_set_state_after_power_outage(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        from boschshcpy.models_impl import SHCSmartPlug
        psc = _make_svc(PowerSwitchConfigurationService, {"stateAfterPowerOutage": "OFF"})
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device("PSM")
        obj._callbacks = {}
        obj._api = None
        obj._energy_saving_mode_service = None
        obj._led_brightness_configuration_service = None
        obj._power_switch_configuration_service = psc
        obj._power_switch_warning_service = None
        obj._routing_service = None
        obj._powermeter_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        psc.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_state_after_power_outage(
            PowerSwitchConfigurationService.StateAfterPowerOutage.LAST_STATE
        ))
        psc.async_put_state_element.assert_called_once_with(
            "stateAfterPowerOutage", "LAST_STATE"
        )


# ---------------------------------------------------------------------------
# Additional model async coverage for SHCSmartPlugCompact
# ---------------------------------------------------------------------------

class TestSHCSmartPlugCompactAsyncCoverage:
    def _make_compact(self, esm_state=None, led_state=None, psc_state=None, psw_state=None):
        from boschshcpy.services_impl import (
            EnergySavingModeService,
            LedBrightnessConfigurationService,
            PowerSwitchConfigurationService,
            PowerSwitchWarningService,
        )
        from boschshcpy.models_impl import SHCSmartPlugCompact
        esm = _make_svc(EnergySavingModeService, esm_state or {})
        led = _make_svc(LedBrightnessConfigurationService, led_state or {})
        psc = _make_svc(PowerSwitchConfigurationService, psc_state or {})
        psw = _make_svc(PowerSwitchWarningService, psw_state or {})
        obj = SHCSmartPlugCompact.__new__(SHCSmartPlugCompact)
        obj._raw_device = _fake_raw_device("PLUG_COMPACT")
        obj._callbacks = {}
        obj._api = None
        obj._energy_saving_mode_service = esm
        obj._led_brightness_configuration_service = led
        obj._power_switch_configuration_service = psc
        obj._power_switch_warning_service = psw
        obj._powermeter_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        obj._communicationquality_service = None
        return obj, esm, led, psc, psw

    def test_energy_saving_mode_enabled_property(self):
        obj, esm, *_ = self._make_compact(esm_state={"energySavingModeEnabled": True})
        assert obj.energy_saving_mode_enabled is True

    def test_power_threshold_property(self):
        obj, esm, *_ = self._make_compact(esm_state={"powerThreshold": 3.0})
        assert obj.power_threshold == 3.0

    def test_enter_duration_seconds_property(self):
        obj, esm, *_ = self._make_compact(esm_state={"enterDurationSeconds": 180})
        assert obj.enter_duration_seconds == 180

    def test_led_brightness_property(self):
        obj, esm, led, *_ = self._make_compact(led_state={"brightness": 60})
        assert obj.led_brightness == 60

    def test_state_after_power_outage_property(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        obj, esm, led, psc, psw = self._make_compact(
            psc_state={"stateAfterPowerOutage": "ON"}
        )
        assert obj.state_after_power_outage == (
            PowerSwitchConfigurationService.StateAfterPowerOutage.ON
        )

    def test_warning_suppressed_property(self):
        obj, esm, led, psc, psw = self._make_compact(psw_state={"warningSuppressed": True})
        assert obj.warning_suppressed is True

    def test_async_set_energy_saving_mode_enabled(self):
        from unittest.mock import AsyncMock
        obj, esm, *_ = self._make_compact(esm_state={"energySavingModeEnabled": False})
        esm.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_energy_saving_mode_enabled(True))
        esm.async_put_state_element.assert_called_once_with("energySavingModeEnabled", True)

    def test_async_set_power_threshold(self):
        from unittest.mock import AsyncMock
        obj, esm, *_ = self._make_compact(esm_state={"powerThreshold": 1.0})
        esm.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_power_threshold(9.0))
        esm.async_put_state_element.assert_called_once_with("powerThreshold", 9.0)

    def test_async_set_enter_duration_seconds(self):
        from unittest.mock import AsyncMock
        obj, esm, *_ = self._make_compact(esm_state={"enterDurationSeconds": 60})
        esm.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_enter_duration_seconds(240))
        esm.async_put_state_element.assert_called_once_with("enterDurationSeconds", 240)

    def test_async_set_led_brightness(self):
        from unittest.mock import AsyncMock
        obj, esm, led, *_ = self._make_compact(led_state={"brightness": 50})
        led.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_led_brightness(75))
        led.async_put_state_element.assert_called_once_with("brightness", 75)

    def test_async_set_state_after_power_outage(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        obj, esm, led, psc, psw = self._make_compact(psc_state={"stateAfterPowerOutage": "OFF"})
        psc.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_state_after_power_outage(
            PowerSwitchConfigurationService.StateAfterPowerOutage.ON
        ))
        psc.async_put_state_element.assert_called_once_with("stateAfterPowerOutage", "ON")

    def test_async_set_warning_suppressed(self):
        from unittest.mock import AsyncMock
        obj, esm, led, psc, psw = self._make_compact(psw_state={"warningSuppressed": False})
        psw.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_warning_suppressed(True))
        psw.async_put_state_element.assert_called_once_with("warningSuppressed", True)

    def test_absent_services_return_defaults(self):
        from boschshcpy.models_impl import SHCSmartPlugCompact
        obj = SHCSmartPlugCompact.__new__(SHCSmartPlugCompact)
        obj._energy_saving_mode_service = None
        obj._led_brightness_configuration_service = None
        obj._power_switch_configuration_service = None
        obj._power_switch_warning_service = None
        assert obj.energy_saving_mode_enabled is False
        assert obj.power_threshold is None
        assert obj.enter_duration_seconds == 0
        assert obj.led_brightness is None
        assert obj.state_after_power_outage is None
        assert obj.warning_suppressed is False


# ---------------------------------------------------------------------------
# Additional model async coverage for SHCMotionDetector2
# ---------------------------------------------------------------------------

class TestSHCMotionDetector2AsyncManualLevel:
    def _make_md2(self, ssc_state=None):
        from boschshcpy.services_impl import SmartSensitivityControlService
        from boschshcpy.models_impl import SHCMotionDetector2
        ssc = _make_svc(SmartSensitivityControlService, ssc_state or {"sensitivities": []})
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._walktest_service = None
        obj._smart_sensitivity_control_service = ssc
        return obj, ssc

    def test_async_set_smart_sensitivity_manual_level(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SmartSensitivityControlService
        # APK: manualLevel is MotionSensitivity enum string, not int
        sens = [{"context": "SECURITY", "automaticLevel": "HIGH", "manualLevel": "MIDDLE"}]
        obj, ssc = self._make_md2({"enabled": True, "sensitivities": sens})
        ssc.async_put_state = AsyncMock()
        asyncio.run(obj.async_set_smart_sensitivity_manual_level(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY,
            SmartSensitivityControlService.MotionSensitivity.HIGH,
        ))
        call_args = ssc.async_put_state.call_args[0][0]
        security = next(e for e in call_args["sensitivities"] if e["context"] == "SECURITY")
        assert security["manualLevel"] == "HIGH"

    def test_async_set_smart_sensitivity_manual_level_absent_service_no_error(self):
        from boschshcpy.models_impl import SHCMotionDetector2
        from boschshcpy.services_impl import SmartSensitivityControlService
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._smart_sensitivity_control_service = None
        # Should not raise even when service is absent
        asyncio.run(obj.async_set_smart_sensitivity_manual_level(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY,
            SmartSensitivityControlService.MotionSensitivity.LOW,
        ))


# ---------------------------------------------------------------------------
# Additional model coverage for SHCTwinguard async_set_pre_alarm_enabled
# ---------------------------------------------------------------------------

class TestSHCTwinguardPreAlarmAsync:
    def test_async_set_pre_alarm_enabled(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SmokeSensitivityService
        from boschshcpy.models_impl import SHCTwinguard
        ss = _make_svc(SmokeSensitivityService, {"smokeSensitivity": "HIGH", "preAlarmEnabled": False})
        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._smoke_sensitivity_service = ss
        obj._twinguard_nightly_promise_service = None
        ss.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_pre_alarm_enabled(True))
        ss.async_put_state_element.assert_called_once_with("preAlarmEnabled", True)
