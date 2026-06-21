"""Tests for boschshcpy 0.2.127 additions and unknown-enum coverage.

Items covered:
  8. Unknown-enum ValueError raise-path tests for services lacking them.
  9. MD2 write-path setter tests (SHCMotionDetector2).
 10. comfortZone property + PowerSwitchProgram setter.

Run:
    PYTHONPATH=/tmp/lib-0127 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
        python3 -m pytest tests/test_services_impl_0127.py -q -o addopts=
"""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

from boschshcpy.services_impl import (
    AlarmService,
    AirQualityLevelService,
    BlindsControlService,
    HeatingCircuitService,
    KeypadService,
    PowerSwitchService,
    PowerSwitchProgramService,
    RoomClimateControlService,
    RoutingService,
    ShutterContactService,
    SilentModeService,
    SurveillanceAlarmService,
    WaterLeakageSensorService,
    WaterLeakageSensorTiltService,
)


# ---------------------------------------------------------------------------
# Helper — mirrors test_services_impl.py _make_svc
# ---------------------------------------------------------------------------

def _make_svc(cls, state_dict, faults=None):
    svc = cls.__new__(cls)
    raw = {
        "id": cls.__name__,
        "deviceId": "test-device",
        "path": "/test",
        "state": {"@type": "testType", **state_dict},
    }
    if faults is not None:
        raw["faults"] = faults
    svc._api = MagicMock()
    svc._raw_device_service = raw
    svc._raw_state = raw["state"]
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


def _mock_api():
    calls = []
    api = SimpleNamespace(
        put_device_service_state=lambda dev, svc, body: calls.append((dev, svc, body)),
    )
    return api, calls


def _make_svc_with_api(cls, state_dict):
    svc = cls.__new__(cls)
    raw = {
        "id": cls.__name__,
        "deviceId": "test-device",
        "path": "/test",
        "state": {"@type": "testType", **state_dict},
    }
    api, calls = _mock_api()
    svc._api = api
    svc._raw_device_service = raw
    svc._raw_state = raw["state"]
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc, calls


# ===========================================================================
# 8. Unknown-enum ValueError raise-path tests
# ===========================================================================

