"""APK BATCH 1 — crash-fixes + device recognition tests.

Covers:
1. ValveTappet.State — 3 new FIX_MOTOR_LOGIC_* enum members + previously missing members
2. Model ID aliases — BWTH24, WRC2, SWD2_DUAL, PLUG_COMPACT_DUAL in registry + accessors
3. HeatingCircuit.heating_type — HeatingType enum + missing-field guard
4. OccupancyDetection.last_occupancy_change_time — present + missing guard (service snake_case)
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_svc(cls, state_dict):
    """Build a service object via __new__ with injected fake state."""
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


def _fake_raw_device(model="HEATING_CIRCUIT"):
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
# 1. ValveTappet.State enum — all APK-spec members parse without ValueError
# ---------------------------------------------------------------------------

class TestValveTappetStateNewMembers:
    """The 3 new FIX_MOTOR_LOGIC_* members added for APK 10.33 batch 1."""

    def test_fix_motor_logic_requested_parses(self):
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "FIX_MOTOR_LOGIC_REQUESTED"})
        assert svc.value == ValveTappetService.State.FIX_MOTOR_LOGIC_REQUESTED

    def test_fix_motor_logic_in_progress_parses(self):
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "FIX_MOTOR_LOGIC_IN_PROGRESS"})
        assert svc.value == ValveTappetService.State.FIX_MOTOR_LOGIC_IN_PROGRESS

    def test_fix_motor_logic_successful_parses(self):
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "FIX_MOTOR_LOGIC_SUCCESSFUL"})
        assert svc.value == ValveTappetService.State.FIX_MOTOR_LOGIC_SUCCESSFUL

    def test_valve_adaption_requested_parses(self):
        """APK-confirmed member that was missing in the lib pre-batch1."""
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "VALVE_ADAPTION_REQUESTED"})
        assert svc.value == ValveTappetService.State.VALVE_ADAPTION_REQUESTED

    def test_start_position_requested_parses(self):
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "START_POSITION_REQUESTED"})
        assert svc.value == ValveTappetService.State.START_POSITION_REQUESTED

    def test_range_too_small_parses(self):
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "RANGE_TOO_SMALL"})
        assert svc.value == ValveTappetService.State.RANGE_TOO_SMALL

    def test_error_parses(self):
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "ERROR"})
        assert svc.value == ValveTappetService.State.ERROR

    def test_unknown_parses(self):
        from boschshcpy.services_impl import ValveTappetService
        svc = _make_svc(ValveTappetService, {"position": 0, "value": "UNKNOWN"})
        assert svc.value == ValveTappetService.State.UNKNOWN

    def test_all_known_states_are_distinct(self):
        """Sanity: all 17 APK-spec State members are unique strings."""
        from boschshcpy.services_impl import ValveTappetService
        values = [m.value for m in ValveTappetService.State]
        assert len(values) == len(set(values))

    def test_fix_motor_logic_requested_string_value(self):
        from boschshcpy.services_impl import ValveTappetService
        assert ValveTappetService.State.FIX_MOTOR_LOGIC_REQUESTED.value == "FIX_MOTOR_LOGIC_REQUESTED"

    def test_fix_motor_logic_in_progress_string_value(self):
        from boschshcpy.services_impl import ValveTappetService
        assert ValveTappetService.State.FIX_MOTOR_LOGIC_IN_PROGRESS.value == "FIX_MOTOR_LOGIC_IN_PROGRESS"

    def test_fix_motor_logic_successful_string_value(self):
        from boschshcpy.services_impl import ValveTappetService
        assert ValveTappetService.State.FIX_MOTOR_LOGIC_SUCCESSFUL.value == "FIX_MOTOR_LOGIC_SUCCESSFUL"

    def test_unknown_does_not_raise_valueerror(self):
        """Regression: firmware-added enum values must not crash via ValueError."""
        from boschshcpy.services_impl import ValveTappetService
        # All 3 new members parseable
        for name in ("FIX_MOTOR_LOGIC_REQUESTED", "FIX_MOTOR_LOGIC_IN_PROGRESS",
                     "FIX_MOTOR_LOGIC_SUCCESSFUL"):
            state = ValveTappetService.State(name)
            assert state.value == name


# ---------------------------------------------------------------------------
# 2. Model ID aliases — registry + device_helper accessor membership
# ---------------------------------------------------------------------------

class TestModelIdAliases:
    """BWTH24, WRC2, SWD2_DUAL, PLUG_COMPACT_DUAL must be in SUPPORTED_MODELS
    and map to the correct class."""

    def test_bwth24_in_supported_models(self):
        from boschshcpy.models_impl import SUPPORTED_MODELS
        assert "BWTH24" in SUPPORTED_MODELS

    def test_bwth24_maps_to_wall_thermostat(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCWallThermostat
        assert MODEL_MAPPING["BWTH24"] is SHCWallThermostat

    def test_wrc2_in_supported_models(self):
        from boschshcpy.models_impl import SUPPORTED_MODELS
        assert "WRC2" in SUPPORTED_MODELS

    def test_wrc2_maps_to_universal_switch(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCUniversalSwitch
        assert MODEL_MAPPING["WRC2"] is SHCUniversalSwitch

    def test_swd2_dual_in_supported_models(self):
        from boschshcpy.models_impl import SUPPORTED_MODELS
        assert "SWD2_DUAL" in SUPPORTED_MODELS

    def test_swd2_dual_maps_to_shutter_contact2(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCShutterContact2
        assert MODEL_MAPPING["SWD2_DUAL"] is SHCShutterContact2

    def test_plug_compact_dual_in_supported_models(self):
        from boschshcpy.models_impl import SUPPORTED_MODELS
        assert "PLUG_COMPACT_DUAL" in SUPPORTED_MODELS

    def test_plug_compact_dual_maps_to_smart_plug_compact(self):
        from boschshcpy.models_impl import MODEL_MAPPING, SHCSmartPlugCompact
        assert MODEL_MAPPING["PLUG_COMPACT_DUAL"] is SHCSmartPlugCompact


# ---------------------------------------------------------------------------
# 3. HeatingCircuit.heating_type — HeatingType enum + missing-field guard
# ---------------------------------------------------------------------------

class TestHeatingCircuitHeatingType:
    """HeatingType is new in APK 10.33; field may be absent on older firmware."""

    def _make_heating_svc(self, extra_state=None):
        from boschshcpy.services_impl import HeatingCircuitService
        state = {
            "operationMode": "AUTOMATIC",
            "setpointTemperature": 22.0,
            "setpointTemperatureForLevelEco": 18.0,
            "setpointTemperatureForLevelComfort": 23.0,
        }
        if extra_state:
            state.update(extra_state)
        return _make_svc(HeatingCircuitService, state)

    def _make_heating_model(self, extra_state=None):
        from boschshcpy.models_impl import SHCHeatingCircuit
        svc = self._make_heating_svc(extra_state)
        obj = SHCHeatingCircuit.__new__(SHCHeatingCircuit)
        obj._raw_device = _fake_raw_device(model="HEATING_CIRCUIT")
        obj._device_services_by_id = {"HeatingCircuit": svc}
        obj._callbacks = {}
        obj._api = None
        obj._heating_circuit_service = svc
        return obj

    def test_heating_type_radiator(self):
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._make_heating_svc({"heatingType": "RADIATOR"})
        assert svc.heating_type == HeatingCircuitService.HeatingType.RADIATOR

    def test_heating_type_convector(self):
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._make_heating_svc({"heatingType": "CONVECTOR"})
        assert svc.heating_type == HeatingCircuitService.HeatingType.CONVECTOR

    def test_heating_type_floor(self):
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._make_heating_svc({"heatingType": "FLOOR"})
        assert svc.heating_type == HeatingCircuitService.HeatingType.FLOOR

    def test_heating_type_airheating(self):
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._make_heating_svc({"heatingType": "AIRHEATING"})
        assert svc.heating_type == HeatingCircuitService.HeatingType.AIRHEATING

    def test_heating_type_fancoil(self):
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._make_heating_svc({"heatingType": "FANCOIL"})
        assert svc.heating_type == HeatingCircuitService.HeatingType.FANCOIL

    def test_heating_type_unknown_explicit(self):
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._make_heating_svc({"heatingType": "UNKNOWN"})
        assert svc.heating_type == HeatingCircuitService.HeatingType.UNKNOWN

    def test_heating_type_unrecognised_falls_back_to_unknown(self):
        """Future firmware values must not raise ValueError."""
        from boschshcpy.services_impl import HeatingCircuitService
        svc = self._make_heating_svc({"heatingType": "SOME_FUTURE_VALUE"})
        assert svc.heating_type == HeatingCircuitService.HeatingType.UNKNOWN

    def test_heating_type_missing_returns_none(self):
        """Field absent (older firmware) → None, not an exception."""
        svc = self._make_heating_svc()
        assert svc.heating_type is None

    def test_heating_type_passthrough_on_model(self):
        """SHCHeatingCircuit.heating_type delegates to the service."""
        from boschshcpy.services_impl import HeatingCircuitService
        obj = self._make_heating_model({"heatingType": "FLOOR"})
        assert obj.heating_type == HeatingCircuitService.HeatingType.FLOOR

    def test_heating_type_missing_passthrough_on_model(self):
        obj = self._make_heating_model()
        assert obj.heating_type is None

    def test_heating_type_enum_values_are_strings(self):
        from boschshcpy.services_impl import HeatingCircuitService
        for member in HeatingCircuitService.HeatingType:
            assert member.value == member.name


# ---------------------------------------------------------------------------
# 4. OccupancyDetection.last_occupancy_change_time (snake_case on service)
# ---------------------------------------------------------------------------

class TestOccupancyDetectionSnakeCase:
    """Service-level snake_case property added in batch 1 (returns None when absent)."""

    def test_last_occupancy_change_time_present(self):
        from boschshcpy.services_impl import OccupancyDetectionService
        svc = _make_svc(OccupancyDetectionService,
                        {"isOccupied": True, "lastOccupancyChangeTime": "2024-06-01T12:00:00+02:00"})
        assert svc.last_occupancy_change_time == "2024-06-01T12:00:00+02:00"

    def test_last_occupancy_change_time_absent_returns_none(self):
        from boschshcpy.services_impl import OccupancyDetectionService
        svc = _make_svc(OccupancyDetectionService, {"isOccupied": False})
        assert svc.last_occupancy_change_time is None

    def test_last_occupancy_change_time_none_value_in_state(self):
        """Explicit null in JSON → None."""
        from boschshcpy.services_impl import OccupancyDetectionService
        svc = _make_svc(OccupancyDetectionService,
                        {"isOccupied": False, "lastOccupancyChangeTime": None})
        assert svc.last_occupancy_change_time is None

    def test_camelcase_property_still_works(self):
        """Existing camelCase property must still return 'n/a' when absent (no regression)."""
        from boschshcpy.services_impl import OccupancyDetectionService
        svc = _make_svc(OccupancyDetectionService, {"isOccupied": False})
        assert svc.lastOccupancyChangeTime == "n/a"

    def test_camelcase_property_returns_value_when_present(self):
        from boschshcpy.services_impl import OccupancyDetectionService
        svc = _make_svc(OccupancyDetectionService,
                        {"isOccupied": True, "lastOccupancyChangeTime": "2025-01-01T00:00:00Z"})
        assert svc.lastOccupancyChangeTime == "2025-01-01T00:00:00Z"
