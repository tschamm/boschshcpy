"""Isolation-safe tests for information.py, message.py, room.py, scenario.py,
userdefinedstate.py.

Style: mirror test_reliability.py / test_emma.py — no HA harness, no network.
Bypass __init__ via Cls.__new__(Cls) + inject fakes / SimpleNamespace where
the real constructor would call the API or zeroconf.
"""

import io
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _shc_info_ns():
    """Minimal SHCInformation namespace sufficient for SHCUserDefinedState."""
    ns = SimpleNamespace()
    ns.macAddress = "AA:BB:CC:DD:EE:FF"
    return ns


# ===========================================================================
# format_mac
# ===========================================================================

from boschshcpy.information import format_mac


def test_format_mac_colon_separated():
    assert format_mac("AA:BB:CC:DD:EE:FF") == "aa-bb-cc-dd-ee-ff"


def test_format_mac_dash_separated_already():
    assert format_mac("aa-bb-cc-dd-ee-ff") == "aa-bb-cc-dd-ee-ff"


def test_format_mac_no_separator_12_hex():
    assert format_mac("AABBCCDDEEFF") == "aa-bb-cc-dd-ee-ff"


def test_format_mac_dot_separated():
    # 14 chars with 2 dots: AABB.CCDD.EEFF
    assert format_mac("AABB.CCDD.EEFF") == "aa-bb-cc-dd-ee-ff"


def test_format_mac_unknown_format_returns_original():
    assert format_mac("ZZZZ") == "ZZZZ"


# ===========================================================================
# SHCInformation — bypass __init__, inject _pub_info directly
# ===========================================================================

from boschshcpy.information import SHCInformation
from boschshcpy.exceptions import SHCConnectionError, SHCAuthenticationError


def _make_shc_info(ip="192.168.1.1", mac="AA:BB:CC:DD:EE:FF",
                   sw_version="9.91.7", sw_state="NO_UPDATE_AVAILABLE"):
    obj = SHCInformation.__new__(SHCInformation)
    obj._api = None
    obj._unique_id = None
    obj._name = None
    obj._pub_info = {
        "shcIpAddress": ip,
        "macAddress": mac,
        "softwareUpdateState": {
            "swInstalledVersion": sw_version,
            "swUpdateState": sw_state,
        },
    }
    return obj


def test_shcinformation_version():
    info = _make_shc_info(sw_version="9.91.7")
    assert info.version == "9.91.7"


def test_shcinformation_update_state_no_update():
    info = _make_shc_info(sw_state="NO_UPDATE_AVAILABLE")
    assert info.updateState == SHCInformation.UpdateState.NO_UPDATE_AVAILABLE


def test_shcinformation_update_state_downloading():
    info = _make_shc_info(sw_state="DOWNLOADING")
    assert info.updateState == SHCInformation.UpdateState.DOWNLOADING


def test_shcinformation_update_state_in_progress():
    info = _make_shc_info(sw_state="UPDATE_IN_PROGRESS")
    assert info.updateState == SHCInformation.UpdateState.UPDATE_IN_PROGRESS


def test_shcinformation_update_state_available():
    info = _make_shc_info(sw_state="UPDATE_AVAILABLE")
    assert info.updateState == SHCInformation.UpdateState.UPDATE_AVAILABLE


def test_shcinformation_update_state_invalid_returns_none():
    # BUG 4 fix: unknown swUpdateState values used to raise ValueError;
    # after the fix they return None so HA doesn't crash on new FW.
    info = _make_shc_info(sw_state="INVALID_STATE")
    assert info.updateState is None


def test_shcinformation_shc_ip_address():
    info = _make_shc_info(ip="10.0.0.5")
    assert info.shcIpAddress == "10.0.0.5"


def test_shcinformation_shc_ip_address_missing():
    info = _make_shc_info()
    del info._pub_info["shcIpAddress"]
    assert info.shcIpAddress is None


def test_shcinformation_mac_address():
    info = _make_shc_info(mac="11:22:33:44:55:66")
    assert info.macAddress == "11:22:33:44:55:66"


def test_shcinformation_mac_address_missing():
    info = _make_shc_info()
    del info._pub_info["macAddress"]
    assert info.macAddress is None


def test_shcinformation_name_and_unique_id_initially_none():
    info = _make_shc_info()
    assert info.name is None
    assert info.unique_id is None


def test_shcinformation_unique_id_set():
    info = _make_shc_info()
    info._unique_id = "aa-bb-cc-dd-ee-ff"
    assert info.unique_id == "aa-bb-cc-dd-ee-ff"


