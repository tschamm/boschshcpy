"""Tests for supports_* boolean properties added to models_impl.py classes.

Each class's supports_* property returns True when the underlying service was
found by device_service(), False/None when absent.  We bypass __init__ and
inject the service attributes directly.

Isolation: NO HA harness, NO real network.
"""
from __future__ import annotations

import pytest

from boschshcpy.models_impl import (
    SHCSmokeDetector,
    SHCSmartPlug,
    SHCSmartPlugCompact,
    SHCMicromoduleRelay,
    SHCThermostatGen2,
    SHCRoomThermostat2,
    SHCMotionDetector2,
    SHCTwinguard,
)


# ---------------------------------------------------------------------------
# SHCSmokeDetector.supports_smoke_sensitivity
# ---------------------------------------------------------------------------

class TestSHCSmokeDetectorSupports:
    def _obj(self, svc=None):
        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._smoke_sensitivity_service = svc
        return obj

    def test_supports_smoke_sensitivity_true(self):
        assert self._obj(svc=object()).supports_smoke_sensitivity is True

    def test_supports_smoke_sensitivity_false(self):
        assert self._obj(svc=None).supports_smoke_sensitivity is False


# ---------------------------------------------------------------------------
# SHCSmartPlug supports_*
# ---------------------------------------------------------------------------

class TestSHCSmartPlugSupports:
    def _obj(self, **services):
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._energy_saving_mode_service = services.get("esm")
        obj._led_brightness_configuration_service = services.get("lbc")
        obj._power_switch_configuration_service = services.get("psc")
        obj._power_switch_warning_service = services.get("psw")
        return obj

    def test_supports_energy_saving_mode_true(self):
        assert self._obj(esm=object()).supports_energy_saving_mode is True

    def test_supports_energy_saving_mode_false(self):
        assert self._obj().supports_energy_saving_mode is False

    def test_supports_led_brightness_true(self):
        assert self._obj(lbc=object()).supports_led_brightness is True

    def test_supports_led_brightness_false(self):
        assert self._obj().supports_led_brightness is False

    def test_supports_power_switch_configuration_true(self):
        assert self._obj(psc=object()).supports_power_switch_configuration is True

    def test_supports_power_switch_configuration_false(self):
        assert self._obj().supports_power_switch_configuration is False

    def test_supports_power_switch_warning_true(self):
        assert self._obj(psw=object()).supports_power_switch_warning is True

    def test_supports_power_switch_warning_false(self):
        assert self._obj().supports_power_switch_warning is False


# ---------------------------------------------------------------------------
# SHCSmartPlugCompact supports_*
# ---------------------------------------------------------------------------

class TestSHCSmartPlugCompactSupports:
    def _obj(self, **services):
        obj = SHCSmartPlugCompact.__new__(SHCSmartPlugCompact)
        obj._energy_saving_mode_service = services.get("esm")
        obj._led_brightness_configuration_service = services.get("lbc")
        obj._power_switch_configuration_service = services.get("psc")
        obj._power_switch_warning_service = services.get("psw")
        return obj

    def test_supports_energy_saving_mode_true(self):
        assert self._obj(esm=object()).supports_energy_saving_mode is True

    def test_supports_energy_saving_mode_false(self):
        assert self._obj().supports_energy_saving_mode is False

    def test_supports_led_brightness_true(self):
        assert self._obj(lbc=object()).supports_led_brightness is True

    def test_supports_led_brightness_false(self):
        assert self._obj().supports_led_brightness is False

    def test_supports_power_switch_configuration_true(self):
        assert self._obj(psc=object()).supports_power_switch_configuration is True

    def test_supports_power_switch_configuration_false(self):
        assert self._obj().supports_power_switch_configuration is False

    def test_supports_power_switch_warning_true(self):
        assert self._obj(psw=object()).supports_power_switch_warning is True

    def test_supports_power_switch_warning_false(self):
        assert self._obj().supports_power_switch_warning is False


# ---------------------------------------------------------------------------
# SHCMicromoduleRelay.supports_switch_configuration
# ---------------------------------------------------------------------------

class TestSHCMicromoduleRelaySupports:
    def _obj(self, svc=None):
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._switch_config_service = svc
        return obj

    def test_supports_switch_configuration_true(self):
        assert self._obj(svc=object()).supports_switch_configuration is True

    def test_supports_switch_configuration_false(self):
        assert self._obj().supports_switch_configuration is False


