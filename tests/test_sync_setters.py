"""Tests for sync setters added to model classes (STEP 2).

Each new sync setter is exercised with a real put_state_element MagicMock to
confirm it delegates to the underlying service setter, just like the existing
async_set_* counterparts already tested in test_apk_batches_2_4.py.
"""
import asyncio
from unittest.mock import MagicMock
import pytest


# ---------------------------------------------------------------------------
# Helpers (mirrors pattern from test_apk_batches_2_4.py)
# ---------------------------------------------------------------------------

def _make_svc(cls, state_dict):
    """Build a service via __new__ with injected fake state (mirrors test_apk_batches_2_4)."""
    obj = cls.__new__(cls)
    raw = {
        "id": cls.__name__,
        "deviceId": "test-device",
        "path": "/test",
        "state": {"@type": "testType", **state_dict},
    }
    obj._api = None
    obj._raw_device_service = raw
    obj._raw_state = raw["state"]
    obj._last_update = None
    obj._callbacks = {}
    obj._event_callbacks = {}
    return obj


def _fake_raw_device(model):
    return {
        "id": "test-id",
        "deviceModel": model,
        "manufacturer": "BOSCH",
        "name": "Test Device",
    }


# ---------------------------------------------------------------------------
# SHCSmartPlug sync setters
# ---------------------------------------------------------------------------

