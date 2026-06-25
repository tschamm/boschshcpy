"""Additional coverage tests for boschshcpy/models_impl.py.

Targets the ~118 lines still missing after test_models_impl.py:
  - All mixin-class __init__ bodies (lines 10-11, 30-31, 44-45 …)
  - Setter paths in RoomClimateControl, HeatingCircuit, TemperatureOffset
  - SHCMicromoduleBlinds properties/setters
  - SHCMicromoduleShutterControl.eventtype setter
  - SHCMicromoduleRelay.impulse_length, instant_of_last_impulse, trigger_impulse_state
  - SHCUniversalSwitch.eventtypes (returns KeyEvent class)
  - put_state-tracking for child_lock setters, switch setters, bypass setter, ...
  - build() function (line 1142)

Isolation: no HA harness — mirrors test_models_impl.py style exactly.
"""

from types import SimpleNamespace
import pytest


# ---------------------------------------------------------------------------
# Shared helpers (same pattern as test_models_impl.py)
# ---------------------------------------------------------------------------

def _fake_raw_device(model="PSM", device_id="device-1"):
    return {
        "id": device_id,
        "rootDeviceId": "root-1",
        "manufacturer": "BOSCH",
        "roomId": "room-1",
        "deviceModel": model,
        "serial": "SER-001",
        "profile": model,
        "name": "Test Device",
        "status": "AVAILABLE",
        "deviceServiceIds": [],
    }


def _fake_svc(cls, svc_id, state, api=None):
    """Build an injected service with optional mock api."""
    svc = cls.__new__(cls)
    svc._api = api
    svc._raw_device_service = {"id": svc_id, "deviceId": "device-1", "path": f"/x/{svc_id}", "state": state}
    svc._raw_state = state
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


def _mock_api():
    """Return (api, calls) where calls is a list that captures put_device_service_state invocations."""
    calls = []
    api = SimpleNamespace(
        put_device_service_state=lambda dev, svc, body: calls.append((dev, svc, body)),
    )
    return api, calls


# ---------------------------------------------------------------------------
# Exercise __init__ bodies via real constructors (raw_device_services=[])
#
# Each mixin/composite __init__ calls super().__init__ then self.device_service().
# Passing raw_device_services=[] causes _init_services to loop over nothing, so
# device_service() returns None for every id — still hits lines 10-11, 30-31 … etc.
# ---------------------------------------------------------------------------