def test_shcinformation_name_set():
    info = _make_shc_info()
    info._name = "Bosch-SHC"
    assert info.name == "Bosch-SHC"


def test_shcinformation_summary_prints(capsys):
    info = _make_shc_info()
    info._unique_id = "aa-bb-cc-dd-ee-ff"
    info._name = "192.168.1.1"
    info.summary()
    out = capsys.readouterr().out
    assert "192.168.1.1" in out
    assert "9.91.7" in out
    assert "NO_UPDATE_AVAILABLE" in out


def test_shcinformation_get_unique_id_from_mac():
    """get_unique_id(None) with macAddress present → _unique_id = macAddress, _name = ip."""
    info = _make_shc_info(ip="192.168.1.1", mac="AA:BB:CC:DD:EE:FF")
    info.get_unique_id(zeroconf=None)
    assert info._unique_id == "AA:BB:CC:DD:EE:FF"
    assert info._name == "192.168.1.1"


def test_shcinformation_get_unique_id_no_mac_no_ip_raises():
    """No mac, no ip → SHCConnectionError."""
    info = _make_shc_info()
    del info._pub_info["macAddress"]
    del info._pub_info["shcIpAddress"]
    with pytest.raises(SHCConnectionError):
        info.get_unique_id(zeroconf=None)


def test_shcinformation_init_raises_connection_error_on_none_pub_info():
    """__init__ raises SHCConnectionError when get_public_information returns None."""
    mock_api = MagicMock()
    mock_api.get_public_information.return_value = None
    with pytest.raises(SHCConnectionError):
        SHCInformation(api=mock_api, authenticate=False)


def test_shcinformation_init_raises_auth_error():
    """__init__ raises SHCAuthenticationError when get_information returns None."""
    mock_api = MagicMock()
    mock_api.get_public_information.return_value = {
        "shcIpAddress": "192.168.1.1",
        "macAddress": "AA:BB:CC:DD:EE:FF",
        "softwareUpdateState": {
            "swInstalledVersion": "9.91.7",
            "swUpdateState": "NO_UPDATE_AVAILABLE",
        },
    }
    mock_api.get_information.return_value = None
    with pytest.raises(SHCAuthenticationError):
        SHCInformation(api=mock_api, authenticate=True)


# ===========================================================================
# SHCInformation.UpdateState enum
# ===========================================================================

def test_update_state_enum_members():
    states = [s.value for s in SHCInformation.UpdateState]
    assert "NO_UPDATE_AVAILABLE" in states
    assert "DOWNLOADING" in states
    assert "UPDATE_IN_PROGRESS" in states
    assert "UPDATE_AVAILABLE" in states


# ===========================================================================
# SHCMessage
# ===========================================================================

from boschshcpy.message import SHCMessage


def _make_message(flags=None, arguments=None):
    raw = {
        "id": "msg-001",
        "messageCode": {"name": "SMOKE_ALARM", "category": "ALARM"},
        "sourceType": "DEVICE",
        "timestamp": 1718700000000,
        "flags": flags if flags is not None else ["MANDATORY"],
        "arguments": arguments if arguments is not None else {"deviceId": "dev-123"},
    }
    return SHCMessage(api=None, raw_message=raw)


def test_message_id():
    msg = _make_message()
    assert msg.id == "msg-001"


def test_message_source_type():
    msg = _make_message()
    assert msg.source_type == "DEVICE"


def test_message_timestamp():
    msg = _make_message()
    assert msg.timestamp == 1718700000000


def test_message_flags():
    msg = _make_message(flags=["MANDATORY", "PUSH"])
    assert msg.flags == ["MANDATORY", "PUSH"]


def test_message_flags_empty():
    msg = _make_message(flags=[])
    assert msg.flags == []


def test_message_arguments():
    msg = _make_message(arguments={"deviceId": "dev-123"})
    assert msg.arguments == {"deviceId": "dev-123"}


def test_message_message_code_is_dict():
    """message_code property returns a MessageCode object with .name/.category."""
    msg = _make_message()
    mc = msg.message_code
    assert mc.name == "SMOKE_ALARM"
    assert mc.category == "ALARM"


def test_message_code_class_name():
    mc = SHCMessage.MessageCode({"name": "LOW_BATTERY", "category": "WARNING"})
    assert mc.name == "LOW_BATTERY"


def test_message_code_class_category():
    mc = SHCMessage.MessageCode({"name": "LOW_BATTERY", "category": "WARNING"})
    assert mc.category == "WARNING"


