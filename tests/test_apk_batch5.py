"""APK BATCH 5 — Display/thermostat config services + new device models.

Services:
    DisplayConfiguration, DisplayDirection, DisplayedTemperatureConfiguration,
    TerminalConfiguration, WallThermostatConfiguration

Models:
    SHCThermostatGen2 (TRV_GEN2, TRV_GEN2_DUAL)
    SHCRoomThermostat2 (RTH2_230, RTH2_BAT) — extended with new services
"""

import asyncio


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_svc(cls, state_dict):
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


def _fake_raw_device(model="TRV_GEN2"):
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


# ---------------------------------------------------------------------------
# BATCH 5: DisplayConfiguration
# ---------------------------------------------------------------------------

class TestDisplayConfiguration:
    def _svc(self, **state):
        from boschshcpy.services_impl import DisplayConfiguration
        return _make_svc(DisplayConfiguration, state)

    def test_display_brightness_value(self):
        svc = self._svc(displayBrightness=75)
        assert svc.display_brightness == 75

    def test_display_brightness_missing_returns_none(self):
        svc = self._svc()
        assert svc.display_brightness is None

    def test_display_brightness_max(self):
        svc = self._svc(displayBrightnessMax=100)
        assert svc.display_brightness_max == 100

    def test_display_brightness_min(self):
        svc = self._svc(displayBrightnessMin=0)
        assert svc.display_brightness_min == 0

    def test_display_brightness_step_size(self):
        svc = self._svc(displayBrightnessStepSize=5)
        assert svc.display_brightness_step_size == 5

    def test_display_brightness_max_missing_returns_none(self):
        svc = self._svc()
        assert svc.display_brightness_max is None

    def test_display_brightness_min_missing_returns_none(self):
        svc = self._svc()
        assert svc.display_brightness_min is None

    def test_display_brightness_step_size_missing_returns_none(self):
        svc = self._svc()
        assert svc.display_brightness_step_size is None

    def test_display_on_time_value(self):
        svc = self._svc(displayOnTime=30)
        assert svc.display_on_time == 30

    def test_display_on_time_missing_returns_none(self):
        svc = self._svc()
        assert svc.display_on_time is None

    def test_display_on_time_max(self):
        svc = self._svc(displayOnTimeMax=60)
        assert svc.display_on_time_max == 60

    def test_display_on_time_min(self):
        svc = self._svc(displayOnTimeMin=5)
        assert svc.display_on_time_min == 5

    def test_display_on_time_step_size(self):
        svc = self._svc(displayOnTimeStepSize=5)
        assert svc.display_on_time_step_size == 5

    def test_display_on_time_max_missing_returns_none(self):
        svc = self._svc()
        assert svc.display_on_time_max is None

    def test_humidity_warning_enabled_true(self):
        svc = self._svc(humidityWarningEnabled=True)
        assert svc.humidity_warning_enabled is True

    def test_humidity_warning_enabled_false(self):
        svc = self._svc(humidityWarningEnabled=False)
        assert svc.humidity_warning_enabled is False

    def test_humidity_warning_enabled_missing_defaults_none(self):
        svc = self._svc()
        assert svc.humidity_warning_enabled is None

    def test_async_setter_display_brightness(self):
        from unittest.mock import AsyncMock
        svc = self._svc(displayBrightness=50)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_displayBrightness(90))
        svc.async_put_state_element.assert_called_once_with("displayBrightness", 90)

    def test_property_setter_display_brightness(self):
        from unittest.mock import MagicMock
        svc = self._svc(displayBrightness=50)
        svc.put_state_element = MagicMock()
        svc.display_brightness = 30
        svc.put_state_element.assert_called_once_with("displayBrightness", 30)

    def test_async_setter_display_on_time(self):
        from unittest.mock import AsyncMock
        svc = self._svc(displayOnTime=10)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_displayOnTime(60))
        svc.async_put_state_element.assert_called_once_with("displayOnTime", 60)

    def test_property_setter_display_on_time(self):
        from unittest.mock import MagicMock
        svc = self._svc(displayOnTime=10)
        svc.put_state_element = MagicMock()
        svc.display_on_time = 20
        svc.put_state_element.assert_called_once_with("displayOnTime", 20)

    def test_async_setter_humidity_warning_enabled(self):
        from unittest.mock import AsyncMock
        svc = self._svc(humidityWarningEnabled=False)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_humidityWarningEnabled(True))
        svc.async_put_state_element.assert_called_once_with("humidityWarningEnabled", True)

    def test_property_setter_humidity_warning_enabled(self):
        from unittest.mock import MagicMock
        svc = self._svc(humidityWarningEnabled=False)
        svc.put_state_element = MagicMock()
        svc.humidity_warning_enabled = True
        svc.put_state_element.assert_called_once_with("humidityWarningEnabled", True)

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, DisplayConfiguration
        assert "DisplayConfiguration" in SERVICE_MAPPING
        assert SERVICE_MAPPING["DisplayConfiguration"] is DisplayConfiguration


