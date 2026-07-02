"""Isolation-safe tests for boschshcpy/services_impl.py.

No HA harness, no network. All services built via __new__ + injected fake state.
"""

import pytest
from unittest.mock import MagicMock, call

from boschshcpy.services_impl import (
    # Part 1 — temperature / climate / shutter / camera
    TemperatureOffsetService,
    TemperatureLevelService,
    HumidityLevelService,
    RoomClimateControlService,
    HeatingCircuitService,
    SilentModeService,
    ShutterContactService,
    BypassService,
    ShutterControlService,
    BlindsControlService,
    BlindsSceneControlService,
    CameraLightService,
    CameraAmbientLightService,
    CameraFrontLightService,
    PrivacyModeService,
    CameraNotificationService,
    # Part 2 — power / sensors / alarm / battery / keypad etc.
    VibrationSensorService,
    ValveTappetService,
    PowerSwitchService,
    PowerMeterService,
    RoutingService,
    PowerSwitchProgramService,
    BinarySwitchService,
    MultiLevelSwitchService,
    MultiLevelSensorService,
    HueColorTemperatureService,
    HSBColorActuatorService,
    SmokeDetectorCheckService,
    AlarmService,
    BatteryLevelService,
    ThermostatService,
    CommunicationQualityService,
    WaterLeakageSensorService,
    WaterLeakageSensorTiltService,
    WaterLeakageSensorCheckService,
    PresenceSimulationConfigurationService,
    ImpulseSwitchService,
    ChildProtectionService,
    KeypadService,
    LatestMotionService,
    DetectionTestService,
    LatestTamperService,
    PollControlService,
    PirSensorConfigurationService,
    OccupancyDetectionService,
    PetImmunityService,
    AirQualityLevelService,
    SurveillanceAlarmService,
    SERVICE_MAPPING,
    build,
)


# ---------------------------------------------------------------------------
# helper
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


# ===========================================================================
# PART 1 — TemperatureOffsetService
# ===========================================================================

def test_temperature_offset_reads_offset():
    svc = _make_svc(TemperatureOffsetService, {"offset": 1.5})
    assert svc.offset == 1.5


def test_temperature_offset_default_zero():
    svc = _make_svc(TemperatureOffsetService, {})
    assert svc.offset == 0.0


def test_temperature_step_size():
    svc = _make_svc(TemperatureOffsetService, {"stepSize": 0.5})
    assert svc.step_size == 0.5


def test_temperature_min_offset():
    svc = _make_svc(TemperatureOffsetService, {"minOffset": -5.0})
    assert svc.min_offset == -5.0


def test_temperature_max_offset():
    svc = _make_svc(TemperatureOffsetService, {"maxOffset": 5.0})
    assert svc.max_offset == 5.0


def test_temperature_offset_setter():
    svc = _make_svc(TemperatureOffsetService, {"offset": 0.0})
    svc.offset = 2.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "TemperatureOffsetService", {"@type": "testType", "offset": 2.0}
    )


# ===========================================================================
# TemperatureLevelService
# ===========================================================================

def test_temperature_level_reads():
    svc = _make_svc(TemperatureLevelService, {"temperature": 21.5})
    assert svc.temperature == 21.5


def test_temperature_level_default():
    svc = _make_svc(TemperatureLevelService, {})
    assert svc.temperature == 0.0


# ===========================================================================
# HumidityLevelService
# ===========================================================================

def test_humidity_reads():
    svc = _make_svc(HumidityLevelService, {"humidity": 55.0})
    assert svc.humidity == 55.0


def test_humidity_default():
    svc = _make_svc(HumidityLevelService, {})
    assert svc.humidity == 0.0


# ===========================================================================
# RoomClimateControlService
# ===========================================================================

def test_rcc_operation_mode_automatic():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "AUTOMATIC"})
    assert svc.operation_mode == RoomClimateControlService.OperationMode.AUTOMATIC


def test_rcc_operation_mode_manual():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
    assert svc.operation_mode == RoomClimateControlService.OperationMode.MANUAL


def test_rcc_setpoint_temperature():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "setpointTemperature": 20.5})
    assert svc.setpoint_temperature == 20.5


def test_rcc_setpoint_temperature_setter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "setpointTemperature": 20.0})
    svc.setpoint_temperature = 22.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "setpointTemperature": 22.0}
    )


def test_rcc_setpoint_eco():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "AUTOMATIC", "setpointTemperatureForLevelEco": 16.0})
    assert svc.setpoint_temperature_eco == 16.0


def test_rcc_setpoint_comfort():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "AUTOMATIC", "setpointTemperatureForLevelComfort": 22.0})
    assert svc.setpoint_temperature_comfort == 22.0


def test_rcc_ventilation_mode():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "ventilationMode": True})
    assert svc.ventilation_mode is True


def test_rcc_low_getter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "low": False})
    assert svc.low is False


def test_rcc_low_setter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "low": False})
    svc.low = True
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "low": True}
    )


def test_rcc_boost_mode_getter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "boostMode": True})
    assert svc.boost_mode is True


def test_rcc_boost_mode_setter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "boostMode": False})
    svc.boost_mode = True
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "boostMode": True}
    )


def test_rcc_summer_mode_getter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "summerMode": True})
    assert svc.summer_mode is True


def test_rcc_summer_mode_setter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "summerMode": True})
    svc.summer_mode = False
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "summerMode": False}
    )


def test_rcc_room_control_mode_default():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
    assert svc.room_control_mode == "HEATING"


def test_rcc_room_control_mode_setter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "HEATING"})
    svc.room_control_mode = "COOLING"
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "roomControlMode": "COOLING"}
    )


def test_rcc_cooling_mode_true():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "COOLING"})
    assert svc.cooling_mode is True


def test_rcc_cooling_mode_false():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "HEATING"})
    assert svc.cooling_mode is False


def test_rcc_cooling_mode_setter_true():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "HEATING"})
    svc.cooling_mode = True
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "roomControlMode": "COOLING"}
    )


def test_rcc_cooling_mode_setter_false():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "COOLING"})
    svc.cooling_mode = False
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "roomControlMode": "HEATING"}
    )


def test_rcc_supports_cooling_true_when_cooling():
    # roomControlMode present with value COOLING → cooling capable.
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "COOLING"})
    assert svc.supports_cooling is True


def test_rcc_supports_cooling_true_when_heating():
    # Regression for #67: roomControlMode present with value HEATING must still
    # report supports_cooling=True so HA keeps HVACMode.COOL available and the
    # user can re-enable cooling from HA after turning it off.
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "HEATING"})
    assert svc.supports_cooling is True


def test_rcc_supports_cooling_true_when_off():
    # roomControlMode present with value OFF → field is present → cooling capable.
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "roomControlMode": "OFF"})
    assert svc.supports_cooling is True


def test_rcc_supports_cooling_false_when_absent():
    # roomControlMode absent → heating-only room (classic TRV/radiator thermostat).
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
    assert svc.supports_cooling is False


def test_rcc_supports_low_present():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "low": False})
    assert svc.supports_low is True


def test_rcc_supports_low_absent():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
    assert svc.supports_low is False


def test_rcc_supports_boost_mode():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "supportsBoostMode": True})
    assert svc.supports_boost_mode is True


def test_rcc_show_setpoint_temperature_present():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL", "showSetpointTemperature": True})
    assert svc.show_setpoint_temperature is True


def test_rcc_show_setpoint_temperature_absent():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
    assert svc.show_setpoint_temperature is False


# ===========================================================================
# HeatingCircuitService
# ===========================================================================

def test_hcs_operation_mode_automatic():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "AUTOMATIC"})
    assert svc.operation_mode == HeatingCircuitService.OperationMode.AUTOMATIC


def test_hcs_operation_mode_manual():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL"})
    assert svc.operation_mode == HeatingCircuitService.OperationMode.MANUAL


def test_hcs_setpoint_temperature_getter():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "setpointTemperature": 19.5})
    assert svc.setpoint_temperature == 19.5


def test_hcs_setpoint_temperature_setter():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "setpointTemperature": 19.5})
    svc.setpoint_temperature = 21.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "HeatingCircuitService", {"@type": "testType", "setpointTemperature": 21.0}
    )


def test_hcs_setpoint_eco_getter():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "setpointTemperatureForLevelEco": 15.0})
    assert svc.setpoint_temperature_eco == 15.0


def test_hcs_setpoint_eco_setter():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "setpointTemperatureForLevelEco": 15.0})
    svc.setpoint_temperature_eco = 14.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "HeatingCircuitService", {"@type": "testType", "setpointTemperatureForLevelEco": 14.0}
    )


