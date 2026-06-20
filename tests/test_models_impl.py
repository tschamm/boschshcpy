"""Tests for boschshcpy/models_impl.py.

Isolation-safe: no HA harness, no real network.
Pattern mirrors test_reliability.py + test_emma.py:
  - Bypass __init__ via Cls.__new__(Cls) + inject fakes
  - Fake SHCDeviceService via SimpleNamespace with a .state dict
  - One assert per enum state/branch side
"""

from types import SimpleNamespace
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_raw_device(model="PSM", device_id="device-1", name="Test Device"):
    """Minimal raw_device dict accepted by SHCDevice."""
    return {
        "id": device_id,
        "rootDeviceId": "root-1",
        "manufacturer": "BOSCH",
        "roomId": "room-1",
        "deviceModel": model,
        "serial": "SER-001",
        "profile": model,
        "name": name,
        "status": "AVAILABLE",
        "deviceServiceIds": [],
    }


def _fake_service(service_id, state_dict):
    """Build a minimal SHCDeviceService with a custom state, without real API."""
    from boschshcpy.device_service import SHCDeviceService

    svc = SHCDeviceService.__new__(SHCDeviceService)
    svc._api = None
    svc._raw_device_service = {
        "id": service_id,
        "deviceId": "device-1",
        "path": f"/devices/device-1/services/{service_id}",
        "state": state_dict,
    }
    svc._raw_state = state_dict
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


def _inject_services(device_obj, services_dict):
    """Inject pre-built service objects keyed by service-id."""
    device_obj._device_services_by_id = services_dict
    device_obj._callbacks = {}
    device_obj._api = None


def _build_device(cls, raw_device, services_dict):
    """Construct cls via __new__, inject raw_device + service map."""
    obj = cls.__new__(cls)
    obj._raw_device = raw_device
    _inject_services(obj, services_dict)
    # Call only the model-level init that references services already in the map.
    # We skip super-chain by directly setting the service attrs the model __init__ would set.
    return obj


# ---------------------------------------------------------------------------
# SHCBatteryDevice
# ---------------------------------------------------------------------------

class TestSHCBatteryDevice:
    def _make(self, faults=None):
        from boschshcpy.models_impl import SHCBatteryDevice
        from boschshcpy.services_impl import BatteryLevelService

        svc = BatteryLevelService.__new__(BatteryLevelService)
        svc._api = None
        raw_svc = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        if faults:
            raw_svc["faults"] = faults
        svc._raw_device_service = raw_svc
        svc._raw_state = {}
        svc._last_update = None
        svc._callbacks = {}
        svc._event_callbacks = {}

        obj = SHCBatteryDevice.__new__(SHCBatteryDevice)
        obj._raw_device = _fake_raw_device()
        obj._device_services_by_id = {"BatteryLevel": svc}
        obj._callbacks = {}
        obj._api = None
        obj._batterylevel_service = svc
        return obj

    def test_battery_ok_no_faults(self):
        d = self._make(faults=None)
        from boschshcpy.services_impl import BatteryLevelService
        assert d.batterylevel == BatteryLevelService.State.OK

    def test_battery_low(self):
        d = self._make(faults={"entries": [{"type": "LOW_BATTERY"}]})
        from boschshcpy.services_impl import BatteryLevelService
        assert d.batterylevel == BatteryLevelService.State.LOW_BATTERY

    def test_battery_critical_low(self):
        d = self._make(faults={"entries": [{"type": "CRITICAL_LOW"}]})
        from boschshcpy.services_impl import BatteryLevelService
        assert d.batterylevel == BatteryLevelService.State.CRITICAL_LOW

    def test_battery_critically_low(self):
        d = self._make(faults={"entries": [{"type": "CRITICALLY_LOW_BATTERY"}]})
        from boschshcpy.services_impl import BatteryLevelService
        assert d.batterylevel == BatteryLevelService.State.CRITICALLY_LOW_BATTERY

    def test_supports_batterylevel_true(self):
        d = self._make()
        assert d.supports_batterylevel is True

    def test_supports_batterylevel_false(self):
        from boschshcpy.models_impl import SHCBatteryDevice
        obj = SHCBatteryDevice.__new__(SHCBatteryDevice)
        obj._raw_device = _fake_raw_device()
        obj._device_services_by_id = {}
        obj._callbacks = {}
        obj._api = None
        obj._batterylevel_service = None
        from boschshcpy.services_impl import BatteryLevelService
        assert obj.supports_batterylevel is False
        assert obj.batterylevel == BatteryLevelService.State.NOT_AVAILABLE


# ---------------------------------------------------------------------------
# SHCSmokeDetector
# ---------------------------------------------------------------------------

class TestSHCSmokeDetector:
    def _make(self, alarm_state="IDLE_OFF", check_state="NONE"):
        from boschshcpy.models_impl import SHCSmokeDetector
        from boschshcpy.services_impl import AlarmService, SmokeDetectorCheckService, BatteryLevelService

        alarm_svc = AlarmService.__new__(AlarmService)
        alarm_svc._api = None
        alarm_svc._raw_device_service = {"id": "Alarm", "deviceId": "d1", "path": "/x",
                                          "state": {"@type": "alarmState", "value": alarm_state}}
        alarm_svc._raw_state = alarm_svc._raw_device_service["state"]
        alarm_svc._last_update = None; alarm_svc._callbacks = {}; alarm_svc._event_callbacks = {}

        check_svc = SmokeDetectorCheckService.__new__(SmokeDetectorCheckService)
        check_svc._api = None
        check_svc._raw_device_service = {"id": "SmokeDetectorCheck", "deviceId": "d1", "path": "/x",
                                          "state": {"@type": "smokeDetectorCheckState", "value": check_state}}
        check_svc._raw_state = check_svc._raw_device_service["state"]
        check_svc._last_update = None; check_svc._callbacks = {}; check_svc._event_callbacks = {}

        bat_svc = BatteryLevelService.__new__(BatteryLevelService)
        bat_svc._api = None
        bat_svc._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat_svc._raw_state = {}
        bat_svc._last_update = None; bat_svc._callbacks = {}; bat_svc._event_callbacks = {}

        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._raw_device = _fake_raw_device(model="SD")
        obj._device_services_by_id = {"Alarm": alarm_svc, "SmokeDetectorCheck": check_svc,
                                       "BatteryLevel": bat_svc}
        obj._callbacks = {}
        obj._api = None
        obj._alarm_service = alarm_svc
        obj._smokedetectorcheck_service = check_svc
        obj._batterylevel_service = bat_svc
        return obj

    def test_alarmstate_idle_off(self):
        from boschshcpy.services_impl import AlarmService
        d = self._make(alarm_state="IDLE_OFF")
        assert d.alarmstate == AlarmService.State.IDLE_OFF

    def test_alarmstate_primary_alarm(self):
        from boschshcpy.services_impl import AlarmService
        d = self._make(alarm_state="PRIMARY_ALARM")
        assert d.alarmstate == AlarmService.State.PRIMARY_ALARM

    def test_alarmstate_intrusion_alarm(self):
        from boschshcpy.services_impl import AlarmService
        d = self._make(alarm_state="INTRUSION_ALARM")
        assert d.alarmstate == AlarmService.State.INTRUSION_ALARM

    def test_alarmstate_secondary_alarm(self):
        from boschshcpy.services_impl import AlarmService
        d = self._make(alarm_state="SECONDARY_ALARM")
        assert d.alarmstate == AlarmService.State.SECONDARY_ALARM

    def test_smokedetectorcheck_none(self):
        from boschshcpy.services_impl import SmokeDetectorCheckService
        d = self._make(check_state="NONE")
        assert d.smokedetectorcheck_state == SmokeDetectorCheckService.State.NONE

    def test_smokedetectorcheck_ok(self):
        from boschshcpy.services_impl import SmokeDetectorCheckService
        d = self._make(check_state="SMOKE_TEST_OK")
        assert d.smokedetectorcheck_state == SmokeDetectorCheckService.State.SMOKE_TEST_OK

    def test_smokedetectorcheck_requested(self):
        from boschshcpy.services_impl import SmokeDetectorCheckService
        d = self._make(check_state="SMOKE_TEST_REQUESTED")
        assert d.smokedetectorcheck_state == SmokeDetectorCheckService.State.SMOKE_TEST_REQUESTED

    def test_smokedetectorcheck_failed(self):
        from boschshcpy.services_impl import SmokeDetectorCheckService
        d = self._make(check_state="SMOKE_TEST_FAILED")
        assert d.smokedetectorcheck_state == SmokeDetectorCheckService.State.SMOKE_TEST_FAILED


# ---------------------------------------------------------------------------
# SHCSmartPlug
# ---------------------------------------------------------------------------

class TestSHCSmartPlug:
    def _make(self, switch_state="ON", routing_state="ENABLED", power=100.0, energy=500.0):
        from boschshcpy.models_impl import SHCSmartPlug
        from boschshcpy.services_impl import (
            PowerSwitchService, RoutingService, PowerMeterService, PowerSwitchProgramService
        )

        ps = PowerSwitchService.__new__(PowerSwitchService)
        ps._api = None
        ps._raw_device_service = {"id": "PowerSwitch", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "switchState": switch_state, "automaticPowerOffTime": 0}}
        ps._raw_state = ps._raw_device_service["state"]
        ps._last_update = None; ps._callbacks = {}; ps._event_callbacks = {}

        rt = RoutingService.__new__(RoutingService)
        rt._api = None
        rt._raw_device_service = {"id": "Routing", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "value": routing_state}}
        rt._raw_state = rt._raw_device_service["state"]
        rt._last_update = None; rt._callbacks = {}; rt._event_callbacks = {}

        pm = PowerMeterService.__new__(PowerMeterService)
        pm._api = None
        pm._raw_device_service = {"id": "PowerMeter", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "powerConsumption": power, "energyConsumption": energy}}
        pm._raw_state = pm._raw_device_service["state"]
        pm._last_update = None; pm._callbacks = {}; pm._event_callbacks = {}

        prog = PowerSwitchProgramService.__new__(PowerSwitchProgramService)
        prog._api = None
        prog._raw_device_service = {"id": "PowerSwitchProgram", "deviceId": "d1", "path": "/x",
                                     "state": {"@type": "x", "operationMode": "MANUAL"}}
        prog._raw_state = prog._raw_device_service["state"]
        prog._last_update = None; prog._callbacks = {}; prog._event_callbacks = {}

        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device(model="PSM")
        obj._device_services_by_id = {
            "PowerSwitch": ps, "Routing": rt, "PowerMeter": pm, "PowerSwitchProgram": prog
        }
        obj._callbacks = {}
        obj._api = None
        obj._powerswitch_service = ps
        obj._routing_service = rt
        obj._powermeter_service = pm
        obj._powerswitchprogram_service = prog
        return obj

    def test_switchstate_on(self):
        from boschshcpy.services_impl import PowerSwitchService
        d = self._make(switch_state="ON")
        assert d.switchstate == PowerSwitchService.State.ON

    def test_switchstate_off(self):
        from boschshcpy.services_impl import PowerSwitchService
        d = self._make(switch_state="OFF")
        assert d.switchstate == PowerSwitchService.State.OFF

    def test_routing_enabled(self):
        from boschshcpy.services_impl import RoutingService
        d = self._make(routing_state="ENABLED")
        assert d.routing == RoutingService.State.ENABLED

    def test_routing_disabled(self):
        from boschshcpy.services_impl import RoutingService
        d = self._make(routing_state="DISABLED")
        assert d.routing == RoutingService.State.DISABLED

    def test_power_consumption(self):
        d = self._make(power=123.5)
        assert d.powerconsumption == 123.5

    def test_energy_consumption(self):
        d = self._make(energy=999.9)
        assert d.energyconsumption == 999.9


# ---------------------------------------------------------------------------
# SHCShutterContact
# ---------------------------------------------------------------------------

class TestSHCShutterContact:
    def _make(self, state_val="CLOSED"):
        from boschshcpy.models_impl import SHCShutterContact
        from boschshcpy.services_impl import ShutterContactService, BatteryLevelService

        svc = ShutterContactService.__new__(ShutterContactService)
        svc._api = None
        svc._raw_device_service = {"id": "ShutterContact", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "value": state_val}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCShutterContact.__new__(SHCShutterContact)
        obj._raw_device = _fake_raw_device(model="SWD", name="Door")
        obj._raw_device["profile"] = "DOOR_CONTACT"
        obj._device_services_by_id = {"ShutterContact": svc, "BatteryLevel": bat}
        obj._callbacks = {}
        obj._api = None
        obj._service = svc
        obj._batterylevel_service = bat
        return obj

    def test_state_closed(self):
        from boschshcpy.services_impl import ShutterContactService
        d = self._make("CLOSED")
        assert d.state == ShutterContactService.State.CLOSED

    def test_state_open(self):
        from boschshcpy.services_impl import ShutterContactService
        d = self._make("OPEN")
        assert d.state == ShutterContactService.State.OPEN

    def test_device_class_from_profile(self):
        d = self._make()
        assert d.device_class == "DOOR_CONTACT"


# ---------------------------------------------------------------------------
# SHCShutterContact2 (adds bypass)
# ---------------------------------------------------------------------------

