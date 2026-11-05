"""Domestic hot water service (Bosch app 10.36 model) and RoomClimateControl away flag."""

from boschshcpy import (
    DomesticHotWaterService,
    RoomClimateControlService,
    SHCDomesticHotWater,
)
from boschshcpy.device_helper import SHCDeviceHelper


def _raw_device(model="K40_DHW"):
    return {
        "@type": "device",
        "rootDeviceId": "root",
        "id": "dhw-1",
        "deviceServiceIds": ["DomesticHotWater"],
        "manufacturer": "BOSCH",
        "roomId": "hz_1",
        "deviceModel": model,
        "serial": "FAKE000000",
        "profile": "GENERIC",
        "name": "Hot water",
        "status": "AVAILABLE",
        "childDeviceIds": [],
    }


def _raw_service(state):
    return {
        "@type": "DeviceServiceData",
        "id": "DomesticHotWater",
        "deviceId": "dhw-1",
        "path": "/devices/dhw-1/services/DomesticHotWater",
        "state": {"@type": "domesticHotWaterState", **state},
    }


def test_unknown_model_with_service_becomes_dhw_device():
    helper = SHCDeviceHelper(api=None)
    state = {
        "operationMode": "AUTOMATIC",
        "currentTemperatureLevel": "ECO",
        "tankTemperature": 48.5,
        "chargeRemainingTime": 30,
        "chargeDuration": {"value": 60.0, "unitOfMeasure": "MINUTES"},
    }
    device = helper.device_init(_raw_device(), [_raw_service(state)])
    assert isinstance(device, SHCDomesticHotWater)
    assert helper.domestic_hot_water == [device]
    assert device.operation_mode == DomesticHotWaterService.OperationMode.AUTOMATIC
    assert (
        device.current_temperature_level == DomesticHotWaterService.TemperatureLevel.ECO
    )
    assert device.tank_temperature == 48.5
    assert device.charge_remaining_time == 30
    assert device.charge_duration == 60.0


def test_missing_and_unknown_values_are_tolerated():
    helper = SHCDeviceHelper(api=None)
    state = {"operationMode": "SOMETHING_NEW", "currentTemperatureLevel": "X"}
    device = helper.device_init(_raw_device(), [_raw_service(state)])
    assert device.operation_mode == DomesticHotWaterService.OperationMode.UNKNOWN
    assert (
        device.current_temperature_level
        == DomesticHotWaterService.TemperatureLevel.UNKNOWN
    )
    assert device.tank_temperature is None
    assert device.charge_remaining_time is None
    assert device.charge_duration is None


def test_unknown_model_without_service_stays_generic():
    helper = SHCDeviceHelper(api=None)
    raw = _raw_device("SOMETHING_ELSE")
    raw["deviceServiceIds"] = []
    device = helper.device_init(raw, [])
    assert not isinstance(device, SHCDomesticHotWater)
    assert helper.domestic_hot_water == []


def test_room_climate_away_flag():
    svc = RoomClimateControlService.__new__(RoomClimateControlService)
    svc._raw_device_service = {"state": {"away": True}}
    svc._raw_state = {"away": True}
    assert svc.away is True
    svc._raw_state = {}
    assert svc.away is False


def test_wrong_typed_values_return_none():
    helper = SHCDeviceHelper(api=None)
    state = {
        "tankTemperature": "n/a",
        "chargeRemainingTime": "soon",
        "chargeDuration": 5,
    }
    device = helper.device_init(_raw_device(), [_raw_service(state)])
    assert device.tank_temperature is None
    assert device.charge_remaining_time is None
    assert device.charge_duration is None