class TestInitBodies:
    """Each test instantiates a class via its real __init__ to cover the init lines."""

    def _rd(self, model):
        return _fake_raw_device(model=model)

    def test_shcbatterydevice_init(self):
        from boschshcpy.models_impl import SHCBatteryDevice
        obj = SHCBatteryDevice(api=None, raw_device=self._rd("PSM"), raw_device_services=[])
        assert obj._batterylevel_service is None                    # lines 10-11

    def test_communicationquality_mixin_via_smartplugcompact(self):
        from boschshcpy.models_impl import SHCSmartPlugCompact
        obj = SHCSmartPlugCompact(api=None, raw_device=self._rd("PLUG_COMPACT"), raw_device_services=[])
        assert obj._communicationquality_service is None           # lines 30-31

    def test_powermeter_mixin_via_smartplug(self):
        from boschshcpy.models_impl import SHCSmartPlug
        obj = SHCSmartPlug(api=None, raw_device=self._rd("PSM"), raw_device_services=[])
        assert obj._powermeter_service is None                     # lines 44-45

    def test_childprotection_mixin_via_lightswitch(self):
        from boschshcpy.models_impl import SHCLightSwitch
        obj = SHCLightSwitch(api=None, raw_device=self._rd("MICROMODULE_LIGHT_ATTACHED"), raw_device_services=[])
        assert obj._childprotection_service is None                # lines 62-63

    def test_thermostat_mixin_via_thermostat(self):
        from boschshcpy.models_impl import SHCThermostat
        obj = SHCThermostat(api=None, raw_device=self._rd("TRV"), raw_device_services=[])
        assert obj._thermostat_service is None                     # lines 80-81

    def test_powerswitch_mixin_via_smartplug(self):
        from boschshcpy.models_impl import SHCSmartPlug
        obj = SHCSmartPlug(api=None, raw_device=self._rd("PSM"), raw_device_services=[])
        assert obj._powerswitch_service is None                    # lines 100-101

    def test_powerswitchprogram_mixin_via_smartplug(self):
        from boschshcpy.models_impl import SHCSmartPlug
        obj = SHCSmartPlug(api=None, raw_device=self._rd("PSM"), raw_device_services=[])
        assert obj._powerswitchprogram_service is None             # lines 120-121

    def test_temperaturelevel_mixin_via_walltherm(self):
        from boschshcpy.models_impl import SHCWallThermostat
        obj = SHCWallThermostat(api=None, raw_device=self._rd("THB"), raw_device_services=[])
        assert obj._temperaturelevel_service is None               # lines 130-131

    def test_humiditylevel_mixin_via_walltherm(self):
        from boschshcpy.models_impl import SHCWallThermostat
        obj = SHCWallThermostat(api=None, raw_device=self._rd("THB"), raw_device_services=[])
        assert obj._humiditylevel_service is None                  # lines 142-143

    def test_temperatureoffset_mixin_via_thermostat(self):
        from boschshcpy.models_impl import SHCThermostat
        obj = SHCThermostat(api=None, raw_device=self._rd("TRV"), raw_device_services=[])
        assert obj._temperatureoffset_service is None              # lines 156-157

    def test_silentmode_mixin_via_thermostat(self):
        from boschshcpy.models_impl import SHCThermostat
        obj = SHCThermostat(api=None, raw_device=self._rd("TRV"), raw_device_services=[])
        assert obj._silentmode_service is None                     # lines 186-187

    def test_smokedetector_init(self):
        from boschshcpy.models_impl import SHCSmokeDetector
        obj = SHCSmokeDetector(api=None, raw_device=self._rd("SD"), raw_device_services=[])
        assert obj._alarm_service is None                          # lines 210-213

    def test_smartplug_init(self):
        from boschshcpy.models_impl import SHCSmartPlug
        obj = SHCSmartPlug(api=None, raw_device=self._rd("PSM"), raw_device_services=[])
        assert obj._routing_service is None                        # lines 239-241

    def test_micromodulerelay_init(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        obj = SHCMicromoduleRelay(api=None, raw_device=self._rd("MICROMODULE_RELAY"), raw_device_services=[])
        assert obj._impulseswitch_service is None                  # lines 284-286

    def test_shuttercontrol_init(self):
        from boschshcpy.models_impl import SHCShutterControl
        obj = SHCShutterControl(api=None, raw_device=self._rd("BBL"), raw_device_services=[])
        assert obj._service is None                                # lines 318-319

    def test_micromoduleshuttercontrol_init(self):
        from boschshcpy.models_impl import SHCMicromoduleShutterControl
        obj = SHCMicromoduleShutterControl(api=None, raw_device=self._rd("MICROMODULE_SHUTTER"), raw_device_services=[])
        assert obj._keypad_service is None                         # lines 343-344

    def test_micromoduleblinds_init(self):
        from boschshcpy.models_impl import SHCMicromoduleBlinds
        obj = SHCMicromoduleBlinds(api=None, raw_device=self._rd("MICROMODULE_BLINDS"), raw_device_services=[])
        assert obj._blindscontrol_service is None                  # lines 379-381

    def test_shuttercontact_init(self):
        from boschshcpy.models_impl import SHCShutterContact
        obj = SHCShutterContact(api=None, raw_device=self._rd("SWD"), raw_device_services=[])
        assert obj._service is None                                # lines 415-416

    def test_shuttercontact2_init(self):
        from boschshcpy.models_impl import SHCShutterContact2
        obj = SHCShutterContact2(api=None, raw_device=self._rd("SWD2"), raw_device_services=[])
        assert obj._bypass_service is None                         # lines 431-432

    def test_shuttercontact2plus_init(self):
        from boschshcpy.models_impl import SHCShutterContact2Plus
        obj = SHCShutterContact2Plus(api=None, raw_device=self._rd("SWD2_PLUS"), raw_device_services=[])
        assert obj._vibrationsensor_service is None                # lines 449-450

    def test_camera360_init(self):
        from boschshcpy.models_impl import SHCCamera360
        obj = SHCCamera360(api=None, raw_device=self._rd("CAMERA_360"), raw_device_services=[])
        assert obj._privacymode_service is None                    # lines 477-480

    def test_cameraeyes_init(self):
        from boschshcpy.models_impl import SHCCameraEyes
        obj = SHCCameraEyes(api=None, raw_device=self._rd("CAMERA_EYES"), raw_device_services=[])
        assert obj._cameralight_service is None                    # lines 511-512

    def test_cameraoutdoorgen2_init(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        obj = SHCCameraOutdoorGen2(api=None, raw_device=self._rd("CAMERA_OUTDOOR_GEN2"), raw_device_services=[])
        assert obj._cameraambientlight_service is None             # lines 531-533

    def test_thermostat_valvetappet_init(self):
        from boschshcpy.models_impl import SHCThermostat
        obj = SHCThermostat(api=None, raw_device=self._rd("TRV"), raw_device_services=[])
        assert obj._valvetappet_service is None                    # lines 574-575

    def test_climatecontrol_init(self):
        from boschshcpy.models_impl import SHCClimateControl
        obj = SHCClimateControl(api=None, raw_device=self._rd("ROOM_CLIMATE_CONTROL"), raw_device_services=[])
        assert obj._roomclimatecontrol_service is None             # lines 590-591

    def test_heatingcircuit_init(self):
        from boschshcpy.models_impl import SHCHeatingCircuit
        obj = SHCHeatingCircuit(api=None, raw_device=self._rd("HEATING_CIRCUIT"), raw_device_services=[])
        assert obj._heating_circuit_service is None                # lines 662-663

    def test_universalswitch_init(self):
        from boschshcpy.models_impl import SHCUniversalSwitch
        obj = SHCUniversalSwitch(api=None, raw_device=self._rd("WRC2"), raw_device_services=[])
        assert obj._keypad_service is None                         # lines 715-716

    def test_universalswitch2_init(self):
        from boschshcpy.models_impl import SHCUniversalSwitch2
        obj = SHCUniversalSwitch2(api=None, raw_device=self._rd("SWITCH2"), raw_device_services=[])
        assert obj._keypad_service is None                         # line 747 (super().__init__)

    def test_motiondetector_init(self):
        from boschshcpy.models_impl import SHCMotionDetector
        obj = SHCMotionDetector(api=None, raw_device=self._rd("MD"), raw_device_services=[])
        assert obj._service is None                                # lines 763-765

    def test_motiondetector2_init(self):
        from boschshcpy.models_impl import SHCMotionDetector2
        obj = SHCMotionDetector2(api=None, raw_device=self._rd("MD2"), raw_device_services=[])
        assert obj._multi_level_switch_service is None             # lines 793-805

    def test_twinguard_init(self):
        from boschshcpy.models_impl import SHCTwinguard
        obj = SHCTwinguard(api=None, raw_device=self._rd("TWINGUARD"), raw_device_services=[])
        assert obj._airqualitylevel_service is None                # lines 864-866

    def test_smokedetectionsystem_init(self):
        from boschshcpy.models_impl import SHCSmokeDetectionSystem
        obj = SHCSmokeDetectionSystem(api=None, raw_device=self._rd("SMOKE_DETECTION_SYSTEM"), raw_device_services=[])
        assert obj._surveillancealarm_service is None              # lines 914-915

    def test_presencesimulationsystem_init(self):
        from boschshcpy.models_impl import SHCPresenceSimulationSystem
        obj = SHCPresenceSimulationSystem(api=None, raw_device=self._rd("PRESENCE_SIMULATION_SERVICE"), raw_device_services=[])
        assert obj._presencesimulationconfiguration_service is None  # lines 927-928

    def test_shclight_init_no_services(self):
        from boschshcpy.models_impl import SHCLight
        obj = SHCLight(api=None, raw_device=self._rd("LEDVANCE_LIGHT"), raw_device_services=[])
        # Lines 955-968: init body + capabilities block
        assert obj._binaryswitch_service is None
        assert obj._multilevelswitch_service is None
        assert not obj.supports_brightness
        assert not obj.supports_color_temp
        assert not obj.supports_color_hsb

    def test_waterleakagesensor_init(self):
        from boschshcpy.models_impl import SHCWaterLeakageSensor
        obj = SHCWaterLeakageSensor(api=None, raw_device=self._rd("WLS"), raw_device_services=[])
        assert obj._leakage_service is None                        # lines 1046-1050

    def test_shclight_init_with_all_services_hits_capability_branches(self):
        """Lines 964, 966, 968 — the three `|=` arms only execute when init sees real services."""
        from boschshcpy.models_impl import SHCLight
        raw_device = {
            "id": "light-1", "rootDeviceId": "root-1", "manufacturer": "BOSCH",
            "roomId": "room-1", "deviceModel": "LEDVANCE_LIGHT", "serial": "SER-001",
            "profile": "LEDVANCE_LIGHT", "name": "Light", "status": "AVAILABLE",
            "deviceServiceIds": [],
        }
        raw_svcs = [
            {"id": "BinarySwitch", "deviceId": "light-1", "path": "/x",
             "@type": "DeviceServiceData",
             "state": {"@type": "bsState", "on": True}},
            {"id": "MultiLevelSwitch", "deviceId": "light-1", "path": "/x",
             "@type": "DeviceServiceData",
             "state": {"@type": "mlState", "level": 80}},
            {"id": "HueColorTemperature", "deviceId": "light-1", "path": "/x",
             "@type": "DeviceServiceData",
             "state": {"@type": "hctState", "colorTemperature": 4000,
                       "colorTemperatureRange": {"minCt": 2700, "maxCt": 6500}}},
            {"id": "HSBColorActuator", "deviceId": "light-1", "path": "/x",
             "@type": "DeviceServiceData",
             "state": {"@type": "hsbState", "rgb": 0xFF0000, "gamut": "A",
                       "colorTemperatureRange": {"minCt": 2000, "maxCt": 6500}}},
        ]
        obj = SHCLight(api=None, raw_device=raw_device, raw_device_services=raw_svcs)
        assert obj.supports_brightness is True                     # line 964 hit
        assert obj.supports_color_temp is True                     # line 966 hit
        assert obj.supports_color_hsb is True                      # line 968 hit


# ---------------------------------------------------------------------------
# Setter paths: TemperatureOffset.offset setter (line 165)
# ---------------------------------------------------------------------------

class TestTemperatureOffsetSetter:
    def _make(self):
        from boschshcpy.services_impl import TemperatureOffsetService
        from boschshcpy.models_impl import SHCThermostat

        api, calls = _mock_api()
        state = {"@type": "to", "offset": 0.0, "stepSize": 0.5, "minOffset": -5.0, "maxOffset": 5.0}
        to_svc = _fake_svc(TemperatureOffsetService, "TemperatureOffset", state, api=api)

        from boschshcpy.services_impl import (
            ValveTappetService, ThermostatService, TemperatureLevelService,
            BatteryLevelService, CommunicationQualityService, SilentModeService,
        )
        obj = SHCThermostat.__new__(SHCThermostat)
        obj._raw_device = _fake_raw_device(model="TRV")
        obj._callbacks = {}
        obj._api = api
        obj._temperatureoffset_service = to_svc
        # Stubs not under test:
        for attr in ("_valvetappet_service", "_thermostat_service", "_temperaturelevel_service",
                     "_batterylevel_service", "_communicationquality_service", "_silentmode_service"):
            setattr(obj, attr, None)
        return obj, calls

    def test_offset_setter_dispatches_put(self):
        obj, calls = self._make()
        obj.offset = 1.5                                           # line 165
        assert len(calls) == 1
        assert calls[0][1] == "TemperatureOffset"
        assert calls[0][2]["offset"] == 1.5

    def test_offset_setter_value_roundtrip(self):
        obj, calls = self._make()
        obj.offset = -2.0
        assert calls[0][2]["offset"] == -2.0


# ---------------------------------------------------------------------------
# Setter paths: SHCClimateControl setters (lines 599,607,615,627,635,643,651)
# ---------------------------------------------------------------------------

class TestClimateControlSetters:
    def _make(self):
        from boschshcpy.models_impl import SHCClimateControl
        from boschshcpy.services_impl import RoomClimateControlService, TemperatureLevelService

        api, calls = _mock_api()
        state = {
            "@type": "rcc",
            "operationMode": "AUTOMATIC",
            "setpointTemperature": 21.0,
            "setpointTemperatureForLevelEco": 17.0,
            "setpointTemperatureForLevelComfort": 22.0,
            "ventilationMode": False,
            "low": False,
            "boostMode": False,
            "summerMode": False,
            "supportsBoostMode": True,
            "roomControlMode": "HEATING",
        }
        rcc = _fake_svc(RoomClimateControlService, "RoomClimateControl", state, api=api)

        tl_state = {"@type": "tl", "temperature": 20.0}
        tl = _fake_svc(TemperatureLevelService, "TemperatureLevel", tl_state)

        obj = SHCClimateControl.__new__(SHCClimateControl)
        obj._raw_device = _fake_raw_device(model="ROOM_CLIMATE_CONTROL")
        obj._callbacks = {}
        obj._api = api
        obj._roomclimatecontrol_service = rcc
        obj._temperaturelevel_service = tl
        return obj, calls

    def test_setpoint_temperature_setter(self):
        obj, calls = self._make()
        obj.setpoint_temperature = 23.0                            # line 599
        assert any(c[2].get("setpointTemperature") == 23.0 for c in calls)

    def test_operation_mode_setter(self):
        from boschshcpy.services_impl import RoomClimateControlService
        obj, calls = self._make()
        obj.operation_mode = RoomClimateControlService.OperationMode.MANUAL  # line 607
        assert any(c[2].get("operationMode") == "MANUAL" for c in calls)

    def test_boost_mode_setter_true(self):
        obj, calls = self._make()
        obj.boost_mode = True                                      # line 615
        assert any(c[2].get("boostMode") is True for c in calls)

    def test_boost_mode_setter_false(self):
        obj, calls = self._make()
        obj.boost_mode = False
        assert any(c[2].get("boostMode") is False for c in calls)

    def test_low_setter_true(self):
        obj, calls = self._make()
        obj.low = True                                             # line 627
        assert any(c[2].get("low") is True for c in calls)

    def test_summer_mode_setter_true(self):
        obj, calls = self._make()
        obj.summer_mode = True                                     # line 635
        assert any(c[2].get("summerMode") is True for c in calls)

    def test_room_control_mode_setter(self):
        obj, calls = self._make()
        obj.room_control_mode = "COOLING"                          # line 643
        assert any(c[2].get("roomControlMode") == "COOLING" for c in calls)

    def test_cooling_mode_setter_true(self):
        obj, calls = self._make()
        obj.cooling_mode = True                                    # line 651 → sets roomControlMode=COOLING
        assert any(c[2].get("roomControlMode") == "COOLING" for c in calls)

    def test_cooling_mode_setter_false(self):
        obj, calls = self._make()
        obj.cooling_mode = False
        assert any(c[2].get("roomControlMode") == "HEATING" for c in calls)


# ---------------------------------------------------------------------------
# Setter path: SHCHeatingCircuit.operation_mode setter (line 679)
# ---------------------------------------------------------------------------

class TestHeatingCircuitSetter:
    def _make(self):
        from boschshcpy.models_impl import SHCHeatingCircuit
        from boschshcpy.services_impl import HeatingCircuitService

        api, calls = _mock_api()
        state = {
            "@type": "hc",
            "operationMode": "AUTOMATIC",
            "setpointTemperature": 22.0,
            "setpointTemperatureForLevelEco": 18.0,
            "setpointTemperatureForLevelComfort": 23.0,
            "temperatureOverrideModeActive": False,
            "temperatureOverrideFeatureEnabled": True,
            "energySavingFeatureEnabled": False,
            "on": True,
        }
        hc_svc = _fake_svc(HeatingCircuitService, "HeatingCircuit", state, api=api)

        obj = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
        obj._raw_device = _fake_raw_device(model="HEATING_CIRCUIT")
        obj._callbacks = {}
        obj._api = api
        obj._heating_circuit_service = hc_svc
        return obj, calls

    def test_setpoint_temperature_setter(self):
        obj, calls = self._make()
        obj.setpoint_temperature = 24.0
        assert any(c[2].get("setpointTemperature") == 24.0 for c in calls)

    def test_operation_mode_setter(self):
        from boschshcpy.services_impl import HeatingCircuitService
        obj, calls = self._make()
        obj.operation_mode = HeatingCircuitService.OperationMode.MANUAL  # line 679
        assert any(c[2].get("operationMode") == "MANUAL" for c in calls)


# ---------------------------------------------------------------------------
# SHCUniversalSwitch.eventtypes returns KeyEvent enum class (line 724)
# ---------------------------------------------------------------------------

class TestUniversalSwitchEventtypes:
    def _make(self):
        from boschshcpy.models_impl import SHCUniversalSwitch
        from boschshcpy.services_impl import KeypadService, BatteryLevelService

        kp = _fake_svc(KeypadService, "Keypad",
                       {"@type": "x", "keyCode": 1, "keyName": "LOWER_BUTTON",
                        "eventType": "PRESS_SHORT", "eventTimestamp": 1})
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

    def test_eventtypes_returns_keyevent_enum(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make()
        et = d.eventtypes                                          # line 724
        assert et is KeypadService.KeyEvent

    def test_eventtypes_contains_press_short(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make()
        assert KeypadService.KeyEvent.PRESS_SHORT in d.eventtypes


# ---------------------------------------------------------------------------
# SHCMicromoduleRelay: impulse_length getter (line 302),
#   trigger_impulse_state (297-298), instant_of_last_impulse with value (311)
# ---------------------------------------------------------------------------

class TestMicromoduleRelayImpulse:
    def _make(self, impulse_length=200, instant=None):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import (
            CommunicationQualityService, ChildProtectionService,
            PowerSwitchService, PowerSwitchProgramService, ImpulseSwitchService,
        )

        api, calls = _mock_api()
        imp_state = {"@type": "x", "impulseState": False, "impulseLength": impulse_length}
        if instant is not None:
            imp_state["instantOfLastImpulse"] = instant

        imp = _fake_svc(ImpulseSwitchService, "ImpulseSwitch", imp_state, api=api)
        cq = _fake_svc(CommunicationQualityService, "CommunicationQuality",
                       {"@type": "x", "quality": "GOOD"})
        cp = _fake_svc(ChildProtectionService, "ChildProtection",
                       {"@type": "x", "childLockActive": False})
        ps = _fake_svc(PowerSwitchService, "PowerSwitch",
                       {"@type": "x", "switchState": "OFF", "automaticPowerOffTime": 0})
        prog = _fake_svc(PowerSwitchProgramService, "PowerSwitchProgram",
                         {"@type": "x", "operationMode": "MANUAL"})

        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_RELAY")
        obj._device_services_by_id = {
            "CommunicationQuality": cq, "ChildProtection": cp,
            "PowerSwitch": ps, "PowerSwitchProgram": prog, "ImpulseSwitch": imp,
        }
        obj._callbacks = {}
        obj._api = api
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        obj._powerswitch_service = ps
        obj._powerswitchprogram_service = prog
        obj._impulseswitch_service = imp
        return obj, calls

    def test_impulse_length_getter(self):
        obj, _ = self._make(impulse_length=350)
        assert obj.impulse_length == 350                           # line 302

    def test_impulse_length_setter(self):
        obj, calls = self._make()
        obj.impulse_length = 500                                   # line 306
        assert any(c[2].get("impulseLength") == 500 for c in calls)

    def test_instant_of_last_impulse_present(self):
        obj, _ = self._make(instant="2024-06-01T10:00:00")
        assert obj.instant_of_last_impulse == "2024-06-01T10:00:00"  # line 311

    def test_instant_of_last_impulse_absent(self):
        obj, _ = self._make(instant=None)
        assert obj.instant_of_last_impulse is None

    def test_trigger_impulse_state_dispatches(self):
        obj, calls = self._make()
        obj.trigger_impulse_state()                                # lines 297-298
        assert any(c[2].get("impulseState") is True for c in calls)

    def test_trigger_impulse_state_no_service(self):
        obj, calls = self._make()
        obj._impulseswitch_service = None
        obj.trigger_impulse_state()                                # branch: service is None → no-op
        assert calls == []


# ---------------------------------------------------------------------------
# SHCMicromoduleShutterControl: eventtype setter (line 368)
# ---------------------------------------------------------------------------

class TestMicromoduleShutterControlEventtype:
    def _make(self):
        from boschshcpy.models_impl import SHCMicromoduleShutterControl
        from boschshcpy.services_impl import (
            ShutterControlService, CommunicationQualityService,
            ChildProtectionService, PowerMeterService, KeypadService,
        )

        kp = _fake_svc(KeypadService, "Keypad",
                       {"@type": "x", "keyCode": 0, "keyName": "UNDEFINED_BUTTON",
                        "eventType": "SWITCH_ON", "eventTimestamp": 0})
        sc = _fake_svc(ShutterControlService, "ShutterControl",
                       {"@type": "x", "operationState": "STOPPED", "level": 0.0, "calibrated": True})
        cq = _fake_svc(CommunicationQualityService, "CommunicationQuality",
                       {"@type": "x", "quality": "GOOD"})
        cp = _fake_svc(ChildProtectionService, "ChildProtection",
                       {"@type": "x", "childLockActive": False})
        pm = _fake_svc(PowerMeterService, "PowerMeter",
                       {"@type": "x", "powerConsumption": 0.0, "energyConsumption": 0.0})

        obj = SHCMicromoduleShutterControl.__new__(SHCMicromoduleShutterControl)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_SHUTTER")
        obj._device_services_by_id = {
            "Keypad": kp, "ShutterControl": sc, "CommunicationQuality": cq,
            "ChildProtection": cp, "PowerMeter": pm,
        }
        obj._callbacks = {}
        obj._api = None
        obj._keypad_service = kp
        obj._service = sc
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        obj._powermeter_service = pm
        return obj

    def test_keystates_contains_undefined(self):
        d = self._make()
        assert "UNDEFINED_BUTTON" in d.keystates

    def test_eventtypes_contains_switch_off(self):
        d = self._make()
        assert "SWITCH_OFF" in d.eventtypes

    def test_eventtype_setter_updates_state(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make()
        d.eventtype = KeypadService.KeyEvent.SWITCH_OFF            # line 368
        assert d._keypad_service._raw_state["eventType"] == "SWITCH_OFF"

    def test_eventtype_getter(self):
        from boschshcpy.services_impl import KeypadService
        d = self._make()
        assert d.eventtype == KeypadService.KeyEvent.SWITCH_ON

    def test_eventtimestamp(self):
        d = self._make()
        assert d.eventtimestamp == 0


# ---------------------------------------------------------------------------
# SHCMicromoduleBlinds: all blind-specific properties and setters
# (lines 385,389,393,397,401,405,408)
# ---------------------------------------------------------------------------

class TestMicromoduleBlinds:
    def _make(self):
        from boschshcpy.models_impl import SHCMicromoduleBlinds
        from boschshcpy.services_impl import (
            ShutterControlService, CommunicationQualityService,
            ChildProtectionService, PowerMeterService, KeypadService,
            BlindsControlService, BlindsSceneControlService,
        )

        api, calls = _mock_api()

        kp = _fake_svc(KeypadService, "Keypad",
                       {"@type": "x", "keyCode": 0, "keyName": "UNDEFINED_BUTTON",
                        "eventType": "SWITCH_ON", "eventTimestamp": 0})
        sc = _fake_svc(ShutterControlService, "ShutterControl",
                       {"@type": "x", "operationState": "STOPPED", "level": 0.5, "calibrated": True})
        cq = _fake_svc(CommunicationQualityService, "CommunicationQuality",
                       {"@type": "x", "quality": "GOOD"})
        cp = _fake_svc(ChildProtectionService, "ChildProtection",
                       {"@type": "x", "childLockActive": False})
        pm = _fake_svc(PowerMeterService, "PowerMeter",
                       {"@type": "x", "powerConsumption": 0.0, "energyConsumption": 0.0})
        bc = _fake_svc(BlindsControlService, "BlindsControl",
                       {"@type": "bc", "currentAngle": 45.0, "targetAngle": 90.0,
                        "blindsType": "EXTERIOR_BLINDS"}, api=api)
        bsc = _fake_svc(BlindsSceneControlService, "BlindsSceneControl",
                        {"@type": "bsc", "level": 0.75}, api=api)

        obj = SHCMicromoduleBlinds.__new__(SHCMicromoduleBlinds)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_BLINDS")
        obj._device_services_by_id = {
            "Keypad": kp, "ShutterControl": sc, "CommunicationQuality": cq,
            "ChildProtection": cp, "PowerMeter": pm,
            "BlindsControl": bc, "BlindsSceneControl": bsc,
        }
        obj._callbacks = {}
        obj._api = api
        obj._keypad_service = kp
        obj._service = sc
        obj._communicationquality_service = cq
        obj._childprotection_service = cp
        obj._powermeter_service = pm
        obj._blindscontrol_service = bc
        obj._blindsscenecontrol_service = bsc
        return obj, calls

    def test_current_angle(self):
        obj, _ = self._make()
        assert obj.current_angle == 45.0                          # line 385

    def test_target_angle_getter(self):
        obj, _ = self._make()
        assert obj.target_angle == 90.0                           # line 389

    def test_target_angle_setter(self):
        obj, calls = self._make()
        obj.target_angle = 60.0                                   # line 393
        assert any(c[2].get("targetAngle") == 60.0 for c in calls)

    def test_blinds_level_getter(self):
        obj, _ = self._make()
        assert obj.blinds_level == 0.75                           # line 397

    def test_blinds_level_setter(self):
        obj, calls = self._make()
        obj.blinds_level = 0.25                                   # line 401
        assert any(c[2].get("level") == 0.25 for c in calls)

    def test_blinds_type(self):
        obj, _ = self._make()
        from boschshcpy.services_impl import BlindsControlService
        assert obj.blinds_type == BlindsControlService.BlindsType.EXTERIOR_BLINDS

    def test_stop_blinds(self):
        from unittest.mock import MagicMock
        obj, calls = self._make()
        obj._service.put_state_element = MagicMock()
        obj.stop_blinds()
        obj._service.put_state_element.assert_called_once_with(
            "operationState", "STOPPED"
        )


# ---------------------------------------------------------------------------
# build() function (line 1142)
# ---------------------------------------------------------------------------

class TestBuildFunction:
    def test_build_psm(self):
        from boschshcpy.models_impl import build, SHCSmartPlug
        rd = _fake_raw_device(model="PSM")
        obj = build(api=None, raw_device=rd, raw_device_services=[])
        assert isinstance(obj, SHCSmartPlug)                      # line 1142

    def test_build_sd(self):
        from boschshcpy.models_impl import build, SHCSmokeDetector
        rd = _fake_raw_device(model="SD")
        obj = build(api=None, raw_device=rd, raw_device_services=[])
        assert isinstance(obj, SHCSmokeDetector)

    def test_build_camera_360(self):
        from boschshcpy.models_impl import build, SHCCamera360
        rd = _fake_raw_device(model="CAMERA_360")
        obj = build(api=None, raw_device=rd, raw_device_services=[])
        assert isinstance(obj, SHCCamera360)

    def test_build_unsupported_raises(self):
        from boschshcpy.models_impl import build
        rd = _fake_raw_device(model="UNKNOWN_MODEL_XYZ")
        with pytest.raises(ValueError):
            build(api=None, raw_device=rd, raw_device_services=[])


# ---------------------------------------------------------------------------
# put_state-tracked setter paths not covered by existing tests
# ---------------------------------------------------------------------------

class TestChildLockSetter:
    """_ChildProtection.child_lock setter (line 71) via SHCLightSwitch."""

    def _make(self):
        from boschshcpy.models_impl import SHCLightSwitch
        from boschshcpy.services_impl import (
            ChildProtectionService, PowerSwitchService, PowerSwitchProgramService,
        )
        api, calls = _mock_api()
        cp = _fake_svc(ChildProtectionService, "ChildProtection",
                       {"@type": "cp", "childLockActive": False}, api=api)
        ps = _fake_svc(PowerSwitchService, "PowerSwitch",
                       {"@type": "x", "switchState": "OFF", "automaticPowerOffTime": 0})
        prog = _fake_svc(PowerSwitchProgramService, "PowerSwitchProgram",
                         {"@type": "x", "operationMode": "MANUAL"})

        obj = SHCLightSwitch.__new__(SHCLightSwitch)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_LIGHT_ATTACHED")
        obj._callbacks = {}
        obj._api = api
        obj._childprotection_service = cp
        obj._powerswitch_service = ps
        obj._powerswitchprogram_service = prog
        return obj, calls

    def test_child_lock_setter_true(self):
        obj, calls = self._make()
        obj.child_lock = True                                      # line 71
        assert any(c[2].get("childLockActive") is True for c in calls)

    def test_child_lock_setter_false(self):
        obj, calls = self._make()
        obj.child_lock = False
        assert any(c[2].get("childLockActive") is False for c in calls)


class TestThermostatChildLockSetter:
    """_Thermostat.child_lock setter (line 89-91)."""

    def _make(self):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import ThermostatService

        api, calls = _mock_api()
        th = _fake_svc(ThermostatService, "Thermostat",
                       {"@type": "th", "childLock": "OFF"}, api=api)

        obj = SHCThermostat.__new__(SHCThermostat)
        obj._raw_device = _fake_raw_device(model="TRV")
        obj._callbacks = {}
        obj._api = api
        obj._thermostat_service = th
        for attr in ("_valvetappet_service", "_temperaturelevel_service",
                     "_batterylevel_service", "_communicationquality_service",
                     "_silentmode_service", "_temperatureoffset_service"):
            setattr(obj, attr, None)
        return obj, calls

    def test_child_lock_true_sends_on(self):
        obj, calls = self._make()
        obj.child_lock = True                                      # line 89-91
        assert any(c[2].get("childLock") == "ON" for c in calls)

    def test_child_lock_false_sends_off(self):
        obj, calls = self._make()
        obj.child_lock = False
        assert any(c[2].get("childLock") == "OFF" for c in calls)


class TestPowerSwitchSetter:
    """_PowerSwitch.switchstate setter (line 108-111)."""

    def _make(self):
        from boschshcpy.models_impl import SHCSmartPlug
        from boschshcpy.services_impl import (
            PowerSwitchService, RoutingService, PowerMeterService, PowerSwitchProgramService,
        )
        api, calls = _mock_api()
        ps = _fake_svc(PowerSwitchService, "PowerSwitch",
                       {"@type": "x", "switchState": "OFF", "automaticPowerOffTime": 0}, api=api)
        rt = _fake_svc(RoutingService, "Routing",
                       {"@type": "x", "value": "ENABLED"})
        pm = _fake_svc(PowerMeterService, "PowerMeter",
                       {"@type": "x", "powerConsumption": 0.0, "energyConsumption": 0.0})
        prog = _fake_svc(PowerSwitchProgramService, "PowerSwitchProgram",
                         {"@type": "x", "operationMode": "MANUAL"})

        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device(model="PSM")
        obj._callbacks = {}
        obj._api = api
        obj._powerswitch_service = ps
        obj._routing_service = rt
        obj._powermeter_service = pm
        obj._powerswitchprogram_service = prog
        return obj, calls

    def test_switchstate_setter_true(self):
        obj, calls = self._make()
        obj.switchstate = True                                     # line 108-111
        assert any(c[2].get("switchState") == "ON" for c in calls)

    def test_switchstate_setter_false(self):
        obj, calls = self._make()
        obj.switchstate = False
        assert any(c[2].get("switchState") == "OFF" for c in calls)

    def test_routing_setter_true(self):
        from boschshcpy.services_impl import RoutingService
        from boschshcpy.models_impl import SHCSmartPlug
        api, calls = _mock_api()
        rt = _fake_svc(RoutingService, "Routing",
                       {"@type": "x", "value": "DISABLED"}, api=api)
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device(model="PSM")
        obj._callbacks = {}
        obj._api = api
        obj._routing_service = rt
        for attr in ("_powerswitch_service", "_powermeter_service", "_powerswitchprogram_service"):
            setattr(obj, attr, None)
        obj.routing = True
        assert any(c[2].get("value") == "ENABLED" for c in calls)

    def test_routing_setter_false(self):
        from boschshcpy.services_impl import RoutingService
        from boschshcpy.models_impl import SHCSmartPlug
        api, calls = _mock_api()
        rt = _fake_svc(RoutingService, "Routing",
                       {"@type": "x", "value": "ENABLED"}, api=api)
        obj = SHCSmartPlug.__new__(SHCSmartPlug)
        obj._raw_device = _fake_raw_device(model="PSM")
        obj._callbacks = {}
        obj._api = api
        obj._routing_service = rt
        for attr in ("_powerswitch_service", "_powermeter_service", "_powerswitchprogram_service"):
            setattr(obj, attr, None)
        obj.routing = False
        assert any(c[2].get("value") == "DISABLED" for c in calls)


class TestBypassSetter:
    """SHCShutterContact2.bypass setter (line 440-442)."""

    def _make(self):
        from boschshcpy.models_impl import SHCShutterContact2
        from boschshcpy.services_impl import (
            BypassService, ShutterContactService, BatteryLevelService, CommunicationQualityService,
        )
        api, calls = _mock_api()
        bypass = _fake_svc(BypassService, "Bypass",
                           {"@type": "x", "state": "BYPASS_INACTIVE"}, api=api)
        sc = _fake_svc(ShutterContactService, "ShutterContact",
                       {"@type": "x", "value": "CLOSED"})
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}
        cq = _fake_svc(CommunicationQualityService, "CommunicationQuality",
                       {"@type": "x", "quality": "GOOD"})

        obj = SHCShutterContact2.__new__(SHCShutterContact2)
        obj._raw_device = _fake_raw_device(model="SWD2")
        obj._callbacks = {}
        obj._api = api
        obj._bypass_service = bypass
        obj._service = sc
        obj._batterylevel_service = bat
        obj._communicationquality_service = cq
        return obj, calls

    def test_bypass_setter_true(self):
        obj, calls = self._make()
        obj.bypass = True                                          # line 440-442
        assert any(c[2].get("state") == "BYPASS_ACTIVE" for c in calls)

    def test_bypass_setter_false(self):
        obj, calls = self._make()
        obj.bypass = False
        assert any(c[2].get("state") == "BYPASS_INACTIVE" for c in calls)


class TestVibrationSensorSetter:
    """SHCShutterContact2Plus.enabled and sensitivity setters."""

    def _make(self):
        from boschshcpy.models_impl import SHCShutterContact2Plus
        from boschshcpy.services_impl import (
            VibrationSensorService, BypassService,
            ShutterContactService, BatteryLevelService, CommunicationQualityService,
        )
        api, calls = _mock_api()
        vib = _fake_svc(VibrationSensorService, "VibrationSensor",
                        {"@type": "x", "value": "NO_VIBRATION", "enabled": True,
                         "sensitivity": "HIGH"}, api=api)
        bypass = _fake_svc(BypassService, "Bypass",
                           {"@type": "x", "state": "BYPASS_INACTIVE"})
        sc = _fake_svc(ShutterContactService, "ShutterContact",
                       {"@type": "x", "value": "CLOSED"})
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}
        cq = _fake_svc(CommunicationQualityService, "CommunicationQuality",
                       {"@type": "x", "quality": "GOOD"})

        obj = SHCShutterContact2Plus.__new__(SHCShutterContact2Plus)
        obj._raw_device = _fake_raw_device(model="SWD2_PLUS")
        obj._callbacks = {}
        obj._api = api
        obj._vibrationsensor_service = vib
        obj._bypass_service = bypass
        obj._service = sc
        obj._batterylevel_service = bat
        obj._communicationquality_service = cq
        return obj, calls

    def test_enabled_setter_false(self):
        obj, calls = self._make()
        obj.enabled = False                                        # line 462
        assert any(c[2].get("enabled") is False for c in calls)

    def test_sensitivity_setter(self):
        from boschshcpy.services_impl import VibrationSensorService
        obj, calls = self._make()
        obj.sensitivity = VibrationSensorService.SensitivityState.LOW  # line 470
        assert any(c[2].get("sensitivity") == "LOW" for c in calls)


class TestCameraPrivacySetters:
    """SHCCamera360.privacymode and cameranotification setters."""

    def _make(self, has_notif=True):
        from boschshcpy.models_impl import SHCCamera360
        from boschshcpy.services_impl import PrivacyModeService, CameraNotificationService

        api, calls = _mock_api()
        priv = _fake_svc(PrivacyModeService, "PrivacyMode",
                         {"@type": "x", "value": "DISABLED"}, api=api)
        notif = None
        if has_notif:
            notif = _fake_svc(CameraNotificationService, "CameraNotification",
                              {"@type": "x", "value": "ENABLED"}, api=api)

        obj = SHCCamera360.__new__(SHCCamera360)
        obj._raw_device = _fake_raw_device(model="CAMERA_360")
        obj._callbacks = {}
        obj._api = api
        obj._privacymode_service = priv
        obj._cameranotification_service = notif
        return obj, calls

    def test_privacymode_setter_on(self):
        obj, calls = self._make()
        obj.privacymode = True                                     # → "DISABLED" (privacy ON = stream OFF)
        assert any(c[2].get("value") == "DISABLED" for c in calls)

    def test_privacymode_setter_off(self):
        obj, calls = self._make()
        obj.privacymode = False
        assert any(c[2].get("value") == "ENABLED" for c in calls)

    def test_cameranotification_setter_true(self):
        obj, calls = self._make()
        obj.cameranotification = True                              # line 500-502
        assert any(c[2].get("value") == "ENABLED" for c in calls)

    def test_cameranotification_setter_false(self):
        obj, calls = self._make()
        obj.cameranotification = False
        assert any(c[2].get("value") == "DISABLED" for c in calls)

    def test_cameranotification_setter_noop_when_absent(self):
        obj, calls = self._make(has_notif=False)
        obj.cameranotification = True                              # no service → no call
        assert calls == []


class TestCameraLightSetters:
    """SHCCameraEyes.cameralight setter."""

    def _make(self, has_light=True):
        from boschshcpy.models_impl import SHCCameraEyes
        from boschshcpy.services_impl import (
            PrivacyModeService, CameraNotificationService, CameraLightService,
        )
        api, calls = _mock_api()
        priv = _fake_svc(PrivacyModeService, "PrivacyMode",
                         {"@type": "x", "value": "DISABLED"})
        notif = _fake_svc(CameraNotificationService, "CameraNotification",
                          {"@type": "x", "value": "ENABLED"})
        light = None
        if has_light:
            light = _fake_svc(CameraLightService, "CameraLight",
                              {"@type": "x", "value": "OFF"}, api=api)

        obj = SHCCameraEyes.__new__(SHCCameraEyes)
        obj._raw_device = _fake_raw_device(model="CAMERA_EYES")
        obj._callbacks = {}
        obj._api = api
        obj._privacymode_service = priv
        obj._cameranotification_service = notif
        obj._cameralight_service = light
        return obj, calls

    def test_cameralight_setter_on(self):
        obj, calls = self._make()
        obj.cameralight = True                                     # line 522
        assert any(c[2].get("value") == "ON" for c in calls)

    def test_cameralight_setter_off(self):
        obj, calls = self._make()
        obj.cameralight = False
        assert any(c[2].get("value") == "OFF" for c in calls)

    def test_cameralight_setter_noop_when_absent(self):
        obj, calls = self._make(has_light=False)
        obj.cameralight = True
        assert calls == []


class TestCameraOutdoorGen2Setters:
    """SHCCameraOutdoorGen2 ambient/front light setters."""

    def _make(self):
        from boschshcpy.models_impl import SHCCameraOutdoorGen2
        from boschshcpy.services_impl import (
            PrivacyModeService, CameraNotificationService,
            CameraAmbientLightService, CameraFrontLightService,
        )
        api, calls = _mock_api()
        priv = _fake_svc(PrivacyModeService, "PrivacyMode",
                         {"@type": "x", "value": "DISABLED"})
        notif = _fake_svc(CameraNotificationService, "CameraNotification",
                          {"@type": "x", "value": "ENABLED"})
        amb = _fake_svc(CameraAmbientLightService, "CameraAmbientLight",
                        {"@type": "x", "value": "OFF"}, api=api)
        front = _fake_svc(CameraFrontLightService, "CameraFrontLight",
                          {"@type": "x", "value": "OFF"}, api=api)

        obj = SHCCameraOutdoorGen2.__new__(SHCCameraOutdoorGen2)
        obj._raw_device = _fake_raw_device(model="CAMERA_OUTDOOR_GEN2")
        obj._callbacks = {}
        obj._api = api
        obj._privacymode_service = priv
        obj._cameranotification_service = notif
        obj._cameraambientlight_service = amb
        obj._camerafrontlight_service = front
        return obj, calls

    def test_ambient_setter_on(self):
        obj, calls = self._make()
        obj.cameraambientlight = True                              # line 543
        assert any(c[2].get("value") == "ON" for c in calls)

    def test_ambient_setter_off(self):
        obj, calls = self._make()
        obj.cameraambientlight = False
        assert any(c[2].get("value") == "OFF" for c in calls)

    def test_front_setter_on(self):
        obj, calls = self._make()
        obj.camerafrontlight = True                                # line 555
        assert any(c[2].get("value") == "ON" for c in calls)

    def test_front_setter_off(self):
        obj, calls = self._make()
        obj.camerafrontlight = False
        assert any(c[2].get("value") == "OFF" for c in calls)

    def test_ambient_setter_noop_when_absent(self):
        obj, calls = self._make()
        obj._cameraambientlight_service = None
        obj.cameraambientlight = True
        # only front-light calls possible, no ambient call
        assert not any(c[1] == "CameraAmbientLight" for c in calls)

    def test_front_setter_noop_when_absent(self):
        obj, calls = self._make()
        obj._camerafrontlight_service = None
        obj.camerafrontlight = True
        assert not any(c[1] == "CameraFrontLight" for c in calls)


class TestSilentModeSetter:
    """_SilentMode.silentmode setter and no-service branch."""

    def _make(self, has_service=True):
        from boschshcpy.models_impl import SHCThermostat
        from boschshcpy.services_impl import SilentModeService

        api, calls = _mock_api()
        sm = None
        if has_service:
            sm = _fake_svc(SilentModeService, "SilentMode",
                           {"@type": "x", "mode": "MODE_NORMAL"}, api=api)

        obj = SHCThermostat.__new__(SHCThermostat)
        obj._raw_device = _fake_raw_device(model="TRV")
        obj._callbacks = {}
        obj._api = api
        obj._silentmode_service = sm
        for attr in ("_valvetappet_service", "_thermostat_service", "_temperaturelevel_service",
                     "_batterylevel_service", "_communicationquality_service",
                     "_temperatureoffset_service", "_batterylevel_service"):
            setattr(obj, attr, None)
        return obj, calls

    def test_silentmode_setter_true(self):
        obj, calls = self._make()
        obj.silentmode = True                                      # line 201-203
        assert any(c[2].get("mode") == "MODE_SILENT" for c in calls)

    def test_silentmode_setter_false(self):
        obj, calls = self._make()
        obj.silentmode = False
        assert any(c[2].get("mode") == "MODE_NORMAL" for c in calls)

    def test_silentmode_setter_noop_when_absent(self):
        obj, calls = self._make(has_service=False)
        obj.silentmode = True
        assert calls == []

    def test_silentmode_getter_none_when_absent(self):
        obj, _ = self._make(has_service=False)
        assert obj.silentmode is None


class TestPresenceSimulationSetter:
    """SHCPresenceSimulationSystem.enabled setter."""

    def _make(self):
        from boschshcpy.models_impl import SHCPresenceSimulationSystem
        from boschshcpy.services_impl import PresenceSimulationConfigurationService

        api, calls = _mock_api()
        svc = _fake_svc(PresenceSimulationConfigurationService,
                        "PresenceSimulationConfiguration",
                        {"@type": "x", "enabled": False}, api=api)
        obj = SHCPresenceSimulationSystem.__new__(SHCPresenceSimulationSystem)
        obj._raw_device = _fake_raw_device(model="PRESENCE_SIMULATION_SERVICE")
        obj._callbacks = {}
        obj._api = api
        obj._presencesimulationconfiguration_service = svc
        return obj, calls

    def test_enabled_setter_true(self):
        obj, calls = self._make()
        obj.enabled = True                                         # line 938
        assert any(c[2].get("enabled") is True for c in calls)

    def test_enabled_setter_false(self):
        obj, calls = self._make()
        obj.enabled = False
        assert any(c[2].get("enabled") is False for c in calls)


class TestSmokeDetectorSetters:
    """SHCSmokeDetector.alarmstate setter and smoketest_requested."""

    def _make(self):
        from boschshcpy.models_impl import SHCSmokeDetector
        from boschshcpy.services_impl import AlarmService, SmokeDetectorCheckService, BatteryLevelService

        api, calls = _mock_api()
        alarm = _fake_svc(AlarmService, "Alarm",
                          {"@type": "x", "value": "IDLE_OFF"}, api=api)
        check = _fake_svc(SmokeDetectorCheckService, "SmokeDetectorCheck",
                          {"@type": "x", "value": "NONE"}, api=api)
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCSmokeDetector.__new__(SHCSmokeDetector)
        obj._raw_device = _fake_raw_device(model="SD")
        obj._callbacks = {}
        obj._api = api
        obj._alarm_service = alarm
        obj._smokedetectorcheck_service = check
        obj._batterylevel_service = bat
        return obj, calls

    def test_alarmstate_setter(self):
        obj, calls = self._make()
        obj.alarmstate = "INTRUSION_ALARM"                         # line 221
        assert any(c[2].get("value") == "INTRUSION_ALARM" for c in calls)

    def test_smoketest_requested(self):
        obj, calls = self._make()
        obj.smoketest_requested()                                  # line 228-230
        assert any(c[2].get("value") == "SMOKE_TEST_REQUESTED" for c in calls)


class TestTwinguardSmoketest:
    """SHCTwinguard.smoketest_requested."""

    def _make(self):
        from boschshcpy.models_impl import SHCTwinguard
        from boschshcpy.services_impl import AirQualityLevelService, SmokeDetectorCheckService, BatteryLevelService

        api, calls = _mock_api()
        aql_state = {
            "@type": "x", "combinedRating": "GOOD", "description": "OK",
            "temperature": 22, "temperatureRating": "GOOD",
            "humidity": 55, "humidityRating": "GOOD",
            "purity": 800, "purityRating": "GOOD",
        }
        aql = _fake_svc(AirQualityLevelService, "AirQualityLevel", aql_state)
        chk = _fake_svc(SmokeDetectorCheckService, "SmokeDetectorCheck",
                        {"@type": "x", "value": "NONE"}, api=api)
        bat = BatteryLevelService.__new__(BatteryLevelService)
        bat._api = None
        bat._raw_device_service = {"id": "BatteryLevel", "deviceId": "d1", "path": "/x", "state": {}}
        bat._raw_state = {}
        bat._last_update = None; bat._callbacks = {}; bat._event_callbacks = {}

        obj = SHCTwinguard.__new__(SHCTwinguard)
        obj._raw_device = _fake_raw_device(model="TWINGUARD")
        obj._callbacks = {}
        obj._api = api
        obj._airqualitylevel_service = aql
        obj._smokedetectorcheck_service = chk
        obj._batterylevel_service = bat
        return obj, calls

    def test_smoketest_requested(self):
        obj, calls = self._make()
        obj.smoketest_requested()                                  # lines 904-907
        assert any(c[2].get("value") == "SMOKE_TEST_REQUESTED" for c in calls)


class TestShutterControlSetter:
    """SHCShutterControl.level setter and stop()."""

    def _make(self):
        from boschshcpy.models_impl import SHCShutterControl
        from boschshcpy.services_impl import ShutterControlService

        api, calls = _mock_api()
        svc = _fake_svc(ShutterControlService, "ShutterControl",
                        {"@type": "x", "operationState": "STOPPED", "level": 0.0, "calibrated": True},
                        api=api)
        obj = SHCShutterControl.__new__(SHCShutterControl)
        obj._raw_device = _fake_raw_device(model="BBL")
        obj._callbacks = {}
        obj._api = api
        obj._service = svc
        return obj, calls

    def test_level_setter(self):
        obj, calls = self._make()
        obj.level = 0.8                                            # line 327
        assert any(c[2].get("level") == 0.8 for c in calls)

    def test_stop(self):
        obj, calls = self._make()
        obj.stop()                                                 # line 330
        assert any(c[2].get("operationState") == "STOPPED" for c in calls)


class TestMicromoduleDimmerBinarystateSetter:
    """SHCMicromoduleDimmer.binarystate setter (line 1086-1089)."""

    def _make(self):
        from boschshcpy.models_impl import SHCMicromoduleDimmer
        from boschshcpy.services_impl import (
            PowerSwitchService, BinarySwitchService, MultiLevelSwitchService,
            CommunicationQualityService, ChildProtectionService,
        )
        api, calls = _mock_api()
        ps = _fake_svc(PowerSwitchService, "PowerSwitch",
                       {"@type": "x", "switchState": "OFF", "automaticPowerOffTime": 0}, api=api)
        bs = _fake_svc(BinarySwitchService, "BinarySwitch", {"@type": "x", "on": False})
        mls = _fake_svc(MultiLevelSwitchService, "MultiLevelSwitch", {"@type": "x", "level": 50})
        cq = _fake_svc(CommunicationQualityService, "CommunicationQuality", {"@type": "x", "quality": "GOOD"})
        cp = _fake_svc(ChildProtectionService, "ChildProtection", {"@type": "x", "childLockActive": False})

        obj = SHCMicromoduleDimmer.__new__(SHCMicromoduleDimmer)
        obj._raw_device = _fake_raw_device(model="MICROMODULE_DIMMER")
        obj._callbacks = {}
        obj._api = api
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
        return obj, calls

    def test_binarystate_setter_true(self):
        obj, calls = self._make()
        obj.binarystate = True                                     # line 1086-1089
        assert any(c[2].get("switchState") == "ON" for c in calls)

    def test_binarystate_setter_false(self):
        obj, calls = self._make()
        obj.binarystate = False
        assert any(c[2].get("switchState") == "OFF" for c in calls)

    def test_binarystate_getter_on(self):
        obj, _ = self._make()
        obj._powerswitch_service._raw_state["switchState"] = "ON"
        assert obj.binarystate is True

    def test_binarystate_getter_off(self):
        obj, _ = self._make()
        obj._powerswitch_service._raw_state["switchState"] = "OFF"
        assert obj.binarystate is False

    def test_binarystate_setter_noop_no_service(self):
        obj, calls = self._make()
        obj._powerswitch_service = None
        obj.binarystate = True
        assert calls == []