# ---------------------------------------------------------------------------
# SHCThermostatGen2 supports_*
# ---------------------------------------------------------------------------

class TestSHCThermostatGen2Supports:
    def _obj(self, **services):
        obj = SHCThermostatGen2.__new__(SHCThermostatGen2)
        obj._display_config_service = services.get("dc")
        obj._display_direction_service = services.get("dd")
        obj._displayed_temp_service = services.get("dt")
        obj._wall_thermostat_config_service = services.get("wt")
        return obj

    def test_supports_display_configuration_true(self):
        assert self._obj(dc=object()).supports_display_configuration is True

    def test_supports_display_configuration_false(self):
        assert self._obj().supports_display_configuration is False

    def test_supports_display_direction_true(self):
        assert self._obj(dd=object()).supports_display_direction is True

    def test_supports_display_direction_false(self):
        assert self._obj().supports_display_direction is False

    def test_supports_displayed_temperature_true(self):
        assert self._obj(dt=object()).supports_displayed_temperature is True

    def test_supports_displayed_temperature_false(self):
        assert self._obj().supports_displayed_temperature is False

    def test_supports_wall_thermostat_configuration_true(self):
        assert self._obj(wt=object()).supports_wall_thermostat_configuration is True

    def test_supports_wall_thermostat_configuration_false(self):
        assert self._obj().supports_wall_thermostat_configuration is False


# ---------------------------------------------------------------------------
# SHCRoomThermostat2 supports_*
# ---------------------------------------------------------------------------

class TestSHCRoomThermostat2Supports:
    def _obj(self, **services):
        obj = SHCRoomThermostat2.__new__(SHCRoomThermostat2)
        obj._display_config_service = services.get("dc")
        obj._display_direction_service = services.get("dd")
        obj._displayed_temp_service = services.get("dt")
        obj._terminal_config_service = services.get("tc")
        return obj

    def test_supports_display_configuration_true(self):
        assert self._obj(dc=object()).supports_display_configuration is True

    def test_supports_display_configuration_false(self):
        assert self._obj().supports_display_configuration is False

    def test_supports_display_direction_true(self):
        assert self._obj(dd=object()).supports_display_direction is True

    def test_supports_display_direction_false(self):
        assert self._obj().supports_display_direction is False

    def test_supports_displayed_temperature_true(self):
        assert self._obj(dt=object()).supports_displayed_temperature is True

    def test_supports_displayed_temperature_false(self):
        assert self._obj().supports_displayed_temperature is False

    def test_supports_terminal_configuration_true(self):
        assert self._obj(tc=object()).supports_terminal_configuration is True

    def test_supports_terminal_configuration_false(self):
        assert self._obj().supports_terminal_configuration is False


# ---------------------------------------------------------------------------
# SHCMotionDetector2 supports_*
# ---------------------------------------------------------------------------

class TestSHCMotionDetector2Supports:
    def _obj(self, **services):
        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._walktest_service = services.get("wt")
        obj._smart_sensitivity_control_service = services.get("ss")
        return obj

    def test_supports_walk_test_true(self):
        assert self._obj(wt=object()).supports_walk_test is True

    def test_supports_walk_test_false(self):
        assert self._obj().supports_walk_test is False

    def test_supports_smart_sensitivity_true(self):
        assert self._obj(ss=object()).supports_smart_sensitivity is True

    def test_supports_smart_sensitivity_false(self):
        assert self._obj().supports_smart_sensitivity is False


# ---------------------------------------------------------------------------
# SHCTwinguard supports_*
# ---------------------------------------------------------------------------

class TestSHCTwinguardSupports:
    def _obj(self, **services):
        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._smoke_sensitivity_service = services.get("ss")
        obj._twinguard_nightly_promise_service = services.get("np")
        return obj

    def test_supports_smoke_sensitivity_true(self):
        assert self._obj(ss=object()).supports_smoke_sensitivity is True

    def test_supports_smoke_sensitivity_false(self):
        assert self._obj().supports_smoke_sensitivity is False

    def test_supports_nightly_promise_true(self):
        assert self._obj(np=object()).supports_nightly_promise is True

    def test_supports_nightly_promise_false(self):
        assert self._obj().supports_nightly_promise is False
