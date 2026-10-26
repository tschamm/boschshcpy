"""Sync twins of the async-only writes (needed by sync consumers such as ha-core)."""

from unittest.mock import MagicMock

from boschshcpy.information import SHCInformation
from boschshcpy.models_impl import (
    SHCClimateControl,
    SHCOutdoorSiren,
    SHCShutterControl,
    SHCSmartPlug,
)
from boschshcpy.services_impl import (
    DimmerConfigurationService,
    OutdoorSirenService,
    PowerMeterService,
    ShutterControlService,
)


def _make_svc(cls, state):
    svc = cls.__new__(cls)
    svc._api = MagicMock()
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


def _operation(svc):
    call = svc._api.post_device_service_operation.call_args
    return call.args[2], call.args[3]


def test_reset_energy_summation_posts_empty_array():
    svc = _make_svc(PowerMeterService, {})
    svc.reset_energy_summation()
    assert _operation(svc) == ("resetEnergySummation", [])


def test_shutter_reset_calibration_and_open_posts_empty_array():
    svc = _make_svc(ShutterControlService, {"calibrated": True})
    svc.reset_calibration_and_open()
    assert _operation(svc) == ("resetCalibrationAndOpen", [])
    svc._api.put_device_service_state.assert_not_called()


def test_shutter_calibrate_puts_calibrating():
    svc = _make_svc(ShutterControlService, {"operationState": "STOPPED"})
    svc.calibrate()
    call = svc._api.put_device_service_state.call_args
    assert call.args[2]["operationState"] == "CALIBRATING"
    svc._api.post_device_service_operation.assert_not_called()


def test_siren_test_alarm_uses_given_or_configured_level():
    svc = _make_svc(OutdoorSirenService, {"outdoorSirenConfiguration": {"soundLevel": "MEDIUM"}})
    svc.trigger_test_alarm()
    assert _operation(svc) == ("triggerTestAlarm", ["MEDIUM"])
    svc.trigger_test_alarm(OutdoorSirenService.SoundLevel.HIGH)
    assert _operation(svc) == ("triggerTestAlarm", ["HIGH"])


def test_dimmer_preview_operations():
    svc = _make_svc(DimmerConfigurationService, {})
    svc.preview_max_brightness()
    assert _operation(svc)[0] == "previewMaxBrightness"
    svc.preview_min_brightness()
    assert _operation(svc)[0] == "previewMinBrightness"


def test_device_delegations():
    plug = SHCSmartPlug.__new__(SHCSmartPlug)
    plug._powermeter_service = MagicMock()
    plug.reset_energy_summation()
    plug._powermeter_service.reset_energy_summation.assert_called_once_with()

    shutter = SHCShutterControl.__new__(SHCShutterControl)
    shutter._service = MagicMock()
    shutter.reset_calibration_and_open()
    shutter.calibrate()
    shutter._service.reset_calibration_and_open.assert_called_once_with()
    shutter._service.calibrate.assert_called_once_with()

    siren = SHCOutdoorSiren.__new__(SHCOutdoorSiren)
    siren._siren_service = MagicMock()
    siren.trigger_test_alarm(OutdoorSirenService.SoundLevel.LOW)
    siren._siren_service.trigger_test_alarm.assert_called_once_with(
        OutdoorSirenService.SoundLevel.LOW
    )


def test_climate_set_hvac_control_mode_puts_room_endpoint():
    climate = SHCClimateControl.__new__(SHCClimateControl)
    climate._api = MagicMock()
    climate._raw_device = {"id": "hdm:room:1"}
    climate.set_hvac_control_mode("OFF")
    climate._api.put_domain_action.assert_called_once_with(
        "roomclimatecontrol/roomControlMode", {climate.id: "OFF"}
    )


def test_information_refresh_replaces_public_info():
    info = SHCInformation.__new__(SHCInformation)
    info._api = MagicMock()
    info._pub_info = {"softwareUpdateState": {"swInstalledVersion": "1"}}
    info._api.get_public_information.return_value = {
        "softwareUpdateState": {"swInstalledVersion": "2"}
    }
    info.refresh()
    assert info.version == "2"
    info._api.get_public_information.return_value = None
    info.refresh()
    assert info.version == "2"