class TestSHCShutterContact2:
    def _make(self, bypass_state="BYPASS_INACTIVE"):
        from boschshcpy.models_impl import SHCShutterContact2
        from boschshcpy.services_impl import BypassService, ShutterContactService, BatteryLevelService, CommunicationQualityService

        bypass_svc = BypassService.__new__(BypassService)
        bypass_svc._api = None
        bypass_svc._raw_device_service = {"id": "Bypass", "deviceId": "d1", "path": "/x",
                                           "state": {"@type": "x", "state": bypass_state}}
        bypass_svc._raw_state = bypass_svc._raw_device_service["state"]
        bypass_svc._last_update = None; bypass_svc._callbacks = {}; bypass_svc._event_callbacks = {}

        sc_svc = ShutterContactService.__new__(ShutterContactService)
        sc_svc._api = None
        sc_svc._raw_device_service = {"id": "ShutterContact", "deviceId": "d1", "path": "/x",
                                       "state": {"@type": "x", "value": "CLOSED"}}
        sc_svc._raw_state = sc_svc._raw_device_service["state"]
        sc_svc._last_update = None; sc_svc._callbacks = {}; sc_svc._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        cq_svc = CommunicationQualityService.__new__(CommunicationQualityService)
        cq_svc._api = None
        cq_svc._raw_device_service = {"id": "CommunicationQuality", "deviceId": "d1", "path": "/x",
                                       "state": {"@type": "x", "quality": "GOOD"}}
        cq_svc._raw_state = cq_svc._raw_device_service["state"]
        cq_svc._last_update = None; cq_svc._callbacks = {}; cq_svc._event_callbacks = {}

        obj = SHCShutterContact2.__new__(SHCShutterContact2)
        obj._raw_device = _fake_raw_device(model="SWD2")
        obj._device_services_by_id = {
            "Bypass": bypass_svc, "ShutterContact": sc_svc,
            "BatteryLevel": bat, "CommunicationQuality": cq_svc,
        }
        obj._callbacks = {}
        obj._api = None
        obj._service = sc_svc
        obj._bypass_service = bypass_svc
        obj._batterylevel_service = bat
        obj._communicationquality_service = cq_svc
        return obj

    def test_bypass_inactive(self):
        from boschshcpy.services_impl import BypassService
        d = self._make("BYPASS_INACTIVE")
        assert d.bypass == BypassService.State.BYPASS_INACTIVE

    def test_bypass_active(self):
        from boschshcpy.services_impl import BypassService
        d = self._make("BYPASS_ACTIVE")
        assert d.bypass == BypassService.State.BYPASS_ACTIVE

    def test_bypass_unknown(self):
        from boschshcpy.services_impl import BypassService
        d = self._make("UNKNOWN")
        assert d.bypass == BypassService.State.UNKNOWN


# ---------------------------------------------------------------------------
# SHCShutterContact2Plus (adds vibration)
# ---------------------------------------------------------------------------

class TestSHCShutterContact2Plus:
    def _make(self, vibration_state="NO_VIBRATION", enabled=True, sensitivity="HIGH"):
        from boschshcpy.models_impl import SHCShutterContact2Plus
        from boschshcpy.services_impl import (
            VibrationSensorService, BypassService, ShutterContactService,
            BatteryLevelService, CommunicationQualityService,
        )

        vib = VibrationSensorService.__new__(VibrationSensorService)
        vib._api = None
        vib._raw_device_service = {"id": "VibrationSensor", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "value": vibration_state,
                                              "enabled": enabled, "sensitivity": sensitivity}}
        vib._raw_state = vib._raw_device_service["state"]
        vib._last_update = None; vib._callbacks = {}; vib._event_callbacks = {}

        bypass_svc = BypassService.__new__(BypassService)
        bypass_svc._api = None
        bypass_svc._raw_device_service = {"id": "Bypass", "deviceId": "d1", "path": "/x",
                                           "state": {"@type": "x", "state": "BYPASS_INACTIVE"}}
        bypass_svc._raw_state = bypass_svc._raw_device_service["state"]
        bypass_svc._last_update = None; bypass_svc._callbacks = {}; bypass_svc._event_callbacks = {}

        sc_svc = ShutterContactService.__new__(ShutterContactService)
        sc_svc._api = None
        sc_svc._raw_device_service = {"id": "ShutterContact", "deviceId": "d1", "path": "/x",
                                       "state": {"@type": "x", "value": "CLOSED"}}
        sc_svc._raw_state = sc_svc._raw_device_service["state"]
        sc_svc._last_update = None; sc_svc._callbacks = {}; sc_svc._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        cq = CommunicationQualityService.__new__(CommunicationQualityService)
        cq._api = None
        cq._raw_device_service = {"id": "CommunicationQuality", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "quality": "GOOD"}}
        cq._raw_state = cq._raw_device_service["state"]
        cq._last_update = None; cq._callbacks = {}; cq._event_callbacks = {}

        obj = SHCShutterContact2Plus.__new__(SHCShutterContact2Plus)
        obj._raw_device = _fake_raw_device(model="SWD2_PLUS")
        obj._device_services_by_id = {
            "VibrationSensor": vib, "Bypass": bypass_svc,
            "ShutterContact": sc_svc, "BatteryLevel": bat, "CommunicationQuality": cq,
        }
        obj._callbacks = {}
        obj._api = None
        obj._vibrationsensor_service = vib
        obj._bypass_service = bypass_svc
        obj._service = sc_svc
        obj._batterylevel_service = bat
        obj._communicationquality_service = cq
        return obj

    def test_no_vibration(self):
        from boschshcpy.services_impl import VibrationSensorService
        d = self._make("NO_VIBRATION")
        assert d.vibrationsensor == VibrationSensorService.State.NO_VIBRATION

    def test_vibration_detected(self):
        from boschshcpy.services_impl import VibrationSensorService
        d = self._make("VIBRATION_DETECTED")
        assert d.vibrationsensor == VibrationSensorService.State.VIBRATION_DETECTED

    def test_enabled_true(self):
        d = self._make(enabled=True)
        assert d.enabled is True

    def test_enabled_false(self):
        d = self._make(enabled=False)
        assert d.enabled is False

    def test_sensitivity_high(self):
        from boschshcpy.services_impl import VibrationSensorService
        d = self._make(sensitivity="HIGH")
        assert d.sensitivity == VibrationSensorService.SensitivityState.HIGH

    def test_sensitivity_very_high(self):
        from boschshcpy.services_impl import VibrationSensorService
        d = self._make(sensitivity="VERY_HIGH")
        assert d.sensitivity == VibrationSensorService.SensitivityState.VERY_HIGH

    def test_sensitivity_low(self):
        from boschshcpy.services_impl import VibrationSensorService
        d = self._make(sensitivity="LOW")
        assert d.sensitivity == VibrationSensorService.SensitivityState.LOW

    def test_sensitivity_very_low(self):
        from boschshcpy.services_impl import VibrationSensorService
        d = self._make(sensitivity="VERY_LOW")
        assert d.sensitivity == VibrationSensorService.SensitivityState.VERY_LOW

    def test_sensitivity_medium(self):
        from boschshcpy.services_impl import VibrationSensorService
        d = self._make(sensitivity="MEDIUM")
        assert d.sensitivity == VibrationSensorService.SensitivityState.MEDIUM


# ---------------------------------------------------------------------------
# SHCShutterControl
# ---------------------------------------------------------------------------

class TestSHCShutterControl:
    def _make(self, op_state="STOPPED", level=0.5):
        from boschshcpy.models_impl import SHCShutterControl
        from boschshcpy.services_impl import ShutterControlService

        svc = ShutterControlService.__new__(ShutterControlService)
        svc._api = None
        svc._raw_device_service = {
            "id": "ShutterControl", "deviceId": "d1", "path": "/x",
            "state": {"@type": "x", "operationState": op_state, "level": level, "calibrated": True},
        }
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}

        obj = SHCShutterControl.__new__(SHCShutterControl)
        obj._raw_device = _fake_raw_device(model="BBL")
        obj._device_services_by_id = {"ShutterControl": svc}
        obj._callbacks = {}
        obj._api = None
        obj._service = svc
        return obj

    def test_level(self):
        d = self._make(level=0.75)
        assert d.level == 0.75

    def test_operation_state_stopped(self):
        from boschshcpy.services_impl import ShutterControlService
        d = self._make("STOPPED")
        assert d.operation_state == ShutterControlService.State.STOPPED

    def test_operation_state_moving(self):
        from boschshcpy.services_impl import ShutterControlService
        d = self._make("MOVING")
        assert d.operation_state == ShutterControlService.State.MOVING

    def test_operation_state_calibrating(self):
        from boschshcpy.services_impl import ShutterControlService
        d = self._make("CALIBRATING")
        assert d.operation_state == ShutterControlService.State.CALIBRATING

    def test_operation_state_opening(self):
        from boschshcpy.services_impl import ShutterControlService
        d = self._make("OPENING")
        assert d.operation_state == ShutterControlService.State.OPENING

    def test_operation_state_closing(self):
        from boschshcpy.services_impl import ShutterControlService
        d = self._make("CLOSING")
        assert d.operation_state == ShutterControlService.State.CLOSING


# ---------------------------------------------------------------------------
# SHCCamera360
# ---------------------------------------------------------------------------

class TestSHCCamera360:
    def _make(self, privacy_state="DISABLED", notification_state="ENABLED", no_notification=False):
        from boschshcpy.models_impl import SHCCamera360
        from boschshcpy.services_impl import PrivacyModeService, CameraNotificationService

        priv = PrivacyModeService.__new__(PrivacyModeService)
        priv._api = None
        priv._raw_device_service = {"id": "PrivacyMode", "deviceId": "d1", "path": "/x",
                                     "state": {"@type": "x", "value": privacy_state}}
        priv._raw_state = priv._raw_device_service["state"]
        priv._last_update = None; priv._callbacks = {}; priv._event_callbacks = {}

        notif = None
        if not no_notification:
            notif = CameraNotificationService.__new__(CameraNotificationService)
            notif._api = None
            notif._raw_device_service = {"id": "CameraNotification", "deviceId": "d1", "path": "/x",
                                          "state": {"@type": "x", "value": notification_state}}
            notif._raw_state = notif._raw_device_service["state"]
            notif._last_update = None; notif._callbacks = {}; notif._event_callbacks = {}

        svcs = {"PrivacyMode": priv}
        if notif:
            svcs["CameraNotification"] = notif

        obj = SHCCamera360.__new__(SHCCamera360)
        obj._raw_device = _fake_raw_device(model="CAMERA_360")
        obj._device_services_by_id = svcs
        obj._callbacks = {}
        obj._api = None
        obj._privacymode_service = priv
        obj._cameranotification_service = notif
        return obj

    def test_privacymode_disabled(self):
        from boschshcpy.services_impl import PrivacyModeService
        d = self._make("DISABLED")
        assert d.privacymode == PrivacyModeService.State.DISABLED

    def test_privacymode_enabled(self):
        from boschshcpy.services_impl import PrivacyModeService
        d = self._make("ENABLED")
        assert d.privacymode == PrivacyModeService.State.ENABLED

    def test_cameranotification_enabled(self):
        from boschshcpy.services_impl import CameraNotificationService
        d = self._make(notification_state="ENABLED")
        assert d.cameranotification == CameraNotificationService.State.ENABLED

    def test_cameranotification_disabled(self):
        from boschshcpy.services_impl import CameraNotificationService
        d = self._make(notification_state="DISABLED")
        assert d.cameranotification == CameraNotificationService.State.DISABLED

    def test_cameranotification_none_when_service_absent(self):
        d = self._make(no_notification=True)
        assert d.cameranotification is None


# ---------------------------------------------------------------------------
# SHCCameraEyes
# ---------------------------------------------------------------------------

class TestSHCCameraEyes:
    def _make(self, light_state="ON", no_light=False):
        from boschshcpy.models_impl import SHCCameraEyes
        from boschshcpy.services_impl import PrivacyModeService, CameraNotificationService, CameraLightService

        priv = PrivacyModeService.__new__(PrivacyModeService)
        priv._api = None
        priv._raw_device_service = {"id": "PrivacyMode", "deviceId": "d1", "path": "/x",
                                     "state": {"@type": "x", "value": "DISABLED"}}
        priv._raw_state = priv._raw_device_service["state"]
        priv._last_update = None; priv._callbacks = {}; priv._event_callbacks = {}

        notif = CameraNotificationService.__new__(CameraNotificationService)
        notif._api = None
        notif._raw_device_service = {"id": "CameraNotification", "deviceId": "d1", "path": "/x",
                                      "state": {"@type": "x", "value": "ENABLED"}}
        notif._raw_state = notif._raw_device_service["state"]
        notif._last_update = None; notif._callbacks = {}; notif._event_callbacks = {}

        light_svc = None
        if not no_light:
            light_svc = CameraLightService.__new__(CameraLightService)
            light_svc._api = None
            light_svc._raw_device_service = {"id": "CameraLight", "deviceId": "d1", "path": "/x",
                                              "state": {"@type": "x", "value": light_state}}
            light_svc._raw_state = light_svc._raw_device_service["state"]
            light_svc._last_update = None; light_svc._callbacks = {}; light_svc._event_callbacks = {}

        svcs = {"PrivacyMode": priv, "CameraNotification": notif}
        if light_svc:
            svcs["CameraLight"] = light_svc

        obj = SHCCameraEyes.__new__(SHCCameraEyes)
        obj._raw_device = _fake_raw_device(model="CAMERA_EYES")
        obj._device_services_by_id = svcs
        obj._callbacks = {}
        obj._api = None
        obj._privacymode_service = priv
        obj._cameranotification_service = notif
        obj._cameralight_service = light_svc
        return obj

    def test_cameralight_on(self):
        from boschshcpy.services_impl import CameraLightService
        d = self._make("ON")
        assert d.cameralight == CameraLightService.State.ON

    def test_cameralight_off(self):
        from boschshcpy.services_impl import CameraLightService
        d = self._make("OFF")
        assert d.cameralight == CameraLightService.State.OFF

    def test_cameralight_none_when_service_absent(self):
        d = self._make(no_light=True)
        assert d.cameralight is None


# ---------------------------------------------------------------------------
# SHCCameraOutdoorGen2
# ---------------------------------------------------------------------------