# ---------------------------------------------------------------------------
# BATCH 5: DisplayDirection
# ---------------------------------------------------------------------------

class TestDisplayDirection:
    def _svc(self, **state):
        from boschshcpy.services_impl import DisplayDirection
        return _make_svc(DisplayDirection, state)

    def test_direction_normal(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = self._svc(direction="NORMAL")
        assert svc.direction == DisplayDirection.Direction.NORMAL

    def test_direction_reversed(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = self._svc(direction="REVERSED")
        assert svc.direction == DisplayDirection.Direction.REVERSED

    def test_direction_unknown_explicit(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = self._svc(direction="UNKNOWN")
        assert svc.direction == DisplayDirection.Direction.UNKNOWN

    def test_direction_missing_returns_none(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = self._svc()
        assert svc.direction is None

    def test_direction_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import DisplayDirection
        svc = self._svc(direction="FUTURE_VALUE")
        assert svc.direction == DisplayDirection.Direction.UNKNOWN

    def test_enum_values(self):
        from boschshcpy.services_impl import DisplayDirection
        assert DisplayDirection.Direction.NORMAL.value == "NORMAL"
        assert DisplayDirection.Direction.REVERSED.value == "REVERSED"
        assert DisplayDirection.Direction.UNKNOWN.value == "UNKNOWN"

    def test_async_setter_direction(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import DisplayDirection
        svc = self._svc(direction="NORMAL")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_direction(DisplayDirection.Direction.REVERSED))
        svc.async_put_state_element.assert_called_once_with("direction", "REVERSED")

    def test_property_setter_direction(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import DisplayDirection
        svc = self._svc(direction="NORMAL")
        svc.put_state_element = MagicMock()
        svc.direction = DisplayDirection.Direction.REVERSED
        svc.put_state_element.assert_called_once_with("direction", "REVERSED")

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, DisplayDirection
        assert "DisplayDirection" in SERVICE_MAPPING
        assert SERVICE_MAPPING["DisplayDirection"] is DisplayDirection


# ---------------------------------------------------------------------------
# BATCH 5: DisplayedTemperatureConfiguration
# ---------------------------------------------------------------------------

class TestDisplayedTemperatureConfiguration:
    def _svc(self, **state):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        return _make_svc(DisplayedTemperatureConfiguration, state)

    def test_displayed_temperature_setpoint(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = self._svc(displayedTemperature="SETPOINT")
        assert svc.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.SETPOINT
        )

    def test_displayed_temperature_measured(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = self._svc(displayedTemperature="MEASURED")
        assert svc.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.MEASURED
        )

    def test_displayed_temperature_unknown_explicit(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = self._svc(displayedTemperature="UNKNOWN")
        assert svc.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.UNKNOWN
        )

    def test_displayed_temperature_missing_returns_none(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = self._svc()
        assert svc.displayed_temperature is None

    def test_displayed_temperature_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = self._svc(displayedTemperature="FUTURE_VALUE")
        assert svc.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.UNKNOWN
        )

    def test_enum_values(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        DT = DisplayedTemperatureConfiguration.DisplayedTemperature
        assert DT.SETPOINT.value == "SETPOINT"
        assert DT.MEASURED.value == "MEASURED"
        assert DT.UNKNOWN.value == "UNKNOWN"

    def test_async_setter_displayed_temperature(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = self._svc(displayedTemperature="SETPOINT")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_displayedTemperature(
            DisplayedTemperatureConfiguration.DisplayedTemperature.MEASURED
        ))
        svc.async_put_state_element.assert_called_once_with("displayedTemperature", "MEASURED")

    def test_property_setter_displayed_temperature(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = self._svc(displayedTemperature="SETPOINT")
        svc.put_state_element = MagicMock()
        svc.displayed_temperature = (
            DisplayedTemperatureConfiguration.DisplayedTemperature.MEASURED
        )
        svc.put_state_element.assert_called_once_with("displayedTemperature", "MEASURED")

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, DisplayedTemperatureConfiguration
        assert "DisplayedTemperatureConfiguration" in SERVICE_MAPPING
        assert (
            SERVICE_MAPPING["DisplayedTemperatureConfiguration"]
            is DisplayedTemperatureConfiguration
        )


# ---------------------------------------------------------------------------
# BATCH 5: TerminalConfiguration
# ---------------------------------------------------------------------------

class TestTerminalConfiguration:
    def _svc(self, **state):
        from boschshcpy.services_impl import TerminalConfiguration
        return _make_svc(TerminalConfiguration, state)

    def test_type_not_connected(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="NOT_CONNECTED")
        assert svc.type == TerminalConfiguration.Type.NOT_CONNECTED

    def test_type_floor_sensor_connected(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="FLOOR_SENSOR_CONNECTED")
        assert svc.type == TerminalConfiguration.Type.FLOOR_SENSOR_CONNECTED

    def test_type_floor_sensor_used_for_regulation(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="FLOOR_SENSOR_USED_FOR_REGULATION")
        assert svc.type == TerminalConfiguration.Type.FLOOR_SENSOR_USED_FOR_REGULATION

    def test_type_floor_sensor_displayed(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="FLOOR_SENSOR_DISPLAYED")
        assert svc.type == TerminalConfiguration.Type.FLOOR_SENSOR_DISPLAYED

    def test_type_floor_sensor_displayed_and_used(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="FLOOR_SENSOR_DISPLAYED_AND_USED_FOR_REGULATION")
        assert svc.type == (
            TerminalConfiguration.Type.FLOOR_SENSOR_DISPLAYED_AND_USED_FOR_REGULATION
        )

    def test_type_volt_free_sensor_connected(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="VOLT_FREE_SENSOR_CONNECTED")
        assert svc.type == TerminalConfiguration.Type.VOLT_FREE_SENSOR_CONNECTED

    def test_type_volt_free_sensor_used(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="VOLT_FREE_SENSOR_CONNECTED_AND_USED_FOR_OPERATION")
        assert svc.type == (
            TerminalConfiguration.Type.VOLT_FREE_SENSOR_CONNECTED_AND_USED_FOR_OPERATION
        )

    def test_type_outdoor_sensor_connected(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="OUTDOOR_SENSOR_CONNECTED")
        assert svc.type == TerminalConfiguration.Type.OUTDOOR_SENSOR_CONNECTED

    def test_type_unknown_explicit(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="UNKNOWN")
        assert svc.type == TerminalConfiguration.Type.UNKNOWN

    def test_type_missing_returns_none(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc()
        assert svc.type is None

    def test_type_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="FUTURE_TYPE")
        assert svc.type == TerminalConfiguration.Type.UNKNOWN

    def test_supported_types_list(self):
        svc = self._svc(supportedTypes=["NOT_CONNECTED", "FLOOR_SENSOR_CONNECTED"])
        assert svc.supported_types == ["NOT_CONNECTED", "FLOOR_SENSOR_CONNECTED"]

    def test_supported_types_missing_returns_empty(self):
        svc = self._svc()
        assert svc.supported_types == []

    def test_temperature_value(self):
        svc = self._svc(temperature=22.5)
        assert svc.temperature == 22.5

    def test_temperature_missing_returns_none(self):
        svc = self._svc()
        assert svc.temperature is None

    def test_async_setter_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="NOT_CONNECTED")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_type(TerminalConfiguration.Type.OUTDOOR_SENSOR_CONNECTED))
        svc.async_put_state_element.assert_called_once_with(
            "type", "OUTDOOR_SENSOR_CONNECTED"
        )

    def test_property_setter_type(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import TerminalConfiguration
        svc = self._svc(type="NOT_CONNECTED")
        svc.put_state_element = MagicMock()
        svc.type = TerminalConfiguration.Type.FLOOR_SENSOR_DISPLAYED
        svc.put_state_element.assert_called_once_with("type", "FLOOR_SENSOR_DISPLAYED")

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, TerminalConfiguration
        assert "TerminalConfiguration" in SERVICE_MAPPING
        assert SERVICE_MAPPING["TerminalConfiguration"] is TerminalConfiguration


# ---------------------------------------------------------------------------
# BATCH 5: WallThermostatConfiguration
# ---------------------------------------------------------------------------

class TestWallThermostatConfiguration:
    def _svc(self, **state):
        from boschshcpy.services_impl import WallThermostatConfiguration
        return _make_svc(WallThermostatConfiguration, state)

    def test_valve_type_normally_close(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(valveType="NORMALLY_CLOSE")
        assert svc.valve_type == WallThermostatConfiguration.ValveType.NORMALLY_CLOSE

    def test_valve_type_normally_open(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(valveType="NORMALLY_OPEN")
        assert svc.valve_type == WallThermostatConfiguration.ValveType.NORMALLY_OPEN

    def test_valve_type_unknown_explicit(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(valveType="UNKNOWN")
        assert svc.valve_type == WallThermostatConfiguration.ValveType.UNKNOWN

    def test_valve_type_missing_returns_none(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc()
        assert svc.valve_type is None

    def test_valve_type_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(valveType="FUTURE_VALVE")
        assert svc.valve_type == WallThermostatConfiguration.ValveType.UNKNOWN

    def test_heater_type_floor_heating(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="FLOOR_HEATING")
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.FLOOR_HEATING

    def test_heater_type_floor_heating_low_energy(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="FLOOR_HEATING_LOW_ENERGY")
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.FLOOR_HEATING_LOW_ENERGY

    def test_heater_type_radiator(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="RADIATOR")
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.RADIATOR

    def test_heater_type_convector_passive(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="CONVECTOR_PASSIVE")
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.CONVECTOR_PASSIVE

    def test_heater_type_convector_active(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="CONVECTOR_ACTIVE")
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.CONVECTOR_ACTIVE

    def test_heater_type_unknown_explicit(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="UNKNOWN")
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.UNKNOWN

    def test_heater_type_missing_returns_none(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc()
        assert svc.heater_type is None

    def test_heater_type_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="FUTURE_HEATER")
        assert svc.heater_type == WallThermostatConfiguration.HeaterType.UNKNOWN

    def test_async_setter_valve_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(valveType="NORMALLY_CLOSE")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_valveType(WallThermostatConfiguration.ValveType.NORMALLY_OPEN))
        svc.async_put_state_element.assert_called_once_with("valveType", "NORMALLY_OPEN")

    def test_property_setter_valve_type(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(valveType="NORMALLY_CLOSE")
        svc.put_state_element = MagicMock()
        svc.valve_type = WallThermostatConfiguration.ValveType.NORMALLY_OPEN
        svc.put_state_element.assert_called_once_with("valveType", "NORMALLY_OPEN")

    def test_async_setter_heater_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="RADIATOR")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(
            svc.async_set_heaterType(WallThermostatConfiguration.HeaterType.CONVECTOR_ACTIVE)
        )
        svc.async_put_state_element.assert_called_once_with("heaterType", "CONVECTOR_ACTIVE")

    def test_property_setter_heater_type(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = self._svc(heaterType="RADIATOR")
        svc.put_state_element = MagicMock()
        svc.heater_type = WallThermostatConfiguration.HeaterType.FLOOR_HEATING
        svc.put_state_element.assert_called_once_with("heaterType", "FLOOR_HEATING")

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, WallThermostatConfiguration
        assert "WallThermostatConfiguration" in SERVICE_MAPPING
        assert SERVICE_MAPPING["WallThermostatConfiguration"] is WallThermostatConfiguration

    # -- supported_heater_types (APK field, rawscan-confirmed hass#274/#330) --

    def test_supported_heater_types_rth2_230(self):
        # rawscan (hass#330): RTH2_230's supported set is smaller than BWTH's.
        svc = self._svc(supportedHeaterTypes=["VOLT_FREE_HEATING", "FLOOR_HEATING"])
        assert svc.supported_heater_types == ["VOLT_FREE_HEATING", "FLOOR_HEATING"]

    def test_supported_heater_types_bwth_wider_set(self):
        # rawscan (hass#274): BWTH advertises a wider set than RTH2_230.
        svc = self._svc(
            supportedHeaterTypes=[
                "CONVECTOR_ACTIVE",
                "RADIATOR",
                "CONVECTOR_PASSIVE",
                "FLOOR_HEATING",
                "FLOOR_HEATING_LOW_ENERGY",
            ]
        )
        assert svc.supported_heater_types == [
            "CONVECTOR_ACTIVE",
            "RADIATOR",
            "CONVECTOR_PASSIVE",
            "FLOOR_HEATING",
            "FLOOR_HEATING_LOW_ENERGY",
        ]

    def test_supported_heater_types_missing_returns_empty_list(self):
        svc = self._svc()
        assert svc.supported_heater_types == []

    # -- decalcification_protection_enabled (APK field, rawscan-confirmed hass#330) --

    def test_decalcification_protection_enabled_true(self):
        svc = self._svc(decalcificationProtectionEnabled=True)
        assert svc.decalcification_protection_enabled is True

    def test_decalcification_protection_enabled_false(self):
        svc = self._svc(decalcificationProtectionEnabled=False)
        assert svc.decalcification_protection_enabled is False

    def test_decalcification_protection_enabled_missing_returns_none(self):
        # Absent on older firmware (confirmed via rawscan-database.md).
        svc = self._svc()
        assert svc.decalcification_protection_enabled is None


# ---------------------------------------------------------------------------
# Model mappings
# ---------------------------------------------------------------------------

class TestModelMappings:
    def test_trv_gen2_maps_to_thermostatgen2(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCThermostatGen2
        assert MODEL_MAPPING["TRV_GEN2"] is SHCThermostatGen2

    def test_trv_gen2_dual_maps_to_thermostatgen2(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCThermostatGen2
        assert MODEL_MAPPING["TRV_GEN2_DUAL"] is SHCThermostatGen2

    def test_rth2_230_maps_to_roomthermostat2(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCRoomThermostat2
        assert MODEL_MAPPING["RTH2_230"] is SHCRoomThermostat2

    def test_rth2_bat_maps_to_roomthermostat2(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCRoomThermostat2
        assert MODEL_MAPPING["RTH2_BAT"] is SHCRoomThermostat2

    def test_thermostatgen2_is_subclass_of_thermostat(self):
        from boschshcpy.models_impl import SHCThermostatGen2, SHCThermostat
        assert issubclass(SHCThermostatGen2, SHCThermostat)

    def test_roomthermostat2_is_subclass_of_wallthermostat(self):
        from boschshcpy.models_impl import SHCRoomThermostat2, SHCWallThermostat
        assert issubclass(SHCRoomThermostat2, SHCWallThermostat)


# ---------------------------------------------------------------------------
# SHCThermostatGen2 bindings
# ---------------------------------------------------------------------------

class TestSHCThermostatGen2Bindings:
    def _make_trv_gen2(
        self,
        dc_state=None,
        dd_state=None,
        dtc_state=None,
        wtc_state=None,
    ):
        from boschshcpy.services_impl import (
            DisplayConfiguration,
            DisplayDirection,
            DisplayedTemperatureConfiguration,
            WallThermostatConfiguration,
        )
        from boschshcpy.models_impl import SHCThermostatGen2

        dc = _make_svc(DisplayConfiguration, dc_state or {})
        dd = _make_svc(DisplayDirection, dd_state or {})
        dtc = _make_svc(DisplayedTemperatureConfiguration, dtc_state or {})
        wtc = _make_svc(WallThermostatConfiguration, wtc_state or {})

        obj = SHCThermostatGen2.__new__(SHCThermostatGen2)
        obj._raw_device = _fake_raw_device("TRV_GEN2")
        obj._callbacks = {}
        obj._api = None
        obj._device_services_by_id = {
            "DisplayConfiguration": dc,
            "DisplayDirection": dd,
            "DisplayedTemperatureConfiguration": dtc,
            "WallThermostatConfiguration": wtc,
        }
        obj._display_config_service = dc
        obj._display_direction_service = dd
        obj._displayed_temp_service = dtc
        obj._wall_thermostat_config_service = wtc
        # Other inherited services
        obj._valvetappet_service = None
        obj._thermostat_service = None
        obj._batterylevel_service = None
        obj._communicationquality_service = None
        obj._silentmode_service = None
        obj._temperaturelevel_service = None
        obj._temperatureoffset_service = None
        return obj

    def test_display_brightness_passthrough(self):
        obj = self._make_trv_gen2(dc_state={"displayBrightness": 60})
        assert obj.display_brightness == 60

    def test_display_brightness_absent_service_returns_none(self):
        from boschshcpy.models_impl import SHCThermostatGen2
        obj = SHCThermostatGen2.__new__(SHCThermostatGen2)
        obj._display_config_service = None
        obj._display_direction_service = None
        obj._displayed_temp_service = None
        obj._wall_thermostat_config_service = None
        assert obj.display_brightness is None
        assert obj.display_on_time is None
        assert obj.humidity_warning_enabled is None
        assert obj.display_direction is None
        assert obj.displayed_temperature is None
        assert obj.valve_type is None
        assert obj.heater_type is None

    def test_display_on_time_passthrough(self):
        obj = self._make_trv_gen2(dc_state={"displayOnTime": 20})
        assert obj.display_on_time == 20

    def test_humidity_warning_enabled_passthrough(self):
        obj = self._make_trv_gen2(dc_state={"humidityWarningEnabled": True})
        assert obj.humidity_warning_enabled is True

    def test_display_direction_passthrough(self):
        from boschshcpy.services_impl import DisplayDirection
        obj = self._make_trv_gen2(dd_state={"direction": "REVERSED"})
        assert obj.display_direction == DisplayDirection.Direction.REVERSED

    def test_displayed_temperature_passthrough(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        obj = self._make_trv_gen2(dtc_state={"displayedTemperature": "MEASURED"})
        assert obj.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.MEASURED
        )

    def test_valve_type_passthrough(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make_trv_gen2(wtc_state={"valveType": "NORMALLY_OPEN"})
        assert obj.valve_type == WallThermostatConfiguration.ValveType.NORMALLY_OPEN

    def test_heater_type_passthrough(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make_trv_gen2(wtc_state={"heaterType": "RADIATOR"})
        assert obj.heater_type == WallThermostatConfiguration.HeaterType.RADIATOR

    def test_async_set_display_brightness(self):
        from unittest.mock import AsyncMock
        obj = self._make_trv_gen2(dc_state={"displayBrightness": 50})
        obj._display_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_display_brightness(80))
        obj._display_config_service.async_put_state_element.assert_called_once_with(
            "displayBrightness", 80
        )

    def test_async_set_display_direction(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import DisplayDirection
        obj = self._make_trv_gen2(dd_state={"direction": "NORMAL"})
        obj._display_direction_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_display_direction(DisplayDirection.Direction.REVERSED))
        obj._display_direction_service.async_put_state_element.assert_called_once_with(
            "direction", "REVERSED"
        )

    def test_async_set_displayed_temperature(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        obj = self._make_trv_gen2(dtc_state={"displayedTemperature": "SETPOINT"})
        obj._displayed_temp_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_displayed_temperature(
            DisplayedTemperatureConfiguration.DisplayedTemperature.MEASURED
        ))
        obj._displayed_temp_service.async_put_state_element.assert_called_once_with(
            "displayedTemperature", "MEASURED"
        )

    def test_async_set_valve_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make_trv_gen2(wtc_state={"valveType": "NORMALLY_CLOSE"})
        obj._wall_thermostat_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_valve_type(WallThermostatConfiguration.ValveType.NORMALLY_OPEN))
        obj._wall_thermostat_config_service.async_put_state_element.assert_called_once_with(
            "valveType", "NORMALLY_OPEN"
        )

    def test_async_set_heater_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make_trv_gen2(wtc_state={"heaterType": "RADIATOR"})
        obj._wall_thermostat_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_heater_type(
            WallThermostatConfiguration.HeaterType.FLOOR_HEATING
        ))
        obj._wall_thermostat_config_service.async_put_state_element.assert_called_once_with(
            "heaterType", "FLOOR_HEATING"
        )


# ---------------------------------------------------------------------------
# SHCRoomThermostat2 bindings (extended with new services)
# ---------------------------------------------------------------------------

class TestSHCRoomThermostat2Bindings:
    def _make_rth2(
        self,
        dc_state=None,
        dd_state=None,
        dtc_state=None,
        tc_state=None,
    ):
        from boschshcpy.services_impl import (
            DisplayConfiguration,
            DisplayDirection,
            DisplayedTemperatureConfiguration,
            TerminalConfiguration,
        )
        from boschshcpy.models_impl import SHCRoomThermostat2

        dc = _make_svc(DisplayConfiguration, dc_state or {})
        dd = _make_svc(DisplayDirection, dd_state or {})
        dtc = _make_svc(DisplayedTemperatureConfiguration, dtc_state or {})
        tc = _make_svc(TerminalConfiguration, tc_state or {})

        obj = SHCRoomThermostat2.__new__(SHCRoomThermostat2)
        obj._raw_device = _fake_raw_device("RTH2_230")
        obj._callbacks = {}
        obj._api = None
        obj._device_services_by_id = {
            "DisplayConfiguration": dc,
            "DisplayDirection": dd,
            "DisplayedTemperatureConfiguration": dtc,
            "TerminalConfiguration": tc,
        }
        obj._display_config_service = dc
        obj._display_direction_service = dd
        obj._displayed_temp_service = dtc
        obj._terminal_config_service = tc
        # Other inherited services
        obj._batterylevel_service = None
        obj._thermostat_service = None
        obj._communicationquality_service = None
        obj._temperaturelevel_service = None
        obj._humiditylevel_service = None
        obj._temperatureoffset_service = None
        return obj

    def test_display_brightness_passthrough(self):
        obj = self._make_rth2(dc_state={"displayBrightness": 70})
        assert obj.display_brightness == 70

    def test_display_brightness_absent_service_returns_none(self):
        from boschshcpy.models_impl import SHCRoomThermostat2
        obj = SHCRoomThermostat2.__new__(SHCRoomThermostat2)
        obj._display_config_service = None
        obj._display_direction_service = None
        obj._displayed_temp_service = None
        obj._terminal_config_service = None
        assert obj.display_brightness is None
        assert obj.display_on_time is None
        assert obj.humidity_warning_enabled is None
        assert obj.display_direction is None
        assert obj.displayed_temperature is None
        assert obj.terminal_type is None
        assert obj.terminal_temperature is None
        assert obj.supported_terminal_types == []

    def test_display_on_time_passthrough(self):
        obj = self._make_rth2(dc_state={"displayOnTime": 15})
        assert obj.display_on_time == 15

    def test_humidity_warning_enabled_passthrough(self):
        obj = self._make_rth2(dc_state={"humidityWarningEnabled": True})
        assert obj.humidity_warning_enabled is True

    def test_display_direction_passthrough(self):
        from boschshcpy.services_impl import DisplayDirection
        obj = self._make_rth2(dd_state={"direction": "NORMAL"})
        assert obj.display_direction == DisplayDirection.Direction.NORMAL

    def test_displayed_temperature_passthrough(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        obj = self._make_rth2(dtc_state={"displayedTemperature": "SETPOINT"})
        assert obj.displayed_temperature == (
            DisplayedTemperatureConfiguration.DisplayedTemperature.SETPOINT
        )

    def test_terminal_type_passthrough(self):
        from boschshcpy.services_impl import TerminalConfiguration
        obj = self._make_rth2(tc_state={"type": "FLOOR_SENSOR_CONNECTED"})
        assert obj.terminal_type == TerminalConfiguration.Type.FLOOR_SENSOR_CONNECTED

    def test_terminal_temperature_passthrough(self):
        obj = self._make_rth2(tc_state={"type": "OUTDOOR_SENSOR_CONNECTED", "temperature": 18.5})
        assert obj.terminal_temperature == 18.5

    def test_supported_terminal_types_passthrough(self):
        types = ["NOT_CONNECTED", "FLOOR_SENSOR_CONNECTED"]
        obj = self._make_rth2(tc_state={"type": "NOT_CONNECTED", "supportedTypes": types})
        assert obj.supported_terminal_types == types

    def test_async_set_display_brightness(self):
        from unittest.mock import AsyncMock
        obj = self._make_rth2(dc_state={"displayBrightness": 50})
        obj._display_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_display_brightness(75))
        obj._display_config_service.async_put_state_element.assert_called_once_with(
            "displayBrightness", 75
        )

    def test_async_set_terminal_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import TerminalConfiguration
        obj = self._make_rth2(tc_state={"type": "NOT_CONNECTED"})
        obj._terminal_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_terminal_type(TerminalConfiguration.Type.OUTDOOR_SENSOR_CONNECTED))
        obj._terminal_config_service.async_put_state_element.assert_called_once_with(
            "type", "OUTDOOR_SENSOR_CONNECTED"
        )


# ---------------------------------------------------------------------------
# device_helper accessor checks
# ---------------------------------------------------------------------------

class TestDeviceHelperAccessors:
    def test_thermostats_accessor_includes_trv_gen2(self):
        from boschshcpy.device_helper import SHCDeviceHelper
        from boschshcpy.models_impl import SHCThermostatGen2
        helper = SHCDeviceHelper.__new__(SHCDeviceHelper)
        helper._devices_by_model = {k: {} for k in ["TRV", "TRV_GEN2", "TRV_GEN2_DUAL"]}
        # Create a fake TRV_GEN2 entry
        fake = object()
        helper._devices_by_model["TRV_GEN2"]["dev1"] = fake
        result = helper.thermostats
        assert fake in result

    def test_thermostats_accessor_includes_trv_gen2_dual(self):
        from boschshcpy.device_helper import SHCDeviceHelper
        helper = SHCDeviceHelper.__new__(SHCDeviceHelper)
        helper._devices_by_model = {k: {} for k in ["TRV", "TRV_GEN2", "TRV_GEN2_DUAL"]}
        fake = object()
        helper._devices_by_model["TRV_GEN2_DUAL"]["dev1"] = fake
        result = helper.thermostats
        assert fake in result

    def test_roomthermostats_accessor_includes_rth2_230(self):
        from boschshcpy.device_helper import SHCDeviceHelper
        helper = SHCDeviceHelper.__new__(SHCDeviceHelper)
        helper._devices_by_model = {k: {} for k in ["RTH2_BAT", "RTH2_230"]}
        fake = object()
        helper._devices_by_model["RTH2_230"]["dev1"] = fake
        result = helper.roomthermostats
        assert fake in result

    def test_roomthermostats_accessor_includes_rth2_bat(self):
        from boschshcpy.device_helper import SHCDeviceHelper
        helper = SHCDeviceHelper.__new__(SHCDeviceHelper)
        helper._devices_by_model = {k: {} for k in ["RTH2_BAT", "RTH2_230"]}
        fake = object()
        helper._devices_by_model["RTH2_BAT"]["dev1"] = fake
        result = helper.roomthermostats
        assert fake in result


# ---------------------------------------------------------------------------
# summary() smoke tests
# ---------------------------------------------------------------------------

class TestSummaryMethods:
    def test_display_configuration_summary(self, capsys):
        from boschshcpy.services_impl import DisplayConfiguration
        svc = _make_svc(
            DisplayConfiguration,
            {"displayBrightness": 50, "displayOnTime": 30, "humidityWarningEnabled": False},
        )
        svc.summary()
        captured = capsys.readouterr()
        assert "displayBrightness" in captured.out

    def test_display_direction_summary(self, capsys):
        from boschshcpy.services_impl import DisplayDirection
        svc = _make_svc(DisplayDirection, {"direction": "NORMAL"})
        svc.summary()
        captured = capsys.readouterr()
        assert "direction" in captured.out

    def test_displayed_temperature_configuration_summary(self, capsys):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        svc = _make_svc(DisplayedTemperatureConfiguration, {"displayedTemperature": "SETPOINT"})
        svc.summary()
        captured = capsys.readouterr()
        assert "displayedTemperature" in captured.out

    def test_terminal_configuration_summary(self, capsys):
        from boschshcpy.services_impl import TerminalConfiguration
        svc = _make_svc(
            TerminalConfiguration,
            {"type": "NOT_CONNECTED", "supportedTypes": [], "temperature": None},
        )
        svc.summary()
        captured = capsys.readouterr()
        assert "type" in captured.out

    def test_wall_thermostat_configuration_summary(self, capsys):
        from boschshcpy.services_impl import WallThermostatConfiguration
        svc = _make_svc(
            WallThermostatConfiguration,
            {"valveType": "NORMALLY_CLOSE", "heaterType": "RADIATOR"},
        )
        svc.summary()
        captured = capsys.readouterr()
        assert "valveType" in captured.out