def test_hcs_setpoint_comfort_getter():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "setpointTemperatureForLevelComfort": 23.0})
    assert svc.setpoint_temperature_comfort == 23.0


def test_hcs_setpoint_comfort_setter():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "setpointTemperatureForLevelComfort": 23.0})
    svc.setpoint_temperature_comfort = 24.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "HeatingCircuitService", {"@type": "testType", "setpointTemperatureForLevelComfort": 24.0}
    )


def test_hcs_temperature_override_mode_active():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "temperatureOverrideModeActive": True})
    assert svc.temperature_override_mode_active is True


def test_hcs_temperature_override_feature_enabled():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "temperatureOverrideFeatureEnabled": False})
    assert svc.temperature_override_feature_enabled is False


def test_hcs_energy_saving_feature_enabled():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "energySavingFeatureEnabled": True})
    assert svc.energy_saving_feature_enabled is True


def test_hcs_on():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL", "on": True})
    assert svc.on is True


# ===========================================================================
# SilentModeService
# ===========================================================================

def test_silent_mode_silent():
    svc = _make_svc(SilentModeService, {"mode": "MODE_SILENT"})
    assert svc.mode == SilentModeService.State.MODE_SILENT


def test_silent_mode_normal():
    svc = _make_svc(SilentModeService, {"mode": "MODE_NORMAL"})
    assert svc.mode == SilentModeService.State.MODE_NORMAL


# ===========================================================================
# ShutterContactService
# ===========================================================================

def test_shutter_contact_closed():
    svc = _make_svc(ShutterContactService, {"value": "CLOSED"})
    assert svc.value == ShutterContactService.State.CLOSED


def test_shutter_contact_open():
    svc = _make_svc(ShutterContactService, {"value": "OPEN"})
    assert svc.value == ShutterContactService.State.OPEN


# ===========================================================================
# BypassService
# ===========================================================================

def test_bypass_inactive():
    svc = _make_svc(BypassService, {"state": "BYPASS_INACTIVE"})
    assert svc.value == BypassService.State.BYPASS_INACTIVE


def test_bypass_active():
    svc = _make_svc(BypassService, {"state": "BYPASS_ACTIVE"})
    assert svc.value == BypassService.State.BYPASS_ACTIVE


def test_bypass_unknown():
    svc = _make_svc(BypassService, {"state": "UNKNOWN"})
    assert svc.value == BypassService.State.UNKNOWN


# ===========================================================================
# ShutterControlService
# ===========================================================================

def test_shutter_operation_state_stopped():
    svc = _make_svc(ShutterControlService, {"operationState": "STOPPED", "calibrated": True})
    assert svc.operation_state == ShutterControlService.State.STOPPED


def test_shutter_operation_state_moving():
    svc = _make_svc(ShutterControlService, {"operationState": "MOVING", "calibrated": True})
    assert svc.operation_state == ShutterControlService.State.MOVING


def test_shutter_operation_state_calibrating():
    svc = _make_svc(ShutterControlService, {"operationState": "CALIBRATING", "calibrated": False})
    assert svc.operation_state == ShutterControlService.State.CALIBRATING


def test_shutter_operation_state_opening():
    svc = _make_svc(ShutterControlService, {"operationState": "OPENING", "calibrated": True})
    assert svc.operation_state == ShutterControlService.State.OPENING


def test_shutter_operation_state_closing():
    svc = _make_svc(ShutterControlService, {"operationState": "CLOSING", "calibrated": True})
    assert svc.operation_state == ShutterControlService.State.CLOSING


def test_shutter_calibrated():
    svc = _make_svc(ShutterControlService, {"operationState": "STOPPED", "calibrated": True})
    assert svc.calibrated is True


def test_shutter_level_present():
    svc = _make_svc(ShutterControlService, {"operationState": "STOPPED", "calibrated": True, "level": 0.75})
    assert svc.level == 0.75


def test_shutter_level_absent_default():
    svc = _make_svc(ShutterControlService, {"operationState": "STOPPED", "calibrated": True})
    assert svc.level == 0.0


# ===========================================================================
# BlindsControlService
# ===========================================================================

def test_blinds_current_angle():
    svc = _make_svc(BlindsControlService, {"currentAngle": 45.0, "targetAngle": 0.0})
    assert svc.current_angle == 45.0


def test_blinds_target_angle_getter():
    svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 90.0})
    assert svc.target_angle == 90.0


def test_blinds_target_angle_setter():
    svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 0.0})
    svc.target_angle = 45.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "BlindsControlService", {"@type": "testType", "targetAngle": 45.0}
    )


def test_blinds_type():
    svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 0.0, "blindsType": "DEGREE_90"})
    assert svc.blinds_type == BlindsControlService.BlindsType.DEGREE_90


# ===========================================================================
# BlindsSceneControlService
# ===========================================================================

def test_blinds_scene_level_getter():
    svc = _make_svc(BlindsSceneControlService, {"level": 0.5, "angle": 0.0})
    assert svc.level == 0.5


def test_blinds_scene_level_setter():
    svc = _make_svc(BlindsSceneControlService, {"level": 0.5, "angle": 0.0})
    svc.level = 1.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device",
        "BlindsSceneControlService",
        {"@type": "testType", "level": 1.0, "angle": 0.0},
    )


def test_blinds_scene_angle_getter():
    svc = _make_svc(BlindsSceneControlService, {"level": 0.0, "angle": 30.0})
    assert svc.angle == 30.0


def test_blinds_scene_angle_setter():
    svc = _make_svc(BlindsSceneControlService, {"level": 0.0, "angle": 0.0})
    svc.angle = 60.0
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device",
        "BlindsSceneControlService",
        {"@type": "testType", "angle": 60.0, "level": 0.0},
    )


# ===========================================================================
# CameraLightService
# ===========================================================================

def test_camera_light_on():
    svc = _make_svc(CameraLightService, {"value": "ON"})
    assert svc.value == CameraLightService.State.ON


def test_camera_light_off():
    svc = _make_svc(CameraLightService, {"value": "OFF"})
    assert svc.value == CameraLightService.State.OFF


def test_camera_light_none():
    svc = _make_svc(CameraLightService, {"value": "NONE"})
    assert svc.value == CameraLightService.State.NONE


def test_camera_light_value_absent_defaults_none():
    svc = _make_svc(CameraLightService, {})
    assert svc.value == CameraLightService.State.NONE


def test_camera_ambient_light_inherits_value():
    svc = _make_svc(CameraAmbientLightService, {"value": "ON"})
    assert svc.value == CameraAmbientLightService.State.ON


def test_camera_front_light_inherits_value():
    svc = _make_svc(CameraFrontLightService, {"value": "OFF"})
    assert svc.value == CameraFrontLightService.State.OFF


# ===========================================================================
# PrivacyModeService
# ===========================================================================

def test_privacy_mode_enabled():
    svc = _make_svc(PrivacyModeService, {"value": "ENABLED"})
    assert svc.value == PrivacyModeService.State.ENABLED


def test_privacy_mode_disabled():
    svc = _make_svc(PrivacyModeService, {"value": "DISABLED"})
    assert svc.value == PrivacyModeService.State.DISABLED


def test_privacy_mode_absent_defaults_disabled():
    svc = _make_svc(PrivacyModeService, {})
    assert svc.value == PrivacyModeService.State.DISABLED


# ===========================================================================
# CameraNotificationService
# ===========================================================================

def test_camera_notification_enabled():
    svc = _make_svc(CameraNotificationService, {"value": "ENABLED"})
    assert svc.value == CameraNotificationService.State.ENABLED


def test_camera_notification_disabled():
    svc = _make_svc(CameraNotificationService, {"value": "DISABLED"})
    assert svc.value == CameraNotificationService.State.DISABLED


def test_camera_notification_absent_defaults_disabled():
    svc = _make_svc(CameraNotificationService, {})
    assert svc.value == CameraNotificationService.State.DISABLED


# ===========================================================================
# 1. VibrationSensorService
# ===========================================================================


def test_vibration_no_vibration():
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "HIGH"})
    assert svc.value == VibrationSensorService.State.NO_VIBRATION


def test_vibration_detected():
    svc = _make_svc(VibrationSensorService, {"value": "VIBRATION_DETECTED", "enabled": True, "sensitivity": "HIGH"})
    assert svc.value == VibrationSensorService.State.VIBRATION_DETECTED


