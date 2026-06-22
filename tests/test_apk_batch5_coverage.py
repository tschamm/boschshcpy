"""Coverage top-up: hit the __init__ constructors of SHCLightControl,
SHCThermostatGen2, and SHCRoomThermostat2 via the real constructor path.

Missing lines before this file:
  models_impl.py: 520-521, 1243-1249, 1270-1271, 1280-1281,
                  1344-1350, 1369-1370, 1379-1380, 1389-1390, 1401-1402

All lines are __init__ bodies (service binding) and async-setter branches
that only execute when the service is NOT None — which requires constructing
via the real __init__ (not __new__).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _fake_api():
    return MagicMock(name="SHCAPI")


def _raw_device(model="TRV_GEN2", device_id="test-device"):
    return {
        "@type": "device",
        "rootDeviceId": "root",
        "id": device_id,
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


def _raw_svc(svc_id, state_dict, device_id="test-device"):
    """Minimal raw service dict accepted by services_impl.build()."""
    return {
        "@type": "DeviceServiceData",
        "id": svc_id,
        "deviceId": device_id,
        "path": f"/devices/{device_id}/services/{svc_id}",
        "state": {"@type": f"{svc_id}State", **state_dict},
    }


# ---------------------------------------------------------------------------
# SHCLightControl — lines 520-521 (__init__ + service binding)
# ---------------------------------------------------------------------------

class TestSHCLightControlInit:
    """Hit models_impl.py lines 520-521 via the real constructor."""

    def _make(self, switch_type="SWITCH"):
        from boschshcpy.models_impl import SHCLightControl
        services = [
            _raw_svc("SwitchConfiguration", {"switchType": switch_type}),
            _raw_svc("CommunicationQuality", {"quality": "GOOD"}),
            _raw_svc("PowerMeter", {"energyConsumption": 0.0, "powerConsumption": 0.0}),
        ]
        return SHCLightControl(
            api=_fake_api(),
            raw_device=_raw_device("LIGHT_CONTROL"),
            raw_device_services=services,
        )

    def test_init_binds_switch_config_service(self):
        obj = self._make()
        assert obj._switch_config_service is not None

    def test_switch_type_passthrough(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make(switch_type="PUSHBUTTON")
        assert obj.switch_type == SwitchConfiguration.SwitchType.PUSHBUTTON

    def test_async_set_switch_type_not_none(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make(switch_type="SWITCH")
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_switch_type(SwitchConfiguration.SwitchType.PUSHBUTTON))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "switchType", "PUSHBUTTON"
        )

    def test_init_without_switch_config(self):
        """Service missing → service bound to None, property returns None."""
        from boschshcpy.models_impl import SHCLightControl
        obj = SHCLightControl(
            api=_fake_api(),
            raw_device=_raw_device("LIGHT_CONTROL"),
            raw_device_services=[],
        )
        assert obj._switch_config_service is None
        assert obj.switch_type is None


# ---------------------------------------------------------------------------
# SHCThermostatGen2 — lines 1243-1249 (__init__) + async-setter branches
# lines 1270-1271, 1280-1281 (async_set_display_on_time,
#                              async_set_humidity_warning_enabled)
# ---------------------------------------------------------------------------

class TestSHCThermostatGen2Init:
    """Hit models_impl.py lines 1243-1249 (and setter branches) via the real constructor."""

    def _make(self):
        from boschshcpy.models_impl import SHCThermostatGen2
        services = [
            _raw_svc("DisplayConfiguration", {
                "displayBrightness": 50,
                "displayOnTime": 20,
                "humidityWarningEnabled": False,
            }),
            _raw_svc("DisplayDirection", {"direction": "NORMAL"}),
            _raw_svc("DisplayedTemperatureConfiguration", {"displayedTemperature": "SETPOINT"}),
            _raw_svc("WallThermostatConfiguration", {
                "valveType": "NORMALLY_CLOSE",
                "heaterType": "RADIATOR",
            }),
            _raw_svc("BatteryLevel", {}),
            _raw_svc("CommunicationQuality", {"quality": "GOOD"}),
            _raw_svc("SilentMode", {"mode": "NORMAL_MODE"}),
            _raw_svc("Thermostat", {
                "setpointTemperature": 21.0,
                "setpointTemperatureForLevelEco": 17.0,
                "setpointTemperatureForLevelComfort": 22.0,
                "operationMode": "AUTOMATIC",
                "boostMode": False,
                "supportsBoostMode": False,
                "coolingMode": False,
                "supportsCoolingMode": False,
                "childLock": False,
            }),
            _raw_svc("TemperatureLevel", {"temperature": 20.5}),
            _raw_svc("TemperatureOffset", {"offset": 0.0, "stepSize": 0.5,
                                           "minOffset": -5.0, "maxOffset": 5.0}),
            _raw_svc("ValveTappet", {"position": 0, "value": "VALVE_ADAPTION_SUCCESSFUL"}),
        ]
        return SHCThermostatGen2(
            api=_fake_api(),
            raw_device=_raw_device("TRV_GEN2"),
            raw_device_services=services,
        )

    def test_init_binds_all_four_services(self):
        obj = self._make()
        assert obj._display_config_service is not None
        assert obj._display_direction_service is not None
        assert obj._displayed_temp_service is not None
        assert obj._wall_thermostat_config_service is not None

    def test_display_brightness_passthrough(self):
        obj = self._make()
        assert obj.display_brightness == 50

    def test_display_on_time_passthrough(self):
        obj = self._make()
        assert obj.display_on_time == 20

    def test_humidity_warning_passthrough(self):
        obj = self._make()
        assert obj.humidity_warning_enabled is False

    def test_async_set_display_on_time_not_none(self):
        """Line 1270-1271: async_set_display_on_time when service is not None."""
        obj = self._make()
        obj._display_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_display_on_time(60))
        obj._display_config_service.async_put_state_element.assert_called_once_with(
            "displayOnTime", 60
        )

    def test_async_set_humidity_warning_enabled_not_none(self):
        """Line 1280-1281: async_set_humidity_warning_enabled when service is not None."""
        obj = self._make()
        obj._display_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_humidity_warning_enabled(True))
        obj._display_config_service.async_put_state_element.assert_called_once_with(
            "humidityWarningEnabled", True
        )

    def test_async_set_display_direction_not_none(self):
        from boschshcpy.services_impl import DisplayDirection
        obj = self._make()
        obj._display_direction_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_display_direction(DisplayDirection.Direction.REVERSED))
        obj._display_direction_service.async_put_state_element.assert_called_once_with(
            "direction", "REVERSED"
        )

    def test_async_set_displayed_temperature_not_none(self):
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        obj = self._make()
        obj._displayed_temp_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_displayed_temperature(
            DisplayedTemperatureConfiguration.DisplayedTemperature.MEASURED
        ))
        obj._displayed_temp_service.async_put_state_element.assert_called_once_with(
            "displayedTemperature", "MEASURED"
        )

    def test_async_set_valve_type_not_none(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make()
        obj._wall_thermostat_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_valve_type(WallThermostatConfiguration.ValveType.NORMALLY_OPEN))
        obj._wall_thermostat_config_service.async_put_state_element.assert_called_once_with(
            "valveType", "NORMALLY_OPEN"
        )

    def test_async_set_heater_type_not_none(self):
        from boschshcpy.services_impl import WallThermostatConfiguration
        obj = self._make()
        obj._wall_thermostat_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_heater_type(
            WallThermostatConfiguration.HeaterType.FLOOR_HEATING
        ))
        obj._wall_thermostat_config_service.async_put_state_element.assert_called_once_with(
            "heaterType", "FLOOR_HEATING"
        )


# ---------------------------------------------------------------------------
# SHCRoomThermostat2 — lines 1344-1350 (__init__) + async-setter branches
# lines 1369-1370, 1379-1380, 1389-1390, 1401-1402
# ---------------------------------------------------------------------------

class TestSHCRoomThermostat2Init:
    """Hit models_impl.py lines 1344-1350 (and setter branches) via the real constructor."""

    def _make(self):
        from boschshcpy.models_impl import SHCRoomThermostat2
        services = [
            _raw_svc("DisplayConfiguration", {
                "displayBrightness": 70,
                "displayOnTime": 30,
                "humidityWarningEnabled": True,
            }),
            _raw_svc("DisplayDirection", {"direction": "REVERSED"}),
            _raw_svc("DisplayedTemperatureConfiguration", {"displayedTemperature": "MEASURED"}),
            _raw_svc("TerminalConfiguration", {
                "type": "FLOOR_SENSOR_CONNECTED",
                "supportedTypes": ["NOT_CONNECTED", "FLOOR_SENSOR_CONNECTED"],
                "temperature": 19.0,
            }),
            _raw_svc("BatteryLevel", {}),
            _raw_svc("CommunicationQuality", {"quality": "GOOD"}),
            _raw_svc("Thermostat", {
                "setpointTemperature": 21.0,
                "setpointTemperatureForLevelEco": 17.0,
                "setpointTemperatureForLevelComfort": 22.0,
                "operationMode": "AUTOMATIC",
                "boostMode": False,
                "supportsBoostMode": False,
                "coolingMode": False,
                "supportsCoolingMode": False,
                "childLock": False,
            }),
            _raw_svc("TemperatureLevel", {"temperature": 20.0}),
            _raw_svc("HumidityLevel", {"humidity": 50.0}),
            _raw_svc("TemperatureOffset", {"offset": 0.0, "stepSize": 0.5,
                                           "minOffset": -5.0, "maxOffset": 5.0}),
        ]
        return SHCRoomThermostat2(
            api=_fake_api(),
            raw_device=_raw_device("RTH2_230"),
            raw_device_services=services,
        )

    def test_init_binds_all_four_services(self):
        obj = self._make()
        assert obj._display_config_service is not None
        assert obj._display_direction_service is not None
        assert obj._displayed_temp_service is not None
        assert obj._terminal_config_service is not None

    def test_display_brightness_passthrough(self):
        obj = self._make()
        assert obj.display_brightness == 70

    def test_display_on_time_passthrough(self):
        obj = self._make()
        assert obj.display_on_time == 30

    def test_humidity_warning_passthrough(self):
        obj = self._make()
        assert obj.humidity_warning_enabled is True

    def test_async_set_display_on_time_not_none(self):
        """Line 1369-1370: async_set_display_on_time when service is not None."""
        obj = self._make()
        obj._display_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_display_on_time(45))
        obj._display_config_service.async_put_state_element.assert_called_once_with(
            "displayOnTime", 45
        )

    def test_async_set_humidity_warning_enabled_not_none(self):
        """Line 1379-1380: async_set_humidity_warning_enabled when service is not None."""
        obj = self._make()
        obj._display_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_humidity_warning_enabled(False))
        obj._display_config_service.async_put_state_element.assert_called_once_with(
            "humidityWarningEnabled", False
        )

    def test_async_set_display_direction_not_none(self):
        """Line 1389-1390: async_set_display_direction when service is not None."""
        from boschshcpy.services_impl import DisplayDirection
        obj = self._make()
        obj._display_direction_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_display_direction(DisplayDirection.Direction.NORMAL))
        obj._display_direction_service.async_put_state_element.assert_called_once_with(
            "direction", "NORMAL"
        )

    def test_async_set_displayed_temperature_not_none(self):
        """Line 1401-1402: async_set_displayed_temperature when service is not None."""
        from boschshcpy.services_impl import DisplayedTemperatureConfiguration
        obj = self._make()
        obj._displayed_temp_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_displayed_temperature(
            DisplayedTemperatureConfiguration.DisplayedTemperature.SETPOINT
        ))
        obj._displayed_temp_service.async_put_state_element.assert_called_once_with(
            "displayedTemperature", "SETPOINT"
        )

    def test_terminal_type_passthrough(self):
        from boschshcpy.services_impl import TerminalConfiguration
        obj = self._make()
        assert obj.terminal_type == TerminalConfiguration.Type.FLOOR_SENSOR_CONNECTED

    def test_terminal_temperature_passthrough(self):
        obj = self._make()
        assert obj.terminal_temperature == 19.0

    def test_supported_terminal_types_passthrough(self):
        obj = self._make()
        assert "FLOOR_SENSOR_CONNECTED" in obj.supported_terminal_types

    def test_async_set_terminal_type_not_none(self):
        from boschshcpy.services_impl import TerminalConfiguration
        obj = self._make()
        obj._terminal_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_terminal_type(
            TerminalConfiguration.Type.OUTDOOR_SENSOR_CONNECTED
        ))
        obj._terminal_config_service.async_put_state_element.assert_called_once_with(
            "type", "OUTDOOR_SENSOR_CONNECTED"
        )