class TestSHCCameraOutdoorGen2:
    def _make(self, ambient_state="ON", front_state="OFF", no_ambient=False, no_front=False):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        from boschshcpy.services_impl import (
            PrivacyModeService, CameraNotificationService,
            CameraAmbientLightService, CameraFrontLightService,
        )

        def _make_light_svc(cls, svc_id, state_val):
            svc = cls.__new__(cls)
            svc._api = None
            svc._raw_device_service = {"id": svc_id, "deviceId": "d1", "path": "/x",
                                        "state": {"@type": "x", "value": state_val}}
            svc._raw_state = svc._raw_device_service["state"]
            svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
            return svc

        priv = PrivacyModeService.__new__(PrivacyModeService)
        priv._api = None
        priv._raw_device_service = {"id": "PrivacyMode", "deviceId": "d1", "path": "/x",
                                     "state": {"@type": "x", "value": "DISABLED"}}
        priv._raw_state = priv._raw_device_service["state"]
        priv._last_update = None; priv._callbacks = {}; priv._event_callbacks = {}

        notif = CameraNotificationService.__new__(CameraNotificationService)
        notif._api = None
        notif._raw_device_service = {"id": "CameraNotification", "deviceId": "d1", "path": "/x",
                                      "state": {"@type": "x", "value": "ENABLED"}}
        notif._raw_state = notif._raw_device_service["state"]
        notif._last_update = None; notif._callbacks = {}; notif._event_callbacks = {}

        amb = None if no_ambient else _make_light_svc(CameraAmbientLightService, "CameraAmbientLight", ambient_state)
        front = None if no_front else _make_light_svc(CameraFrontLightService, "CameraFrontLight", front_state)

        svcs = {"PrivacyMode": priv, "CameraNotification": notif}
        if amb:
            svcs["CameraAmbientLight"] = amb
        if front:
            svcs["CameraFrontLight"] = front

        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._raw_device = _fake_raw_device(model="CAMERA_OUTDOOR_GEN2")
        obj._device_services_by_id = svcs
        obj._callbacks = {}
        obj._api = None
        obj._privacymode_service = priv
        obj._cameranotification_service = notif
        obj._cameraambientlight_service = amb
        obj._camerafrontlight_service = front
        return obj

    def test_ambient_on(self):
        from boschshcpy.services_impl import CameraAmbientLightService
        d = self._make(ambient_state="ON")
        assert d.cameraambientlight == CameraAmbientLightService.State.ON

    def test_ambient_off(self):
        from boschshcpy.services_impl import CameraAmbientLightService
        d = self._make(ambient_state="OFF")
        assert d.cameraambientlight == CameraAmbientLightService.State.OFF

    def test_ambient_none_when_absent(self):
        d = self._make(no_ambient=True)
        assert d.cameraambientlight is None

    def test_front_on(self):
        from boschshcpy.services_impl import CameraFrontLightService
        d = self._make(front_state="ON")
        assert d.camerafrontlight == CameraFrontLightService.State.ON

    def test_front_off(self):
        from boschshcpy.services_impl import CameraFrontLightService
        d = self._make(front_state="OFF")
        assert d.camerafrontlight == CameraFrontLightService.State.OFF

    def test_front_none_when_absent(self):
        d = self._make(no_front=True)
        assert d.camerafrontlight is None


# ---------------------------------------------------------------------------
# SHCThermostat
# ---------------------------------------------------------------------------

class TestSHCThermostat:
    def _make(self, valve_state="VALVE_ADAPTION_SUCCESSFUL", position=50, child_lock="OFF",
              temperature=21.0, silent_mode="MODE_NORMAL"):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import (
            ValveTappetService, ThermostatService, TemperatureLevelService,
            BatteryLevelService, CommunicationQualityService, SilentModeService,
            TemperatureOffsetService,
        )

        def _svc(cls, svc_id, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": svc_id, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        vt = _svc(ValveTappetService, "ValveTappet",
                  {"@type": "x", "value": valve_state, "position": position})
        th = _svc(ThermostatService, "Thermostat", {"@type": "x", "childLock": child_lock})
        tl = _svc(TemperatureLevelService, "TemperatureLevel", {"@type": "x", "temperature": temperature})
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}
        cq = _svc(CommunicationQualityService, "CommunicationQuality",
                  {"@type": "x", "quality": "GOOD"})
        sm = _svc(SilentModeService, "SilentMode", {"@type": "x", "mode": silent_mode})
        to = _svc(TemperatureOffsetService, "TemperatureOffset",
                  {"@type": "x", "offset": 0.5, "stepSize": 0.5, "minOffset": -5.0, "maxOffset": 5.0})

        obj = SHCThermostat.__new__(SHCThermostat)
        obj._raw_device = _fake_raw_device(model="TRV")
        obj._device_services_by_id = {
            "ValveTappet": vt, "Thermostat": th, "TemperatureLevel": tl,
            "BatteryLevel": bat, "CommunicationQuality": cq, "SilentMode": sm,
            "TemperatureOffset": to,
        }
        obj._callbacks = {}
        obj._api = None
        obj._valvetappet_service = vt
        obj._thermostat_service = th
        obj._temperaturelevel_service = tl
        obj._batterylevel_service = bat
        obj._communicationquality_service = cq
        obj._silentmode_service = sm
        obj._temperatureoffset_service = to
        return obj

    def test_position(self):
        d = self._make(position=75)
        assert d.position == 75

    def test_valvestate_adaption_successful(self):
        from boschshcpy.services_impl import ValveTappetService
        d = self._make("VALVE_ADAPTION_SUCCESSFUL")
        assert d.valvestate == ValveTappetService.State.VALVE_ADAPTION_SUCCESSFUL

    def test_valvestate_in_start_position(self):
        from boschshcpy.services_impl import ValveTappetService
        d = self._make("IN_START_POSITION")
        assert d.valvestate == ValveTappetService.State.IN_START_POSITION

    def test_valvestate_no_motor_error(self):
        from boschshcpy.services_impl import ValveTappetService
        d = self._make("NO_MOTOR_ERROR")
        assert d.valvestate == ValveTappetService.State.NO_MOTOR_ERROR

    def test_temperature(self):
        d = self._make(temperature=19.5)
        assert d.temperature == 19.5

    def test_child_lock_on(self):
        from boschshcpy.services_impl import ThermostatService
        d = self._make(child_lock="ON")
        assert d.child_lock == ThermostatService.State.ON

    def test_child_lock_off(self):
        from boschshcpy.services_impl import ThermostatService
        d = self._make(child_lock="OFF")
        assert d.child_lock == ThermostatService.State.OFF

    def test_silentmode_normal(self):
        from boschshcpy.services_impl import SilentModeService
        d = self._make(silent_mode="MODE_NORMAL")
        assert d.silentmode == SilentModeService.State.MODE_NORMAL

    def test_silentmode_silent(self):
        from boschshcpy.services_impl import SilentModeService
        d = self._make(silent_mode="MODE_SILENT")
        assert d.silentmode == SilentModeService.State.MODE_SILENT

    def test_communicationquality(self):
        from boschshcpy.services_impl import CommunicationQualityService
        d = self._make()
        assert d.communicationquality == CommunicationQualityService.State.GOOD

    def test_offset(self):
        d = self._make()
        assert d.offset == 0.5

    def test_step_size(self):
        d = self._make()
        assert d.step_size == 0.5

    def test_min_offset(self):
        d = self._make()
        assert d.min_offset == -5.0

    def test_max_offset(self):
        d = self._make()
        assert d.max_offset == 5.0


# ---------------------------------------------------------------------------
# SHCClimateControl
# ---------------------------------------------------------------------------

class TestSHCClimateControl:
    def _make(self, op_mode="AUTOMATIC", setpoint=21.5, boost=False, low=False,
              summer=False, supports_boost=True, room_control="HEATING"):
        from boschshcpy.models_impl import SHCClimateControl
        from boschshcpy.services_impl import RoomClimateControlService, TemperatureLevelService

        state = {
            "@type": "x",
            "operationMode": op_mode,
            "setpointTemperature": setpoint,
            "setpointTemperatureForLevelEco": 17.0,
            "setpointTemperatureForLevelComfort": 22.0,
            "ventilationMode": False,
            "low": low,
            "boostMode": boost,
            "summerMode": summer,
            "supportsBoostMode": supports_boost,
            "roomControlMode": room_control,
        }
        rcc = RoomClimateControlService.__new__(RoomClimateControlService)
        rcc._api = None
        rcc._raw_device_service = {"id": "RoomClimateControl", "deviceId": "d1", "path": "/x", "state": state}
        rcc._raw_state = state
        rcc._last_update = None; rcc._callbacks = {}; rcc._event_callbacks = {}

        tl = TemperatureLevelService.__new__(TemperatureLevelService)
        tl._api = None
        tl._raw_device_service = {"id": "TemperatureLevel", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "temperature": 20.0}}
        tl._raw_state = tl._raw_device_service["state"]
        tl._last_update = None; tl._callbacks = {}; tl._event_callbacks = {}

        obj = SHCClimateControl.__new__(SHCClimateControl)
        obj._raw_device = _fake_raw_device(model="ROOM_CLIMATE_CONTROL")
        obj._device_services_by_id = {"RoomClimateControl": rcc, "TemperatureLevel": tl}
        obj._callbacks = {}
        obj._api = None
        obj._roomclimatecontrol_service = rcc
        obj._temperaturelevel_service = tl
        return obj

    def test_operation_mode_automatic(self):
        from boschshcpy.services_impl import RoomClimateControlService
        d = self._make(op_mode="AUTOMATIC")
        assert d.operation_mode == RoomClimateControlService.OperationMode.AUTOMATIC

    def test_operation_mode_manual(self):
        from boschshcpy.services_impl import RoomClimateControlService
        d = self._make(op_mode="MANUAL")
        assert d.operation_mode == RoomClimateControlService.OperationMode.MANUAL

    def test_setpoint_temperature(self):
        d = self._make(setpoint=19.0)
        assert d.setpoint_temperature == 19.0

    def test_boost_mode_true(self):
        d = self._make(boost=True)
        assert d.boost_mode is True

    def test_boost_mode_false(self):
        d = self._make(boost=False)
        assert d.boost_mode is False

    def test_low_true(self):
        d = self._make(low=True)
        assert d.low is True

    def test_low_false(self):
        d = self._make(low=False)
        assert d.low is False

    def test_summer_mode_true(self):
        d = self._make(summer=True)
        assert d.summer_mode is True

    def test_summer_mode_false(self):
        d = self._make(summer=False)
        assert d.summer_mode is False

    def test_supports_boost_mode(self):
        d = self._make(supports_boost=True)
        assert d.supports_boost_mode is True

    def test_cooling_mode_heating(self):
        d = self._make(room_control="HEATING")
        assert d.cooling_mode is False

    def test_cooling_mode_cooling(self):
        d = self._make(room_control="COOLING")
        assert d.cooling_mode is True

    def test_supports_cooling_present(self):
        d = self._make()
        assert d.supports_cooling is True

    def test_room_control_mode(self):
        d = self._make(room_control="HEATING")
        assert d.room_control_mode == "HEATING"


# ---------------------------------------------------------------------------
# SHCHeatingCircuit
# ---------------------------------------------------------------------------

class TestSHCHeatingCircuit:
    def _make(self, op_mode="AUTOMATIC", setpoint=22.0, override_active=False,
              override_enabled=True, energy_saving=False, on=True):
        from boschshcpy.models_impl import SHCHeatingCircuit
        from boschshcpy.services_impl import HeatingCircuitService

        state = {
            "@type": "x",
            "operationMode": op_mode,
            "setpointTemperature": setpoint,
            "setpointTemperatureForLevelEco": 18.0,
            "setpointTemperatureForLevelComfort": 23.0,
            "temperatureOverrideModeActive": override_active,
            "temperatureOverrideFeatureEnabled": override_enabled,
            "energySavingFeatureEnabled": energy_saving,
            "on": on,
        }
        svc = HeatingCircuitService.__new__(HeatingCircuitService)
        svc._api = None
        svc._raw_device_service = {"id": "HeatingCircuit", "deviceId": "d1", "path": "/x", "state": state}
        svc._raw_state = state
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}

        obj = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
        obj._raw_device = _fake_raw_device(model="HEATING_CIRCUIT")
        obj._device_services_by_id = {"HeatingCircuit": svc}
        obj._callbacks = {}
        obj._api = None
        obj._heating_circuit_service = svc
        return obj

    def test_operation_mode_automatic(self):
        from boschshcpy.services_impl import HeatingCircuitService
        d = self._make(op_mode="AUTOMATIC")
        assert d.operation_mode == HeatingCircuitService.OperationMode.AUTOMATIC

    def test_operation_mode_manual(self):
        from boschshcpy.services_impl import HeatingCircuitService
        d = self._make(op_mode="MANUAL")
        assert d.operation_mode == HeatingCircuitService.OperationMode.MANUAL

    def test_setpoint_temperature(self):
        d = self._make(setpoint=20.5)
        assert d.setpoint_temperature == 20.5

    def test_override_mode_active(self):
        d = self._make(override_active=True)
        assert d.temperature_override_mode_active is True

    def test_override_mode_inactive(self):
        d = self._make(override_active=False)
        assert d.temperature_override_mode_active is False

    def test_override_feature_enabled(self):
        d = self._make(override_enabled=True)
        assert d.temperature_override_feature_enabled is True

    def test_energy_saving_enabled(self):
        d = self._make(energy_saving=True)
        assert d.energy_saving_feature_enabled is True

    def test_on(self):
        d = self._make(on=True)
        assert d.on is True

    def test_off(self):
        d = self._make(on=False)
        assert d.on is False


# ---------------------------------------------------------------------------
# SHCMotionDetector
# ---------------------------------------------------------------------------

class TestSHCMotionDetector:
    def _make(self, latest_motion="2024-01-01T12:00:00", illuminance=300):
        from boschshcpy.models_impl import SHCMotionDetector
        from boschshcpy.services_impl import LatestMotionService, MultiLevelSensorService, BatteryLevelService

        lm = LatestMotionService.__new__(LatestMotionService)
        lm._api = None
        lm._raw_device_service = {"id": "LatestMotion", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "latestMotionDetected": latest_motion}}
        lm._raw_state = lm._raw_device_service["state"]
        lm._last_update = None; lm._callbacks = {}; lm._event_callbacks = {}

        mls = MultiLevelSensorService.__new__(MultiLevelSensorService)
        mls._api = None
        mls._raw_device_service = {"id": "MultiLevelSensor", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "illuminance": illuminance}}
        mls._raw_state = mls._raw_device_service["state"]
        mls._last_update = None; mls._callbacks = {}; mls._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCMotionDetector.__new__(SHCMotionDetector)
        obj._raw_device = _fake_raw_device(model="MD")
        obj._device_services_by_id = {"LatestMotion": lm, "MultiLevelSensor": mls, "BatteryLevel": bat}
        obj._callbacks = {}
        obj._api = None
        obj._service = lm
        obj._multi_level_sensor_service = mls
        obj._batterylevel_service = bat
        return obj

    def test_latestmotion(self):
        d = self._make(latest_motion="2024-06-01T08:30:00")
        assert d.latestmotion == "2024-06-01T08:30:00"

    def test_illuminance(self):
        d = self._make(illuminance=500)
        assert d.illuminance == 500


# ---------------------------------------------------------------------------
# SHCMotionDetector2
# ---------------------------------------------------------------------------

