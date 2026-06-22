"""Tests: absent field key in state dict → getter returns None (not UNKNOWN).

Each APK service getter that was changed to distinguish "key absent" (→ None)
from "key present but unrecognised value" (→ UNKNOWN):

- PowerSwitchConfigurationService.state_after_power_outage
- SmokeSensitivityService.smoke_sensitivity
- DisplayDirection.direction
- DisplayedTemperatureConfiguration.displayed_temperature
- TerminalConfiguration.type
- WallThermostatConfiguration.valve_type
- WallThermostatConfiguration.heater_type
- SwitchConfiguration.switch_type
- SwitchConfiguration.actuator_type
- SwitchConfiguration.output_mode

Concrete motivation: PLUG_COMPACT ("Brunnen") advertises
PowerSwitchConfiguration but its state dict only contains
`supportedStatesAfterPowerOutage`, NOT `stateAfterPowerOutage`.
Before this fix the getter returned UNKNOWN, which bypassed the
`is not None` guard in select.py and created an unavailable entity.
"""

from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_svc(cls, state_dict):
    svc = cls.__new__(cls)
    raw = {
        "id": cls.__name__,
        "deviceId": "test-device",
        "path": "/test",
        "state": {"@type": "testType", **state_dict},
    }
    svc._api = MagicMock()
    svc._raw_device_service = raw
    svc._raw_state = raw["state"]
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


# ---------------------------------------------------------------------------
# PowerSwitchConfigurationService.state_after_power_outage
# ---------------------------------------------------------------------------