def test_vibration_unknown():
    svc = _make_svc(VibrationSensorService, {"value": "UNKNOWN", "enabled": True, "sensitivity": "MEDIUM"})
    assert svc.value == VibrationSensorService.State.UNKNOWN


def test_vibration_enabled():
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "LOW"})
    assert svc.enabled is True


def test_vibration_sensitivity_very_high():
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "VERY_HIGH"})
    assert svc.sensitivity == VibrationSensorService.SensitivityState.VERY_HIGH


def test_vibration_sensitivity_high():
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "HIGH"})
    assert svc.sensitivity == VibrationSensorService.SensitivityState.HIGH


def test_vibration_sensitivity_medium():
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "MEDIUM"})
    assert svc.sensitivity == VibrationSensorService.SensitivityState.MEDIUM


def test_vibration_sensitivity_low():
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "LOW"})
    assert svc.sensitivity == VibrationSensorService.SensitivityState.LOW


def test_vibration_sensitivity_very_low():
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "VERY_LOW"})
    assert svc.sensitivity == VibrationSensorService.SensitivityState.VERY_LOW


# ===========================================================================
# 2. ValveTappetService
# ===========================================================================


def test_valve_position():
    svc = _make_svc(ValveTappetService, {"position": 42, "value": "VALVE_ADAPTION_SUCCESSFUL"})
    assert svc.position == 42
    assert isinstance(svc.position, int)


def test_valve_position_is_int_per_apk_model():
    # OpenAPI types Thermostat-II position as generic "number", but the
    # Bosch APK's own ValveTappetState client model declares this field as
    # Integer (unlike sibling TemperatureOffsetState/TemperatureLevelState,
    # which use Double) — so position must stay int, matching the app's
    # ground-truth model rather than the loose OpenAPI typing.
    svc = _make_svc(ValveTappetService, {"position": 42, "value": "VALVE_ADAPTION_SUCCESSFUL"})
    assert svc.position == 42
    assert isinstance(svc.position, int)


def test_valve_state_successful():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "VALVE_ADAPTION_SUCCESSFUL"})
    assert svc.value == ValveTappetService.State.VALVE_ADAPTION_SUCCESSFUL


def test_valve_state_in_progress():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "VALVE_ADAPTION_IN_PROGRESS"})
    assert svc.value == ValveTappetService.State.VALVE_ADAPTION_IN_PROGRESS


def test_valve_state_range_too_big():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "RANGE_TOO_BIG"})
    assert svc.value == ValveTappetService.State.RANGE_TOO_BIG


def test_valve_state_run_to_start():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "RUN_TO_START_POSITION"})
    assert svc.value == ValveTappetService.State.RUN_TO_START_POSITION


def test_valve_state_in_start():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "IN_START_POSITION"})
    assert svc.value == ValveTappetService.State.IN_START_POSITION


def test_valve_state_not_available():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "NOT_AVAILABLE"})
    assert svc.value == ValveTappetService.State.NOT_AVAILABLE


def test_valve_state_no_valve_body_error():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "NO_VALVE_BODY_ERROR"})
    assert svc.value == ValveTappetService.State.NO_VALVE_BODY_ERROR


def test_valve_state_no_motor_error():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "NO_MOTOR_ERROR"})
    assert svc.value == ValveTappetService.State.NO_MOTOR_ERROR


def test_valve_state_valve_too_tight():
    svc = _make_svc(ValveTappetService, {"position": 0, "value": "VALVE_TOO_TIGHT"})
    assert svc.value == ValveTappetService.State.VALVE_TOO_TIGHT


# ===========================================================================
# 3. PowerSwitchService
# ===========================================================================


def test_power_switch_on():
    svc = _make_svc(PowerSwitchService, {"switchState": "ON", "automaticPowerOffTime": 0})
    assert svc.value == PowerSwitchService.State.ON


def test_power_switch_off():
    svc = _make_svc(PowerSwitchService, {"switchState": "OFF", "automaticPowerOffTime": 0})
    assert svc.value == PowerSwitchService.State.OFF


def test_power_switch_powerofftime():
    svc = _make_svc(PowerSwitchService, {"switchState": "ON", "automaticPowerOffTime": 120})
    assert svc.powerofftime == 120


# ===========================================================================
# 4. PowerMeterService
# ===========================================================================


def test_power_consumption():
    svc = _make_svc(PowerMeterService, {"powerConsumption": 1.23, "energyConsumption": 0.0})
    assert svc.powerconsumption == pytest.approx(1.23)


def test_energy_consumption():
    svc = _make_svc(PowerMeterService, {"powerConsumption": 0.0, "energyConsumption": 456.78})
    assert svc.energyconsumption == pytest.approx(456.78)


def test_energy_yield_present():
    # #331: Smart Plug [+M] Mini-PV mode reports energyYield (Wh).
    svc = _make_svc(
        PowerMeterService,
        {"powerConsumption": -800.0, "energyConsumption": 123.0, "energyYield": 234.0},
    )
    assert svc.energyyield == pytest.approx(234.0)


def test_energy_yield_absent_returns_none():
    # Older Zigbee plugs / firmware omit the field → None (not KeyError).
    svc = _make_svc(
        PowerMeterService, {"powerConsumption": 1.0, "energyConsumption": 123.0}
    )
    assert svc.energyyield is None


# ===========================================================================
# 5. RoutingService
# ===========================================================================


def test_routing_enabled():
    svc = _make_svc(RoutingService, {"value": "ENABLED"})
    assert svc.value == RoutingService.State.ENABLED


def test_routing_disabled():
    svc = _make_svc(RoutingService, {"value": "DISABLED"})
    assert svc.value == RoutingService.State.DISABLED


# ===========================================================================
# 6. PowerSwitchProgramService
# ===========================================================================


def test_power_switch_program_manual():
    svc = _make_svc(PowerSwitchProgramService, {"operationMode": "MANUAL"})
    assert svc.value == PowerSwitchProgramService.State.MANUAL


def test_power_switch_program_automatic():
    svc = _make_svc(PowerSwitchProgramService, {"operationMode": "AUTOMATIC"})
    assert svc.value == PowerSwitchProgramService.State.AUTOMATIC


# ===========================================================================
# 7. BinarySwitchService
# ===========================================================================


def test_binary_switch_true():
    svc = _make_svc(BinarySwitchService, {"on": True})
    assert svc.value is True


def test_binary_switch_false():
    svc = _make_svc(BinarySwitchService, {"on": False})
    assert svc.value is False


# ===========================================================================
# 8. MultiLevelSwitchService
# ===========================================================================


def test_multi_level_switch_value():
    svc = _make_svc(MultiLevelSwitchService, {"level": 75})
    assert svc.value == 75


# ===========================================================================
# 9. MultiLevelSensorService
# ===========================================================================


def test_multi_level_sensor_illuminance():
    svc = _make_svc(MultiLevelSensorService, {"illuminance": 512})
    assert svc.illuminance == 512


# ===========================================================================
# 10. HueColorTemperatureService
# ===========================================================================


def test_hue_color_temp_value():
    svc = _make_svc(HueColorTemperatureService, {
        "colorTemperature": 4000,
        "colorTemperatureRange": {"minCt": 2700, "maxCt": 6500},
    })
    assert svc.value == 4000


def test_hue_color_temp_min():
    svc = _make_svc(HueColorTemperatureService, {
        "colorTemperature": 4000,
        "colorTemperatureRange": {"minCt": 2700, "maxCt": 6500},
    })
    assert svc.min_value == 2700


def test_hue_color_temp_max():
    svc = _make_svc(HueColorTemperatureService, {
        "colorTemperature": 4000,
        "colorTemperatureRange": {"minCt": 2700, "maxCt": 6500},
    })
    assert svc.max_value == 6500


# ===========================================================================
# 11. HSBColorActuatorService
# ===========================================================================


def test_hsb_value():
    svc = _make_svc(HSBColorActuatorService, {
        "rgb": 0xFF8800,
        "gamut": "RGB",
        "colorTemperatureRange": {"minCt": 2200, "maxCt": 6000},
    })
    assert svc.value == 0xFF8800


def test_hsb_gamut():
    svc = _make_svc(HSBColorActuatorService, {
        "rgb": 0,
        "gamut": "RGB",
        "colorTemperatureRange": {"minCt": 2200, "maxCt": 6000},
    })
    assert svc.gamut == "RGB"