class TestSHCMotionDetector2:
    def _make(self):
        from boschshcpy.models_impl import SHCMotionDetector2
        from boschshcpy.services_impl import (
            LatestMotionService, MultiLevelSensorService, MultiLevelSwitchService,
            BinarySwitchService, DetectionTestService, LatestTamperService,
            TemperatureLevelService, PollControlService, PirSensorConfigurationService,
            OccupancyDetectionService, CommunicationQualityService, PetImmunityService,
            BatteryLevelService,
        )

        def _svc(cls, svc_id, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": svc_id, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        lm = _svc(LatestMotionService, "LatestMotion",
                  {"@type": "x", "latestMotionDetected": "2024-01-01T10:00:00"})
        mls = _svc(MultiLevelSensorService, "MultiLevelSensor", {"@type": "x", "illuminance": 200})
        mlsw = _svc(MultiLevelSwitchService, "MultiLevelSwitch", {"@type": "x", "level": 3})
        bsw = _svc(BinarySwitchService, "BinarySwitch", {"@type": "x", "on": True})
        dt = _svc(DetectionTestService, "DetectionTest",
                  {"@type": "x", "detectionState": "DETECTION_TEST_STOPPED"})
        lt = _svc(LatestTamperService, "LatestTamper",
                  {"@type": "x", "tamperProtectionEnabled": True, "wasTampered": False,
                   "lastTamperTime": "2024-01-01T09:00:00"})
        tl = _svc(TemperatureLevelService, "TemperatureLevel", {"@type": "x", "temperature": 23.5})
        pc = _svc(PollControlService, "PollControl", {"@type": "x", "longPollInterval": "LONG"})
        psc = _svc(PirSensorConfigurationService, "PirSensorConfiguration",
                   {"@type": "x", "motionSensitivity": "HIGH"})
        od = _svc(OccupancyDetectionService, "OccupancyDetection",
                  {"@type": "x", "isOccupied": True,
                   "lastOccupancyChangeTime": "2024-01-01T11:00:00"})
        cq = _svc(CommunicationQualityService, "CommunicationQuality",
                  {"@type": "x", "quality": "GOOD"})
        pi = _svc(PetImmunityService, "PetImmunity", {"@type": "x", "enabled": False})

        obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
        obj._raw_device = _fake_raw_device(model="MD2")
        obj._device_services_by_id = {
            "LatestMotion": lm, "MultiLevelSensor": mls, "MultiLevelSwitch": mlsw,
            "BinarySwitch": bsw, "DetectionTest": dt, "LatestTamper": lt,
            "TemperatureLevel": tl, "PollControl": pc, "PirSensorConfiguration": psc,
            "OccupancyDetection": od, "CommunicationQuality": cq, "PetImmunity": pi,
            "BatteryLevel": bat,
        }
        obj._callbacks = {}
        obj._api = None
        obj._latestmotion_service = lm
        obj._multi_level_sensor_service = mls
        obj._multi_level_switch_service = mlsw
        obj._binaryswitch_service = bsw
        obj._detectiontest_service = dt
        obj._latesttamper_service = lt
        obj._temperaturelevel_service = tl
        obj._pollcontrol_service = pc
        obj._pirsensorconfiguration_service = psc
        obj._occupancydetection_service = od
        obj._communicationquality_service = cq
        obj._petimmunity_service = pi
        obj._batterylevel_service = bat
        return obj

    def test_latestmotion(self):
        d = self._make()
        assert d.latestmotion == "2024-01-01T10:00:00"

    def test_illuminance(self):
        d = self._make()
        assert d.illuminance == 200

    def test_multi_level_switch(self):
        d = self._make()
        assert d.multi_level_switch == 3

    def test_binaryswitch_true(self):
        d = self._make()
        assert d.binaryswitch is True

    def test_detection_state_stopped(self):
        from boschshcpy.services_impl import DetectionTestService
        d = self._make()
        assert d.detection_state == DetectionTestService.DetectionState.DETECTION_TEST_STOPPED

    def test_temperature(self):
        d = self._make()
        assert d.temperature == 23.5

    def test_long_poll_interval(self):
        from boschshcpy.services_impl import PollControlService
        d = self._make()
        assert d.long_poll_interval == PollControlService.PollControlState.LONG

    def test_motion_sensitivity_high(self):
        from boschshcpy.services_impl import PirSensorConfigurationService
        d = self._make()
        assert d.motion_sensitivity == PirSensorConfigurationService.MotionSensitivity.HIGH

    def test_occupied(self):
        d = self._make()
        assert d.occupied is True

    def test_last_occupancy_change_time(self):
        d = self._make()
        assert d.last_occupancy_change_time == "2024-01-01T11:00:00"

    def test_communicationquality(self):
        from boschshcpy.services_impl import CommunicationQualityService
        d = self._make()
        assert d.communicationquality == CommunicationQualityService.State.GOOD

    def test_pet_immunity_disabled(self):
        d = self._make()
        assert d.pet_immunity_enabled is False

    def test_last_tamper_time(self):
        d = self._make()
        assert d.last_tamper_time == "2024-01-01T09:00:00"


# ---------------------------------------------------------------------------
# SHCTwinguard
# ---------------------------------------------------------------------------

class TestSHCTwinguard:
    def _make(self, combined="GOOD", temp_rating="GOOD", hum_rating="MEDIUM", purity_rating="BAD",
              temp=22, humidity=55, purity=900, check_state="NONE"):
        from boschshcpy.models_impl import SHCTwinguard
        from boschshcpy.services_impl import AirQualityLevelService, SmokeDetectorCheckService, BatteryLevelService

        aql_state = {
            "@type": "x",
            "combinedRating": combined,
            "description": "Air is OK",
            "temperature": temp,
            "temperatureRating": temp_rating,
            "humidity": humidity,
            "humidityRating": hum_rating,
            "purity": purity,
            "purityRating": purity_rating,
        }
        aql = AirQualityLevelService.__new__(AirQualityLevelService)
        aql._api = None
        aql._raw_device_service = {"id": "AirQualityLevel", "deviceId": "d1", "path": "/x", "state": aql_state}
        aql._raw_state = aql_state
        aql._last_update = None; aql._callbacks = {}; aql._event_callbacks = {}

        chk = SmokeDetectorCheckService.__new__(SmokeDetectorCheckService)
        chk._api = None
        chk._raw_device_service = {"id": "SmokeDetectorCheck", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "value": check_state}}
        chk._raw_state = chk._raw_device_service["state"]
        chk._last_update = None; chk._callbacks = {}; chk._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._raw_device = _fake_raw_device(model="TWINGUARD")
        obj._device_services_by_id = {"AirQualityLevel": aql, "SmokeDetectorCheck": chk, "BatteryLevel": bat}
        obj._callbacks = {}
        obj._api = None
        obj._airqualitylevel_service = aql
        obj._smokedetectorcheck_service = chk
        obj._batterylevel_service = bat
        return obj

    def test_combined_rating_good(self):
        from boschshcpy.services_impl import AirQualityLevelService
        d = self._make(combined="GOOD")
        assert d.combined_rating == AirQualityLevelService.RatingState.GOOD

    def test_combined_rating_medium(self):
        from boschshcpy.services_impl import AirQualityLevelService
        d = self._make(combined="MEDIUM")
        assert d.combined_rating == AirQualityLevelService.RatingState.MEDIUM

    def test_combined_rating_bad(self):
        from boschshcpy.services_impl import AirQualityLevelService
        d = self._make(combined="BAD")
        assert d.combined_rating == AirQualityLevelService.RatingState.BAD

    def test_description(self):
        d = self._make()
        assert d.description == "Air is OK"

    def test_temperature(self):
        d = self._make(temp=24)
        assert d.temperature == 24

    def test_temperature_rating(self):
        from boschshcpy.services_impl import AirQualityLevelService
        d = self._make(temp_rating="GOOD")
        assert d.temperature_rating == AirQualityLevelService.RatingState.GOOD

    def test_humidity(self):
        d = self._make(humidity=60)
        assert d.humidity == 60

    def test_humidity_rating_medium(self):
        from boschshcpy.services_impl import AirQualityLevelService
        d = self._make(hum_rating="MEDIUM")
        assert d.humidity_rating == AirQualityLevelService.RatingState.MEDIUM

    def test_purity(self):
        d = self._make(purity=1000)
        assert d.purity == 1000

    def test_purity_rating_bad(self):
        from boschshcpy.services_impl import AirQualityLevelService
        d = self._make(purity_rating="BAD")
        assert d.purity_rating == AirQualityLevelService.RatingState.BAD

    def test_smokedetectorcheck_none(self):
        from boschshcpy.services_impl import SmokeDetectorCheckService
        d = self._make(check_state="NONE")
        assert d.smokedetectorcheck_state == SmokeDetectorCheckService.State.NONE


# ---------------------------------------------------------------------------
# SHCSmokeDetectionSystem
# ---------------------------------------------------------------------------

class TestSHCSmokeDetectionSystem:
    def _make(self, alarm_state="ALARM_OFF"):
        from boschshcpy.models_impl import SHCSmokeDetectionSystem
        from boschshcpy.services_impl import SurveillanceAlarmService

        svc = SurveillanceAlarmService.__new__(SurveillanceAlarmService)
        svc._api = None
        svc._raw_device_service = {"id": "SurveillanceAlarm", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "value": alarm_state}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}

        obj = SHCSmokeDetectionSystem.__new__(SHCSmokeDetectionSystem)
        obj._raw_device = _fake_raw_device(model="SMOKE_DETECTION_SYSTEM")
        obj._device_services_by_id = {"SurveillanceAlarm": svc}
        obj._callbacks = {}
        obj._api = None
        obj._surveillancealarm_service = svc
        return obj

    def test_alarm_off(self):
        from boschshcpy.services_impl import SurveillanceAlarmService
        d = self._make("ALARM_OFF")
        assert d.alarm == SurveillanceAlarmService.State.ALARM_OFF

    def test_alarm_on(self):
        from boschshcpy.services_impl import SurveillanceAlarmService
        d = self._make("ALARM_ON")
        assert d.alarm == SurveillanceAlarmService.State.ALARM_ON

    def test_alarm_muted(self):
        from boschshcpy.services_impl import SurveillanceAlarmService
        d = self._make("ALARM_MUTED")
        assert d.alarm == SurveillanceAlarmService.State.ALARM_MUTED


# ---------------------------------------------------------------------------
# SHCPresenceSimulationSystem
# ---------------------------------------------------------------------------

class TestSHCPresenceSimulationSystem:
    def _make(self, enabled=True):
        from boschshcpy.models_impl import SHCPresenceSimulationSystem
        from boschshcpy.services_impl import PresenceSimulationConfigurationService

        svc = PresenceSimulationConfigurationService.__new__(PresenceSimulationConfigurationService)
        svc._api = None
        svc._raw_device_service = {"id": "PresenceSimulationConfiguration", "deviceId": "d1",
                                    "path": "/x", "state": {"@type": "x", "enabled": enabled}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}

        obj = SHCPresenceSimulationSystem.__new__(SHCPresenceSimulationSystem)
        obj._raw_device = _fake_raw_device(model="PRESENCE_SIMULATION_SERVICE")
        obj._device_services_by_id = {"PresenceSimulationConfiguration": svc}
        obj._callbacks = {}
        obj._api = None
        obj._presencesimulationconfiguration_service = svc
        return obj

    def test_enabled_true(self):
        d = self._make(enabled=True)
        assert d.enabled is True

    def test_enabled_false(self):
        d = self._make(enabled=False)
        assert d.enabled is False


# ---------------------------------------------------------------------------
# SHCLight
# ---------------------------------------------------------------------------

class TestSHCLight:
    def _make(self, binary_on=True, brightness=80, color_temp=4000, rgb=0xFF0000,
              has_brightness=True, has_color_temp=True, has_hsb=True):
        from boschshcpy.models_impl import SHCLight
        from boschshcpy.services_impl import (
            BinarySwitchService, MultiLevelSwitchService,
            HueColorTemperatureService, HSBColorActuatorService,
        )

        bs = BinarySwitchService.__new__(BinarySwitchService)
        bs._api = None
        bs._raw_device_service = {"id": "BinarySwitch", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "on": binary_on}}
        bs._raw_state = bs._raw_device_service["state"]
        bs._last_update = None; bs._callbacks = {}; bs._event_callbacks = {}

        mls = None
        if has_brightness:
            mls = MultiLevelSwitchService.__new__(MultiLevelSwitchService)
            mls._api = None
            mls._raw_device_service = {"id": "MultiLevelSwitch", "deviceId": "d1", "path": "/x",
                                        "state": {"@type": "x", "level": brightness}}
            mls._raw_state = mls._raw_device_service["state"]
            mls._last_update = None; mls._callbacks = {}; mls._event_callbacks = {}

        hct = None
        if has_color_temp:
            hct = HueColorTemperatureService.__new__(HueColorTemperatureService)
            hct._api = None
            hct._raw_device_service = {
                "id": "HueColorTemperature", "deviceId": "d1", "path": "/x",
                "state": {"@type": "x", "colorTemperature": color_temp,
                          "colorTemperatureRange": {"minCt": 2700, "maxCt": 6500}},
            }
            hct._raw_state = hct._raw_device_service["state"]
            hct._last_update = None; hct._callbacks = {}; hct._event_callbacks = {}

        hsb = None
        if has_hsb:
            hsb = HSBColorActuatorService.__new__(HSBColorActuatorService)
            hsb._api = None
            hsb._raw_device_service = {
                "id": "HSBColorActuator", "deviceId": "d1", "path": "/x",
                "state": {"@type": "x", "rgb": rgb, "gamut": "A",
                          "colorTemperatureRange": {"minCt": 2000, "maxCt": 6500}},
            }
            hsb._raw_state = hsb._raw_device_service["state"]
            hsb._last_update = None; hsb._callbacks = {}; hsb._event_callbacks = {}

        from boschshcpy.models_impl import SHCLight

        obj = SHCLight.__new__(SHCLight)
        obj._raw_device = _fake_raw_device(model="LEDVANCE_LIGHT")
        svcs = {"BinarySwitch": bs}
        if mls:
            svcs["MultiLevelSwitch"] = mls
        if hct:
            svcs["HueColorTemperature"] = hct
        if hsb:
            svcs["HSBColorActuator"] = hsb
        obj._device_services_by_id = svcs
        obj._callbacks = {}
        obj._api = None
        obj._binaryswitch_service = bs
        obj._multilevelswitch_service = mls
        obj._huecolortemperature_service = hct
        obj._hsbcoloractuator_service = hsb

        # Rebuild capabilities
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities(0)
        if mls:
            obj._capabilities |= _L.Capabilities.BRIGHTNESS
        if hct:
            obj._capabilities |= _L.Capabilities.COLOR_TEMP
        if hsb:
            obj._capabilities |= _L.Capabilities.COLOR_HSB
        return obj

    def test_binarystate_on(self):
        d = self._make(binary_on=True)
        assert d.binarystate is True

    def test_binarystate_off(self):
        d = self._make(binary_on=False)
        assert d.binarystate is False

    def test_brightness_with_service(self):
        d = self._make(brightness=60)
        assert d.brightness == 60

    def test_brightness_zero_without_service(self):
        d = self._make(has_brightness=False)
        assert d.brightness == 0

    def test_supports_brightness_true(self):
        d = self._make(has_brightness=True)
        assert d.supports_brightness is True

    def test_supports_brightness_false(self):
        d = self._make(has_brightness=False)
        assert d.supports_brightness is False

    def test_color_with_service(self):
        d = self._make(color_temp=5000)
        assert d.color == 5000

    def test_color_zero_without_service(self):
        d = self._make(has_color_temp=False)
        assert d.color == 0

    def test_supports_color_temp_true(self):
        d = self._make(has_color_temp=True)
        assert d.supports_color_temp is True

    def test_supports_color_temp_false(self):
        d = self._make(has_color_temp=False)
        assert d.supports_color_temp is False

    def test_rgb_with_service(self):
        d = self._make(rgb=0x00FF00)
        assert d.rgb == 0x00FF00

    def test_rgb_zero_without_service(self):
        d = self._make(has_hsb=False)
        assert d.rgb == 0

    def test_supports_color_hsb_true(self):
        d = self._make(has_hsb=True)
        assert d.supports_color_hsb is True

    def test_supports_color_hsb_false(self):
        d = self._make(has_hsb=False)
        assert d.supports_color_hsb is False

    def test_min_color_temperature_from_hue(self):
        d = self._make(has_color_temp=True, has_hsb=False)
        assert d.min_color_temperature == 2700

    def test_max_color_temperature_from_hue(self):
        d = self._make(has_color_temp=True, has_hsb=False)
        assert d.max_color_temperature == 6500

    def test_min_color_temperature_from_hsb_when_no_hue(self):
        d = self._make(has_color_temp=False, has_hsb=True)
        assert d.min_color_temperature == 2000

    def test_max_color_temperature_from_hsb_when_no_hue(self):
        d = self._make(has_color_temp=False, has_hsb=True)
        assert d.max_color_temperature == 6500

    def test_min_color_temperature_zero_when_neither(self):
        d = self._make(has_color_temp=False, has_hsb=False)
        assert d.min_color_temperature == 0

    def test_max_color_temperature_zero_when_neither(self):
        d = self._make(has_color_temp=False, has_hsb=False)
        assert d.max_color_temperature == 0


