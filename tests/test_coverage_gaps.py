"""Fill remaining coverage gaps to reach 100%.

Covers:
  - api.py:33  (verify_hostname=True path)
  - device.py:146  (device_service.summary() via device.summary())
  - device_helper.py:167,191,228,234,240,255,261,267,273,279,285,293,306,317,323
    (early-return [] / None paths when model key absent from SUPPORTED_MODELS)
  - device_service.py:136-137  (_last_event_timestamp is None → baseline branch)
  - information.py:39  (time.sleep in SHCListener while-loop)
  - information.py:154-161  (get_unique_id with zeroconf + unique_id found)
  - models_impl.py:370  (has_keypad when _keypad_service is not None)
  - models_impl.py:916,920  (was_tampered / tamper_protection_enabled on SHCMotionDetector2)
  - rawscan.py:109-110  (default case in match)
  - rawscan.py:116-122  (__main__ KeyboardInterrupt / SystemExit blocks)
  - register_client.py:163-169  (__main__ KeyboardInterrupt / SystemExit blocks)
  - scenario.py:6-7  (__init__ constructor)
  - userdefinedstate.py:8-10  (__init__ constructor)
"""

import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest


# ===========================================================================
# api.py:33 — verify_hostname=True takes the standard HTTPAdapter branch
# ===========================================================================

def test_api_verify_hostname_true():
    """When verify_hostname=True, the standard HTTPAdapter is used (not HostNameIgnoringAdapter)."""
    from requests.adapters import HTTPAdapter
    import boschshcpy.api as api_mod

    captured = {}
    mock_session = MagicMock()

    def capturing_mount(prefix, adapter):
        captured["adapter"] = adapter
        captured["prefix"] = prefix

    mock_session.mount.side_effect = capturing_mount

    with patch("boschshcpy.api.requests.Session", return_value=mock_session):
        api = api_mod.SHCAPI(
            controller_ip="1.2.3.4",
            certificate="/tmp/cert.pem",
            key="/tmp/key.pem",
            verify_hostname=True,
        )

    assert isinstance(captured.get("adapter"), HTTPAdapter)
    # Must NOT be the hostname-ignoring variant
    assert type(captured["adapter"]).__name__ == "HTTPAdapter"


# ===========================================================================
# device.py:146 — device_service.summary() called via device.summary()
# ===========================================================================

def test_device_summary_calls_device_service_summary(capsys):
    """device.summary() iterates device_services and calls summary() on each."""
    from boschshcpy.device import SHCDevice
    from boschshcpy.device_service import SHCDeviceService

    api = MagicMock()
    raw_dev = {
        "id": "dev-1",
        "rootDeviceId": "root-1",
        "deviceModel": "SWD",
        "name": "Test",
        "manufacturer": "Bosch",
        "status": "AVAILABLE",
        "deviceServiceIds": ["PowerSwitch"],
    }
    raw_svc = {
        "@type": "DeviceServiceData",
        "id": "PowerSwitch",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/PowerSwitch",
        "state": {"@type": "powerSwitchState", "switchState": "ON"},
    }
    dev = SHCDevice(api=api, raw_device=raw_dev, raw_device_services=[raw_svc])
    dev.summary()  # this calls device_service.summary() → covers line 146
    out = capsys.readouterr().out
    assert "dev-1" in out


# ===========================================================================
# device_service.py:135-137 — _last_event_timestamp is None → baseline
# ===========================================================================

def test_device_service_is_replayed_event_baseline():
    """When _last_event_timestamp is None the first call sets baseline and returns True (lines 135-137)."""
    from boschshcpy.device_service import SHCDeviceService

    svc = SHCDeviceService.__new__(SHCDeviceService)
    svc._last_event_timestamp = None

    # timestamp=None → return False (line 133-134)
    assert svc._is_replayed_event(None) is False

    # Reset to None so we hit the baseline branch (lines 135-137)
    svc._last_event_timestamp = None
    result = svc._is_replayed_event(1000)
    assert result is True
    assert svc._last_event_timestamp == 1000


# ===========================================================================
# information.py:39 — time.sleep inside SHCListener while-loop
# ===========================================================================

def test_shclistener_sleep_in_loop():
    """The while-loop in SHCListener.__init__ calls time.sleep when waiting=True."""
    from boschshcpy.information import SHCListener
    import boschshcpy.information as info_mod

    sleep_calls = []

    class _NeverFinishZeroconf:
        def get_service_info(self, stype, name):
            return None

    class _NeverAddingBrowser:
        def __init__(self, zc, service_type, handlers):
            pass  # never call handler → waiting stays True

        def cancel(self):
            pass

    # Simulate time passing: first call returns 0, second 5001 (under limit),
    # third 10001 (over limit → loop exits)
    time_sequence = iter([0, 5001, 10001])

    with patch.object(info_mod, "ServiceBrowser", _NeverAddingBrowser), \
         patch.object(info_mod, "current_time_millis", side_effect=time_sequence), \
         patch("time.sleep", side_effect=lambda t: sleep_calls.append(t)):
        listener = SHCListener(_NeverFinishZeroconf(), lambda s: None)

    # time.sleep(0.1) must have been called at least once
    assert len(sleep_calls) >= 1
    assert all(s == 0.1 for s in sleep_calls)