def test_hsb_min_ct():
    svc = _make_svc(HSBColorActuatorService, {
        "rgb": 0,
        "gamut": "RGB",
        "colorTemperatureRange": {"minCt": 2200, "maxCt": 6000},
    })
    assert svc.min_value == 2200


def test_hsb_max_ct():
    svc = _make_svc(HSBColorActuatorService, {
        "rgb": 0,
        "gamut": "RGB",
        "colorTemperatureRange": {"minCt": 2200, "maxCt": 6000},
    })
    assert svc.max_value == 6000


# ===========================================================================
# 12. SmokeDetectorCheckService
# ===========================================================================


def test_smoke_none():
    svc = _make_svc(SmokeDetectorCheckService, {"value": "NONE"})
    assert svc.value == SmokeDetectorCheckService.State.NONE


def test_smoke_ok():
    svc = _make_svc(SmokeDetectorCheckService, {"value": "SMOKE_TEST_OK"})
    assert svc.value == SmokeDetectorCheckService.State.SMOKE_TEST_OK


def test_smoke_requested():
    svc = _make_svc(SmokeDetectorCheckService, {"value": "SMOKE_TEST_REQUESTED"})
    assert svc.value == SmokeDetectorCheckService.State.SMOKE_TEST_REQUESTED


def test_smoke_failed():
    svc = _make_svc(SmokeDetectorCheckService, {"value": "SMOKE_TEST_FAILED"})
    assert svc.value == SmokeDetectorCheckService.State.SMOKE_TEST_FAILED


# ===========================================================================
# 13. AlarmService
# ===========================================================================


def test_alarm_idle_off():
    svc = _make_svc(AlarmService, {"value": "IDLE_OFF"})
    assert svc.value == AlarmService.State.IDLE_OFF


def test_alarm_intrusion():
    svc = _make_svc(AlarmService, {"value": "INTRUSION_ALARM"})
    assert svc.value == AlarmService.State.INTRUSION_ALARM


def test_alarm_secondary():
    svc = _make_svc(AlarmService, {"value": "SECONDARY_ALARM"})
    assert svc.value == AlarmService.State.SECONDARY_ALARM


def test_alarm_primary():
    svc = _make_svc(AlarmService, {"value": "PRIMARY_ALARM"})
    assert svc.value == AlarmService.State.PRIMARY_ALARM


# ===========================================================================
# 14. BatteryLevelService
# ===========================================================================


def test_battery_ok_no_faults():
    svc = _make_svc(BatteryLevelService, {})
    assert svc.warningLevel == BatteryLevelService.State.OK


def test_battery_low():
    svc = _make_svc(BatteryLevelService, {}, faults={"entries": [{"type": "LOW_BATTERY"}]})
    assert svc.warningLevel == BatteryLevelService.State.LOW_BATTERY


def test_battery_critical_low():
    svc = _make_svc(BatteryLevelService, {}, faults={"entries": [{"type": "CRITICAL_LOW"}]})
    assert svc.warningLevel == BatteryLevelService.State.CRITICAL_LOW


def test_battery_critically_low():
    svc = _make_svc(BatteryLevelService, {}, faults={"entries": [{"type": "CRITICALLY_LOW_BATTERY"}]})
    assert svc.warningLevel == BatteryLevelService.State.CRITICALLY_LOW_BATTERY


def test_battery_not_available():
    svc = _make_svc(BatteryLevelService, {}, faults={"entries": [{"type": "NOT_AVAILABLE"}]})
    assert svc.warningLevel == BatteryLevelService.State.NOT_AVAILABLE


def test_battery_faults_none_value():
    # "faults" key exists in raw but its value is None → treated as falsy → OK
    svc = _make_svc(BatteryLevelService, {}, faults=None)
    # faults=None means _make_svc does NOT add the key; verify OK path
    assert svc.warningLevel == BatteryLevelService.State.OK


def test_battery_faults_key_none_explicit():
    # Manually inject faults key with value None
    svc = _make_svc(BatteryLevelService, {})
    svc._raw_device_service["faults"] = None
    assert svc.warningLevel == BatteryLevelService.State.OK


# ===========================================================================
# 15. ThermostatService
# ===========================================================================


def test_thermostat_on():
    svc = _make_svc(ThermostatService, {"childLock": "ON"})
    assert svc.childLock == ThermostatService.State.ON


def test_thermostat_off():
    svc = _make_svc(ThermostatService, {"childLock": "OFF"})
    assert svc.childLock == ThermostatService.State.OFF


# ===========================================================================
# 16. CommunicationQualityService
# ===========================================================================


def test_comm_quality_bad():
    svc = _make_svc(CommunicationQualityService, {"quality": "BAD"})
    assert svc.value == CommunicationQualityService.State.BAD


def test_comm_quality_good():
    svc = _make_svc(CommunicationQualityService, {"quality": "GOOD"})
    assert svc.value == CommunicationQualityService.State.GOOD


def test_comm_quality_medium():
    svc = _make_svc(CommunicationQualityService, {"quality": "MEDIUM"})
    assert svc.value == CommunicationQualityService.State.MEDIUM


def test_comm_quality_normal():
    svc = _make_svc(CommunicationQualityService, {"quality": "NORMAL"})
    assert svc.value == CommunicationQualityService.State.NORMAL


def test_comm_quality_unknown():
    svc = _make_svc(CommunicationQualityService, {"quality": "UNKNOWN"})
    assert svc.value == CommunicationQualityService.State.UNKNOWN


def test_comm_quality_fetching():
    svc = _make_svc(CommunicationQualityService, {"quality": "FETCHING"})
    assert svc.value == CommunicationQualityService.State.FETCHING


# ===========================================================================
# 17. WaterLeakageSensorService
# ===========================================================================


def test_water_leakage_detected():
    svc = _make_svc(WaterLeakageSensorService, {"state": "LEAKAGE_DETECTED"})
    assert svc.value == WaterLeakageSensorService.State.LEAKAGE_DETECTED


def test_water_no_leakage():
    svc = _make_svc(WaterLeakageSensorService, {"state": "NO_LEAKAGE"})
    assert svc.value == WaterLeakageSensorService.State.NO_LEAKAGE


# ===========================================================================
# 18. WaterLeakageSensorTiltService
# ===========================================================================


def test_water_tilt_push_notification_enabled():
    svc = _make_svc(WaterLeakageSensorTiltService, {
        "pushNotificationState": "ENABLED",
        "acousticSignalState": "DISABLED",
    })
    assert svc.pushNotificationState == WaterLeakageSensorTiltService.State.ENABLED


def test_water_tilt_push_notification_disabled():
    svc = _make_svc(WaterLeakageSensorTiltService, {
        "pushNotificationState": "DISABLED",
        "acousticSignalState": "ENABLED",
    })
    assert svc.pushNotificationState == WaterLeakageSensorTiltService.State.DISABLED


def test_water_tilt_acoustic_signal_enabled():
    svc = _make_svc(WaterLeakageSensorTiltService, {
        "pushNotificationState": "DISABLED",
        "acousticSignalState": "ENABLED",
    })
    assert svc.acousticSignalState == WaterLeakageSensorTiltService.State.ENABLED


def test_water_tilt_acoustic_signal_disabled():
    svc = _make_svc(WaterLeakageSensorTiltService, {
        "pushNotificationState": "ENABLED",
        "acousticSignalState": "DISABLED",
    })
    assert svc.acousticSignalState == WaterLeakageSensorTiltService.State.DISABLED


# ===========================================================================
# 19. WaterLeakageSensorCheckService
# ===========================================================================


def test_water_check_result():
    svc = _make_svc(WaterLeakageSensorCheckService, {"result": "PASS"})
    assert svc.value == "PASS"


# ===========================================================================
# 20. PresenceSimulationConfigurationService
# ===========================================================================


def test_presence_simulation_enabled_getter():
    svc = _make_svc(PresenceSimulationConfigurationService, {"enabled": True})
    assert svc.enabled is True


def test_presence_simulation_disabled_getter():
    svc = _make_svc(PresenceSimulationConfigurationService, {"enabled": False})
    assert svc.enabled is False


def test_presence_simulation_setter():
    svc = _make_svc(PresenceSimulationConfigurationService, {"enabled": False})
    svc.enabled = True
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device",
        "PresenceSimulationConfigurationService",
        {"@type": "testType", "enabled": True},
    )


# ===========================================================================
# 21. ImpulseSwitchService
# ===========================================================================


def test_impulse_state():
    svc = _make_svc(ImpulseSwitchService, {"impulseState": True, "impulseLength": 500})
    assert svc.impulse_state is True