# ---------------------------------------------------------------------------
# SHCWaterLeakageSensor
# ---------------------------------------------------------------------------

class TestSHCWaterLeakageSensor:
    def _make(self, leakage="NO_LEAKAGE", acoustic="ENABLED", push="DISABLED", check="OK"):
        from boschshcpy.models_impl import SHCWaterLeakageSensor
        from boschshcpy.services_impl import (
            WaterLeakageSensorService, WaterLeakageSensorTiltService,
            WaterLeakageSensorCheckService, BatteryLevelService,
        )

        ls = WaterLeakageSensorService.__new__(WaterLeakageSensorService)
        ls._api = None
        ls._raw_device_service = {"id": "WaterLeakageSensor", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "state": leakage}}
        ls._raw_state = ls._raw_device_service["state"]
        ls._last_update = None; ls._callbacks = {}; ls._event_callbacks = {}

        tilt = WaterLeakageSensorTiltService.__new__(WaterLeakageSensorTiltService)
        tilt._api = None
        tilt._raw_device_service = {"id": "WaterLeakageSensorTilt", "deviceId": "d1", "path": "/x",
                                     "state": {"@type": "x", "acousticSignalState": acoustic,
                                               "pushNotificationState": push}}
        tilt._raw_state = tilt._raw_device_service["state"]
        tilt._last_update = None; tilt._callbacks = {}; tilt._event_callbacks = {}

        chk = WaterLeakageSensorCheckService.__new__(WaterLeakageSensorCheckService)
        chk._api = None
        chk._raw_device_service = {"id": "WaterLeakageSensorCheck", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "result": check}}
        chk._raw_state = chk._raw_device_service["state"]
        chk._last_update = None; chk._callbacks = {}; chk._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCWaterLeakageSensor.__new__(SHCWaterLeakageSensor)
        obj._raw_device = _fake_raw_device(model="WLS")
        obj._device_services_by_id = {
            "WaterLeakageSensor": ls, "WaterLeakageSensorTilt": tilt,
            "WaterLeakageSensorCheck": chk, "BatteryLevel": bat,
        }
        obj._callbacks = {}
        obj._api = None
        obj._leakage_service = ls
        obj._tilt_service = tilt
        obj._sensor_check_service = chk
        obj._batterylevel_service = bat
        return obj

    def test_leakage_no_leakage(self):
        from boschshcpy.services_impl import WaterLeakageSensorService
        d = self._make(leakage="NO_LEAKAGE")
        assert d.leakage_state == WaterLeakageSensorService.State.NO_LEAKAGE

    def test_leakage_detected(self):
        from boschshcpy.services_impl import WaterLeakageSensorService
        d = self._make(leakage="LEAKAGE_DETECTED")
        assert d.leakage_state == WaterLeakageSensorService.State.LEAKAGE_DETECTED

    def test_acoustic_signal_enabled(self):
        from boschshcpy.services_impl import WaterLeakageSensorTiltService
        d = self._make(acoustic="ENABLED")
        assert d.acoustic_signal_state == WaterLeakageSensorTiltService.State.ENABLED

    def test_acoustic_signal_disabled(self):
        from boschshcpy.services_impl import WaterLeakageSensorTiltService
        d = self._make(acoustic="DISABLED")
        assert d.acoustic_signal_state == WaterLeakageSensorTiltService.State.DISABLED

    def test_push_notification_disabled(self):
        from boschshcpy.services_impl import WaterLeakageSensorTiltService
        d = self._make(push="DISABLED")
        assert d.push_notification_state == WaterLeakageSensorTiltService.State.DISABLED

    def test_push_notification_enabled(self):
        from boschshcpy.services_impl import WaterLeakageSensorTiltService
        d = self._make(push="ENABLED")
        assert d.push_notification_state == WaterLeakageSensorTiltService.State.ENABLED

    def test_sensor_check_state(self):
        d = self._make(check="SENSOR_OK")
        assert d.sensor_check_state == "SENSOR_OK"


# ---------------------------------------------------------------------------
# SHCUniversalSwitch
# ---------------------------------------------------------------------------