class TestPowerSwitchConfigurationAbsentKey:
    """The PLUG_COMPACT scenario: only supportedStatesAfterPowerOutage present."""

    def test_absent_key_returns_none(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        # Simulate PLUG_COMPACT: state dict has the supported list but NOT the current value.
        svc = _make_svc(
            PowerSwitchConfigurationService,
            {"supportedStatesAfterPowerOutage": ["OFF", "ON", "LAST_STATE"]},
        )
        assert svc.state_after_power_outage is None

    def test_empty_state_returns_none(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = _make_svc(PowerSwitchConfigurationService, {})
        assert svc.state_after_power_outage is None

    def test_key_present_recognized_returns_enum(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = _make_svc(
            PowerSwitchConfigurationService,
            {"stateAfterPowerOutage": "OFF"},
        )
        assert svc.state_after_power_outage == (
            PowerSwitchConfigurationService.StateAfterPowerOutage.OFF
        )

    def test_key_present_unrecognized_returns_unknown(self):
        from boschshcpy.services_impl import PowerSwitchConfigurationService
        svc = _make_svc(
            PowerSwitchConfigurationService,
            {"stateAfterPowerOutage": "FUTURE_VALUE"},
        )
        assert svc.state_after_power_outage == (
            PowerSwitchConfigurationService.StateAfterPowerOutage.UNKNOWN
        )


# ---------------------------------------------------------------------------
# SmokeSensitivityService.smoke_sensitivity
# ---------------------------------------------------------------------------


class TestSmokeSensitivityAbsentKey:
    def test_absent_key_returns_none(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = _make_svc(SmokeSensitivityService, {})
        assert svc.smoke_sensitivity is None

    def test_key_present_recognized_returns_enum(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = _make_svc(SmokeSensitivityService, {"smokeSensitivity": "HIGH"})
        assert svc.smoke_sensitivity == (
            SmokeSensitivityService.SmokeSensitivityLevel.HIGH
        )

    def test_key_present_unrecognized_returns_unknown(self):
        from boschshcpy.services_impl import SmokeSensitivityService
        svc = _make_svc(SmokeSensitivityService, {"smokeSensitivity": "ULTRA"})
        assert svc.smoke_sensitivity == (
            SmokeSensitivityService.SmokeSensitivityLevel.UNKNOWN
        )


# ---------------------------------------------------------------------------
# DisplayDirection.direction
# ---------------------------------------------------------------------------


class TestDisplayDirectionAbsentKey:
    def test_absent_key_returns_none(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = _make_svc(DisplayDirection, {})
        assert svc.direction is None

    def test_key_present_recognized_returns_enum(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = _make_svc(DisplayDirection, {"direction": "NORMAL"})
        assert svc.direction == DisplayDirection.Direction.NORMAL

    def test_key_present_unrecognized_returns_unknown(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = _make_svc(DisplayDirection, {"direction": "FUTURE_VALUE"})
        assert svc.direction == DisplayDirection.Direction.UNKNOWN


# ---------------------------------------------------------------------------
# DisplayedTemperatureConfiguration.displayed_temperature
# ---------------------------------------------------------------------------


class TestDisplayedTemperatureAbsentKey:
    def test_absent_key_returns_none(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = _make_svc(DisplayedTemperatureConfiguration, {})
        assert svc.displayed_temperature is None

    def test_key_present_recognized_returns_enum(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = _make_svc(
            DisplayedTemperatureConfiguration, {"displayedTemperature": "SETPOINT"}
        )
        assert svc.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.SETPOINT
        )

    def test_key_present_unrecognized_returns_unknown(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = _make_svc(
            DisplayedTemperatureConfiguration, {"displayedTemperature": "FUTURE"}
        )
        assert svc.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.UNKNOWN
        )


# ---------------------------------------------------------------------------
# TerminalConfiguration.type
# ---------------------------------------------------------------------------


class TestTerminalConfigurationAbsentKey:
    def test_absent_key_returns_none(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = _make_svc(TerminalConfiguration, {})
        assert svc.type is None

    def test_key_present_recognized_returns_enum(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = _make_svc(TerminalConfiguration, {"type": "NOT_CONNECTED"})
        assert svc.type == TerminalConfiguration.Type.NOT_CONNECTED

    def test_key_present_unrecognized_returns_unknown(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = _make_svc(TerminalConfiguration, {"type": "FUTURE_TYPE"})
        assert svc.type == TerminalConfiguration.Type.UNKNOWN


# ---------------------------------------------------------------------------
# WallThermostatConfiguration.valve_type
# ---------------------------------------------------------------------------


class TestWallThermostatValveTypeAbsentKey:
    def test_absent_key_returns_none(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = _make_svc(WallThermostatConfiguration, {})
        assert svc.valve_type is None

    def test_key_present_recognized_returns_enum(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = _make_svc(WallThermostatConfiguration, {"valveType": "NORMALLY_CLOSE"})
        assert svc.valve_type == WallThermostatConfiguration.ValveType.NORMALLY_CLOSE

    def test_key_present_unrecognized_returns_unknown(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = _make_svc(WallThermostatConfiguration, {"valveType": "FUTURE_VALVE"})
        assert svc.valve_type == WallThermostatConfiguration.ValveType.UNKNOWN


# ---------------------------------------------------------------------------
# WallThermostatConfiguration.heater_type
# ---------------------------------------------------------------------------


class TestWallThermostatHeaterTypeAbsentKey:
    def test_absent_key_returns_none(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = _make_svc(WallThermostatConfiguration, {})
        assert svc.heater_type is None

    def test_key_present_recognized_returns_enum(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = _make_svc(WallThermostatConfiguration, {"heaterType": "RADIATOR"})
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.RADIATOR

    def test_key_present_unrecognized_returns_unknown(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = _make_svc(WallThermostatConfiguration, {"heaterType": "FUTURE_HEATER"})
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.UNKNOWN


# ---------------------------------------------------------------------------
# SwitchConfiguration.switch_type / actuator_type / output_mode
# ---------------------------------------------------------------------------


class TestSwitchConfigurationAbsentKeys:
    def _make(self, state_dict):
        from boschshcpy.services_impl import SwitchConfiguration
        return _make_svc(SwitchConfiguration, state_dict)

    # switch_type
    def test_switch_type_absent_returns_none(self):
        svc = self._make({})
        assert svc.switch_type is None

    def test_switch_type_present_recognized(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._make({"switchType": "PUSHBUTTON"})
        assert svc.switch_type == SwitchConfiguration.SwitchType.PUSHBUTTON

    def test_switch_type_present_unrecognized(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._make({"switchType": "FUTURE_TYPE"})
        assert svc.switch_type == SwitchConfiguration.SwitchType.UNKNOWN

    # actuator_type
    def test_actuator_type_absent_returns_none(self):
        svc = self._make({})
        assert svc.actuator_type is None

    def test_actuator_type_present_recognized(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._make({"actuatorType": "NORMALLY_OPEN"})
        assert svc.actuator_type == SwitchConfiguration.ActuatorType.NORMALLY_OPEN

    def test_actuator_type_present_unrecognized(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._make({"actuatorType": "FUTURE_ACTUATOR"})
        assert svc.actuator_type == SwitchConfiguration.ActuatorType.UNKNOWN

    # output_mode
    def test_output_mode_absent_returns_none(self):
        svc = self._make({})
        assert svc.output_mode is None

    def test_output_mode_present_recognized(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._make({"outputMode": "ATTACHED"})
        assert svc.output_mode == SwitchConfiguration.OutputMode.ATTACHED

    def test_output_mode_present_unrecognized(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._make({"outputMode": "FUTURE_MODE"})
        assert svc.output_mode == SwitchConfiguration.OutputMode.UNKNOWN