def test_message_summary_with_flags(capsys):
    msg = _make_message(flags=["MANDATORY"])
    msg.summary()
    out = capsys.readouterr().out
    assert "msg-001" in out
    assert "MANDATORY" in out


def test_message_summary_empty_flags(capsys):
    msg = _make_message(flags=[])
    msg.summary()
    out = capsys.readouterr().out
    assert "msg-001" in out
    # no flags line when empty
    assert "Flags" not in out


def test_message_summary_shows_timestamp(capsys):
    msg = _make_message()
    msg.summary()
    out = capsys.readouterr().out
    assert "1718700000000" in out


# ===========================================================================
# SHCRoom
# ===========================================================================

from boschshcpy.room import SHCRoom


def _make_room(room_id="hz_1", name="Living Room", icon_id="icon_living"):
    raw = {"id": room_id, "name": name, "iconId": icon_id}
    return SHCRoom(api=None, raw_room=raw)


def test_room_id():
    assert _make_room().id == "hz_1"


def test_room_name():
    assert _make_room().name == "Living Room"


def test_room_icon_id():
    assert _make_room().icon_id == "icon_living"


def test_room_summary(capsys):
    _make_room().summary()
    out = capsys.readouterr().out
    assert "hz_1" in out
    assert "Living Room" in out
    assert "icon_living" in out


def test_room_different_values():
    room = _make_room("hz_2", "Kitchen", "icon_kitchen")
    assert room.id == "hz_2"
    assert room.name == "Kitchen"
    assert room.icon_id == "icon_kitchen"


# ===========================================================================
# SHCScenario
# ===========================================================================

from boschshcpy.scenario import SHCScenario


def _make_scenario(scenario_id="sc-1", name="Good Night", icon_id="icon_moon"):
    raw = {"id": scenario_id, "name": name, "iconId": icon_id}
    obj = SHCScenario.__new__(SHCScenario)
    obj._api = MagicMock()
    obj._api._api_root = "https://192.168.1.1:8444/smarthome"
    obj._raw_scenario = raw
    return obj


def test_scenario_id():
    assert _make_scenario().id == "sc-1"


def test_scenario_name():
    assert _make_scenario().name == "Good Night"


def test_scenario_icon_id():
    assert _make_scenario().icon_id == "icon_moon"


def test_scenario_summary(capsys):
    _make_scenario().summary()
    out = capsys.readouterr().out
    assert "sc-1" in out
    assert "Good Night" in out
    assert "icon_moon" in out


def test_scenario_trigger_calls_api():
    sc = _make_scenario()
    sc._api._post_api_or_fail.return_value = {"status": "ok"}
    result = sc.trigger()
    sc._api._post_api_or_fail.assert_called_once_with(
        "https://192.168.1.1:8444/smarthome/scenarios/sc-1/triggers", ""
    )
    assert result == {"status": "ok"}


def test_scenario_trigger_uses_correct_id():
    sc = _make_scenario(scenario_id="sc-999")
    sc._api._post_api_or_fail.return_value = None
    sc.trigger()
    call_args = sc._api._post_api_or_fail.call_args[0][0]
    assert "sc-999" in call_args


# ===========================================================================
# SHCUserDefinedState
# ===========================================================================

from boschshcpy.userdefinedstate import SHCUserDefinedState
from boschshcpy.exceptions import SHCException


def _make_uds(state_id="uds-1", name="Away Mode", deleted=False, state=True):
    raw = {"id": state_id, "name": name, "deleted": deleted, "state": state}
    obj = SHCUserDefinedState.__new__(SHCUserDefinedState)
    obj._api = MagicMock()
    obj._api._api_root = "https://192.168.1.1:8444/smarthome"
    obj._info = _shc_info_ns()
    obj._raw_state = raw
    return obj


def test_uds_id():
    assert _make_uds().id == "uds-1"


def test_uds_name():
    assert _make_uds().name == "Away Mode"


def test_uds_deleted_false():
    assert _make_uds(deleted=False).deleted is False


def test_uds_deleted_true():
    assert _make_uds(deleted=True).deleted is True


def test_uds_state_true():
    assert _make_uds(state=True).state is True


def test_uds_state_false():
    assert _make_uds(state=False).state is False


def test_uds_root_device_id():
    uds = _make_uds()
    assert uds.root_device_id == "AA:BB:CC:DD:EE:FF"