def test_impulse_length():
    svc = _make_svc(ImpulseSwitchService, {"impulseState": False, "impulseLength": 300})
    assert svc.impulse_length == 300


def test_impulse_last_present():
    svc = _make_svc(ImpulseSwitchService, {
        "impulseState": False,
        "impulseLength": 100,
        "instantOfLastImpulse": "2026-06-20T10:00:00Z",
    })
    assert svc.instant_of_last_impulse == "2026-06-20T10:00:00Z"


def test_impulse_last_absent():
    svc = _make_svc(ImpulseSwitchService, {"impulseState": False, "impulseLength": 100})
    assert svc.instant_of_last_impulse is None


def test_impulse_length_preserves_fraction():
    """OpenAPI types impulseLength as "number" (tenths of a second) — a
    fractional value must not be truncated by an int() cast."""
    svc = _make_svc(ImpulseSwitchService, {"impulseState": False, "impulseLength": 12.5})
    assert svc.impulse_length == 12.5


# ===========================================================================
# 22. ChildProtectionService
# ===========================================================================


def test_child_protection_lock_active():
    svc = _make_svc(ChildProtectionService, {"childLockActive": True})
    assert svc.childLockActive is True


def test_child_protection_lock_inactive():
    svc = _make_svc(ChildProtectionService, {"childLockActive": False})
    assert svc.childLockActive is False


# ===========================================================================
# 23. KeypadService
# ===========================================================================


def test_keypad_key_code_present():
    svc = _make_svc(KeypadService, {"keyCode": 7})
    assert svc.keyCode == 7


def test_keypad_key_code_absent():
    svc = _make_svc(KeypadService, {})
    assert svc.keyCode == 0


def test_keypad_key_name_lower_button():
    svc = _make_svc(KeypadService, {"keyName": "LOWER_BUTTON"})
    assert svc.keyName == KeypadService.KeyState.LOWER_BUTTON


def test_keypad_key_name_lower_left_button():
    svc = _make_svc(KeypadService, {"keyName": "LOWER_LEFT_BUTTON"})
    assert svc.keyName == KeypadService.KeyState.LOWER_LEFT_BUTTON


def test_keypad_key_name_lower_right_button():
    svc = _make_svc(KeypadService, {"keyName": "LOWER_RIGHT_BUTTON"})
    assert svc.keyName == KeypadService.KeyState.LOWER_RIGHT_BUTTON


def test_keypad_key_name_upper_button():
    svc = _make_svc(KeypadService, {"keyName": "UPPER_BUTTON"})
    assert svc.keyName == KeypadService.KeyState.UPPER_BUTTON


def test_keypad_key_name_upper_left_button():
    svc = _make_svc(KeypadService, {"keyName": "UPPER_LEFT_BUTTON"})
    assert svc.keyName == KeypadService.KeyState.UPPER_LEFT_BUTTON


def test_keypad_key_name_upper_right_button():
    svc = _make_svc(KeypadService, {"keyName": "UPPER_RIGHT_BUTTON"})
    assert svc.keyName == KeypadService.KeyState.UPPER_RIGHT_BUTTON


def test_keypad_key_name_undefined_button():
    svc = _make_svc(KeypadService, {"keyName": "UNDEFINED_BUTTON"})
    assert svc.keyName == KeypadService.KeyState.UNDEFINED_BUTTON


def test_keypad_key_name_absent():
    svc = _make_svc(KeypadService, {})
    assert svc.keyName is None


def test_keypad_event_type_press_short():
    svc = _make_svc(KeypadService, {"eventType": "PRESS_SHORT"})
    assert svc.eventType == KeypadService.KeyEvent.PRESS_SHORT


def test_keypad_event_type_press_long():
    svc = _make_svc(KeypadService, {"eventType": "PRESS_LONG"})
    assert svc.eventType == KeypadService.KeyEvent.PRESS_LONG


def test_keypad_event_type_press_long_released():
    svc = _make_svc(KeypadService, {"eventType": "PRESS_LONG_RELEASED"})
    assert svc.eventType == KeypadService.KeyEvent.PRESS_LONG_RELEASED


def test_keypad_event_type_switch_on():
    svc = _make_svc(KeypadService, {"eventType": "SWITCH_ON"})
    assert svc.eventType == KeypadService.KeyEvent.SWITCH_ON


def test_keypad_event_type_switch_off():
    svc = _make_svc(KeypadService, {"eventType": "SWITCH_OFF"})
    assert svc.eventType == KeypadService.KeyEvent.SWITCH_OFF


def test_keypad_event_type_absent():
    svc = _make_svc(KeypadService, {})
    assert svc.eventType is None


def test_keypad_event_timestamp_present():
    svc = _make_svc(KeypadService, {"eventTimestamp": 1718700000})
    assert svc.eventTimestamp == 1718700000


def test_keypad_event_timestamp_absent():
    svc = _make_svc(KeypadService, {})
    assert svc.eventTimestamp == 0


def test_keypad_event_type_setter():
    svc = _make_svc(KeypadService, {"eventType": "PRESS_SHORT"})
    svc.eventType = KeypadService.KeyEvent.SWITCH_ON
    # setter writes to state dict directly, NOT via API
    assert svc.state["eventType"] == "SWITCH_ON"
    svc._api.put_device_service_state.assert_not_called()


# ===========================================================================
# 24. LatestMotionService
# ===========================================================================


def test_latest_motion_detected_present():
    svc = _make_svc(LatestMotionService, {"latestMotionDetected": "2026-06-20T09:00:00Z"})
    assert svc.latestMotionDetected == "2026-06-20T09:00:00Z"


def test_latest_motion_detected_absent():
    svc = _make_svc(LatestMotionService, {})
    assert svc.latestMotionDetected == "n/a"


# ===========================================================================
# 25. DetectionTestService
# ===========================================================================


def test_detection_started():
    svc = _make_svc(DetectionTestService, {"detectionState": "DETECTION_TEST_STARTED"})
    assert svc.detection_state == DetectionTestService.DetectionState.DETECTION_TEST_STARTED


def test_detection_stopped():
    svc = _make_svc(DetectionTestService, {"detectionState": "DETECTION_TEST_STOPPED"})
    assert svc.detection_state == DetectionTestService.DetectionState.DETECTION_TEST_STOPPED


# ===========================================================================
# 26. LatestTamperService
# ===========================================================================


def test_tamper_protection_enabled():
    svc = _make_svc(LatestTamperService, {
        "tamperProtectionEnabled": True,
        "wasTampered": False,
    })
    assert svc.tamper_protection_enabled is True


def test_was_tampered():
    svc = _make_svc(LatestTamperService, {
        "tamperProtectionEnabled": False,
        "wasTampered": True,
    })
    assert svc.was_tampered is True


def test_last_tamper_time_present():
    svc = _make_svc(LatestTamperService, {
        "tamperProtectionEnabled": True,
        "wasTampered": False,
        "lastTamperTime": "2026-06-20T08:00:00Z",
    })
    assert svc.last_tamper_time == "2026-06-20T08:00:00Z"


def test_last_tamper_time_absent():
    svc = _make_svc(LatestTamperService, {
        "tamperProtectionEnabled": True,
        "wasTampered": False,
    })
    assert svc.last_tamper_time == "n/a"


# ===========================================================================
# 27. PollControlService
# ===========================================================================


def test_poll_control_long():
    svc = _make_svc(PollControlService, {"longPollInterval": "LONG"})
    assert svc.longPollInterval == PollControlService.PollControlState.LONG


def test_poll_control_short():
    svc = _make_svc(PollControlService, {"longPollInterval": "SHORT"})
    assert svc.longPollInterval == PollControlService.PollControlState.SHORT


# ===========================================================================
# 28. PirSensorConfigurationService
# ===========================================================================


def test_pir_high():
    svc = _make_svc(PirSensorConfigurationService, {"motionSensitivity": "HIGH"})
    assert svc.motionSensitivity == PirSensorConfigurationService.MotionSensitivity.HIGH


def test_pir_middle():
    svc = _make_svc(PirSensorConfigurationService, {"motionSensitivity": "MIDDLE"})
    assert svc.motionSensitivity == PirSensorConfigurationService.MotionSensitivity.MIDDLE


def test_pir_low():
    svc = _make_svc(PirSensorConfigurationService, {"motionSensitivity": "LOW"})
    assert svc.motionSensitivity == PirSensorConfigurationService.MotionSensitivity.LOW


# ===========================================================================
# 29. OccupancyDetectionService
# ===========================================================================