class TestAlarmServiceUnknownEnum:
    def test_alarm_unknown_raises_value_error(self):
        svc = _make_svc(AlarmService, {"value": "UNKNOWN_STATE_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.value


class TestSilentModeServiceUnknownEnum:
    def test_silent_mode_unknown_raises_value_error(self):
        svc = _make_svc(SilentModeService, {"mode": "UNKNOWN_MODE_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.mode


class TestShutterContactServiceUnknownEnum:
    def test_shutter_contact_unknown_raises_value_error(self):
        svc = _make_svc(ShutterContactService, {"value": "UNKNOWN_STATE_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.value


class TestPowerSwitchServiceUnknownEnum:
    def test_power_switch_unknown_raises_value_error(self):
        svc = _make_svc(
            PowerSwitchService,
            {"switchState": "UNKNOWN_XYZ", "automaticPowerOffTime": 0},
        )
        with pytest.raises(ValueError):
            _ = svc.value


class TestRoutingServiceUnknownEnum:
    def test_routing_unknown_raises_value_error(self):
        svc = _make_svc(RoutingService, {"value": "UNKNOWN_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.value


class TestRoomClimateControlOperationModeUnknownEnum:
    def test_rcc_operation_mode_unknown_raises_value_error(self):
        svc = _make_svc(
            RoomClimateControlService,
            {"operationMode": "UNKNOWN_XYZ", "setpointTemperature": 21.0},
        )
        with pytest.raises(ValueError):
            _ = svc.operation_mode


class TestKeypadServiceKeyNameUnknownEnum:
    def test_keypad_key_name_unknown_raises_value_error(self):
        svc = _make_svc(KeypadService, {"keyName": "TOTALLY_UNKNOWN_BUTTON"})
        with pytest.raises(ValueError):
            _ = svc.keyName

    def test_keypad_event_type_unknown_raises_value_error(self):
        svc = _make_svc(KeypadService, {"eventType": "TOTALLY_UNKNOWN_EVENT"})
        with pytest.raises(ValueError):
            _ = svc.eventType


class TestSurveillanceAlarmServiceUnknownEnum:
    def test_surveillance_alarm_unknown_raises_value_error(self):
        svc = _make_svc(SurveillanceAlarmService, {"value": "UNKNOWN_STATE_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.value


class TestAirQualityLevelServiceCombinedRatingUnknownEnum:
    _AQ_BASE = {
        "combinedRating": "GOOD",
        "description": "OK",
        "temperature": 22,
        "temperatureRating": "GOOD",
        "humidity": 55,
        "humidityRating": "GOOD",
        "purity": 800,
        "purityRating": "GOOD",
    }

    def test_combined_rating_unknown_raises_value_error(self):
        svc = _make_svc(AirQualityLevelService,
                        {**self._AQ_BASE, "combinedRating": "UNKNOWN_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.combinedRating


class TestBlindsControlServiceBlindsType:
    def test_blinds_type_degree_90_valid(self):
        svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 0.0,
                                               "blindsType": "DEGREE_90"})
        assert svc.blinds_type == BlindsControlService.BlindsType.DEGREE_90

    def test_blinds_type_degree_180_valid(self):
        svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 0.0,
                                               "blindsType": "DEGREE_180"})
        assert svc.blinds_type == BlindsControlService.BlindsType.DEGREE_180

    def test_blinds_type_absent_returns_none(self):
        svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 0.0})
        assert svc.blinds_type is None

    def test_blinds_type_unknown_raises_value_error(self):
        svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 0.0,
                                               "blindsType": "UNKNOWN_TYPE_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.blinds_type


class TestWaterLeakageSensorServiceUnknownEnum:
    def test_water_leakage_unknown_raises_value_error(self):
        svc = _make_svc(WaterLeakageSensorService, {"state": "UNKNOWN_STATE_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.value


class TestWaterLeakageSensorTiltServiceUnknownEnum:
    def test_push_notification_unknown_raises_value_error(self):
        svc = _make_svc(WaterLeakageSensorTiltService,
                        {"pushNotificationState": "UNKNOWN_XYZ",
                         "acousticSignalState": "ENABLED"})
        with pytest.raises(ValueError):
            _ = svc.pushNotificationState

    def test_acoustic_signal_unknown_raises_value_error(self):
        svc = _make_svc(WaterLeakageSensorTiltService,
                        {"pushNotificationState": "ENABLED",
                         "acousticSignalState": "UNKNOWN_XYZ"})
        with pytest.raises(ValueError):
            _ = svc.acousticSignalState


# ===========================================================================
# 9. MD2 write-path setter tests
# ===========================================================================

class TestMD2Setters:
    """Test SHCMotionDetector2 setter paths via direct service put_state_element."""

    def _make_md2(self):
        from boschshcpy.models_impl import SHCMotionDetector2
        from boschshcpy.services_impl import (
            MultiLevelSwitchService,
            BinarySwitchService,
            PetImmunityService,
            PirSensorConfigurationService,
            LatestMotionService,
            MultiLevelSensorService,
            DetectionTestService,
            LatestTamperService,
            TemperatureLevelService,
            PollControlService,
            OccupancyDetectionService,
            CommunicationQualityService,
        )

        api, calls = _mock_api()

        mls = _make_svc(MultiLevelSwitchService, {"level": 50})
        mls._api = api
        bs = _make_svc(BinarySwitchService, {"on": False})
        bs._api = api
        pi = _make_svc(PetImmunityService, {"enabled": False})
        pi._api = api
        pir = _make_svc(PirSensorConfigurationService, {"motionSensitivity": "HIGH"})
        pir._api = api

        # Stub services not under test
        lm = _make_svc(LatestMotionService, {"latestMotionDetected": "n/a"})
        mls_sensor = _make_svc(MultiLevelSensorService, {"illuminance": 0})
        dt = _make_svc(DetectionTestService,
                       {"detectionState": "DETECTION_TEST_STOPPED"})
        lt = _make_svc(LatestTamperService,
                       {"tamperProtectionEnabled": False, "wasTampered": False})
        tl = _make_svc(TemperatureLevelService, {"temperature": 20.0})
        pc = _make_svc(PollControlService, {"longPollInterval": "LONG"})
        od = _make_svc(OccupancyDetectionService, {"isOccupied": False})
        cq = _make_svc(CommunicationQualityService, {"quality": "GOOD"})

        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._raw_device = {
            "id": "md2-1", "rootDeviceId": "root-1", "manufacturer": "BOSCH",
            "roomId": "room-1", "deviceModel": "MD2", "serial": "SER-MD2",
            "profile": "MD2", "name": "MD2 Device", "status": "AVAILABLE",
            "deviceServiceIds": [],
        }
        obj._callbacks = {}
        obj._api = api
        obj._multi_level_switch_service = mls
        obj._binaryswitch_service = bs
        obj._petimmunity_service = pi
        obj._pirsensorconfiguration_service = pir
        obj._latestmotion_service = lm
        obj._multi_level_sensor_service = mls_sensor
        obj._detectiontest_service = dt
        obj._latesttamper_service = lt
        obj._temperaturelevel_service = tl
        obj._pollcontrol_service = pc
        obj._occupancydetection_service = od
        obj._communicationquality_service = cq
        obj._batterylevel_service = None
        return obj, calls

    def test_multi_level_switch_setter(self):
        obj, calls = self._make_md2()
        obj.multi_level_switch = 75
        assert any(c[2].get("level") == 75 for c in calls), \
            f"Expected level=75 in calls, got {calls}"

    def test_binaryswitch_setter_true(self):
        obj, calls = self._make_md2()
        obj.binaryswitch = True
        assert any(c[2].get("on") is True for c in calls), \
            f"Expected on=True in calls, got {calls}"

    def test_binaryswitch_setter_false(self):
        obj, calls = self._make_md2()
        obj.binaryswitch = False
        assert any(c[2].get("on") is False for c in calls), \
            f"Expected on=False in calls, got {calls}"

    def test_pet_immunity_enabled_setter_true(self):
        obj, calls = self._make_md2()
        obj.pet_immunity_enabled = True
        assert any(c[2].get("enabled") is True for c in calls), \
            f"Expected enabled=True in calls, got {calls}"

    def test_pet_immunity_enabled_setter_false(self):
        obj, calls = self._make_md2()
        obj.pet_immunity_enabled = False
        assert any(c[2].get("enabled") is False for c in calls), \
            f"Expected enabled=False in calls, got {calls}"

    def test_motion_sensitivity_setter(self):
        from boschshcpy.services_impl import PirSensorConfigurationService
        obj, calls = self._make_md2()
        obj.motion_sensitivity = PirSensorConfigurationService.MotionSensitivity.LOW
        assert any(c[2].get("motionSensitivity") == "LOW" for c in calls), \
            f"Expected motionSensitivity=LOW in calls, got {calls}"


# ===========================================================================
# 10. comfortZone property + PowerSwitchProgram setter
# ===========================================================================

class TestAirQualityComfortZone:
    _AQ_BASE = {
        "combinedRating": "GOOD",
        "description": "OK",
        "temperature": 22,
        "temperatureRating": "GOOD",
        "humidity": 55,
        "humidityRating": "GOOD",
        "purity": 800,
        "purityRating": "GOOD",
    }

    def test_comfort_zone_present(self):
        zone = {"minTemperature": 19, "maxTemperature": 24}
        svc = _make_svc(AirQualityLevelService,
                        {**self._AQ_BASE, "comfortZone": zone})
        assert svc.comfortZone == zone

    def test_comfort_zone_absent_returns_empty_dict(self):
        svc = _make_svc(AirQualityLevelService, self._AQ_BASE)
        assert svc.comfortZone == {}


class TestPowerSwitchProgramSetter:
    def test_setter_manual(self):
        svc, calls = _make_svc_with_api(PowerSwitchProgramService,
                                        {"operationMode": "AUTOMATIC"})
        svc.value = PowerSwitchProgramService.State.MANUAL
        assert any(c[2].get("operationMode") == "MANUAL" for c in calls), \
            f"Expected operationMode=MANUAL in calls, got {calls}"

    def test_setter_automatic(self):
        svc, calls = _make_svc_with_api(PowerSwitchProgramService,
                                        {"operationMode": "MANUAL"})
        svc.value = PowerSwitchProgramService.State.AUTOMATIC
        assert any(c[2].get("operationMode") == "AUTOMATIC" for c in calls), \
            f"Expected operationMode=AUTOMATIC in calls, got {calls}"

    def test_setter_returns_correct_state_after_update(self):
        """Getter round-trip: after updating state dict, getter returns new value."""
        svc = _make_svc(PowerSwitchProgramService, {"operationMode": "MANUAL"})
        svc._raw_state["operationMode"] = "AUTOMATIC"
        assert svc.value == PowerSwitchProgramService.State.AUTOMATIC


# ===========================================================================
# Robustness: RoomClimateControlService optional fields with safe defaults
# ===========================================================================

class TestRoomClimateControlOptionalFields:
    def test_ventilation_mode_absent_defaults_false(self):
        svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
        assert svc.ventilation_mode is False

    def test_low_absent_defaults_false(self):
        svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
        assert svc.low is False

    def test_boost_mode_absent_defaults_false(self):
        svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
        assert svc.boost_mode is False

    def test_summer_mode_absent_defaults_false(self):
        svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
        assert svc.summer_mode is False


# ===========================================================================
# Robustness: PowerSwitchService.powerofftime absent → 0
# ===========================================================================

class TestPowerSwitchPowerofftimeAbsent:
    def test_powerofftime_absent_returns_zero(self):
        svc = _make_svc(PowerSwitchService, {"switchState": "ON"})
        assert svc.powerofftime == 0


# ===========================================================================
# Robustness: HeatingCircuitService optional fields
# ===========================================================================

class TestHeatingCircuitOptionalFields:
    _HC_BASE = {"operationMode": "AUTOMATIC", "setpointTemperature": 20.0}

    def test_temperature_override_mode_active_absent(self):
        svc = _make_svc(HeatingCircuitService, self._HC_BASE)
        assert svc.temperature_override_mode_active is False

    def test_temperature_override_feature_enabled_absent(self):
        svc = _make_svc(HeatingCircuitService, self._HC_BASE)
        assert svc.temperature_override_feature_enabled is False

    def test_energy_saving_feature_enabled_absent(self):
        svc = _make_svc(HeatingCircuitService, self._HC_BASE)
        assert svc.energy_saving_feature_enabled is False

    def test_on_absent_defaults_false(self):
        svc = _make_svc(HeatingCircuitService, self._HC_BASE)
        assert svc.on is False
