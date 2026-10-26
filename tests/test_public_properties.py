"""Public accessors that integrations previously reached through private services."""

import pytest

from boschshcpy.models_impl import (
    SHCHeatingCircuit,
    SHCLightControl,
    SHCMicromoduleRelay,
    SHCTwinguard,
)
from boschshcpy.services_impl import (
    AirQualityLevelService,
    HeatingCircuitService,
    SwitchConfiguration,
)


def _svc(cls, svc_id, state):
    svc = cls.__new__(cls)
    svc._api = None
    svc._raw_device_service = {
        "id": svc_id,
        "deviceId": "device-1",
        "path": f"/x/{svc_id}",
        "state": state,
    }
    svc._raw_state = state
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


def test_heating_circuit_eco_and_comfort_setpoints():
    service = _svc(
        HeatingCircuitService,
        "HeatingCircuit",
        {
            "setpointTemperatureForLevelEco": 18.0,
            "setpointTemperatureForLevelComfort": 23.5,
        },
    )
    device = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
    device._heating_circuit_service = service

    assert device.setpoint_temperature_eco == 18.0
    assert device.setpoint_temperature_comfort == 23.5


def test_heating_circuit_setpoints_none_when_not_configured():
    service = _svc(HeatingCircuitService, "HeatingCircuit", {})
    device = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
    device._heating_circuit_service = service

    assert device.setpoint_temperature_eco is None
    assert device.setpoint_temperature_comfort is None


@pytest.mark.parametrize("cls", [SHCMicromoduleRelay, SHCLightControl])
def test_supported_output_modes(cls):
    service = _svc(
        SwitchConfiguration,
        "SwitchConfiguration",
        {"supportedOutputModes": ["PUSHBUTTON", "SWITCH"]},
    )
    device = cls.__new__(cls)
    device._switch_config_service = service

    assert device.supported_output_modes == ["PUSHBUTTON", "SWITCH"]


@pytest.mark.parametrize("cls", [SHCMicromoduleRelay, SHCLightControl])
def test_supported_output_modes_empty_without_service(cls):
    device = cls.__new__(cls)
    device._switch_config_service = None

    assert device.supported_output_modes == []


def test_twinguard_comfort_zone():
    zone = {"temperature": {"minimum": 18, "maximum": 24}}
    service = _svc(AirQualityLevelService, "AirQualityLevel", {"comfortZone": zone})
    device = SHCTwinguard.__new__(SHCTwinguard)
    device._airqualitylevel_service = service

    assert device.comfort_zone == zone


def test_twinguard_comfort_zone_empty_when_missing():
    service = _svc(AirQualityLevelService, "AirQualityLevel", {})
    device = SHCTwinguard.__new__(SHCTwinguard)
    device._airqualitylevel_service = service

    assert device.comfort_zone == {}