def test_occupancy_is_occupied_true():
    svc = _make_svc(OccupancyDetectionService, {"isOccupied": True})
    assert svc.isOccupied is True


def test_occupancy_is_occupied_false():
    svc = _make_svc(OccupancyDetectionService, {"isOccupied": False})
    assert svc.isOccupied is False


def test_occupancy_last_change_time_present():
    svc = _make_svc(OccupancyDetectionService, {
        "isOccupied": True,
        "lastOccupancyChangeTime": "2026-06-20T07:30:00Z",
    })
    assert svc.lastOccupancyChangeTime == "2026-06-20T07:30:00Z"


def test_occupancy_last_change_time_absent():
    svc = _make_svc(OccupancyDetectionService, {"isOccupied": False})
    assert svc.lastOccupancyChangeTime == "n/a"


# ===========================================================================
# 30. PetImmunityService
# ===========================================================================


def test_pet_immunity_enabled_true():
    svc = _make_svc(PetImmunityService, {"enabled": True})
    assert svc.enabled is True


def test_pet_immunity_enabled_false():
    svc = _make_svc(PetImmunityService, {"enabled": False})
    assert svc.enabled is False


# ===========================================================================
# 31. AirQualityLevelService
# ===========================================================================

_AQ_BASE = {
    "combinedRating": "GOOD",
    "description": "All fine",
    "temperature": 22,
    "temperatureRating": "GOOD",
    "humidity": 45,
    "humidityRating": "MEDIUM",
    "purity": 800,
    "purityRating": "BAD",
}


def test_air_quality_combined_rating_good():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "combinedRating": "GOOD"})
    assert svc.combinedRating == AirQualityLevelService.RatingState.GOOD


def test_air_quality_combined_rating_medium():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "combinedRating": "MEDIUM"})
    assert svc.combinedRating == AirQualityLevelService.RatingState.MEDIUM


def test_air_quality_combined_rating_bad():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "combinedRating": "BAD"})
    assert svc.combinedRating == AirQualityLevelService.RatingState.BAD


def test_air_quality_temperature():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "temperature": 21})
    assert svc.temperature == 21
    assert isinstance(svc.temperature, float)


def test_air_quality_temperature_keeps_decimals():
    # Bosch sends one decimal; int() previously truncated 21.7 -> 21 (#352).
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "temperature": 21.7})
    assert svc.temperature == 21.7
    assert isinstance(svc.temperature, float)


def test_air_quality_temperature_rating():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "temperatureRating": "MEDIUM"})
    assert svc.temperatureRating == AirQualityLevelService.RatingState.MEDIUM


def test_air_quality_humidity():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "humidity": 60})
    assert svc.humidity == 60
    assert isinstance(svc.humidity, float)


def test_air_quality_humidity_keeps_decimals():
    # Bosch types humidity as number; int() previously truncated it (#352 follow-up).
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "humidity": 55.5})
    assert svc.humidity == 55.5
    assert isinstance(svc.humidity, float)


def test_air_quality_humidity_rating():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "humidityRating": "BAD"})
    assert svc.humidityRating == AirQualityLevelService.RatingState.BAD


def test_air_quality_purity():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "purity": 1200})
    assert svc.purity == 1200
    assert isinstance(svc.purity, float)


def test_air_quality_purity_keeps_decimals():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "purity": 812.5})
    assert svc.purity == 812.5
    assert isinstance(svc.purity, float)


def test_air_quality_purity_rating():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "purityRating": "GOOD"})
    assert svc.purityRating == AirQualityLevelService.RatingState.GOOD


def test_air_quality_description():
    svc = _make_svc(AirQualityLevelService, {**_AQ_BASE, "description": "Very clean air"})
    assert svc.description == "Very clean air"


# ===========================================================================
# 32. SurveillanceAlarmService
# ===========================================================================


def test_surveillance_alarm_off():
    svc = _make_svc(SurveillanceAlarmService, {"value": "ALARM_OFF"})
    assert svc.value == SurveillanceAlarmService.State.ALARM_OFF


def test_surveillance_alarm_on():
    svc = _make_svc(SurveillanceAlarmService, {"value": "ALARM_ON"})
    assert svc.value == SurveillanceAlarmService.State.ALARM_ON


def test_surveillance_alarm_muted():
    svc = _make_svc(SurveillanceAlarmService, {"value": "ALARM_MUTED"})
    assert svc.value == SurveillanceAlarmService.State.ALARM_MUTED


# ===========================================================================
# 33. SERVICE_MAPPING
# ===========================================================================


def test_service_mapping_keys_present():
    assert "PowerSwitch" in SERVICE_MAPPING
    assert "BatteryLevel" in SERVICE_MAPPING
    assert "Keypad" in SERVICE_MAPPING


# ===========================================================================
# 34. build() function
# ===========================================================================


def test_build_power_switch():
    api = MagicMock()
    raw = {
        "id": "PowerSwitch",
        "deviceId": "d",
        "path": "/p",
        "state": {"@type": "t", "switchState": "ON", "automaticPowerOffTime": 0},
    }
    svc = build(api=api, raw_device_service=raw)
    assert isinstance(svc, PowerSwitchService)
    assert svc.value == PowerSwitchService.State.ON


def test_build_unknown_raises():
    api = MagicMock()
    raw = {
        "id": "Unknown",
        "deviceId": "d",
        "path": "/p",
        "state": {"@type": "t"},
    }
    with pytest.raises(ValueError):
        build(api=api, raw_device_service=raw)


# ===========================================================================
# summary() smoke tests — exercises the print paths for coverage
# ===========================================================================

def test_summary_temperature_offset(capsys):
    svc = _make_svc(TemperatureOffsetService, {"offset": 1.0, "stepSize": 0.5, "minOffset": -5.0, "maxOffset": 5.0})
    svc.summary()
    out = capsys.readouterr().out
    assert "TemperatureOffset" in out


def test_summary_temperature_level(capsys):
    svc = _make_svc(TemperatureLevelService, {"temperature": 20.0})
    svc.summary()
    out = capsys.readouterr().out
    assert "Temperature" in out


def test_summary_humidity_level(capsys):
    svc = _make_svc(HumidityLevelService, {"humidity": 50.0})
    svc.summary()
    out = capsys.readouterr().out
    assert "Humidity" in out


def test_summary_room_climate_control(capsys):
    svc = _make_svc(RoomClimateControlService, {
        "operationMode": "AUTOMATIC",
        "setpointTemperature": 20.0,
        "setpointTemperatureForLevelEco": 16.0,
        "setpointTemperatureForLevelComfort": 22.0,
        "ventilationMode": False,
        "low": False,
        "boostMode": False,
        "summerMode": False,
        "supportsBoostMode": True,
    })
    svc.summary()
    out = capsys.readouterr().out
    assert "Operation Mode" in out


def test_summary_heating_circuit(capsys):
    svc = _make_svc(HeatingCircuitService, {
        "operationMode": "MANUAL",
        "setpointTemperature": 19.0,
        "setpointTemperatureForLevelEco": 14.0,
        "setpointTemperatureForLevelComfort": 23.0,
        "temperatureOverrideModeActive": False,
        "temperatureOverrideFeatureEnabled": True,
        "energySavingFeatureEnabled": False,
        "on": True,
    })
    svc.summary()
    out = capsys.readouterr().out
    assert "Operation Mode" in out


def test_summary_shutter_contact(capsys):
    svc = _make_svc(ShutterContactService, {"value": "CLOSED"})
    svc.summary()
    out = capsys.readouterr().out
    assert "Value" in out


def test_summary_bypass(capsys):
    svc = _make_svc(BypassService, {"state": "BYPASS_INACTIVE"})
    svc.summary()
    out = capsys.readouterr().out
    assert "State" in out


def test_summary_vibration_sensor(capsys):
    svc = _make_svc(VibrationSensorService, {"value": "NO_VIBRATION", "enabled": True, "sensitivity": "HIGH"})
    svc.summary()
    out = capsys.readouterr().out
    assert "Value" in out


def test_summary_power_switch(capsys):
    svc = _make_svc(PowerSwitchService, {"switchState": "ON", "automaticPowerOffTime": 0})
    svc.summary()
    out = capsys.readouterr().out
    assert "switchState" in out


def test_summary_power_meter(capsys):
    svc = _make_svc(PowerMeterService, {"powerConsumption": 1.0, "energyConsumption": 2.0})
    svc.summary()
    out = capsys.readouterr().out
    assert "powerConsumption" in out