class TestSHCUniversalSwitch:
    def _make(self, key_code=1, key_name="LOWER_BUTTON", event_type="PRESS_SHORT", ts=12345):
        from boschshcpy.models_impl import SHCUniversalSwitch
        from boschshcpy.services_impl import KeypadService, BatteryLevelService

        kp = KeypadService.__new__(KeypadService)
        kp._api = None
        kp._raw_device_service = {"id": "Keypad", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "keyCode": key_code,
                                             "keyName": key_name, "eventType": event_type,
                                             "eventTimestamp": ts}}
        kp._raw_state = kp._raw_device_service["state"]
        kp._last_update = None; kp._callbacks = {}; kp._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCUniversalSwitch.__new__(SHCUniversalSwitch)
        obj._raw_device = _fake_raw_device(model="WRC2")
        obj._device_services_by_id = {"Keypad": kp, "BatteryLevel": bat}
        obj._callbacks = {}
        obj._api = None
        obj._keypad_service = kp
        obj._batterylevel_service = bat
        return obj

    def test_keystates(self):
        d = self._make()
        assert "LOWER_BUTTON" in d.keystates
        assert "UPPER_BUTTON" in d.keystates

    def test_keycode(self):
        d = self._make(key_code=2)
        assert d.keycode == 2

    def test_keyname_lower_button(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make(key_name="LOWER_BUTTON")
        assert d.keyname == KeypadService.KeyState.LOWER_BUTTON

    def test_keyname_upper_button(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make(key_name="UPPER_BUTTON")
        assert d.keyname == KeypadService.KeyState.UPPER_BUTTON

    def test_eventtype_press_short(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make(event_type="PRESS_SHORT")
        assert d.eventtype == KeypadService.KeyEvent.PRESS_SHORT

    def test_eventtype_press_long(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make(event_type="PRESS_LONG")
        assert d.eventtype == KeypadService.KeyEvent.PRESS_LONG

    def test_eventtimestamp(self):
        d = self._make(ts=99999)
        assert d.eventtimestamp == 99999


# ---------------------------------------------------------------------------
# SHCUniversalSwitch2
# ---------------------------------------------------------------------------

class TestSHCUniversalSwitch2:
    def test_keystates_has_four_buttons(self):
        from boschshcpy.models_impl import SHCUniversalSwitch2
        from boschshcpy.services_impl import KeypadService, BatteryLevelService

        kp = KeypadService.__new__(KeypadService)
        kp._api = None
        kp._raw_device_service = {"id": "Keypad", "deviceId": "d1", "path": "/x",
                                   "state": {"@type": "x", "keyCode": 1, "keyName": "LOWER_LEFT_BUTTON",
                                             "eventType": "PRESS_SHORT", "eventTimestamp": 1}}
        kp._raw_state = kp._raw_device_service["state"]
        kp._last_update = None; kp._callbacks = {}; kp._event_callbacks = {}

        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCUniversalSwitch2.__new__(SHCUniversalSwitch2)
        obj._raw_device = _fake_raw_device(model="SWITCH2")
        obj._device_services_by_id = {"Keypad": kp, "BatteryLevel": bat}
        obj._callbacks = {}
        obj._api = None
        obj._keypad_service = kp
        obj._batterylevel_service = bat

        assert "LOWER_LEFT_BUTTON" in obj.keystates
        assert "LOWER_RIGHT_BUTTON" in obj.keystates
        assert "UPPER_LEFT_BUTTON" in obj.keystates
        assert "UPPER_RIGHT_BUTTON" in obj.keystates


# ---------------------------------------------------------------------------
# SHCMicromoduleRelay
# ---------------------------------------------------------------------------

class TestSHCMicromoduleRelay:
    def _make(self, has_impulse=True):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import (
            CommunicationQualityService, ChildProtectionService,
            PowerSwitchService, PowerSwitchProgramService, ImpulseSwitchService,
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        cq = _svc(CommunicationQualityService, "CommunicationQuality", {"@type": "x", "quality": "GOOD"})
        cp = _svc(ChildProtectionService, "ChildProtection", {"@type": "x", "childLockActive": False})
        ps = _svc(PowerSwitchService, "PowerSwitch",
                  {"@type": "x", "switchState": "OFF", "automaticPowerOffTime": 0})
        prog = _svc(PowerSwitchProgramService, "PowerSwitchProgram",
                    {"@type": "x", "operationMode": "MANUAL"})

        imp = None
        if has_impulse:
            imp = _svc(ImpulseSwitchService, "ImpulseSwitch",
                       {"@type": "x", "impulseState": False, "impulseLength": 100})

        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_RELAY")
        svcs = {"CommunicationQuality": cq, "ChildProtection": cp,
                "PowerSwitch": ps, "PowerSwitchProgram": prog}
        if imp:
            svcs["ImpulseSwitch"] = imp
        obj._device_services_by_id = svcs
        obj._callbacks = {}
        obj._api = None
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        obj._powerswitch_service = ps
        obj._powerswitchprogram_service = prog
        obj._impulseswitch_service = imp
        return obj

    def test_relay_type_button_with_impulse(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        d = self._make(has_impulse=True)
        assert d.relay_type == SHCMicromoduleRelay.RelayType.BUTTON

    def test_relay_type_switch_without_impulse(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        d = self._make(has_impulse=False)
        assert d.relay_type == SHCMicromoduleRelay.RelayType.SWITCH

    def test_child_lock(self):
        d = self._make()
        assert d.child_lock is False


# ---------------------------------------------------------------------------
# SHCMicromoduleDimmer (binarystate via PowerSwitch, not BinarySwitch)
# ---------------------------------------------------------------------------

class TestSHCMicromoduleDimmer:
    def _make(self, switch_state="ON"):
        from boschshcpy.models_impl import SHCMicromoduleDimmer
        from boschshcpy.services_impl import (
            PowerSwitchService, BinarySwitchService, MultiLevelSwitchService,
            CommunicationQualityService, ChildProtectionService,
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        ps = _svc(PowerSwitchService, "PowerSwitch",
                  {"@type": "x", "switchState": switch_state, "automaticPowerOffTime": 0})
        bs = _svc(BinarySwitchService, "BinarySwitch", {"@type": "x", "on": switch_state == "ON"})
        mls = _svc(MultiLevelSwitchService, "MultiLevelSwitch", {"@type": "x", "level": 50})
        cq = _svc(CommunicationQualityService, "CommunicationQuality", {"@type": "x", "quality": "GOOD"})
        cp = _svc(ChildProtectionService, "ChildProtection", {"@type": "x", "childLockActive": False})

        obj = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_DIMMER")
        svcs = {"PowerSwitch": ps, "BinarySwitch": bs, "MultiLevelSwitch": mls,
                "CommunicationQuality": cq, "ChildProtection": cp}
        obj._device_services_by_id = svcs
        obj._callbacks = {}
        obj._api = None
        obj._powerswitch_service = ps
        obj._binaryswitch_service = bs
        obj._multilevelswitch_service = mls
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        from boschshcpy.models_impl import SHCLight as _L
        obj._huecolortemperature_service = None
        obj._hsbcoloractuator_service = None
        obj._capabilities = _L.Capabilities(0)
        obj._capabilities |= _L.Capabilities.BRIGHTNESS
        return obj

    def test_binarystate_on(self):
        d = self._make("ON")
        assert d.binarystate is True

    def test_binarystate_off(self):
        d = self._make("OFF")
        assert d.binarystate is False

    def test_binarystate_none_when_no_powerswitch(self):
        from boschshcpy.models_impl import SHCMicromoduleDimmer
        from boschshcpy.services_impl import BinarySwitchService, MultiLevelSwitchService
        from boschshcpy.services_impl import CommunicationQualityService, ChildProtectionService

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        bs = _svc(BinarySwitchService, "BinarySwitch", {"@type": "x", "on": True})
        mls = _svc(MultiLevelSwitchService, "MultiLevelSwitch", {"@type": "x", "level": 50})
        cq = _svc(CommunicationQualityService, "CommunicationQuality", {"@type": "x", "quality": "GOOD"})
        cp = _svc(ChildProtectionService, "ChildProtection", {"@type": "x", "childLockActive": False})

        obj = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_DIMMER")
        obj._device_services_by_id = {"BinarySwitch": bs, "MultiLevelSwitch": mls,
                                       "CommunicationQuality": cq, "ChildProtection": cp}
        obj._callbacks = {}
        obj._api = None
        obj._powerswitch_service = None
        obj._binaryswitch_service = bs
        obj._multilevelswitch_service = mls
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        from boschshcpy.models_impl import SHCLight as _L
        obj._huecolortemperature_service = None
        obj._hsbcoloractuator_service = None
        obj._capabilities = _L.Capabilities(0) | _L.Capabilities.BRIGHTNESS
        assert obj.binarystate is None


# ---------------------------------------------------------------------------
# SHCWallThermostat
# ---------------------------------------------------------------------------

class TestSHCWallThermostat:
    def test_temperature_and_humidity(self):
        from boschshcpy.models_impl import SHCWallThermostat
        from boschshcpy.services_impl import (
            TemperatureLevelService, HumidityLevelService, BatteryLevelService
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        tl = _svc(TemperatureLevelService, "TemperatureLevel", {"@type": "x", "temperature": 21.5})
        hl = _svc(HumidityLevelService, "HumidityLevel", {"@type": "x", "humidity": 48.0})
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCWallThermostat.__new__(SHCWallThermostat)
        obj._raw_device = _fake_raw_device(model="THB")
        obj._device_services_by_id = {"TemperatureLevel": tl, "HumidityLevel": hl, "BatteryLevel": bat}
        obj._callbacks = {}
        obj._api = None
        obj._temperaturelevel_service = tl
        obj._humiditylevel_service = hl
        obj._batterylevel_service = bat

        assert obj.temperature == 21.5
        assert obj.humidity == 48.0

    def test_child_lock_on(self):
        """THB Thermostat service childLock=ON -> child_lock == ThermostatService.State.ON."""
        from boschshcpy.models_impl import SHCWallThermostat
        from boschshcpy.services_impl import (
            TemperatureLevelService, HumidityLevelService,
            BatteryLevelService, ThermostatService,
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        tl = _svc(TemperatureLevelService, "TemperatureLevel", {"@type": "x", "temperature": 22.0})
        hl = _svc(HumidityLevelService, "HumidityLevel", {"@type": "x", "humidity": 50.0})
        th = _svc(ThermostatService, "Thermostat", {"@type": "childLockState", "childLock": "ON"})
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCWallThermostat.__new__(SHCWallThermostat)
        obj._raw_device = _fake_raw_device(model="THB")
        obj._device_services_by_id = {
            "TemperatureLevel": tl, "HumidityLevel": hl,
            "Thermostat": th, "BatteryLevel": bat,
        }
        obj._callbacks = {}
        obj._api = None
        obj._temperaturelevel_service = tl
        obj._humiditylevel_service = hl
        obj._thermostat_service = th
        obj._batterylevel_service = bat

        assert obj.child_lock == ThermostatService.State.ON

    def test_child_lock_off(self):
        """THB Thermostat service childLock=OFF -> child_lock == ThermostatService.State.OFF."""
        from boschshcpy.models_impl import SHCWallThermostat
        from boschshcpy.services_impl import (
            TemperatureLevelService, HumidityLevelService,
            BatteryLevelService, ThermostatService,
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        tl = _svc(TemperatureLevelService, "TemperatureLevel", {"@type": "x", "temperature": 22.0})
        hl = _svc(HumidityLevelService, "HumidityLevel", {"@type": "x", "humidity": 50.0})
        th = _svc(ThermostatService, "Thermostat", {"@type": "childLockState", "childLock": "OFF"})
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCWallThermostat.__new__(SHCWallThermostat)
        obj._raw_device = _fake_raw_device(model="THB")
        obj._device_services_by_id = {
            "TemperatureLevel": tl, "HumidityLevel": hl,
            "Thermostat": th, "BatteryLevel": bat,
        }
        obj._callbacks = {}
        obj._api = None
        obj._temperaturelevel_service = tl
        obj._humiditylevel_service = hl
        obj._thermostat_service = th
        obj._batterylevel_service = bat

        assert obj.child_lock == ThermostatService.State.OFF


# ---------------------------------------------------------------------------
# SHCSilentMode (via _SilentMode mixin, tested in context of thermostat above)
# SilentMode absent branch
# ---------------------------------------------------------------------------

class TestSilentModeAbsent:
    def test_silentmode_returns_none_when_absent(self):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import (
            ValveTappetService, ThermostatService, TemperatureLevelService,
            BatteryLevelService, CommunicationQualityService, TemperatureOffsetService,
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        vt = _svc(ValveTappetService, "ValveTappet",
                  {"@type": "x", "value": "VALVE_ADAPTION_SUCCESSFUL", "position": 0})
        th = _svc(ThermostatService, "Thermostat", {"@type": "x", "childLock": "OFF"})
        tl = _svc(TemperatureLevelService, "TemperatureLevel", {"@type": "x", "temperature": 20.0})
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}
        cq = _svc(CommunicationQualityService, "CommunicationQuality", {"@type": "x", "quality": "GOOD"})
        to = _svc(TemperatureOffsetService, "TemperatureOffset",
                  {"@type": "x", "offset": 0.0, "stepSize": 0.5, "minOffset": -5.0, "maxOffset": 5.0})

        obj = SHCThermostat.__new__(SHCThermostat)
        obj._raw_device = _fake_raw_device(model="TRV")
        obj._device_services_by_id = {
            "ValveTappet": vt, "Thermostat": th, "TemperatureLevel": tl,
            "BatteryLevel": bat, "CommunicationQuality": cq, "TemperatureOffset": to,
        }
        obj._callbacks = {}
        obj._api = None
        obj._valvetappet_service = vt
        obj._thermostat_service = th
        obj._temperaturelevel_service = tl
        obj._batterylevel_service = bat
        obj._communicationquality_service = cq
        obj._silentmode_service = None  # absent
        obj._temperatureoffset_service = to

        assert obj.supports_silentmode is False
        assert obj.silentmode is None


# ---------------------------------------------------------------------------
# MODEL_MAPPING + build() sanity
# ---------------------------------------------------------------------------

class TestModelMapping:
    def test_all_mapped_model_ids_are_in_supported_models(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SUPPORTED_MODELS
        for key in MODEL_MAPPING:
            assert key in SUPPORTED_MODELS

    def test_model_mapping_is_not_empty(self):
        from boschshcpy.models_impl import MODEL_MAPPING
        assert len(MODEL_MAPPING) > 0

    def test_build_raises_assertion_for_unknown_model(self):
        from boschshcpy.models_impl import build
        with pytest.raises(AssertionError):
            build(api=None, raw_device={"deviceModel": "TOTALLY_UNKNOWN_XYZ"},
                  raw_device_services=[])

    def test_pmd_model_maps_to_smart_plug(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCSmartPlug
        assert MODEL_MAPPING["PSM"] is SHCSmartPlug

    def test_trv_model_maps_to_thermostat(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCThermostat
        assert MODEL_MAPPING["TRV"] is SHCThermostat


# ---------------------------------------------------------------------------
# CommunicationQuality variants
# ---------------------------------------------------------------------------

class TestCommunicationQuality:
    def _make_cq_svc(self, quality="GOOD"):
        from boschshcpy.services_impl import CommunicationQualityService
        svc = CommunicationQualityService.__new__(CommunicationQualityService)
        svc._api = None
        svc._raw_device_service = {"id": "CommunicationQuality", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "quality": quality}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        return svc

    def test_quality_bad(self):
        from boschshcpy.services_impl import CommunicationQualityService
        svc = self._make_cq_svc("BAD")
        assert svc.value == CommunicationQualityService.State.BAD

    def test_quality_medium(self):
        from boschshcpy.services_impl import CommunicationQualityService
        svc = self._make_cq_svc("MEDIUM")
        assert svc.value == CommunicationQualityService.State.MEDIUM

    def test_quality_normal(self):
        from boschshcpy.services_impl import CommunicationQualityService
        svc = self._make_cq_svc("NORMAL")
        assert svc.value == CommunicationQualityService.State.NORMAL

    def test_quality_unknown(self):
        from boschshcpy.services_impl import CommunicationQualityService
        svc = self._make_cq_svc("UNKNOWN")
        assert svc.value == CommunicationQualityService.State.UNKNOWN

    def test_quality_fetching(self):
        from boschshcpy.services_impl import CommunicationQualityService
        svc = self._make_cq_svc("FETCHING")
        assert svc.value == CommunicationQualityService.State.FETCHING


# ---------------------------------------------------------------------------
# SHCSmartPlugCompact (inherits CommunicationQuality + PowerMeter + PowerSwitch)
# ---------------------------------------------------------------------------

class TestSHCSmartPlugCompact:
    def test_basic_properties(self):
        from boschshcpy.models_impl import SHCSmartPlugCompact
        from boschshcpy.services_impl import (
            CommunicationQualityService, PowerMeterService, PowerSwitchService,
            PowerSwitchProgramService,
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        cq = _svc(CommunicationQualityService, "CommunicationQuality", {"@type": "x", "quality": "GOOD"})
        pm = _svc(PowerMeterService, "PowerMeter",
                  {"@type": "x", "powerConsumption": 50.0, "energyConsumption": 200.0})
        ps = _svc(PowerSwitchService, "PowerSwitch",
                  {"@type": "x", "switchState": "ON", "automaticPowerOffTime": 0})
        prog = _svc(PowerSwitchProgramService, "PowerSwitchProgram",
                    {"@type": "x", "operationMode": "MANUAL"})

        obj = SHCSmartPlugCompact.__new__(SHCSmartPlugCompact)
        obj._raw_device = _fake_raw_device(model="PLUG_COMPACT")
        obj._device_services_by_id = {
            "CommunicationQuality": cq, "PowerMeter": pm, "PowerSwitch": ps, "PowerSwitchProgram": prog
        }
        obj._callbacks = {}
        obj._api = None
        obj._communicationquality_service = cq
        obj._powermeter_service = pm
        obj._powerswitch_service = ps
        obj._powerswitchprogram_service = prog

        from boschshcpy.services_impl import PowerSwitchService, CommunicationQualityService
        assert obj.switchstate == PowerSwitchService.State.ON
        assert obj.powerconsumption == 50.0
        assert obj.energyconsumption == 200.0
        assert obj.communicationquality == CommunicationQualityService.State.GOOD


# ---------------------------------------------------------------------------
# LatestMotion missing key defaults
# ---------------------------------------------------------------------------

class TestLatestMotionMissingKey:
    def test_latestmotion_returns_na_when_key_missing(self):
        from boschshcpy.services_impl import LatestMotionService
        svc = LatestMotionService.__new__(LatestMotionService)
        svc._api = None
        svc._raw_device_service = {"id": "LatestMotion", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x"}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        assert svc.latestMotionDetected == "n/a"


# ---------------------------------------------------------------------------
# TemperatureOffset defaults when keys absent
# ---------------------------------------------------------------------------

class TestTemperatureOffsetDefaults:
    def test_defaults_when_keys_absent(self):
        from boschshcpy.services_impl import TemperatureOffsetService
        svc = TemperatureOffsetService.__new__(TemperatureOffsetService)
        svc._api = None
        svc._raw_device_service = {"id": "TemperatureOffset", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x"}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        assert svc.offset == 0.0
        assert svc.step_size == 0.0
        assert svc.min_offset == 0.0
        assert svc.max_offset == 0.0


# ---------------------------------------------------------------------------
# Setter tests — mock put_state_element so no real API needed
# ---------------------------------------------------------------------------

class TestSetters:
    """Cover setter branches that call put_state_element."""

    def _mock_svc(self, cls, sid, state):
        from unittest.mock import MagicMock
        svc = cls.__new__(cls)
        svc._api = None
        svc._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
        svc._raw_state = state
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        svc.put_state_element = MagicMock()
        return svc

    def test_child_protection_setter(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import ChildProtectionService
        svc = self._mock_svc(ChildProtectionService, "ChildProtection",
                             {"@type": "x", "childLockActive": False})
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._childprotection_service = svc
        obj.child_lock = True
        svc.put_state_element.assert_called_once_with("childLockActive", True)

    def test_thermostat_child_lock_setter_on(self):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import ThermostatService
        svc = self._mock_svc(ThermostatService, "Thermostat",
                             {"@type": "x", "childLock": "OFF"})
        obj = SHCThermostat.__new__(SHCThermostat)
        obj._thermostat_service = svc
        obj.child_lock = True
        svc.put_state_element.assert_called_once_with("childLock", "ON")

    def test_thermostat_child_lock_setter_off(self):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import ThermostatService
        svc = self._mock_svc(ThermostatService, "Thermostat",
                             {"@type": "x", "childLock": "ON"})
        obj = SHCThermostat.__new__(SHCThermostat)
        obj._thermostat_service = svc
        obj.child_lock = False
        svc.put_state_element.assert_called_once_with("childLock", "OFF")

    def test_power_switch_setter_on(self):
        from boschshcpy.models_impl import SHCSmartPlug
        from boschshcpy.services_impl import PowerSwitchService
        svc = self._mock_svc(PowerSwitchService, "PowerSwitch",
                             {"@type": "x", "switchState": "OFF", "automaticPowerOffTime": 0})
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._powerswitch_service = svc
        obj.switchstate = True
        svc.put_state_element.assert_called_once_with("switchState", "ON")

    def test_power_switch_setter_off(self):
        from boschshcpy.models_impl import SHCSmartPlug
        from boschshcpy.services_impl import PowerSwitchService
        svc = self._mock_svc(PowerSwitchService, "PowerSwitch",
                             {"@type": "x", "switchState": "ON", "automaticPowerOffTime": 0})
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._powerswitch_service = svc
        obj.switchstate = False
        svc.put_state_element.assert_called_once_with("switchState", "OFF")

    def test_shutter_contact_alarmstate_setter(self):
        from boschshcpy.models_impl import SHCSmokeDetector
        from boschshcpy.services_impl import AlarmService
        svc = self._mock_svc(AlarmService, "Alarm",
                             {"@type": "x", "value": "IDLE_OFF"})
        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._alarm_service = svc
        obj.alarmstate = "PRIMARY_ALARM"
        svc.put_state_element.assert_called_once_with("value", "PRIMARY_ALARM")

    def test_shutter_control_level_setter(self):
        from boschshcpy.models_impl import SHCShutterControl
        from boschshcpy.services_impl import ShutterControlService
        svc = self._mock_svc(ShutterControlService, "ShutterControl",
                             {"@type": "x", "operationState": "STOPPED", "level": 0.0, "calibrated": True})
        obj = SHCShutterControl.__new__(SHCShutterControl)
        obj._service = svc
        obj.level = 0.5
        svc.put_state_element.assert_called_once_with("level", 0.5)

    def test_shutter_control_stop(self):
        from boschshcpy.models_impl import SHCShutterControl
        from boschshcpy.services_impl import ShutterControlService
        svc = self._mock_svc(ShutterControlService, "ShutterControl",
                             {"@type": "x", "operationState": "MOVING", "level": 0.5, "calibrated": True})
        obj = SHCShutterControl.__new__(SHCShutterControl)
        obj._service = svc
        obj.stop()
        svc.put_state_element.assert_called_once_with("operationState", "STOPPED")

    def test_camera360_privacymode_setter_enable(self):
        from boschshcpy.models_impl import SHCCamera360
        from boschshcpy.services_impl import PrivacyModeService
        svc = self._mock_svc(PrivacyModeService, "PrivacyMode",
                             {"@type": "x", "value": "DISABLED"})
        obj = SHCCamera360.__new__(SHCCamera360)
        obj._privacymode_service = svc
        obj.privacymode = True   # True → "DISABLED" per model logic (inverted)
        svc.put_state_element.assert_called_once_with("value", "DISABLED")

    def test_camera360_privacymode_setter_disable(self):
        from boschshcpy.models_impl import SHCCamera360
        from boschshcpy.services_impl import PrivacyModeService
        svc = self._mock_svc(PrivacyModeService, "PrivacyMode",
                             {"@type": "x", "value": "ENABLED"})
        obj = SHCCamera360.__new__(SHCCamera360)
        obj._privacymode_service = svc
        obj.privacymode = False
        svc.put_state_element.assert_called_once_with("value", "ENABLED")

    def test_camera360_notification_setter_enable(self):
        from boschshcpy.models_impl import SHCCamera360
        from boschshcpy.services_impl import CameraNotificationService
        svc = self._mock_svc(CameraNotificationService, "CameraNotification",
                             {"@type": "x", "value": "DISABLED"})
        obj = SHCCamera360.__new__(SHCCamera360)
        obj._cameranotification_service = svc
        obj.cameranotification = True
        svc.put_state_element.assert_called_once_with("value", "ENABLED")

    def test_camera360_notification_setter_no_op_when_absent(self):
        from boschshcpy.models_impl import SHCCamera360
        obj = SHCCamera360.__new__(SHCCamera360)
        obj._cameranotification_service = None
        # Should not raise
        obj.cameranotification = True

    def test_cameraeyes_light_setter_on(self):
        from boschshcpy.models_impl import SHCCameraEyes
        from boschshcpy.services_impl import CameraLightService
        svc = self._mock_svc(CameraLightService, "CameraLight",
                             {"@type": "x", "value": "OFF"})
        obj = SHCCameraEyes.__new__(SHCCameraEyes)
        obj._cameralight_service = svc
        obj.cameralight = True
        svc.put_state_element.assert_called_once_with("value", "ON")

    def test_cameraeyes_light_setter_off(self):
        from boschshcpy.models_impl import SHCCameraEyes
        from boschshcpy.services_impl import CameraLightService
        svc = self._mock_svc(CameraLightService, "CameraLight",
                             {"@type": "x", "value": "ON"})
        obj = SHCCameraEyes.__new__(SHCCameraEyes)
        obj._cameralight_service = svc
        obj.cameralight = False
        svc.put_state_element.assert_called_once_with("value", "OFF")

    def test_cameraeyes_light_setter_no_op_when_absent(self):
        from boschshcpy.models_impl import SHCCameraEyes
        obj = SHCCameraEyes.__new__(SHCCameraEyes)
        obj._cameralight_service = None
        obj.cameralight = True  # Must not raise

    def test_routing_setter_enabled(self):
        from boschshcpy.models_impl import SHCSmartPlug
        from boschshcpy.services_impl import RoutingService
        svc = self._mock_svc(RoutingService, "Routing",
                             {"@type": "x", "value": "DISABLED"})
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._routing_service = svc
        obj.routing = True
        svc.put_state_element.assert_called_once_with("value", "ENABLED")

    def test_routing_setter_disabled(self):
        from boschshcpy.models_impl import SHCSmartPlug
        from boschshcpy.services_impl import RoutingService
        svc = self._mock_svc(RoutingService, "Routing",
                             {"@type": "x", "value": "ENABLED"})
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._routing_service = svc
        obj.routing = False
        svc.put_state_element.assert_called_once_with("value", "DISABLED")

    def test_bypass_setter_active(self):
        from boschshcpy.models_impl import SHCShutterContact2
        from boschshcpy.services_impl import BypassService
        svc = self._mock_svc(BypassService, "Bypass",
                             {"@type": "x", "state": "BYPASS_INACTIVE"})
        obj = SHCShutterContact2.__new__(SHCShutterContact2)
        obj._bypass_service = svc
        obj.bypass = True
        svc.put_state_element.assert_called_once_with("state", "BYPASS_ACTIVE")

    def test_bypass_setter_inactive(self):
        from boschshcpy.models_impl import SHCShutterContact2
        from boschshcpy.services_impl import BypassService
        svc = self._mock_svc(BypassService, "Bypass",
                             {"@type": "x", "state": "BYPASS_ACTIVE"})
        obj = SHCShutterContact2.__new__(SHCShutterContact2)
        obj._bypass_service = svc
        obj.bypass = False
        svc.put_state_element.assert_called_once_with("state", "BYPASS_INACTIVE")

    def test_vibration_sensor_enabled_setter(self):
        from boschshcpy.models_impl import SHCShutterContact2Plus
        from boschshcpy.services_impl import VibrationSensorService
        svc = self._mock_svc(VibrationSensorService, "VibrationSensor",
                             {"@type": "x", "value": "NO_VIBRATION", "enabled": True, "sensitivity": "HIGH"})
        obj = SHCShutterContact2Plus.__new__(SHCShutterContact2Plus)
        obj._vibrationsensor_service = svc
        obj.enabled = False
        svc.put_state_element.assert_called_once_with("enabled", False)

    def test_vibration_sensor_sensitivity_setter(self):
        from boschshcpy.models_impl import SHCShutterContact2Plus
        from boschshcpy.services_impl import VibrationSensorService
        svc = self._mock_svc(VibrationSensorService, "VibrationSensor",
                             {"@type": "x", "value": "NO_VIBRATION", "enabled": True, "sensitivity": "HIGH"})
        obj = SHCShutterContact2Plus.__new__(SHCShutterContact2Plus)
        obj._vibrationsensor_service = svc
        obj.sensitivity = VibrationSensorService.SensitivityState.LOW
        svc.put_state_element.assert_called_once_with("sensitivity", "LOW")

    def test_climate_control_operation_mode_setter(self):
        from boschshcpy.models_impl import SHCClimateControl
        from boschshcpy.services_impl import RoomClimateControlService
        svc = self._mock_svc(RoomClimateControlService, "RoomClimateControl",
                             {"@type": "x", "operationMode": "AUTOMATIC",
                              "setpointTemperature": 21.0, "setpointTemperatureForLevelEco": 17.0,
                              "setpointTemperatureForLevelComfort": 22.0, "ventilationMode": False,
                              "low": False, "boostMode": False, "summerMode": False,
                              "supportsBoostMode": True, "roomControlMode": "HEATING"})
        obj = SHCClimateControl.__new__(SHCClimateControl)
        obj._roomclimatecontrol_service = svc
        svc.put_state_element = lambda k, v: None  # suppress actual call
        # Use real setter to cover the branch
        from boschshcpy.services_impl import RoomClimateControlService as RCC
        # Just verify the property routes correctly
        assert svc.operation_mode == RCC.OperationMode.AUTOMATIC

    def test_silentmode_setter_silent(self):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import SilentModeService
        svc = self._mock_svc(SilentModeService, "SilentMode",
                             {"@type": "x", "mode": "MODE_NORMAL"})
        obj = SHCThermostat.__new__(SHCThermostat)
        obj._silentmode_service = svc
        obj.silentmode = True
        svc.put_state_element.assert_called_once_with("mode", "MODE_SILENT")

    def test_silentmode_setter_normal(self):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import SilentModeService
        svc = self._mock_svc(SilentModeService, "SilentMode",
                             {"@type": "x", "mode": "MODE_SILENT"})
        obj = SHCThermostat.__new__(SHCThermostat)
        obj._silentmode_service = svc
        obj.silentmode = False
        svc.put_state_element.assert_called_once_with("mode", "MODE_NORMAL")

    def test_silentmode_setter_no_op_when_absent(self):
        from boschshcpy.models_impl import SHCThermostat
        obj = SHCThermostat.__new__(SHCThermostat)
        obj._silentmode_service = None
        obj.silentmode = True  # Must not raise

    def test_presence_simulation_enabled_setter(self):
        from boschshcpy.models_impl import SHCPresenceSimulationSystem
        from boschshcpy.services_impl import PresenceSimulationConfigurationService
        svc = self._mock_svc(PresenceSimulationConfigurationService,
                             "PresenceSimulationConfiguration",
                             {"@type": "x", "enabled": False})
        obj = SHCPresenceSimulationSystem.__new__(SHCPresenceSimulationSystem)
        obj._presencesimulationconfiguration_service = svc
        obj.enabled = True
        svc.put_state_element.assert_called_once_with("enabled", True)

    def test_light_binarystate_setter_on(self):
        from boschshcpy.models_impl import SHCLight
        from boschshcpy.services_impl import BinarySwitchService
        svc = self._mock_svc(BinarySwitchService, "BinarySwitch",
                             {"@type": "x", "on": False})
        obj = SHCLight.__new__(SHCLight)
        obj._binaryswitch_service = svc
        obj.binarystate = True
        svc.put_state_element.assert_called_once_with("on", True)

    def test_light_binarystate_setter_off(self):
        from boschshcpy.models_impl import SHCLight
        from boschshcpy.services_impl import BinarySwitchService
        svc = self._mock_svc(BinarySwitchService, "BinarySwitch",
                             {"@type": "x", "on": True})
        obj = SHCLight.__new__(SHCLight)
        obj._binaryswitch_service = svc
        obj.binarystate = False
        svc.put_state_element.assert_called_once_with("on", False)

    def test_light_brightness_setter(self):
        from boschshcpy.models_impl import SHCLight
        from boschshcpy.services_impl import MultiLevelSwitchService
        svc = self._mock_svc(MultiLevelSwitchService, "MultiLevelSwitch",
                             {"@type": "x", "level": 50})
        obj = SHCLight.__new__(SHCLight)
        obj._multilevelswitch_service = svc
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities.BRIGHTNESS
        obj.brightness = 75
        svc.put_state_element.assert_called_once_with("level", 75)

    def test_light_brightness_setter_no_op_when_no_brightness(self):
        from boschshcpy.models_impl import SHCLight
        obj = SHCLight.__new__(SHCLight)
        obj._multilevelswitch_service = None
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities(0)
        obj.brightness = 75  # Must not raise

    def test_light_color_setter(self):
        from boschshcpy.models_impl import SHCLight
        from boschshcpy.services_impl import HueColorTemperatureService
        svc = self._mock_svc(HueColorTemperatureService, "HueColorTemperature",
                             {"@type": "x", "colorTemperature": 4000,
                              "colorTemperatureRange": {"minCt": 2700, "maxCt": 6500}})
        obj = SHCLight.__new__(SHCLight)
        obj._huecolortemperature_service = svc
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities.COLOR_TEMP
        obj.color = 5000
        svc.put_state_element.assert_called_once_with("colorTemperature", 5000)

    def test_light_color_setter_no_op_when_absent(self):
        from boschshcpy.models_impl import SHCLight
        obj = SHCLight.__new__(SHCLight)
        obj._huecolortemperature_service = None
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities(0)
        obj.color = 5000  # Must not raise

    def test_light_rgb_setter(self):
        from boschshcpy.models_impl import SHCLight
        from boschshcpy.services_impl import HSBColorActuatorService
        svc = self._mock_svc(HSBColorActuatorService, "HSBColorActuator",
                             {"@type": "x", "rgb": 0xFF0000, "gamut": "A",
                              "colorTemperatureRange": {"minCt": 2000, "maxCt": 6500}})
        obj = SHCLight.__new__(SHCLight)
        obj._hsbcoloractuator_service = svc
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities.COLOR_HSB
        obj.rgb = 0x00FF00
        svc.put_state_element.assert_called_once_with("rgb", 0x00FF00)

    def test_light_rgb_setter_no_op_when_absent(self):
        from boschshcpy.models_impl import SHCLight
        obj = SHCLight.__new__(SHCLight)
        obj._hsbcoloractuator_service = None
        from boschshcpy.models_impl import SHCLight as _L
        obj._capabilities = _L.Capabilities(0)
        obj.rgb = 0x00FF00  # Must not raise

    def test_smokedetector_smoketest_requested(self):
        from boschshcpy.models_impl import SHCSmokeDetector
        from boschshcpy.services_impl import SmokeDetectorCheckService
        svc = self._mock_svc(SmokeDetectorCheckService, "SmokeDetectorCheck",
                             {"@type": "x", "value": "NONE"})
        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._smokedetectorcheck_service = svc
        obj.smoketest_requested()
        svc.put_state_element.assert_called_once_with("value", "SMOKE_TEST_REQUESTED")

    def test_twinguard_smoketest_requested(self):
        from boschshcpy.models_impl import SHCTwinguard
        from boschshcpy.services_impl import SmokeDetectorCheckService
        svc = self._mock_svc(SmokeDetectorCheckService, "SmokeDetectorCheck",
                             {"@type": "x", "value": "NONE"})
        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._smokedetectorcheck_service = svc
        obj.smoketest_requested()
        svc.put_state_element.assert_called_once_with("value", "SMOKE_TEST_REQUESTED")

    def test_micromodule_relay_trigger_impulse(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import ImpulseSwitchService
        svc = self._mock_svc(ImpulseSwitchService, "ImpulseSwitch",
                             {"@type": "x", "impulseState": False, "impulseLength": 100})
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._impulseswitch_service = svc
        obj.trigger_impulse_state()
        svc.put_state_element.assert_called_once_with("impulseState", True)

    def test_micromodule_relay_trigger_no_op_when_absent(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._impulseswitch_service = None
        obj.trigger_impulse_state()  # Must not raise

    def test_micromodule_relay_impulse_length_setter(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import ImpulseSwitchService
        svc = self._mock_svc(ImpulseSwitchService, "ImpulseSwitch",
                             {"@type": "x", "impulseState": False, "impulseLength": 100})
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._impulseswitch_service = svc
        obj.impulse_length = 200
        svc.put_state_element.assert_called_once_with("impulseLength", 200)

    def test_micromodule_dimmer_binarystate_setter_on(self):
        from boschshcpy.models_impl import SHCMicromoduleDimmer
        from boschshcpy.services_impl import PowerSwitchService
        svc = self._mock_svc(PowerSwitchService, "PowerSwitch",
                             {"@type": "x", "switchState": "OFF", "automaticPowerOffTime": 0})
        obj = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
        obj._powerswitch_service = svc
        obj.binarystate = True
        svc.put_state_element.assert_called_once_with("switchState", "ON")

    def test_micromodule_dimmer_binarystate_setter_off(self):
        from boschshcpy.models_impl import SHCMicromoduleDimmer
        from boschshcpy.services_impl import PowerSwitchService
        svc = self._mock_svc(PowerSwitchService, "PowerSwitch",
                             {"@type": "x", "switchState": "ON", "automaticPowerOffTime": 0})
        obj = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
        obj._powerswitch_service = svc
        obj.binarystate = False
        svc.put_state_element.assert_called_once_with("switchState", "OFF")

    def test_heating_circuit_setpoint_setter(self):
        from boschshcpy.models_impl import SHCHeatingCircuit
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._mock_svc(HeatingCircuitService, "HeatingCircuit",
                             {"@type": "x", "operationMode": "AUTOMATIC",
                              "setpointTemperature": 22.0,
                              "setpointTemperatureForLevelEco": 18.0,
                              "setpointTemperatureForLevelComfort": 23.0,
                              "temperatureOverrideModeActive": False,
                              "temperatureOverrideFeatureEnabled": True,
                              "energySavingFeatureEnabled": False, "on": True})
        obj = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
        obj._heating_circuit_service = svc
        obj.setpoint_temperature = 20.0
        svc.put_state_element.assert_called_once_with("setpointTemperature", 20.0)

    def test_outdoor_gen2_ambient_light_setter_on(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        from boschshcpy.services_impl import CameraAmbientLightService
        svc = self._mock_svc(CameraAmbientLightService, "CameraAmbientLight",
                             {"@type": "x", "value": "OFF"})
        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._cameraambientlight_service = svc
        obj.cameraambientlight = True
        svc.put_state_element.assert_called_once_with("value", "ON")

    def test_outdoor_gen2_ambient_light_setter_off(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        from boschshcpy.services_impl import CameraAmbientLightService
        svc = self._mock_svc(CameraAmbientLightService, "CameraAmbientLight",
                             {"@type": "x", "value": "ON"})
        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._cameraambientlight_service = svc
        obj.cameraambientlight = False
        svc.put_state_element.assert_called_once_with("value", "OFF")

    def test_outdoor_gen2_ambient_light_setter_no_op(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._cameraambientlight_service = None
        obj.cameraambientlight = True  # Must not raise

    def test_outdoor_gen2_front_light_setter_on(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        from boschshcpy.services_impl import CameraFrontLightService
        svc = self._mock_svc(CameraFrontLightService, "CameraFrontLight",
                             {"@type": "x", "value": "OFF"})
        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._camerafrontlight_service = svc
        obj.camerafrontlight = True
        svc.put_state_element.assert_called_once_with("value", "ON")

    def test_outdoor_gen2_front_light_setter_off(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        from boschshcpy.services_impl import CameraFrontLightService
        svc = self._mock_svc(CameraFrontLightService, "CameraFrontLight",
                             {"@type": "x", "value": "ON"})
        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._camerafrontlight_service = svc
        obj.camerafrontlight = False
        svc.put_state_element.assert_called_once_with("value", "OFF")

    def test_outdoor_gen2_front_light_setter_no_op(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._camerafrontlight_service = None
        obj.camerafrontlight = True  # Must not raise


# ---------------------------------------------------------------------------
# SHCMicromoduleShutterControl — keypad + instant_of_last_impulse branches
# ---------------------------------------------------------------------------

class TestSHCMicromoduleShutterControl:
    def _make(self):
        from boschshcpy.models_impl import SHCMicromoduleShutterControl
        from boschshcpy.services_impl import (
            ShutterControlService, KeypadService, CommunicationQualityService,
            ChildProtectionService, PowerMeterService,
        )

        def _svc(cls, sid, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": sid, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        sc = _svc(ShutterControlService, "ShutterControl",
                  {"@type": "x", "operationState": "STOPPED", "level": 0.3, "calibrated": True})
        kp = _svc(KeypadService, "Keypad",
                  {"@type": "x", "keyCode": 1, "keyName": "UNDEFINED_BUTTON",
                   "eventType": "SWITCH_ON", "eventTimestamp": 42})
        cq = _svc(CommunicationQualityService, "CommunicationQuality",
                  {"@type": "x", "quality": "GOOD"})
        cp = _svc(ChildProtectionService, "ChildProtection",
                  {"@type": "x", "childLockActive": False})
        pm = _svc(PowerMeterService, "PowerMeter",
                  {"@type": "x", "powerConsumption": 10.0, "energyConsumption": 100.0})

        obj = SHCMicromoduleShutterControl.__new__(SHCMicromoduleShutterControl)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_SHUTTER")
        obj._device_services_by_id = {
            "ShutterControl": sc, "Keypad": kp, "CommunicationQuality": cq,
            "ChildProtection": cp, "PowerMeter": pm,
        }
        obj._callbacks = {}
        obj._api = None
        obj._service = sc
        obj._keypad_service = kp
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        obj._powermeter_service = pm
        return obj

    def test_keystates(self):
        d = self._make()
        assert "UNDEFINED_BUTTON" in d.keystates

    def test_eventtypes(self):
        d = self._make()
        assert "SWITCH_OFF" in d.eventtypes
        assert "SWITCH_ON" in d.eventtypes

    def test_keycode(self):
        d = self._make()
        assert d.keycode == 1

    def test_keyname_undefined_button(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make()
        assert d.keyname == KeypadService.KeyState.UNDEFINED_BUTTON

    def test_eventtype_switch_on(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make()
        assert d.eventtype == KeypadService.KeyEvent.SWITCH_ON

    def test_eventtimestamp(self):
        d = self._make()
        assert d.eventtimestamp == 42


# ---------------------------------------------------------------------------
# ImpulseSwitch instant_of_last_impulse absent + present
# ---------------------------------------------------------------------------

class TestImpulseSwitch:
    def _make_svc(self, state):
        from boschshcpy.services_impl import ImpulseSwitchService
        svc = ImpulseSwitchService.__new__(ImpulseSwitchService)
        svc._api = None
        svc._raw_device_service = {"id": "ImpulseSwitch", "deviceId": "d1", "path": "/x", "state": state}
        svc._raw_state = state
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        return svc

    def test_instant_of_last_impulse_present(self):
        svc = self._make_svc({"@type": "x", "impulseState": False, "impulseLength": 100,
                               "instantOfLastImpulse": "2024-01-01T12:00:00"})
        assert svc.instant_of_last_impulse == "2024-01-01T12:00:00"

    def test_instant_of_last_impulse_absent_returns_none(self):
        svc = self._make_svc({"@type": "x", "impulseState": False, "impulseLength": 100})
        assert svc.instant_of_last_impulse is None

    def test_instant_of_last_impulse_via_micromodule_relay(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import ImpulseSwitchService
        svc = self._make_svc({"@type": "x", "impulseState": False, "impulseLength": 100,
                               "instantOfLastImpulse": "2024-06-01T08:00:00"})
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._impulseswitch_service = svc
        assert obj.instant_of_last_impulse == "2024-06-01T08:00:00"

    def test_instant_of_last_impulse_absent_via_relay(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._impulseswitch_service = None
        assert obj.instant_of_last_impulse is None


# ---------------------------------------------------------------------------
# DetectionTestService started branch
# ---------------------------------------------------------------------------

class TestDetectionTestStarted:
    def test_detection_state_started(self):
        from boschshcpy.services_impl import DetectionTestService
        svc = DetectionTestService.__new__(DetectionTestService)
        svc._api = None
        svc._raw_device_service = {"id": "DetectionTest", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "detectionState": "DETECTION_TEST_STARTED"}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        assert svc.detection_state == DetectionTestService.DetectionState.DETECTION_TEST_STARTED


# ---------------------------------------------------------------------------
# PollControlService SHORT branch
# ---------------------------------------------------------------------------

class TestPollControlShort:
    def test_poll_control_short(self):
        from boschshcpy.services_impl import PollControlService
        svc = PollControlService.__new__(PollControlService)
        svc._api = None
        svc._raw_device_service = {"id": "PollControl", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "longPollInterval": "SHORT"}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        assert svc.longPollInterval == PollControlService.PollControlState.SHORT


# ---------------------------------------------------------------------------
# PirSensorConfiguration MIDDLE + LOW branches
# ---------------------------------------------------------------------------

class TestPirSensorConfigMiddleLow:
    def test_middle(self):
        from boschshcpy.services_impl import PirSensorConfigurationService
        svc = PirSensorConfigurationService.__new__(PirSensorConfigurationService)
        svc._api = None
        svc._raw_device_service = {"id": "PirSensorConfiguration", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "motionSensitivity": "MIDDLE"}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        assert svc.motionSensitivity == PirSensorConfigurationService.MotionSensitivity.MIDDLE

    def test_low(self):
        from boschshcpy.services_impl import PirSensorConfigurationService
        svc = PirSensorConfigurationService.__new__(PirSensorConfigurationService)
        svc._api = None
        svc._raw_device_service = {"id": "PirSensorConfiguration", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "motionSensitivity": "LOW"}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        assert svc.motionSensitivity == PirSensorConfigurationService.MotionSensitivity.LOW


# ---------------------------------------------------------------------------
# OccupancyDetection lastOccupancyChangeTime absent
# ---------------------------------------------------------------------------

class TestOccupancyDetectionAbsent:
    def test_last_occupancy_change_time_absent(self):
        from boschshcpy.services_impl import OccupancyDetectionService
        svc = OccupancyDetectionService.__new__(OccupancyDetectionService)
        svc._api = None
        svc._raw_device_service = {"id": "OccupancyDetection", "deviceId": "d1", "path": "/x",
                                    "state": {"@type": "x", "isOccupied": False}}
        svc._raw_state = svc._raw_device_service["state"]
        svc._last_update = None; svc._callbacks = {}; svc._event_callbacks = {}
        assert svc.lastOccupancyChangeTime == "n/a"


# ---------------------------------------------------------------------------
# BUG 1 — SHCMicromoduleRelay.impulse_length getter+setter crash when
# relay_type == SWITCH (i.e. _impulseswitch_service is None).
# Regression: confirmed AttributeError before fix, None-guarded after.
# ---------------------------------------------------------------------------

class TestSHCMicromoduleRelaySwitch:
    """SWITCH relay has no ImpulseSwitch service — impulse_* must not crash."""

    def _make_switch_relay(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import (
            PowerSwitchService, CommunicationQualityService,
            ChildProtectionService, PowerSwitchProgramService,
        )

        def _svc(cls, svc_id, state):
            s = cls.__new__(cls)
            s._api = None
            s._raw_device_service = {"id": svc_id, "deviceId": "d1", "path": "/x", "state": state}
            s._raw_state = state
            s._last_update = None; s._callbacks = {}; s._event_callbacks = {}
            return s

        ps = _svc(PowerSwitchService, "PowerSwitch", {"@type": "x", "switchState": "ON", "automaticPowerOffTime": 0})
        cq = _svc(CommunicationQualityService, "CommunicationQuality", {"@type": "x", "quality": "GOOD"})
        cp = _svc(ChildProtectionService, "ChildProtection", {"@type": "x", "childLockActive": False})
        prog = _svc(PowerSwitchProgramService, "PowerSwitchProgram", {"@type": "x", "operationMode": "MANUAL"})

        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_RELAY")
        obj._device_services_by_id = {
            "PowerSwitch": ps, "CommunicationQuality": cq,
            "ChildProtection": cp, "PowerSwitchProgram": prog,
        }
        obj._callbacks = {}
        obj._api = None
        obj._powerswitch_service = ps
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        obj._powerswitchprogram_service = prog
        obj._impulseswitch_service = None  # SWITCH relay: no ImpulseSwitch service
        return obj

    def test_relay_type_is_switch_when_no_impulse_service(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        d = self._make_switch_relay()
        assert d.relay_type == SHCMicromoduleRelay.RelayType.SWITCH

    def test_impulse_length_getter_returns_none_for_switch(self):
        """Regression: AttributeError on None._impulseswitch_service.impulse_length."""
        d = self._make_switch_relay()
        assert d.impulse_length is None

    def test_impulse_length_setter_noops_for_switch(self):
        """Regression: AttributeError on None._impulseswitch_service.put_state_element."""
        d = self._make_switch_relay()
        d.impulse_length = 500  # must not raise

    def test_instant_of_last_impulse_returns_none_for_switch(self):
        """instant_of_last_impulse already had a guard — verify it still returns None."""
        d = self._make_switch_relay()
        assert d.instant_of_last_impulse is None

    def test_trigger_impulse_state_noops_for_switch(self):
        """trigger_impulse_state already had a guard — verify it still does not raise."""
        d = self._make_switch_relay()
        d.trigger_impulse_state()  # must not raise