def test_uds_state_setter_calls_api():
    uds = _make_uds()
    uds.state = False
    uds._api._put_api_or_fail.assert_called_once_with(
        "https://192.168.1.1:8444/smarthome/userdefinedstates/uds-1/state", False
    )


def test_uds_state_setter_true():
    uds = _make_uds()
    uds.state = True
    uds._api._put_api_or_fail.assert_called_once_with(
        "https://192.168.1.1:8444/smarthome/userdefinedstates/uds-1/state", True
    )


def test_uds_update_raw_information_same_id():
    uds = _make_uds(state=True)
    new_raw = {"id": "uds-1", "name": "Away Mode Updated", "deleted": False, "state": False}
    uds.update_raw_information(new_raw)
    assert uds.state is False
    assert uds.name == "Away Mode Updated"


def test_uds_update_raw_information_mismatched_id_raises():
    uds = _make_uds(state_id="uds-1")
    wrong_raw = {"id": "uds-999", "name": "Other", "deleted": False, "state": False}
    with pytest.raises(SHCException):
        uds.update_raw_information(wrong_raw)


def test_uds_update_raw_information_error_message():
    uds = _make_uds(state_id="uds-1")
    wrong_raw = {"id": "uds-999", "name": "Other", "deleted": False, "state": False}
    try:
        uds.update_raw_information(wrong_raw)
    except SHCException as exc:
        assert "mismatching ids" in exc.message


def test_uds_summary(capsys):
    _make_uds().summary()
    out = capsys.readouterr().out
    assert "uds-1" in out
    assert "Away Mode" in out
    assert "True" in out


# ===========================================================================
# SHCInformation — additional branch coverage
# ===========================================================================

from unittest.mock import patch as _patch


def test_shcinformation_filter_no_bosch_services():
    """filter() with no 'Bosch SHC' services → unique_id stays None."""
    info = _make_shc_info()
    fake_service = SimpleNamespace(name="SomeOtherDevice [AA:BB:CC]", server="other.local.",
                                   parsed_addresses=lambda v: ["192.168.1.99"])
    info.filter({"svc": fake_service})
    assert info._unique_id is None
    assert info._name is None


def test_shcinformation_filter_sets_unique_id_and_name():
    """filter() with a matching 'Bosch SHC [MAC]' service → unique_id + name set."""
    info = _make_shc_info(ip="192.168.1.1")
    from zeroconf import IPVersion
    fake_service = SimpleNamespace(
        name="Bosch SHC [AABBCCDDEEFF]",
        server="shc-home.local.",
        parsed_addresses=lambda v: ["192.168.1.1"],
    )
    with _patch("socket.gethostbyname", return_value="192.168.1.1"):
        info.filter({"svc": fake_service})
    assert info._unique_id == "aa-bb-cc-dd-ee-ff"
    assert info._name == "shc-home"


def test_shcinformation_filter_gethostbyname_exception():
    """filter() where gethostbyname raises → host_ip=None → still matches (host_ip is None branch)."""
    info = _make_shc_info(ip="bad-host.local")
    fake_service = SimpleNamespace(
        name="Bosch SHC [AABBCCDDEEFF]",
        server="shc-home.local.",
        parsed_addresses=lambda v: [],
    )
    with _patch("socket.gethostbyname", side_effect=OSError("no address")):
        info.filter({"svc": fake_service})
    # host_ip is None → condition passes → unique_id set
    assert info._unique_id == "aa-bb-cc-dd-ee-ff"
    assert info._name == "shc-home"


def test_shcinformation_filter_server_no_local_suffix():
    """filter() where server has no '.local.' → name stays None → early return, unique_id not set."""
    info = _make_shc_info(ip="192.168.1.1")
    fake_service = SimpleNamespace(
        name="Bosch SHC [AABBCCDDEEFF]",
        server="shc-home.example.com",
        parsed_addresses=lambda v: ["192.168.1.1"],
    )
    with _patch("socket.gethostbyname", return_value="192.168.1.1"):
        info.filter({"svc": fake_service})
    # name is None → early return → unique_id not set
    assert info._unique_id is None


def test_shcinformation_get_unique_id_no_mac_with_ip_getmac_returns_mac():
    """No macAddress, ip present, get_mac_address returns a mac → unique_id formatted."""
    info = _make_shc_info(ip="192.168.1.5")
    del info._pub_info["macAddress"]

    with _patch("boschshcpy.information.get_mac_address", return_value="aa:bb:cc:dd:ee:ff"):
        info.get_unique_id(zeroconf=None)

    assert info._unique_id == "aa-bb-cc-dd-ee-ff"
    assert info._name == "192.168.1.5"