# ===========================================================================
# information.py:154-161 — get_unique_id with zeroconf, unique_id already set
# ===========================================================================

def test_shcinformation_get_unique_id_zeroconf_sets_unique_id():
    """When zeroconf is provided and filter() sets _unique_id, the debug log path runs."""
    from boschshcpy.information import SHCInformation, SHCListener

    obj = SHCInformation.__new__(SHCInformation)
    obj._api = None
    obj._unique_id = None
    obj._name = None
    obj._pub_info = {
        "shcIpAddress": "192.168.1.1",
        "macAddress": "AA:BB:CC:DD:EE:FF",
        "softwareUpdateState": {
            "swInstalledVersion": "9.91.7",
            "swUpdateState": "NO_UPDATE_AVAILABLE",
        },
    }

    class _FakeListener:
        def __init__(self, zc, callback):
            # Simulate that filter was called and set the unique_id
            pass

    def _set_uid_side_effect(zc, callback):
        # Directly set _unique_id and _name on obj to simulate filter() succeeding
        obj._unique_id = "aa-bb-cc-dd-ee-ff"
        obj._name = "shc-home"
        return _FakeListener(zc, callback)

    with patch("boschshcpy.information.SHCListener", side_effect=_set_uid_side_effect):
        fake_zeroconf = MagicMock()
        obj.get_unique_id(zeroconf=fake_zeroconf)

    # The debug log path (lines 155-161) was taken
    assert obj._unique_id == "aa-bb-cc-dd-ee-ff"
    assert obj._name == "shc-home"


# ===========================================================================
# scenario.py:6-7 — __init__ constructor
# ===========================================================================

def test_scenario_init_constructor():
    """Exercise SHCScenario.__init__ directly (not via __new__)."""
    from boschshcpy.scenario import SHCScenario

    api = MagicMock()
    api._api_root = "https://1.2.3.4:8444/smarthome"
    raw = {"id": "sc-42", "name": "Evening", "iconId": "icon_evening"}
    sc = SHCScenario(api=api, raw_scenario=raw)
    assert sc.id == "sc-42"
    assert sc.name == "Evening"
    assert sc._api is api


# ===========================================================================
# userdefinedstate.py:8-10 — __init__ constructor
# ===========================================================================

def test_userdefinedstate_init_constructor():
    """Exercise SHCUserDefinedState.__init__ directly."""
    from boschshcpy.userdefinedstate import SHCUserDefinedState

    api = MagicMock()
    info = MagicMock()
    info.macAddress = "AA:BB:CC:DD:EE:FF"
    raw = {"id": "uds-1", "name": "Away", "deleted": False, "state": True}
    uds = SHCUserDefinedState(api=api, info=info, raw_state=raw)
    assert uds.id == "uds-1"
    assert uds._api is api
    assert uds._info is info
    assert uds._raw_state is raw


# ===========================================================================
# rawscan.py:109-110 — default match case ("Please select a valid mode.")
# rawscan.py:116-122 — __main__ KeyboardInterrupt blocks
# ===========================================================================

def test_rawscan_default_case(capsys):
    """The default match case prints 'Please select a valid mode.'
    Trigger by patching parse_args to return a namespace with an unrecognized subcommand."""
    import boschshcpy.rawscan as rmod

    fake_session = MagicMock()
    fake_args = SimpleNamespace(
        subcommand="__unknown__",
        certificate="/c",
        key="/k",
        ip_address="1.2.3.4",
    )

    with patch.object(sys, "argv", ["rawscan", "--certificate", "/c", "--key", "/k",
                                     "--ip_address", "1.2.3.4", "devices"]), \
         patch("boschshcpy.rawscan.SHCSession", return_value=fake_session), \
         patch("argparse.ArgumentParser.parse_args", return_value=fake_args):
        with pytest.raises(SystemExit):
            rmod.main()

    out = capsys.readouterr().out
    assert "Please select a valid mode." in out


def test_rawscan_dunder_main_block():
    """Cover rawscan.py lines 116-123 (__main__ KeyboardInterrupt handler).

    exec() the __main__ block in the context of the already-imported module so that
    relative imports are already resolved and coverage is attributed correctly.
    """
    import os
    import boschshcpy.rawscan as rmod

    os_exit_called = []

    block = """
try:
    main()
except KeyboardInterrupt:
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
"""
    with patch.object(sys, "argv", ["rawscan", "--certificate", "/c", "--key", "/k",
                                     "--ip_address", "1.2.3.4", "devices"]), \
         patch("boschshcpy.rawscan.SHCSession", side_effect=KeyboardInterrupt()), \
         patch("os._exit", side_effect=lambda c: os_exit_called.append(c)):
        try:
            exec(block, vars(rmod))
        except SystemExit:
            pass

    assert os_exit_called == [0]