class TestSHCSmartPlugSyncSetters:
    def _make_plug(self):
        from boschshcpy.services_impl import (
            EnergySavingModeService,
            LedBrightnessConfigurationService,
            PowerSwitchConfigurationService,
            PowerSwitchWarningService,
        )
        from boschshcpy.models_impl import SHCSmartPlug

        esm = _make_svc(EnergySavingModeService, {
            "energySavingModeEnabled": False,
            "powerThreshold": 5.0,
            "enterDurationSeconds": 60,
        })
        led = _make_svc(LedBrightnessConfigurationService, {"brightness": 50})
        psc = _make_svc(PowerSwitchConfigurationService, {"stateAfterPowerOutage": "OFF"})
        psw = _make_svc(PowerSwitchWarningService, {"warningSuppressed": False})

        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device("PSM")
        obj._callbacks = {}
        obj._api = None
        obj._energy_saving_mode_service = esm
        obj._led_brightness_configuration_service = led
        obj._power_switch_configuration_service = psc
        obj._power_switch_warning_service = psw
        obj._routing_service = None
        obj._powermeter_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        return obj

    def test_energy_saving_mode_enabled_setter(self):
        plug = self._make_plug()
        plug._energy_saving_mode_service.put_state_element = MagicMock()
        plug.energy_saving_mode_enabled = True
        plug._energy_saving_mode_service.put_state_element.assert_called_once_with(
            "energySavingModeEnabled", True
        )

    def test_power_threshold_setter(self):
        plug = self._make_plug()
        plug._energy_saving_mode_service.put_state_element = MagicMock()
        plug.power_threshold = 10.0
        plug._energy_saving_mode_service.put_state_element.assert_called_once_with(
            "powerThreshold", 10.0
        )

    def test_enter_duration_seconds_setter(self):
        plug = self._make_plug()
        plug._energy_saving_mode_service.put_state_element = MagicMock()
        plug.enter_duration_seconds = 300
        plug._energy_saving_mode_service.put_state_element.assert_called_once_with(
            "enterDurationSeconds", 300
        )

    def test_led_brightness_setter(self):
        plug = self._make_plug()
        plug._led_brightness_configuration_service.put_state_element = MagicMock()
        plug.led_brightness = 100
        plug._led_brightness_configuration_service.put_state_element.assert_called_once_with(
            "brightness", 100
        )

    def test_state_after_power_outage_setter(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        plug = self._make_plug()
        plug._power_switch_configuration_service.put_state_element = MagicMock()
        plug.state_after_power_outage = (
            PowerSwitchConfigurationService.StateAfterPowerOutage.LAST_STATE
        )
        plug._power_switch_configuration_service.put_state_element.assert_called_once_with(
            "stateAfterPowerOutage", "LAST_STATE"
        )

    def test_warning_suppressed_setter(self):
        plug = self._make_plug()
        plug._power_switch_warning_service.put_state_element = MagicMock()
        plug.warning_suppressed = True
        plug._power_switch_warning_service.put_state_element.assert_called_once_with(
            "warningSuppressed", True
        )

    def test_setter_noop_when_service_absent(self):
        from boschshcpy.models_impl import SHCSmartPlug
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._energy_saving_mode_service = None
        obj._led_brightness_configuration_service = None
        obj._power_switch_configuration_service = None
        obj._power_switch_warning_service = None
        # Should not raise
        obj.energy_saving_mode_enabled = True
        obj.power_threshold = 5.0
        obj.enter_duration_seconds = 60
        obj.led_brightness = 50
        obj.state_after_power_outage = None
        obj.warning_suppressed = True


# ---------------------------------------------------------------------------
# SHCSmartPlugCompact sync setters
# ---------------------------------------------------------------------------

class TestSHCSmartPlugCompactSyncSetters:
    def _make_compact(self):
        from boschshcpy.services_impl import (
            EnergySavingModeService,
            LedBrightnessConfigurationService,
            PowerSwitchConfigurationService,
            PowerSwitchWarningService,
        )
        from boschshcpy.models_impl import SHCSmartPlugCompact

        esm = _make_svc(EnergySavingModeService, {
            "energySavingModeEnabled": False,
            "powerThreshold": 3.0,
            "enterDurationSeconds": 30,
        })
        led = _make_svc(LedBrightnessConfigurationService, {"brightness": 70})
        psc = _make_svc(PowerSwitchConfigurationService, {"stateAfterPowerOutage": "ON"})
        psw = _make_svc(PowerSwitchWarningService, {"warningSuppressed": False})

        obj = SHCSmartPlugCompact.__new__(SHCSmartPlugCompact)
        obj._raw_device = _fake_raw_device("PSMC")
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
        return obj

    def test_energy_saving_mode_enabled_setter(self):
        obj = self._make_compact()
        obj._energy_saving_mode_service.put_state_element = MagicMock()
        obj.energy_saving_mode_enabled = True
        obj._energy_saving_mode_service.put_state_element.assert_called_once_with(
            "energySavingModeEnabled", True
        )

    def test_power_threshold_setter(self):
        obj = self._make_compact()
        obj._energy_saving_mode_service.put_state_element = MagicMock()
        obj.power_threshold = 7.5
        obj._energy_saving_mode_service.put_state_element.assert_called_once_with(
            "powerThreshold", 7.5
        )

    def test_enter_duration_seconds_setter(self):
        obj = self._make_compact()
        obj._energy_saving_mode_service.put_state_element = MagicMock()
        obj.enter_duration_seconds = 120
        obj._energy_saving_mode_service.put_state_element.assert_called_once_with(
            "enterDurationSeconds", 120
        )

    def test_led_brightness_setter(self):
        obj = self._make_compact()
        obj._led_brightness_configuration_service.put_state_element = MagicMock()
        obj.led_brightness = 80
        obj._led_brightness_configuration_service.put_state_element.assert_called_once_with(
            "brightness", 80
        )

    def test_state_after_power_outage_setter(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        obj = self._make_compact()
        obj._power_switch_configuration_service.put_state_element = MagicMock()
        obj.state_after_power_outage = (
            PowerSwitchConfigurationService.StateAfterPowerOutage.ON
        )
        obj._power_switch_configuration_service.put_state_element.assert_called_once_with(
            "stateAfterPowerOutage", "ON"
        )

    def test_warning_suppressed_setter(self):
        obj = self._make_compact()
        obj._power_switch_warning_service.put_state_element = MagicMock()
        obj.warning_suppressed = True
        obj._power_switch_warning_service.put_state_element.assert_called_once_with(
            "warningSuppressed", True
        )

    def test_setter_noop_when_service_absent(self):
        from boschshcpy.models_impl import SHCSmartPlugCompact
        obj = SHCSmartPlugCompact.__new__(SHCSmartPlugCompact)
        obj._energy_saving_mode_service = None
        obj._led_brightness_configuration_service = None
        obj._power_switch_configuration_service = None
        obj._power_switch_warning_service = None
        obj.energy_saving_mode_enabled = True
        obj.power_threshold = 5.0
        obj.enter_duration_seconds = 60
        obj.led_brightness = 50
        obj.state_after_power_outage = None
        obj.warning_suppressed = True


# ---------------------------------------------------------------------------
# SHCLightControl sync setters
# ---------------------------------------------------------------------------

class TestSHCLightControlSyncSetters:
    def _make_lc(self):
        from boschshcpy.services_impl import SwitchConfiguration
        from boschshcpy.models_impl import SHCLightControl

        svc = _make_svc(SwitchConfiguration, {
            "switchType": "TOGGLE",
            "swapInputs": False,
            "swapOutputs": False,
            "actuatorType": "GENERIC",
            "outputMode": "SINGLE_LIGHT",
        })
        obj = SHCLightControl.__new__(SHCLightControl)
        obj._raw_device = _fake_raw_device("LC")
        obj._callbacks = {}
        obj._api = None
        obj._switch_config_service = svc
        obj._powermeter_service = None
        obj._communicationquality_service = None
        return obj

    def test_switch_type_setter(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_lc()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.switch_type = SwitchConfiguration.SwitchType.PUSHBUTTON
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "switchType", "PUSHBUTTON"
        )

    def test_swap_inputs_setter(self):
        obj = self._make_lc()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.swap_inputs = True
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "swapInputs", True
        )

    def test_swap_outputs_setter(self):
        obj = self._make_lc()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.swap_outputs = True
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "swapOutputs", True
        )

    def test_actuator_type_setter(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_lc()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.actuator_type = SwitchConfiguration.ActuatorType.NORMALLY_CLOSED
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "actuatorType", "NORMALLY_CLOSED"
        )

    def test_output_mode_setter(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_lc()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.output_mode = SwitchConfiguration.OutputMode.ATTACHED
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "outputMode", "ATTACHED"
        )

    def test_setters_noop_when_service_absent(self):
        from boschshcpy.services_impl import SwitchConfiguration
        from boschshcpy.models_impl import SHCLightControl
        obj = SHCLightControl.__new__(SHCLightControl)
        obj._switch_config_service = None
        obj.switch_type = SwitchConfiguration.SwitchType.PUSHBUTTON
        obj.swap_inputs = True
        obj.swap_outputs = True
        obj.actuator_type = SwitchConfiguration.ActuatorType.NORMALLY_CLOSED
        obj.output_mode = SwitchConfiguration.OutputMode.ATTACHED