def test_shcinformation_get_unique_id_no_mac_with_ip_getmac_first_none_second_returns():
    """get_mac_address(ip=) returns None → fallback get_mac_address(hostname=) returns mac."""
    info = _make_shc_info(ip="192.168.1.5")
    del info._pub_info["macAddress"]

    call_results = [None, "aa:bb:cc:dd:ee:ff"]

    with _patch("boschshcpy.information.get_mac_address", side_effect=call_results):
        info.get_unique_id(zeroconf=None)

    assert info._unique_id == "aa-bb-cc-dd-ee-ff"


def test_shcinformation_get_unique_id_no_mac_with_ip_getmac_raises():
    """Regression (fixed): get_mac_address raises → previously UnboundLocalError because the
    except clause never assigned `mac_address = None`. Now `mac_address` is pre-initialised to
    None, so the call must NOT raise and falls back to using the host IP as the unique_id.
    See: information.py get_unique_id (elif self.shcIpAddress branch)."""
    info = _make_shc_info(ip="192.168.1.5")
    del info._pub_info["macAddress"]

    with _patch("boschshcpy.information.get_mac_address", side_effect=OSError("unreachable")):
        info.get_unique_id(zeroconf=None)

    # mac lookup failed → fall back to the IP for both unique_id and name (no crash)
    assert info._unique_id == "192.168.1.5"
    assert info._name == "192.168.1.5"


def test_shcinformation_get_unique_id_no_mac_no_ip_via_getmac_none():
    """No mac, ip present, both get_mac_address calls return None → unique_id = ip."""
    info = _make_shc_info(ip="192.168.1.5")
    del info._pub_info["macAddress"]

    with _patch("boschshcpy.information.get_mac_address", return_value=None):
        info.get_unique_id(zeroconf=None)

    assert info._unique_id == "192.168.1.5"
    assert info._name == "192.168.1.5"


def test_shcinformation_get_unique_id_with_mac_no_ip():
    """mac present, ip missing → _name = macAddress."""
    info = _make_shc_info()
    del info._pub_info["shcIpAddress"]
    info.get_unique_id(zeroconf=None)
    assert info._unique_id == "AA:BB:CC:DD:EE:FF"
    assert info._name == "AA:BB:CC:DD:EE:FF"


def test_shcinformation_init_authenticate_false_skips_auth():
    """With authenticate=False, get_information is never called."""
    mock_api = MagicMock()
    mock_api.get_public_information.return_value = {
        "shcIpAddress": "192.168.1.1",
        "macAddress": "AA:BB:CC:DD:EE:FF",
        "softwareUpdateState": {
            "swInstalledVersion": "9.91.7",
            "swUpdateState": "NO_UPDATE_AVAILABLE",
        },
    }
    obj = SHCInformation(api=mock_api, authenticate=False)
    mock_api.get_information.assert_not_called()
    assert obj.version == "9.91.7"


# ---------------------------------------------------------------------------
# SHCListener — tested via a stub zeroconf that calls callback immediately
# ---------------------------------------------------------------------------

from boschshcpy.information import SHCListener


def test_shclistener_callback_called():
    """SHCListener must invoke callback with its shc_services dict."""
    received = {}

    def fake_callback(services):
        received.update(services)

    class _FakeZeroconf:
        def get_service_info(self, stype, name):
            return None

    class _FakeServiceBrowser:
        def __init__(self, zc, service_type, handlers):
            # immediately call the handler with Added state
            from zeroconf import ServiceStateChange
            handlers[0](zc, service_type, "TestDevice._http._tcp.local.", ServiceStateChange.Added)

        def cancel(self):
            pass

    with _patch("boschshcpy.information.ServiceBrowser", _FakeServiceBrowser):
        with _patch("boschshcpy.information.current_time_millis", side_effect=[0, 20000]):
            listener = SHCListener(_FakeZeroconf(), fake_callback)

    # callback was called; no Bosch SHC service → shc_services stays empty
    assert isinstance(listener.shc_services, dict)


def test_shclistener_ignores_non_added_state():
    """service_update with state != Added must return without adding to shc_services."""
    from zeroconf import ServiceStateChange
    listener = SHCListener.__new__(SHCListener)
    listener.shc_services = {}
    listener.waiting = True
    listener.service_update(None, "_http._tcp.local.", "test", ServiceStateChange.Removed)
    assert listener.shc_services == {}
    assert listener.waiting is True