def test_summary_routing(capsys):
    svc = _make_svc(RoutingService, {"value": "ENABLED"})
    svc.summary()
    out = capsys.readouterr().out
    assert "value" in out


def test_summary_power_switch_program(capsys):
    svc = _make_svc(PowerSwitchProgramService, {"operationMode": "MANUAL"})
    svc.summary()
    out = capsys.readouterr().out
    assert "operationMode" in out


def test_summary_binary_switch(capsys):
    svc = _make_svc(BinarySwitchService, {"on": True})
    svc.summary()
    out = capsys.readouterr().out
    assert "switchState" in out


def test_summary_multi_level_switch(capsys):
    svc = _make_svc(MultiLevelSwitchService, {"level": 50})
    svc.summary()
    out = capsys.readouterr().out
    assert "multiLevelSwitchState" in out


def test_summary_multi_level_sensor(capsys):
    svc = _make_svc(MultiLevelSensorService, {"illuminance": 300})
    svc.summary()
    out = capsys.readouterr().out
    assert "multiLevelSensorState" in out


def test_summary_hue_color_temperature(capsys):
    svc = _make_svc(HueColorTemperatureService, {
        "colorTemperature": 4000,
        "colorTemperatureRange": {"minCt": 2700, "maxCt": 6500},
    })
    svc.summary()
    out = capsys.readouterr().out
    assert "colorTemperature" in out


def test_summary_hsb_color_actuator(capsys):
    svc = _make_svc(HSBColorActuatorService, {
        "rgb": 0xFF0000,
        "gamut": "RGB",
        "colorTemperatureRange": {"minCt": 2200, "maxCt": 6000},
    })
    svc.summary()
    out = capsys.readouterr().out
    assert "rgb" in out


def test_summary_smoke_detector_check(capsys):
    svc = _make_svc(SmokeDetectorCheckService, {"value": "NONE"})
    svc.summary()
    out = capsys.readouterr().out
    assert "smokeDetectorCheckState" in out


def test_summary_alarm(capsys):
    svc = _make_svc(AlarmService, {"value": "IDLE_OFF"})
    svc.summary()
    out = capsys.readouterr().out
    assert "alarmState" in out


def test_summary_battery_level(capsys):
    svc = _make_svc(BatteryLevelService, {})
    svc.summary()
    out = capsys.readouterr().out
    assert "warningLevel" in out


def test_summary_thermostat(capsys):
    svc = _make_svc(ThermostatService, {"childLock": "ON"})
    svc.summary()
    out = capsys.readouterr().out
    assert "childLock" in out


def test_summary_communication_quality(capsys):
    svc = _make_svc(CommunicationQualityService, {"quality": "GOOD"})
    svc.summary()
    out = capsys.readouterr().out
    assert "quality" in out


def test_summary_shutter_control(capsys):
    svc = _make_svc(ShutterControlService, {"operationState": "STOPPED", "calibrated": True, "level": 0.5})
    svc.summary()
    out = capsys.readouterr().out
    assert "operationState" in out


def test_summary_blinds_control(capsys):
    svc = _make_svc(BlindsControlService, {"currentAngle": 0.0, "targetAngle": 45.0})
    svc.summary()
    out = capsys.readouterr().out
    assert "currentAngle" in out


def test_summary_blinds_scene_control(capsys):
    svc = _make_svc(BlindsSceneControlService, {"level": 0.5, "angle": 30.0})
    svc.summary()
    out = capsys.readouterr().out
    assert "level" in out


def test_summary_camera_light(capsys):
    svc = _make_svc(CameraLightService, {"value": "ON"})
    svc.summary()
    out = capsys.readouterr().out
    assert "value" in out


def test_summary_privacy_mode(capsys):
    svc = _make_svc(PrivacyModeService, {"value": "ENABLED"})
    svc.summary()
    out = capsys.readouterr().out
    assert "value" in out


def test_summary_camera_notification(capsys):
    svc = _make_svc(CameraNotificationService, {"value": "ENABLED"})
    svc.summary()
    out = capsys.readouterr().out
    assert "value" in out


def test_summary_child_protection(capsys):
    svc = _make_svc(ChildProtectionService, {"childLockActive": True})
    svc.summary()
    out = capsys.readouterr().out
    assert "childLockActive" in out


def test_summary_keypad(capsys):
    svc = _make_svc(KeypadService, {"keyCode": 1, "keyName": "LOWER_BUTTON", "eventType": "PRESS_SHORT", "eventTimestamp": 1000})
    svc.summary()
    out = capsys.readouterr().out
    assert "keyCode" in out


def test_summary_latest_motion(capsys):
    svc = _make_svc(LatestMotionService, {"latestMotionDetected": "2026-06-20T10:00:00Z"})
    svc.summary()
    out = capsys.readouterr().out
    assert "latestMotionDetected" in out


def test_summary_detection_test(capsys):
    svc = _make_svc(DetectionTestService, {"detectionState": "DETECTION_TEST_STOPPED"})
    svc.summary()
    out = capsys.readouterr().out
    assert "detectionState" in out


def test_summary_latest_tamper(capsys):
    svc = _make_svc(LatestTamperService, {"tamperProtectionEnabled": True, "wasTampered": False})
    svc.summary()
    out = capsys.readouterr().out
    assert "tamperProtectionEnabled" in out


def test_summary_poll_control(capsys):
    svc = _make_svc(PollControlService, {"longPollInterval": "LONG"})
    svc.summary()
    out = capsys.readouterr().out
    assert "longPollInterval" in out


def test_summary_pir_sensor(capsys):
    svc = _make_svc(PirSensorConfigurationService, {"motionSensitivity": "HIGH"})
    svc.summary()
    out = capsys.readouterr().out
    assert "motionSensitivity" in out


def test_summary_occupancy_detection(capsys):
    svc = _make_svc(OccupancyDetectionService, {"isOccupied": True})
    svc.summary()
    out = capsys.readouterr().out
    assert "isOccupied" in out


def test_summary_pet_immunity(capsys):
    svc = _make_svc(PetImmunityService, {"enabled": True})
    svc.summary()
    out = capsys.readouterr().out
    assert "enabled" in out


def test_summary_air_quality_level(capsys):
    svc = _make_svc(AirQualityLevelService, {
        "combinedRating": "GOOD",
        "description": "All fine",
        "temperature": 22,
        "temperatureRating": "GOOD",
        "humidity": 45,
        "humidityRating": "MEDIUM",
        "purity": 800,
        "purityRating": "BAD",
    })
    svc.summary()
    out = capsys.readouterr().out
    assert "combinedRating" in out


def test_summary_surveillance_alarm(capsys):
    svc = _make_svc(SurveillanceAlarmService, {"value": "ALARM_OFF"})
    svc.summary()
    out = capsys.readouterr().out
    assert "value" in out


def test_summary_water_leakage_sensor(capsys):
    svc = _make_svc(WaterLeakageSensorService, {"state": "NO_LEAKAGE"})
    svc.summary()
    out = capsys.readouterr().out
    assert "waterLeakageSensorState" in out


def test_summary_water_leakage_tilt(capsys):
    svc = _make_svc(WaterLeakageSensorTiltService, {
        "pushNotificationState": "ENABLED",
        "acousticSignalState": "DISABLED",
    })
    svc.summary()
    out = capsys.readouterr().out
    assert "pushNotificationState" in out


def test_summary_water_leakage_check(capsys):
    svc = _make_svc(WaterLeakageSensorCheckService, {"result": "PASS"})
    svc.summary()
    out = capsys.readouterr().out
    assert "waterLeakageSensorCheck" in out


def test_summary_presence_simulation(capsys):
    svc = _make_svc(PresenceSimulationConfigurationService, {"enabled": True})
    svc.summary()
    out = capsys.readouterr().out
    assert "presenceSimulationConfigurationState" in out


def test_summary_valve_tappet(capsys):
    svc = _make_svc(ValveTappetService, {"position": 50, "value": "VALVE_ADAPTION_SUCCESSFUL"})
    svc.summary()
    out = capsys.readouterr().out
    assert "Position" in out


# ===========================================================================
# SmartSensitivityControlService and SmokeDetectionControlService stubs
# ===========================================================================

from boschshcpy.services_impl import SmartSensitivityControlService, SmokeDetectionControlService


def test_smart_sensitivity_control_summary(capsys):
    svc = _make_svc(SmartSensitivityControlService, {})
    svc.summary()
    out = capsys.readouterr().out
    # SmartSensitivityControl is now fully implemented; summary shows enabled + sensitivities
    assert "enabled" in out
    assert "sensitivities" in out


