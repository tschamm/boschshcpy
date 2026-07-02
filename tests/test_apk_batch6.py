"""APK BATCH 6 — SwitchConfiguration service (full body).

SwitchConfiguration: SwitchType (NONE/PUSHBUTTON/SWITCH/NO_SWITCH/UNKNOWN),
ActuatorType (NORMALLY_CLOSED/NORMALLY_OPEN/UNSUPPORTED/UNKNOWN),
OutputMode (ATTACHED/DETACHED/DETACHED_SHORT_PRESS/DETACHED_LONG_PRESS/UNSUPPORTED/UNKNOWN)

Models bound: SHCLightControl, SHCMicromoduleRelay
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


def _fake_raw_device(model="MICROMODULE_RELAY"):
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
# BATCH 6: SwitchConfiguration service
# ---------------------------------------------------------------------------

class TestSwitchConfigurationService:
    def _svc(self, **state):
        from boschshcpy.services_impl import SwitchConfiguration
        return _make_svc(SwitchConfiguration, state)

    # SwitchType tests
    def test_switch_type_none(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="NONE")
        assert svc.switch_type == SwitchConfiguration.SwitchType.NONE

    def test_switch_type_pushbutton(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="PUSHBUTTON")
        assert svc.switch_type == SwitchConfiguration.SwitchType.PUSHBUTTON

    def test_switch_type_switch(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="SWITCH")
        assert svc.switch_type == SwitchConfiguration.SwitchType.SWITCH

    def test_switch_type_no_switch(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="NO_SWITCH")
        assert svc.switch_type == SwitchConfiguration.SwitchType.NO_SWITCH

    def test_switch_type_unknown_explicit(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="UNKNOWN")
        assert svc.switch_type == SwitchConfiguration.SwitchType.UNKNOWN

    def test_switch_type_missing_returns_none(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc()
        assert svc.switch_type is None

    def test_switch_type_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="FUTURE_TYPE")
        assert svc.switch_type == SwitchConfiguration.SwitchType.UNKNOWN

    # ActuatorType tests
    def test_actuator_type_normally_closed(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(actuatorType="NORMALLY_CLOSED")
        assert svc.actuator_type == SwitchConfiguration.ActuatorType.NORMALLY_CLOSED

    def test_actuator_type_normally_open(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(actuatorType="NORMALLY_OPEN")
        assert svc.actuator_type == SwitchConfiguration.ActuatorType.NORMALLY_OPEN

    def test_actuator_type_unsupported(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(actuatorType="UNSUPPORTED")
        assert svc.actuator_type == SwitchConfiguration.ActuatorType.UNSUPPORTED

    def test_actuator_type_unknown_explicit(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(actuatorType="UNKNOWN")
        assert svc.actuator_type == SwitchConfiguration.ActuatorType.UNKNOWN

    def test_actuator_type_missing_returns_none(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc()
        assert svc.actuator_type is None

    def test_actuator_type_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(actuatorType="FUTURE_ACTUATOR")
        assert svc.actuator_type == SwitchConfiguration.ActuatorType.UNKNOWN

    # OutputMode tests
    def test_output_mode_attached(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="ATTACHED")
        assert svc.output_mode == SwitchConfiguration.OutputMode.ATTACHED

    def test_output_mode_detached(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="DETACHED")
        assert svc.output_mode == SwitchConfiguration.OutputMode.DETACHED

    def test_output_mode_detached_short_press(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="DETACHED_SHORT_PRESS")
        assert svc.output_mode == SwitchConfiguration.OutputMode.DETACHED_SHORT_PRESS

    def test_output_mode_detached_long_press(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="DETACHED_LONG_PRESS")
        assert svc.output_mode == SwitchConfiguration.OutputMode.DETACHED_LONG_PRESS

    def test_output_mode_unsupported(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="UNSUPPORTED")
        assert svc.output_mode == SwitchConfiguration.OutputMode.UNSUPPORTED

    def test_output_mode_unknown_explicit(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="UNKNOWN")
        assert svc.output_mode == SwitchConfiguration.OutputMode.UNKNOWN

    def test_output_mode_missing_returns_none(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc()
        assert svc.output_mode is None

    def test_output_mode_bad_value_returns_unknown(self):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="FUTURE_MODE")
        assert svc.output_mode == SwitchConfiguration.OutputMode.UNKNOWN

    # Boolean fields
    def test_swap_inputs_true(self):
        svc = self._svc(swapInputs=True)
        assert svc.swap_inputs is True

    def test_swap_inputs_false(self):
        svc = self._svc(swapInputs=False)
        assert svc.swap_inputs is False

    def test_swap_inputs_missing_defaults_false(self):
        svc = self._svc()
        assert svc.swap_inputs is False

    def test_swap_outputs_true(self):
        svc = self._svc(swapOutputs=True)
        assert svc.swap_outputs is True

    def test_swap_outputs_false(self):
        svc = self._svc(swapOutputs=False)
        assert svc.swap_outputs is False

    def test_swap_outputs_missing_defaults_false(self):
        svc = self._svc()
        assert svc.swap_outputs is False

    def test_supports_swap_outputs_true(self):
        svc = self._svc(supportsSwapOutputs=True)
        assert svc.supports_swap_outputs is True

    def test_supports_swap_outputs_missing_returns_none(self):
        svc = self._svc()
        assert svc.supports_swap_outputs is None

    def test_supported_output_modes_list(self):
        modes = ["ATTACHED", "DETACHED"]
        svc = self._svc(supportedOutputModes=modes)
        assert svc.supported_output_modes == modes

    def test_supported_output_modes_missing_returns_empty(self):
        svc = self._svc()
        assert svc.supported_output_modes == []

    # Async setters
    def test_async_setter_switch_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="NONE")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_switchType(SwitchConfiguration.SwitchType.SWITCH))
        svc.async_put_state_element.assert_called_once_with("switchType", "SWITCH")

    def test_async_setter_swap_inputs(self):
        from unittest.mock import AsyncMock
        svc = self._svc(swapInputs=False)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_swapInputs(True))
        svc.async_put_state_element.assert_called_once_with("swapInputs", True)

    def test_async_setter_swap_outputs(self):
        from unittest.mock import AsyncMock
        svc = self._svc(swapOutputs=False)
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_swapOutputs(True))
        svc.async_put_state_element.assert_called_once_with("swapOutputs", True)

    def test_async_setter_actuator_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(actuatorType="NORMALLY_CLOSED")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_actuatorType(SwitchConfiguration.ActuatorType.NORMALLY_OPEN))
        svc.async_put_state_element.assert_called_once_with("actuatorType", "NORMALLY_OPEN")

    def test_async_setter_output_mode(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="ATTACHED")
        svc.async_put_state_element = AsyncMock()
        asyncio.run(svc.async_set_outputMode(SwitchConfiguration.OutputMode.DETACHED_SHORT_PRESS))
        svc.async_put_state_element.assert_called_once_with(
            "outputMode", "DETACHED_SHORT_PRESS"
        )

    # Property setters
    def test_property_setter_switch_type(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(switchType="NONE")
        svc.put_state_element = MagicMock()
        svc.switch_type = SwitchConfiguration.SwitchType.NO_SWITCH
        svc.put_state_element.assert_called_once_with("switchType", "NO_SWITCH")

    def test_property_setter_swap_inputs(self):
        from unittest.mock import MagicMock
        svc = self._svc(swapInputs=False)
        svc.put_state_element = MagicMock()
        svc.swap_inputs = True
        svc.put_state_element.assert_called_once_with("swapInputs", True)

    def test_property_setter_swap_outputs(self):
        from unittest.mock import MagicMock
        svc = self._svc(swapOutputs=False)
        svc.put_state_element = MagicMock()
        svc.swap_outputs = True
        svc.put_state_element.assert_called_once_with("swapOutputs", True)

    def test_property_setter_actuator_type(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(actuatorType="NORMALLY_CLOSED")
        svc.put_state_element = MagicMock()
        svc.actuator_type = SwitchConfiguration.ActuatorType.UNSUPPORTED
        svc.put_state_element.assert_called_once_with("actuatorType", "UNSUPPORTED")

    def test_property_setter_output_mode(self):
        from unittest.mock import MagicMock
        from boschshcpy.services_impl import SwitchConfiguration
        svc = self._svc(outputMode="ATTACHED")
        svc.put_state_element = MagicMock()
        svc.output_mode = SwitchConfiguration.OutputMode.DETACHED_LONG_PRESS
        svc.put_state_element.assert_called_once_with("outputMode", "DETACHED_LONG_PRESS")

    def test_in_service_mapping(self):
        from boschshcpy.services_impl import SERVICE_MAPPING, SwitchConfiguration
        assert "SwitchConfiguration" in SERVICE_MAPPING
        assert SERVICE_MAPPING["SwitchConfiguration"] is SwitchConfiguration

    def test_enum_switch_type_values(self):
        from boschshcpy.services_impl import SwitchConfiguration
        for member in SwitchConfiguration.SwitchType:
            assert member.value == member.name

    def test_enum_actuator_type_values(self):
        from boschshcpy.services_impl import SwitchConfiguration
        for member in SwitchConfiguration.ActuatorType:
            assert member.value == member.name

    def test_enum_output_mode_values(self):
        from boschshcpy.services_impl import SwitchConfiguration
        for member in SwitchConfiguration.OutputMode:
            assert member.value == member.name

    def test_summary(self, capsys):
        from boschshcpy.services_impl import SwitchConfiguration
        svc = _make_svc(
            SwitchConfiguration,
            {
                "switchType": "PUSHBUTTON",
                "swapInputs": False,
                "swapOutputs": False,
                "actuatorType": "NORMALLY_CLOSED",
                "outputMode": "ATTACHED",
                "supportsSwapOutputs": True,
                "supportedOutputModes": ["ATTACHED"],
            },
        )
        svc.summary()
        captured = capsys.readouterr()
        assert "switchType" in captured.out
        assert "actuatorType" in captured.out
        assert "outputMode" in captured.out


# ---------------------------------------------------------------------------
# SHCLightControl — SwitchConfiguration bindings
# ---------------------------------------------------------------------------

class TestSHCLightControlSwitchConfigBindings:
    def _make_light_control(self, sc_state=None):
        from boschshcpy.services_impl import SwitchConfiguration
        from boschshcpy.models_impl import SHCLightControl

        sc = _make_svc(SwitchConfiguration, sc_state or {}) if sc_state is not None else None

        obj = SHCLightControl.__new__(SHCLightControl)
        obj._raw_device = _fake_raw_device("MICROMODULE_LIGHT_CONTROL")
        obj._callbacks = {}
        obj._api = None
        obj._device_services_by_id = {}
        obj._switch_config_service = sc
        obj._communicationquality_service = None
        obj._powermeter_service = None
        return obj

    def test_switch_type_passthrough(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_light_control(sc_state={"switchType": "PUSHBUTTON"})
        assert obj.switch_type == SwitchConfiguration.SwitchType.PUSHBUTTON

    def test_swap_inputs_passthrough(self):
        obj = self._make_light_control(sc_state={"swapInputs": True})
        assert obj.swap_inputs is True

    def test_swap_outputs_passthrough(self):
        obj = self._make_light_control(sc_state={"swapOutputs": True})
        assert obj.swap_outputs is True

    def test_actuator_type_passthrough(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_light_control(sc_state={"actuatorType": "NORMALLY_OPEN"})
        assert obj.actuator_type == SwitchConfiguration.ActuatorType.NORMALLY_OPEN

    def test_output_mode_passthrough(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_light_control(sc_state={"outputMode": "DETACHED"})
        assert obj.output_mode == SwitchConfiguration.OutputMode.DETACHED

    def test_switch_config_absent_service_returns_defaults(self):
        from boschshcpy.models_impl import SHCLightControl
        obj = SHCLightControl.__new__(SHCLightControl)
        obj._switch_config_service = None
        assert obj.switch_type is None
        assert obj.swap_inputs is False
        assert obj.swap_outputs is False
        assert obj.actuator_type is None
        assert obj.output_mode is None

    def test_async_set_switch_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_light_control(sc_state={"switchType": "NONE"})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_switch_type(SwitchConfiguration.SwitchType.PUSHBUTTON))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "switchType", "PUSHBUTTON"
        )

    def test_async_set_swap_inputs(self):
        from unittest.mock import AsyncMock
        obj = self._make_light_control(sc_state={"swapInputs": False})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_swap_inputs(True))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "swapInputs", True
        )

    def test_async_set_swap_outputs(self):
        from unittest.mock import AsyncMock
        obj = self._make_light_control(sc_state={"swapOutputs": False})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_swap_outputs(True))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "swapOutputs", True
        )

    def test_async_set_actuator_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_light_control(sc_state={"actuatorType": "NORMALLY_CLOSED"})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_actuator_type(SwitchConfiguration.ActuatorType.NORMALLY_OPEN))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "actuatorType", "NORMALLY_OPEN"
        )

    def test_async_set_output_mode(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_light_control(sc_state={"outputMode": "ATTACHED"})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_output_mode(SwitchConfiguration.OutputMode.DETACHED))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "outputMode", "DETACHED"
        )

    def test_async_calls_no_op_when_service_absent(self):
        from boschshcpy.models_impl import SHCLightControl
        from boschshcpy.services_impl import SwitchConfiguration
        obj = SHCLightControl.__new__(SHCLightControl)
        obj._switch_config_service = None
        # Should not raise
        asyncio.run(obj.async_set_switch_type(SwitchConfiguration.SwitchType.NONE))
        asyncio.run(obj.async_set_swap_inputs(True))
        asyncio.run(obj.async_set_swap_outputs(True))
        asyncio.run(obj.async_set_actuator_type(SwitchConfiguration.ActuatorType.UNKNOWN))
        asyncio.run(obj.async_set_output_mode(SwitchConfiguration.OutputMode.UNKNOWN))

    # supports_swap_outputs — capability flag, distinct from the swap_outputs
    # value itself (same read-only-capability-vs-actual-value split pattern as
    # DetectionTest's detectionState vs detectionStateRequest). Must be
    # forwarded from the service so boschshc-hass can gate the "Swap Outputs"
    # entity on real device support instead of always creating it.
    def test_supports_swap_outputs_true_passthrough(self):
        obj = self._make_light_control(sc_state={"supportsSwapOutputs": True})
        assert obj.supports_swap_outputs is True

    def test_supports_swap_outputs_false_passthrough(self):
        obj = self._make_light_control(sc_state={"supportsSwapOutputs": False})
        assert obj.supports_swap_outputs is False

    def test_supports_swap_outputs_missing_returns_none(self):
        obj = self._make_light_control(sc_state={})
        assert obj.supports_swap_outputs is None

    def test_supports_swap_outputs_absent_service_returns_none(self):
        from boschshcpy.models_impl import SHCLightControl
        obj = SHCLightControl.__new__(SHCLightControl)
        obj._switch_config_service = None
        assert obj.supports_swap_outputs is None


# ---------------------------------------------------------------------------
# SHCMicromoduleRelay — SwitchConfiguration bindings
# ---------------------------------------------------------------------------

class TestSHCMicromoduleRelaySwitchConfigBindings:
    def _make_relay(self, sc_state=None):
        from boschshcpy.services_impl import SwitchConfiguration
        from boschshcpy.models_impl import SHCMicromoduleRelay

        sc = _make_svc(SwitchConfiguration, sc_state or {}) if sc_state is not None else None

        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._raw_device = _fake_raw_device("MICROMODULE_RELAY")
        obj._callbacks = {}
        obj._api = None
        obj._device_services_by_id = {}
        obj._switch_config_service = sc
        obj._impulseswitch_service = None
        obj._communicationquality_service = None
        obj._childprotection_service = None
        obj._powerswitch_service = None
        obj._powerswitchprogram_service = None
        return obj

    def test_switch_type_passthrough(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay(sc_state={"switchType": "SWITCH"})
        assert obj.switch_type == SwitchConfiguration.SwitchType.SWITCH

    def test_swap_inputs_passthrough(self):
        obj = self._make_relay(sc_state={"swapInputs": True})
        assert obj.swap_inputs is True

    def test_swap_outputs_passthrough(self):
        obj = self._make_relay(sc_state={"swapOutputs": True})
        assert obj.swap_outputs is True

    def test_actuator_type_passthrough(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay(sc_state={"actuatorType": "NORMALLY_CLOSED"})
        assert obj.actuator_type == SwitchConfiguration.ActuatorType.NORMALLY_CLOSED

    def test_output_mode_passthrough(self):
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay(sc_state={"outputMode": "DETACHED_SHORT_PRESS"})
        assert obj.output_mode == SwitchConfiguration.OutputMode.DETACHED_SHORT_PRESS

    def test_switch_config_absent_service_returns_defaults(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._switch_config_service = None
        assert obj.switch_type is None
        assert obj.swap_inputs is False
        assert obj.swap_outputs is False
        assert obj.actuator_type is None
        assert obj.output_mode is None

    def test_async_set_switch_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay(sc_state={"switchType": "NONE"})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_switch_type(SwitchConfiguration.SwitchType.NO_SWITCH))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "switchType", "NO_SWITCH"
        )

    def test_async_set_swap_inputs(self):
        from unittest.mock import AsyncMock
        obj = self._make_relay(sc_state={"swapInputs": False})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_swap_inputs(True))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "swapInputs", True
        )

    def test_async_set_swap_outputs(self):
        from unittest.mock import AsyncMock
        obj = self._make_relay(sc_state={"swapOutputs": False})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_swap_outputs(True))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "swapOutputs", True
        )

    def test_async_set_actuator_type(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay(sc_state={"actuatorType": "NORMALLY_CLOSED"})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_actuator_type(SwitchConfiguration.ActuatorType.UNSUPPORTED))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "actuatorType", "UNSUPPORTED"
        )

    def test_async_set_output_mode(self):
        from unittest.mock import AsyncMock
        from boschshcpy.services_impl import SwitchConfiguration
        obj = self._make_relay(sc_state={"outputMode": "ATTACHED"})
        obj._switch_config_service.async_put_state_element = AsyncMock()
        asyncio.run(obj.async_set_output_mode(SwitchConfiguration.OutputMode.DETACHED_LONG_PRESS))
        obj._switch_config_service.async_put_state_element.assert_called_once_with(
            "outputMode", "DETACHED_LONG_PRESS"
        )

    def test_async_calls_no_op_when_service_absent(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        from boschshcpy.services_impl import SwitchConfiguration
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._switch_config_service = None
        # Should not raise
        asyncio.run(obj.async_set_switch_type(SwitchConfiguration.SwitchType.NONE))
        asyncio.run(obj.async_set_swap_inputs(False))
        asyncio.run(obj.async_set_swap_outputs(False))
        asyncio.run(obj.async_set_actuator_type(SwitchConfiguration.ActuatorType.UNKNOWN))
        asyncio.run(obj.async_set_output_mode(SwitchConfiguration.OutputMode.UNKNOWN))

    # supports_swap_outputs — capability flag, distinct from the swap_outputs
    # value itself. Must be forwarded from the service so boschshc-hass can
    # gate the "Swap Outputs" entity on real device support instead of always
    # creating it (see SHCLightControl tests above for the same pattern).
    def test_supports_swap_outputs_true_passthrough(self):
        obj = self._make_relay(sc_state={"supportsSwapOutputs": True})
        assert obj.supports_swap_outputs is True

    def test_supports_swap_outputs_false_passthrough(self):
        obj = self._make_relay(sc_state={"supportsSwapOutputs": False})
        assert obj.supports_swap_outputs is False

    def test_supports_swap_outputs_missing_returns_none(self):
        obj = self._make_relay(sc_state={})
        assert obj.supports_swap_outputs is None

    def test_supports_swap_outputs_absent_service_returns_none(self):
        from boschshcpy.models_impl import SHCMicromoduleRelay
        obj = SHCMicromoduleRelay.__new__(SHCMicromoduleRelay)
        obj._switch_config_service = None
        assert obj.supports_swap_outputs is None