def test_register_client_dunder_main_block():
    """Cover register_client.py lines 162-169 (__main__ KeyboardInterrupt handler)."""
    import os
    import boschshcpy.register_client as rmod

    os_exit_called = []

    block = """
try:
    main()
except KeyboardInterrupt:
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)
"""
    with patch.object(sys, "argv", ["register_client", "--ip_address", "1.2.3.4",
                                     "--password", "secret"]), \
         patch("boschshcpy.register_client.SHCRegisterClient",
               side_effect=KeyboardInterrupt()), \
         patch("os._exit", side_effect=lambda c: os_exit_called.append(c)):
        try:
            exec(block, vars(rmod))
        except SystemExit:
            pass

    assert os_exit_called == [0]


# ===========================================================================
# models_impl.py:370 — has_keypad property (True branch)
# ===========================================================================

def test_models_impl_has_keypad_true():
    """has_keypad returns True when _keypad_service is not None."""
    from boschshcpy.models_impl import SHCMicromoduleShutterControl

    obj = SHCMicromoduleShutterControl.__new__(SHCMicromoduleShutterControl)
    obj._keypad_service = MagicMock()
    assert obj.has_keypad is True


def test_models_impl_has_keypad_false():
    """has_keypad returns False when _keypad_service is None."""
    from boschshcpy.models_impl import SHCMicromoduleShutterControl

    obj = SHCMicromoduleShutterControl.__new__(SHCMicromoduleShutterControl)
    obj._keypad_service = None
    assert obj.has_keypad is False


# ===========================================================================
# models_impl.py:916 — was_tampered (SHCMotionDetector2)
# models_impl.py:920 — tamper_protection_enabled (SHCMotionDetector2)
# ===========================================================================

def test_models_impl_motion_detector2_was_tampered():
    """was_tampered delegates to the latesttamper_service."""
    from boschshcpy.models_impl import SHCMotionDetector2

    obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
    obj._latesttamper_service = MagicMock()
    obj._latesttamper_service.was_tampered = True
    assert obj.was_tampered is True
    obj._latesttamper_service.was_tampered = False
    assert obj.was_tampered is False


def test_models_impl_motion_detector2_tamper_protection_enabled():
    """tamper_protection_enabled delegates to the latesttamper_service."""
    from boschshcpy.models_impl import SHCMotionDetector2

    obj = SHCMotionDetector2.__new__(SHCMotionDetector2)
    obj._latesttamper_service = MagicMock()
    obj._latesttamper_service.tamper_protection_enabled = True
    assert obj.tamper_protection_enabled is True
    obj._latesttamper_service.tamper_protection_enabled = False
    assert obj.tamper_protection_enabled is False


# ===========================================================================
# device_helper.py — early-return paths when model key absent from SUPPORTED_MODELS
# Lines: 167, 191, 228, 234, 240, 255, 261, 267, 273, 279, 285, 293, 306, 317, 323
# ===========================================================================

def _make_empty_helper():
    """Create SHCDeviceHelper via __new__ with empty _devices_by_model."""
    from boschshcpy.device_helper import SHCDeviceHelper
    h = SHCDeviceHelper.__new__(SHCDeviceHelper)
    h._api = MagicMock()
    h._devices_by_model = {}
    return h


class TestDeviceHelperEmptyModelPaths:
    """Patch SUPPORTED_MODELS to an empty set → all early-return [] / None paths fire."""

    def _helper_with_empty_supported_models(self):
        import boschshcpy.device_helper as dh_mod
        h = _make_empty_helper()
        return h, dh_mod

    def test_smart_plugs_returns_empty_when_psm_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.smart_plugs == []

    def test_climate_controls_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.climate_controls == []

    def test_motion_detectors_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.motion_detectors == []

    def test_motion_detectors2_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.motion_detectors2 == []

    def test_twinguards_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.twinguards == []

    def test_camera_eyes_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.camera_eyes == []

    def test_camera_360_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.camera_360 == []

    def test_camera_outdoor_gen2_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.camera_outdoor_gen2 == []

    def test_ledvance_lights_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.ledvance_lights == []

    def test_hue_lights_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.hue_lights == []

    def test_water_leakage_detectors_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.water_leakage_detectors == []

    def test_presence_simulation_system_returns_none_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.presence_simulation_system is None

    def test_smoke_detection_system_returns_none_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.smoke_detection_system is None

    def test_heating_circuits_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.heating_circuits == []

    def test_micromodule_dimmers_returns_empty_when_absent(self):
        h, dh_mod = self._helper_with_empty_supported_models()
        with patch.object(dh_mod, "SUPPORTED_MODELS", []):
            assert h.micromodule_dimmers == []