def test_smoke_detection_control_summary(capsys):
    svc = _make_svc(SmokeDetectionControlService, {})
    svc.summary()
    out = capsys.readouterr().out
    assert "not yet implemented" in out


# ===========================================================================
# Remaining uncovered lines (operation_mode setters + ShutterControl __init__)
# ===========================================================================

def test_rcc_operation_mode_setter():
    svc = _make_svc(RoomClimateControlService, {"operationMode": "MANUAL"})
    svc.operation_mode = RoomClimateControlService.OperationMode.AUTOMATIC
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "RoomClimateControlService", {"@type": "testType", "operationMode": "AUTOMATIC"}
    )


def test_hcs_operation_mode_setter():
    svc = _make_svc(HeatingCircuitService, {"operationMode": "MANUAL"})
    svc.operation_mode = HeatingCircuitService.OperationMode.AUTOMATIC
    svc._api.put_device_service_state.assert_called_once_with(
        "test-device", "HeatingCircuitService", {"@type": "testType", "operationMode": "AUTOMATIC"}
    )


def test_shutter_control_init_via_constructor():
    """ShutterControlService has an explicit __init__ calling super(); exercise it."""
    raw = {
        "id": "ShutterControl",
        "deviceId": "dev1",
        "path": "/test",
        "state": {"@type": "t", "operationState": "STOPPED", "calibrated": True},
    }
    api = MagicMock()
    svc = ShutterControlService(api=api, raw_device_service=raw)
    assert svc.operation_state == ShutterControlService.State.STOPPED
    assert svc.calibrated is True


# ---------------------------------------------------------------------------
# Regression: issue #311 — Shutter Control I (old model) has no operationState
# and reports level as a string. The cover integration reads operation_state on
# every update, so a KeyError there makes the entity stop working.
# Confirmed against the Bosch API spec (Shutter-local vs Shutter-II).
# ---------------------------------------------------------------------------

def test_shutter_control_i_missing_operation_state_returns_stopped():
    """Shutter Control I state has no operationState -> STOPPED, never KeyError."""
    svc = _make_svc(ShutterControlService, {"level": "1.000"})
    assert svc.operation_state == ShutterControlService.State.STOPPED


def test_shutter_control_ii_operation_state_parsed():
    """Shutter Control II still parses its operationState normally."""
    svc = _make_svc(ShutterControlService, {"operationState": "MOVING", "level": 0.5})
    assert svc.operation_state == ShutterControlService.State.MOVING


def test_shutter_control_i_level_string_coerced_to_float():
    """Shutter Control I reports level as a string -> coerced to float."""
    svc = _make_svc(ShutterControlService, {"level": "1.000"})
    assert svc.level == 1.0
    assert isinstance(svc.level, float)


def test_shutter_control_ii_level_number_preserved():
    svc = _make_svc(ShutterControlService, {"level": 0.59, "operationState": "STOPPED"})
    assert svc.level == 0.59


def test_shutter_control_level_absent_defaults_zero():
    svc = _make_svc(ShutterControlService, {})
    assert svc.level == 0.0


def test_shutter_control_i_calibrated_absent_false():
    """Shutter Control I does not expose `calibrated` -> default False, no KeyError."""
    svc = _make_svc(ShutterControlService, {"level": "0.500"})
    assert svc.calibrated is False


# ===========================================================================
# BUG #311 regression tests — crash on spec-allowed values / missing optional fields
# ===========================================================================


def test_pir_sensor_motion_sensitivity_unknown():
    """BUG 1: MotionSensitivity.UNKNOWN missing — crash when Bosch sends it."""
    svc = _make_svc(PirSensorConfigurationService, {"motionSensitivity": "UNKNOWN"})
    assert svc.motionSensitivity == PirSensorConfigurationService.MotionSensitivity.UNKNOWN


def test_poll_control_state_unknown():
    """BUG 2: PollControlState.UNKNOWN missing — crash when Bosch sends it."""
    svc = _make_svc(PollControlService, {"longPollInterval": "UNKNOWN"})
    assert svc.longPollInterval == PollControlService.PollControlState.UNKNOWN


def test_detection_test_state_unknown():
    """BUG 3: DetectionState.DETECTION_TEST_UNKNOWN missing — crash when Bosch sends it."""
    svc = _make_svc(DetectionTestService, {"detectionState": "DETECTION_TEST_UNKNOWN"})
    assert svc.detection_state == DetectionTestService.DetectionState.DETECTION_TEST_UNKNOWN


def test_blinds_type_degree_360():
    """BUG 4a: BlindsType.DEGREE_360 missing — crash on Shutter-II device."""
    svc = _make_svc(BlindsControlService, {"blindsType": "DEGREE_360", "currentAngle": 45.0, "targetAngle": 90.0})
    assert svc.blinds_type == BlindsControlService.BlindsType.DEGREE_360


def test_blinds_optional_fields_absent_no_keyerror():
    """BUG 4b: currentAngle/targetAngle/blindsType optional — KeyError on empty state."""
    svc = _make_svc(BlindsControlService, {})
    assert svc.current_angle == 0.0
    assert svc.target_angle == 0.0
    assert svc.blinds_type is None


def test_room_climate_supports_boost_mode_absent():
    """BUG 5: supportsBoostMode optional — KeyError when field absent."""
    svc = _make_svc(RoomClimateControlService, {})
    assert svc.supports_boost_mode is False


def test_battery_level_empty_faults_entries_no_assert():
    """BUG 6a: assert len==1 crashes on 0 entries — should return OK."""
    svc = _make_svc(BatteryLevelService, {}, faults={"entries": []})
    assert svc.warningLevel == BatteryLevelService.State.OK


def test_battery_level_multiple_faults_uses_first():
    """BUG 6b: assert len==1 crashes on 2+ entries — should use first entry."""
    faults = {"entries": [{"type": "LOW_BATTERY"}, {"type": "CRITICAL_LOW"}]}
    svc = _make_svc(BatteryLevelService, {}, faults=faults)
    assert svc.warningLevel == BatteryLevelService.State.LOW_BATTERY


# ===========================================================================
# BUG 2 regression — BlindsSceneControlService.level/.angle KeyError when
# the spec-optional fields are absent from the state dict.
# Confirmed: KeyError before fix; .get("level", 0.0) / .get("angle", 0.0) after.
# ===========================================================================

def test_blinds_scene_level_absent_defaults_zero():
    """Regression: KeyError on state['level'] when 'level' key missing."""
    svc = _make_svc(BlindsSceneControlService, {})
    assert svc.level == 0.0


def test_blinds_scene_angle_absent_defaults_zero():
    """Regression: KeyError on state['angle'] when 'angle' key missing."""
    svc = _make_svc(BlindsSceneControlService, {})
    assert svc.angle == 0.0


def test_blinds_scene_only_level_present_angle_defaults():
    """level present, angle absent — angle must not KeyError."""
    svc = _make_svc(BlindsSceneControlService, {"level": 0.75})
    assert svc.level == 0.75
    assert svc.angle == 0.0


def test_blinds_scene_only_angle_present_level_defaults():
    """angle present, level absent — level must not KeyError."""
    svc = _make_svc(BlindsSceneControlService, {"angle": 45.0})
    assert svc.angle == 45.0
    assert svc.level == 0.0


# ---------------------------------------------------------------------------
# RoomClimateControlService.has_demand
# ---------------------------------------------------------------------------

class _FakeRCCService:
    """Minimal stub so we can test has_demand without network/SHC."""
    def __init__(self, state):
        self.state = state


def _make_rcc_service(state):
    from boschshcpy.services_impl import RoomClimateControlService
    svc = RoomClimateControlService.__new__(RoomClimateControlService)
    # Use the standard _raw_state attribute that SHCDeviceService.state reads
    svc._raw_state = state
    return svc


def test_has_demand_true():
    svc = _make_rcc_service({"hasDemand": True})
    assert svc.has_demand is True


def test_has_demand_false():
    svc = _make_rcc_service({"hasDemand": False})
    assert svc.has_demand is False


def test_has_demand_absent_defaults_false():
    """Missing hasDemand key → defaults to False."""
    svc = _make_rcc_service({})
    assert svc.has_demand is False


def test_has_demand_truthy_int():
    """Non-bool truthy value in state is coerced to True."""
    svc = _make_rcc_service({"hasDemand": 1})
    assert svc.has_demand is True