# ---------------------------------------------------------------------------
# SHCMicromoduleRelay sync setters
# ---------------------------------------------------------------------------

class TestSHCMicromoduleRelaySyncSetters:
    def _make_relay(self):
        from boschshcpy.services_impl import SwitchConfiguration
        from boschshcpy.models_impl import SHCMicromoduleRelay

        svc = _make_svc(SwitchConfiguration, {
            "switchType": "PUSH_BUTTON",
            "swapInputs": False,
            "swapOutputs": False,
            "actuatorType": "GENERIC",
            "outputMode": "SINGLE_LIGHT",
        })
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._raw_device = _fake_raw_device("MR")
        obj._callbacks = {}
        obj._api = None
        obj._switch_config_service = svc
        obj._impulseswitch_service = None
        obj._powermeter_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        obj._communicationquality_service = None
        obj._childprotection_service = None
        return obj

    def test_switch_type_setter(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.switch_type = SwitchConfiguration.SwitchType.SWITCH
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "switchType", "SWITCH"
        )

    def test_swap_inputs_setter(self):
        obj = self._make_relay()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.swap_inputs = True
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "swapInputs", True
        )

    def test_swap_outputs_setter(self):
        obj = self._make_relay()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.swap_outputs = True
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "swapOutputs", True
        )

    def test_actuator_type_setter(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.actuator_type = SwitchConfiguration.ActuatorType.NORMALLY_CLOSED
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "actuatorType", "NORMALLY_CLOSED"
        )

    def test_output_mode_setter(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay()
        obj._switch_config_service.put_state_element = MagicMock()
        obj.output_mode = SwitchConfiguration.OutputMode.ATTACHED
        obj._switch_config_service.put_state_element.assert_called_once_with(
            "outputMode", "ATTACHED"
        )

    def test_setters_noop_when_service_absent(self):
        from boschshcpy.services_impl import SwitchConfiguration
        from boschshcpy.models_impl import SHCMicromoduleRelay
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._switch_config_service = None
        obj.switch_type = SwitchConfiguration.SwitchType.SWITCH
        obj.swap_inputs = True
        obj.swap_outputs = True
        obj.actuator_type = SwitchConfiguration.ActuatorType.NORMALLY_CLOSED
        obj.output_mode = SwitchConfiguration.OutputMode.ATTACHED


# ---------------------------------------------------------------------------
# SHCMotionDetector2 sync setters
# ---------------------------------------------------------------------------

class TestSHCMotionDetector2SyncSetters:
    def _make_md2(self):
        from boschshcpy.services_impl import (
            WalkTestService,
            SmartSensitivityControlService,
        )
        from boschshcpy.models_impl import SHCMotionDetector2

        wt = _make_svc(WalkTestService, {"walkStateRequest": "WALK_STATE_START"})
        ssc = _make_svc(SmartSensitivityControlService, {
            "enabled": False,
            "sensitivities": [
                {"context": "SECURITY", "automaticLevel": "HIGH", "manualLevel": "MIDDLE"},
            ],
        })

        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._walktest_service = wt
        obj._smart_sensitivity_control_service = ssc
        return obj

    def test_walk_state_request_setter(self):
        from boschshcpy.services_impl import WalkTestService
        obj = self._make_md2()
        obj._walktest_service.put_state_element = MagicMock()
        obj.walk_state_request = WalkTestService.WalkStateRequest.WALK_STATE_STOP
        obj._walktest_service.put_state_element.assert_called_once_with(
            "walkStateRequest", "WALK_STATE_STOP"
        )

    def test_set_walk_state_request_sync(self):
        from boschshcpy.services_impl import WalkTestService
        obj = self._make_md2()
        obj._walktest_service.put_state_element = MagicMock()
        obj.set_walk_state_request(WalkTestService.WalkStateRequest.WALK_STATE_START)
        obj._walktest_service.put_state_element.assert_called_once_with(
            "walkStateRequest", "WALK_STATE_START"
        )

    def test_smart_sensitivity_enabled_setter(self):
        obj = self._make_md2()
        obj._smart_sensitivity_control_service.put_state_element = MagicMock()
        obj.smart_sensitivity_enabled = True
        obj._smart_sensitivity_control_service.put_state_element.assert_called_once_with(
            "enabled", True
        )

    def test_set_smart_sensitivity_manual_level_sync(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        obj = self._make_md2()
        obj._smart_sensitivity_control_service.put_state = MagicMock()
        obj.set_smart_sensitivity_manual_level(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY,
            SmartSensitivityControlService.MotionSensitivity.HIGH,
        )
        call_args = obj._smart_sensitivity_control_service.put_state.call_args[0][0]
        sec = next(e for e in call_args["sensitivities"] if e["context"] == "SECURITY")
        assert sec["manualLevel"] == "HIGH"

    def test_walk_state_request_setter_noop_absent_service(self):
        from boschshcpy.services_impl import WalkTestService
        from boschshcpy.models_impl import SHCMotionDetector2
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._walktest_service = None
        obj._smart_sensitivity_control_service = None
        obj.walk_state_request = WalkTestService.WalkStateRequest.WALK_STATE_STOP
        obj.smart_sensitivity_enabled = True
        obj.set_walk_state_request(WalkTestService.WalkStateRequest.WALK_STATE_START)

    def test_set_smart_sensitivity_manual_level_noop_absent_service(self):
        from boschshcpy.services_impl import SmartSensitivityControlService
        from boschshcpy.models_impl import SHCMotionDetector2
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._smart_sensitivity_control_service = None
        obj.set_smart_sensitivity_manual_level(
            SmartSensitivityControlService.SmartSensitivityContext.SECURITY,
            SmartSensitivityControlService.MotionSensitivity.LOW,
        )


# ---------------------------------------------------------------------------
# SHCSmokeDetector sync setters (smoke_sensitivity + pre_alarm_enabled)
# ---------------------------------------------------------------------------

class TestSHCSmokeDetectorSyncSetters:
    def _make_det(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        from boschshcpy.models_impl import SHCSmokeDetector

        ss = _make_svc(SmokeSensitivityService, {
            "smokeSensitivity": "HIGH",
            "preAlarmEnabled": False,
        })
        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._smoke_sensitivity_service = ss
        obj._smokedetectorcheck_service = None
        return obj

    def test_smoke_sensitivity_setter(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        obj = self._make_det()
        obj._smoke_sensitivity_service.put_state_element = MagicMock()
        obj.smoke_sensitivity = SmokeSensitivityService.SmokeSensitivityLevel.HIGH
        obj._smoke_sensitivity_service.put_state_element.assert_called_once_with(
            "smokeSensitivity", "HIGH"
        )

    def test_pre_alarm_enabled_setter(self):
        obj = self._make_det()
        obj._smoke_sensitivity_service.put_state_element = MagicMock()
        obj.pre_alarm_enabled = True
        obj._smoke_sensitivity_service.put_state_element.assert_called_once_with(
            "preAlarmEnabled", True
        )

    def test_setters_noop_absent_service(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        from boschshcpy.models_impl import SHCSmokeDetector
        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._smoke_sensitivity_service = None
        obj.smoke_sensitivity = SmokeSensitivityService.SmokeSensitivityLevel.HIGH
        obj.pre_alarm_enabled = True


# ---------------------------------------------------------------------------
# SHCTwinguard sync setters
# ---------------------------------------------------------------------------

class TestSHCTwinguardSyncSetters:
    def _make_tg(self):
        from boschshcpy.services_impl import SmokeSensitivityService, TwinguardNightlyPromiseService
        from boschshcpy.models_impl import SHCTwinguard

        ss = _make_svc(SmokeSensitivityService, {
            "smokeSensitivity": "MIDDLE",
            "preAlarmEnabled": True,
        })
        np = _make_svc(TwinguardNightlyPromiseService, {"nightlyPromiseEnabled": False})

        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._smoke_sensitivity_service = ss
        obj._twinguard_nightly_promise_service = np
        obj._airqualitylevel_service = None
        obj._smokedetectorcheck_service = None
        return obj

    def test_smoke_sensitivity_setter(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        obj = self._make_tg()
        obj._smoke_sensitivity_service.put_state_element = MagicMock()
        obj.smoke_sensitivity = SmokeSensitivityService.SmokeSensitivityLevel.LOW
        obj._smoke_sensitivity_service.put_state_element.assert_called_once_with(
            "smokeSensitivity", "LOW"
        )

    def test_pre_alarm_enabled_setter(self):
        obj = self._make_tg()
        obj._smoke_sensitivity_service.put_state_element = MagicMock()
        obj.pre_alarm_enabled = False
        obj._smoke_sensitivity_service.put_state_element.assert_called_once_with(
            "preAlarmEnabled", False
        )

    def test_nightly_promise_enabled_setter(self):
        obj = self._make_tg()
        obj._twinguard_nightly_promise_service.put_state_element = MagicMock()
        obj.nightly_promise_enabled = True
        obj._twinguard_nightly_promise_service.put_state_element.assert_called_once_with(
            "nightlyPromiseEnabled", True
        )

    def test_setters_noop_absent_service(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        from boschshcpy.models_impl import SHCTwinguard
        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._smoke_sensitivity_service = None
        obj._twinguard_nightly_promise_service = None
        obj.smoke_sensitivity = SmokeSensitivityService.SmokeSensitivityLevel.HIGH
        obj.pre_alarm_enabled = True
        obj.nightly_promise_enabled = True


# ---------------------------------------------------------------------------
# SHCThermostatGen2 sync setters
# ---------------------------------------------------------------------------

class TestSHCThermostatGen2SyncSetters:
    def _make_tg2(self):
        from boschshcpy.services_impl import (
            DisplayConfiguration,
            DisplayDirection,
            DisplayedTemperatureConfiguration,
            WallThermostatConfiguration,
        )
        from boschshcpy.models_impl import SHCThermostatGen2

        dc = _make_svc(DisplayConfiguration, {
            "displayBrightness": 5,
            "displayOnTime": 10,
            "humidityWarningEnabled": False,
        })
        dd = _make_svc(DisplayDirection, {"direction": "NORMAL"})
        dtc = _make_svc(DisplayedTemperatureConfiguration, {"displayedTemperature": "SETPOINT"})
        wtc = _make_svc(WallThermostatConfiguration, {
            "valveType": "NORMALLY_CLOSED",
            "heaterType": "NONE",
        })

        obj = SHCThermostatGen2.__new__(SHCThermostatGen2)
        obj._display_config_service = dc
        obj._display_direction_service = dd
        obj._displayed_temp_service = dtc
        obj._wall_thermostat_config_service = wtc
        # Minimal thermostat attributes
        obj._thermostatservice = None
        obj._heatingcircuitservice = None
        obj._temperaturelevelservice = None
        return obj

    def test_display_brightness_setter(self):
        obj = self._make_tg2()
        obj._display_config_service.put_state_element = MagicMock()
        obj.display_brightness = 8
        obj._display_config_service.put_state_element.assert_called_once_with(
            "displayBrightness", 8
        )

    def test_display_on_time_setter(self):
        obj = self._make_tg2()
        obj._display_config_service.put_state_element = MagicMock()
        obj.display_on_time = 30
        obj._display_config_service.put_state_element.assert_called_once_with(
            "displayOnTime", 30
        )

    def test_humidity_warning_enabled_setter(self):
        obj = self._make_tg2()
        obj._display_config_service.put_state_element = MagicMock()
        obj.humidity_warning_enabled = True
        obj._display_config_service.put_state_element.assert_called_once_with(
            "humidityWarningEnabled", True
        )

    def test_display_direction_setter(self):
        from boschshcpy.services_impl import DisplayDirection
        obj = self._make_tg2()
        obj._display_direction_service.put_state_element = MagicMock()
        obj.display_direction = DisplayDirection.Direction.NORMAL
        obj._display_direction_service.put_state_element.assert_called_once_with(
            "direction", "NORMAL"
        )

    def test_displayed_temperature_setter(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        obj = self._make_tg2()
        obj._displayed_temp_service.put_state_element = MagicMock()
        obj.displayed_temperature = DisplayedTemperatureConfiguration.DisplayedTemperature.SETPOINT
        obj._displayed_temp_service.put_state_element.assert_called_once_with(
            "displayedTemperature", "SETPOINT"
        )

    def test_valve_type_setter(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make_tg2()
        obj._wall_thermostat_config_service.put_state_element = MagicMock()
        obj.valve_type = WallThermostatConfiguration.ValveType.NORMALLY_CLOSE
        obj._wall_thermostat_config_service.put_state_element.assert_called_once_with(
            "valveType", "NORMALLY_CLOSE"
        )

    def test_heater_type_setter(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make_tg2()
        obj._wall_thermostat_config_service.put_state_element = MagicMock()
        obj.heater_type = WallThermostatConfiguration.HeaterType.RADIATOR
        obj._wall_thermostat_config_service.put_state_element.assert_called_once_with(
            "heaterType", "RADIATOR"
        )

    def test_setters_noop_absent_services(self):
        from boschshcpy.services_impl import (
            DisplayDirection,
            DisplayedTemperatureConfiguration,
            WallThermostatConfiguration,
        )
        from boschshcpy.models_impl import SHCThermostatGen2
        obj = SHCThermostatGen2.__new__(SHCThermostatGen2)
        obj._display_config_service = None
        obj._display_direction_service = None
        obj._displayed_temp_service = None
        obj._wall_thermostat_config_service = None
        obj.display_brightness = 5
        obj.display_on_time = 10
        obj.humidity_warning_enabled = True
        obj.display_direction = DisplayDirection.Direction.NORMAL
        obj.displayed_temperature = DisplayedTemperatureConfiguration.DisplayedTemperature.SETPOINT
        obj.valve_type = WallThermostatConfiguration.ValveType.NORMALLY_CLOSE
        obj.heater_type = WallThermostatConfiguration.HeaterType.RADIATOR


# ---------------------------------------------------------------------------
# SHCRoomThermostat2 sync setters
# ---------------------------------------------------------------------------

class TestSHCRoomThermostat2SyncSetters:
    def _make_rt2(self):
        from boschshcpy.services_impl import (
            DisplayConfiguration,
            DisplayDirection,
            DisplayedTemperatureConfiguration,
            TerminalConfiguration,
        )
        from boschshcpy.models_impl import SHCRoomThermostat2

        dc = _make_svc(DisplayConfiguration, {
            "displayBrightness": 4,
            "displayOnTime": 15,
            "humidityWarningEnabled": True,
        })
        dd = _make_svc(DisplayDirection, {"direction": "INVERTED"})
        dtc = _make_svc(DisplayedTemperatureConfiguration, {"displayedTemperature": "CURRENT"})
        tc = _make_svc(TerminalConfiguration, {
            "type": "UNDERFLOOR",
            "temperature": 22.0,
            "supportedTypes": ["UNDERFLOOR", "RADIATOR"],
        })

        obj = SHCRoomThermostat2.__new__(SHCRoomThermostat2)
        obj._display_config_service = dc
        obj._display_direction_service = dd
        obj._displayed_temp_service = dtc
        obj._terminal_config_service = tc
        obj._thermostatservice = None
        obj._heatingcircuitservice = None
        obj._temperaturelevelservice = None
        obj._humiditylevelservice = None
        obj._communicationquality_service = None
        obj._temperatureoffsetservice = None
        return obj

    def test_display_brightness_setter(self):
        obj = self._make_rt2()
        obj._display_config_service.put_state_element = MagicMock()
        obj.display_brightness = 6
        obj._display_config_service.put_state_element.assert_called_once_with(
            "displayBrightness", 6
        )

    def test_display_on_time_setter(self):
        obj = self._make_rt2()
        obj._display_config_service.put_state_element = MagicMock()
        obj.display_on_time = 20
        obj._display_config_service.put_state_element.assert_called_once_with(
            "displayOnTime", 20
        )

    def test_humidity_warning_enabled_setter(self):
        obj = self._make_rt2()
        obj._display_config_service.put_state_element = MagicMock()
        obj.humidity_warning_enabled = False
        obj._display_config_service.put_state_element.assert_called_once_with(
            "humidityWarningEnabled", False
        )

    def test_display_direction_setter(self):
        from boschshcpy.services_impl import DisplayDirection
        obj = self._make_rt2()
        obj._display_direction_service.put_state_element = MagicMock()
        obj.display_direction = DisplayDirection.Direction.REVERSED
        obj._display_direction_service.put_state_element.assert_called_once_with(
            "direction", "REVERSED"
        )

    def test_displayed_temperature_setter(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        obj = self._make_rt2()
        obj._displayed_temp_service.put_state_element = MagicMock()
        obj.displayed_temperature = DisplayedTemperatureConfiguration.DisplayedTemperature.MEASURED
        obj._displayed_temp_service.put_state_element.assert_called_once_with(
            "displayedTemperature", "MEASURED"
        )

    def test_terminal_type_setter(self):
        from boschshcpy.services_impl import TerminalConfiguration
        obj = self._make_rt2()
        obj._terminal_config_service.put_state_element = MagicMock()
        obj.terminal_type = TerminalConfiguration.Type.NOT_CONNECTED
        obj._terminal_config_service.put_state_element.assert_called_once_with(
            "type", "NOT_CONNECTED"
        )

    def test_setters_noop_absent_services(self):
        from boschshcpy.services_impl import (
            DisplayDirection,
            DisplayedTemperatureConfiguration,
            TerminalConfiguration,
        )
        from boschshcpy.models_impl import SHCRoomThermostat2
        obj = SHCRoomThermostat2.__new__(SHCRoomThermostat2)
        obj._display_config_service = None
        obj._display_direction_service = None
        obj._displayed_temp_service = None
        obj._terminal_config_service = None
        obj.display_brightness = 5
        obj.display_on_time = 10
        obj.humidity_warning_enabled = True
        obj.display_direction = DisplayDirection.Direction.NORMAL
        obj.displayed_temperature = DisplayedTemperatureConfiguration.DisplayedTemperature.SETPOINT
        obj.terminal_type = TerminalConfiguration.Type.NOT_CONNECTED