def test_shclistener_zeroconf_error_in_get_service_info():
    """If get_service_info raises ZeroconfError, it is caught and nothing added."""
    from zeroconf import ServiceStateChange, Error as ZeroconfError

    class _FailZeroconf:
        def get_service_info(self, stype, name):
            raise ZeroconfError("fail")

    listener = SHCListener.__new__(SHCListener)
    listener.shc_services = {}
    listener.waiting = True
    listener.service_update(_FailZeroconf(), "_http._tcp.local.", "TestDevice._http._tcp.local.", ServiceStateChange.Added)
    assert listener.shc_services == {}


# ===========================================================================
# BUG 4 regression — SHCInformation.version / .updateState crash on missing
# or unknown softwareUpdateState fields (older/newer FW).
# Confirmed: KeyError + ValueError before fix; .get() + try/except after.
# ===========================================================================

def test_shcinformation_version_field_absent_returns_none():
    """Regression: KeyError on pub_info['softwareUpdateState']['swInstalledVersion'] when absent."""
    from boschshcpy.information import SHCInformation
    obj = SHCInformation.__new__(SHCInformation)
    obj._pub_info = {}  # no softwareUpdateState at all
    assert obj.version is None


def test_shcinformation_version_sw_installed_absent_returns_none():
    """Regression: KeyError when softwareUpdateState exists but swInstalledVersion missing."""
    from boschshcpy.information import SHCInformation
    obj = SHCInformation.__new__(SHCInformation)
    obj._pub_info = {"softwareUpdateState": {"swUpdateState": "NO_UPDATE_AVAILABLE"}}
    assert obj.version is None


def test_shcinformation_version_present_returns_value():
    """Happy path: version returns the string when present."""
    from boschshcpy.information import SHCInformation
    obj = SHCInformation.__new__(SHCInformation)
    obj._pub_info = {"softwareUpdateState": {"swInstalledVersion": "9.40.102", "swUpdateState": "NO_UPDATE_AVAILABLE"}}
    assert obj.version == "9.40.102"


def test_shcinformation_update_state_field_absent_returns_none():
    """Regression: KeyError on pub_info['softwareUpdateState']['swUpdateState'] when absent."""
    from boschshcpy.information import SHCInformation
    obj = SHCInformation.__new__(SHCInformation)
    obj._pub_info = {}  # no softwareUpdateState at all
    assert obj.updateState is None


def test_shcinformation_update_state_sw_update_state_absent_returns_none():
    """Regression: swUpdateState key missing inside softwareUpdateState."""
    from boschshcpy.information import SHCInformation
    obj = SHCInformation.__new__(SHCInformation)
    obj._pub_info = {"softwareUpdateState": {"swInstalledVersion": "9.40.102"}}
    assert obj.updateState is None


def test_shcinformation_update_state_unknown_value_returns_none():
    """Regression: ValueError on UpdateState('FUTURE_STATE') → None, not crash."""
    from boschshcpy.information import SHCInformation
    obj = SHCInformation.__new__(SHCInformation)
    obj._pub_info = {"softwareUpdateState": {"swInstalledVersion": "9.40.102", "swUpdateState": "FUTURE_BOSCH_STATE"}}
    assert obj.updateState is None


def test_shcinformation_update_state_known_values():
    """Happy path: all four known UpdateState values parse correctly."""
    from boschshcpy.information import SHCInformation
    obj = SHCInformation.__new__(SHCInformation)
    for val in ("NO_UPDATE_AVAILABLE", "DOWNLOADING", "UPDATE_IN_PROGRESS", "UPDATE_AVAILABLE"):
        obj._pub_info = {"softwareUpdateState": {"swInstalledVersion": "9.40.102", "swUpdateState": val}}
        assert obj.updateState == SHCInformation.UpdateState(val)


def test_shclistener_bosch_shc_service_sets_waiting_false():
    """A service named 'Bosch SHC ...' sets waiting = False."""
    from zeroconf import ServiceStateChange

    fake_service_info = SimpleNamespace(name="Bosch SHC [AABBCCDDEEFF]._http._tcp.local.")

    class _BoschZeroconf:
        def get_service_info(self, stype, name):
            return fake_service_info

    listener = SHCListener.__new__(SHCListener)
    listener.shc_services = {}
    listener.waiting = True
    listener.service_update(_BoschZeroconf(), "_http._tcp.local.", "Bosch SHC [AABBCCDDEEFF]._http._tcp.local.", ServiceStateChange.Added)
    assert listener.waiting is False
    assert len(listener.shc_services) == 1
