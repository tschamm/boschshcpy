"""Tests for boschshcpy.api — SHCAPI synchronous HTTP layer.

Style mirrors test_rawscan_and_register.py — no HA harness, no real network.
SHCAPI is constructed via __new__ bypass; self._requests_session is replaced
with a MagicMock so zero sockets are opened.

Run:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_api_sync.py \
    -q -o addopts= -p no:cacheprovider \
    --cov=boschshcpy.api --cov-report=term-missing
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from boschshcpy.api import SHCAPI, JSONRPCError
from boschshcpy.exceptions import SHCConnectionError, SHCSessionError

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_IP = "192.168.0.99"
_API_ROOT = f"https://{_IP}:8444/smarthome"
_PUBLIC_ROOT = f"https://{_IP}:8446/smarthome/public"
_RPC_ROOT = f"https://{_IP}:8444/remote/json-rpc"


def _fake_response(body=None, status_code=200):
    """Return a minimal fake requests.Response.

    body: Python object → serialised to JSON bytes; None → empty content.
    """
    resp = SimpleNamespace()
    resp.status_code = status_code
    resp.ok = status_code < 400
    if body is not None:
        resp.content = json.dumps(body).encode()
    else:
        resp.content = b""
    # request stub for _process_nok_result logging
    resp.request = SimpleNamespace(body="", headers={}, url="https://test/")
    resp.raise_for_status = MagicMock()
    return resp


def _make_api() -> SHCAPI:
    """Construct an SHCAPI without touching the network.

    Uses __new__ to bypass __init__, then wires in the derived URL roots and
    a MagicMock session exactly as __init__ would build them.
    """
    api = SHCAPI.__new__(SHCAPI)
    api._controller_ip = _IP
    api._api_root = _API_ROOT
    api._public_root = _PUBLIC_ROOT
    api._rpc_root = _RPC_ROOT
    api._requests_session = MagicMock()
    return api


# ──────────────────────────────────────────────────────────────────────────────
# __init__ smoke tests (without opening sockets)
# ──────────────────────────────────────────────────────────────────────────────


class TestSHCAPIInit:
    def _build(self):
        # urllib3 is imported locally inside __init__ (not at module level),
        # so patch it in the urllib3 namespace directly.
        with patch("boschshcpy.api.requests.Session") as mock_sess_cls, \
             patch("urllib3.disable_warnings"), \
             patch("boschshcpy.api.importlib.resources.files") as mock_files:
            # make resources.files() / chain return a string path so .verify= works
            mock_files.return_value.__truediv__ = lambda self, name: "/fake/tls_ca_chain.pem"
            mock_sess = MagicMock()
            mock_sess_cls.return_value = mock_sess
            api = SHCAPI(_IP, "/cert.pem", "/key.pem")
            return api, mock_sess

    def test_api_root_url(self):
        api, _ = self._build()
        assert api._api_root == f"https://{_IP}:8444/smarthome"

    def test_public_root_url(self):
        api, _ = self._build()
        assert api._public_root == f"https://{_IP}:8446/smarthome/public"

    def test_rpc_root_url(self):
        api, _ = self._build()
        assert api._rpc_root == f"https://{_IP}:8444/remote/json-rpc"

    def test_controller_ip_property(self):
        api, _ = self._build()
        assert api.controller_ip == _IP

    def test_api_version_header_set(self):
        _, sess = self._build()
        header_calls = [c[0][0] for c in sess.headers.update.call_args_list]
        combined = {}
        for h in header_calls:
            combined.update(h)
        assert combined.get("api-version") == "3.2"

    def test_content_type_header_set(self):
        _, sess = self._build()
        header_calls = [c[0][0] for c in sess.headers.update.call_args_list]
        combined = {}
        for h in header_calls:
            combined.update(h)
        assert combined.get("Content-Type") == "application/json"

    def test_pool_maxsize_in_init_source(self):
        import inspect
        src = inspect.getsource(SHCAPI.__init__)
        assert "pool_maxsize=" in src


# ──────────────────────────────────────────────────────────────────────────────
# _get_api_result_or_fail internals
# ──────────────────────────────────────────────────────────────────────────────


class TestGetApiResultOrFail:
    def test_returns_parsed_json_on_ok(self):
        api = _make_api()
        payload = [{"@type": "device", "id": "d1"}]
        api._requests_session.get.return_value = _fake_response(payload)
        result = api._get_api_result_or_fail(f"{_API_ROOT}/devices")
        assert result == payload

    def test_passes_url_to_session_get(self):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response([])
        url = f"{_API_ROOT}/devices"
        api._get_api_result_or_fail(url)
        api._requests_session.get.assert_called_once_with(url, headers=None, timeout=30)

    def test_passes_custom_headers(self):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response({})
        url = f"{_PUBLIC_ROOT}/information"
        api._get_api_result_or_fail(url, headers={})
        _, kwargs = api._requests_session.get.call_args
        assert kwargs["headers"] == {}

    def test_empty_content_returns_empty_dict(self):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response(None)
        result = api._get_api_result_or_fail(f"{_API_ROOT}/information")
        assert result == {}

    def test_nok_response_raises_shcsessionerror(self):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response(None, status_code=403)
        with pytest.raises(SHCSessionError):
            api._get_api_result_or_fail(f"{_API_ROOT}/devices")

    def test_ssl_error_raises_shcconnectionerror(self):
        import requests as req_mod
        api = _make_api()
        api._requests_session.get.side_effect = req_mod.exceptions.SSLError("bad cert")
        with pytest.raises(SHCConnectionError, match="SSLError"):
            api._get_api_result_or_fail(f"{_API_ROOT}/devices")

    def test_expected_type_match_passes(self):
        api = _make_api()
        payload = {"@type": "device", "id": "x"}
        api._requests_session.get.return_value = _fake_response(payload)
        result = api._get_api_result_or_fail(
            f"{_API_ROOT}/devices/x", expected_type="device"
        )
        assert result == payload

    def test_expected_type_mismatch_raises_shcsessionerror(self):
        api = _make_api()
        payload = {"@type": "WRONG", "id": "x"}
        api._requests_session.get.return_value = _fake_response(payload)
        with pytest.raises(SHCSessionError, match="Unexpected @type"):
            api._get_api_result_or_fail(
                f"{_API_ROOT}/devices/x", expected_type="device"
            )

    def test_expected_element_type_all_match_passes(self):
        api = _make_api()
        payload = [{"@type": "device"}, {"@type": "device"}]
        api._requests_session.get.return_value = _fake_response(payload)
        result = api._get_api_result_or_fail(
            f"{_API_ROOT}/devices", expected_element_type="device"
        )
        assert len(result) == 2

    def test_expected_element_type_mismatch_raises(self):
        api = _make_api()
        payload = [{"@type": "device"}, {"@type": "scenario"}]
        api._requests_session.get.return_value = _fake_response(payload)
        with pytest.raises(SHCSessionError, match="Unexpected @type"):
            api._get_api_result_or_fail(
                f"{_API_ROOT}/devices", expected_element_type="device"
            )


# ──────────────────────────────────────────────────────────────────────────────
# _put_api_or_fail
# ──────────────────────────────────────────────────────────────────────────────


class TestPutApiOrFail:
    def test_serialises_body_to_json(self):
        api = _make_api()
        api._requests_session.put.return_value = _fake_response(None)
        body = {"@type": "stateUpdate", "value": True}
        url = f"{_API_ROOT}/devices/d1/services/s1/state"
        api._put_api_or_fail(url, body)
        api._requests_session.put.assert_called_once_with(
            url, data=json.dumps(body), timeout=30
        )

    def test_returns_parsed_json_when_content_present(self):
        api = _make_api()
        resp_body = {"result": "ok"}
        api._requests_session.put.return_value = _fake_response(resp_body)
        result = api._put_api_or_fail(f"{_API_ROOT}/x", {})
        assert result == resp_body

    def test_returns_empty_dict_when_no_content(self):
        api = _make_api()
        api._requests_session.put.return_value = _fake_response(None)
        result = api._put_api_or_fail(f"{_API_ROOT}/x", {})
        assert result == {}

    def test_nok_raises_shcsessionerror(self):
        api = _make_api()
        api._requests_session.put.return_value = _fake_response(None, status_code=500)
        with pytest.raises(SHCSessionError):
            api._put_api_or_fail(f"{_API_ROOT}/x", {})


# ──────────────────────────────────────────────────────────────────────────────
# _post_api_or_fail
# ──────────────────────────────────────────────────────────────────────────────


class TestPostApiOrFail:
    def test_serialises_body_to_json(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(None)
        body = {"action": "trigger"}
        url = f"{_API_ROOT}/scenarios/s1/triggers"
        api._post_api_or_fail(url, body)
        api._requests_session.post.assert_called_once_with(
            url, data=json.dumps(body), timeout=30
        )

    def test_returns_parsed_json_when_content_present(self):
        api = _make_api()
        resp_body = {"status": "done"}
        api._requests_session.post.return_value = _fake_response(resp_body)
        result = api._post_api_or_fail(f"{_API_ROOT}/x", {})
        assert result == resp_body

    def test_returns_empty_dict_when_no_content(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(None)
        result = api._post_api_or_fail(f"{_API_ROOT}/x", {})
        assert result == {}

    def test_nok_raises_shcsessionerror(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(None, status_code=401)
        with pytest.raises(SHCSessionError):
            api._post_api_or_fail(f"{_API_ROOT}/x", {})


# ──────────────────────────────────────────────────────────────────────────────
# _process_nok_result
# ──────────────────────────────────────────────────────────────────────────────


class TestProcessNokResult:
    def test_raises_shcsessionerror_with_status_code(self):
        api = _make_api()
        fake_resp = _fake_response(None, status_code=403)
        with pytest.raises(SHCSessionError, match="403"):
            api._process_nok_result(fake_resp)

    def test_raises_shcsessionerror_with_content(self):
        api = _make_api()
        fake_resp = _fake_response(None, status_code=400)
        fake_resp.content = b"Bad Request Body"
        with pytest.raises(SHCSessionError) as exc_info:
            api._process_nok_result(fake_resp)
        assert b"Bad Request Body" in str(exc_info.value).encode()


# ──────────────────────────────────────────────────────────────────────────────
# GET endpoint methods
# ──────────────────────────────────────────────────────────────────────────────


class TestGetEndpoints:
    def _api_with_get(self, body, status_code=200):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response(body, status_code)
        return api

    # get_information -----------------------------------------------------------
    def test_get_information_url(self):
        api = self._api_with_get({"version": "1.0"})
        api.get_information()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/information"

    def test_get_information_returns_dict(self):
        api = self._api_with_get({"version": "1.0"})
        assert api.get_information() == {"version": "1.0"}

    def test_get_information_returns_none_on_exception(self):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response(None, status_code=500)
        # get_information swallows exceptions and returns None
        result = api.get_information()
        assert result is None

    # get_public_information ----------------------------------------------------
    def test_get_public_information_url(self):
        api = self._api_with_get({"name": "SHC"})
        api.get_public_information()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_PUBLIC_ROOT}/information"

    def test_get_public_information_passes_empty_headers(self):
        api = self._api_with_get({"name": "SHC"})
        api.get_public_information()
        _, kwargs = api._requests_session.get.call_args
        assert kwargs["headers"] == {}

    def test_get_public_information_returns_none_on_exception(self):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response(None, status_code=500)
        result = api.get_public_information()
        assert result is None

    # get_devices ---------------------------------------------------------------
    def test_get_devices_url(self):
        payload = [{"@type": "device", "id": "d1"}]
        api = self._api_with_get(payload)
        api.get_devices()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/devices"

    def test_get_devices_returns_list(self):
        payload = [{"@type": "device", "id": "d1"}, {"@type": "device", "id": "d2"}]
        api = self._api_with_get(payload)
        result = api.get_devices()
        assert result == payload

    def test_get_devices_raises_on_wrong_element_type(self):
        payload = [{"@type": "scenario"}]
        api = self._api_with_get(payload)
        with pytest.raises(SHCSessionError):
            api.get_devices()

    # get_device ----------------------------------------------------------------
    def test_get_device_url(self):
        api = self._api_with_get({"@type": "device", "id": "hdm:ZigBee:abc"})
        api.get_device("hdm:ZigBee:abc")
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/devices/hdm:ZigBee:abc"

    def test_get_device_returns_dict(self):
        payload = {"@type": "device", "id": "hdm:ZigBee:abc"}
        api = self._api_with_get(payload)
        assert api.get_device("hdm:ZigBee:abc") == payload

    def test_get_device_raises_on_wrong_type(self):
        api = self._api_with_get({"@type": "scenario"})
        with pytest.raises(SHCSessionError):
            api.get_device("hdm:ZigBee:abc")

    # put_device ----------------------------------------------------------------
    def test_put_device_url_and_body(self):
        api = _make_api()
        api._requests_session.put.return_value = _fake_response(None)
        body = {"@type": "device", "id": "hdm:ZigBee:abc", "profile": "OUTDOOR"}
        api.put_device("hdm:ZigBee:abc", body)
        called_url = api._requests_session.put.call_args[0][0]
        assert called_url == f"{_API_ROOT}/devices/hdm:ZigBee:abc"
        sent = api._requests_session.put.call_args.kwargs["data"]
        assert '"profile": "OUTDOOR"' in sent

    # get_services --------------------------------------------------------------
    def test_get_services_url(self):
        payload = [{"@type": "DeviceServiceData"}]
        api = self._api_with_get(payload)
        api.get_services()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/services"

    def test_get_services_raises_on_wrong_element_type(self):
        api = self._api_with_get([{"@type": "device"}])
        with pytest.raises(SHCSessionError):
            api.get_services()

    # get_device_services -------------------------------------------------------
    def test_get_device_services_url(self):
        api = self._api_with_get([])
        api.get_device_services("hdm:ZigBee:abc")
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/devices/hdm:ZigBee:abc/services"

    def test_get_device_services_no_type_check(self):
        # No expected_element_type → any content accepted
        api = self._api_with_get([{"@type": "anything"}])
        result = api.get_device_services("hdm:ZigBee:abc")
        assert result == [{"@type": "anything"}]

    # get_device_service --------------------------------------------------------
    def test_get_device_service_url(self):
        payload = {"@type": "DeviceServiceData"}
        api = self._api_with_get(payload)
        api.get_device_service("hdm:ZigBee:abc", "TemperatureLevel")
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/devices/hdm:ZigBee:abc/services/TemperatureLevel"

    def test_get_device_service_raises_on_wrong_type(self):
        api = self._api_with_get({"@type": "WRONG"})
        with pytest.raises(SHCSessionError):
            api.get_device_service("hdm:ZigBee:abc", "TemperatureLevel")

    # get_rooms -----------------------------------------------------------------
    def test_get_rooms_url(self):
        api = self._api_with_get([{"@type": "room"}])
        api.get_rooms()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/rooms"

    def test_get_rooms_raises_on_wrong_element_type(self):
        api = self._api_with_get([{"@type": "device"}])
        with pytest.raises(SHCSessionError):
            api.get_rooms()

    # get_scenarios -------------------------------------------------------------
    def test_get_scenarios_url(self):
        api = self._api_with_get([{"@type": "scenario"}])
        api.get_scenarios()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/scenarios"

    def test_get_scenarios_element_type_checked(self):
        api = self._api_with_get([{"@type": "WRONG"}])
        with pytest.raises(SHCSessionError):
            api.get_scenarios()

    # get_userdefinedstates -----------------------------------------------------
    def test_get_userdefinedstates_url(self):
        api = self._api_with_get([{"@type": "userDefinedState"}])
        api.get_userdefinedstates()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/userdefinedstates"

    def test_get_userdefinedstates_element_type_checked(self):
        api = self._api_with_get([{"@type": "device"}])
        with pytest.raises(SHCSessionError):
            api.get_userdefinedstates()

    # get_messages --------------------------------------------------------------
    def test_get_messages_url(self):
        api = self._api_with_get([{"@type": "message"}])
        api.get_messages()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/messages"

    def test_get_messages_element_type_checked(self):
        api = self._api_with_get([{"@type": "WRONG"}])
        with pytest.raises(SHCSessionError):
            api.get_messages()

    # get_domain_intrusion_detection --------------------------------------------
    def test_get_domain_intrusion_detection_url(self):
        api = self._api_with_get({"@type": "systemState"})
        api.get_domain_intrusion_detection()
        url = api._requests_session.get.call_args[0][0]
        assert url == f"{_API_ROOT}/intrusion/states/system"

    def test_get_domain_intrusion_detection_type_checked(self):
        api = self._api_with_get({"@type": "WRONG"})
        with pytest.raises(SHCSessionError):
            api.get_domain_intrusion_detection()

    def test_get_domain_intrusion_detection_returns_dict(self):
        payload = {"@type": "systemState", "state": "DISARMED"}
        api = self._api_with_get(payload)
        assert api.get_domain_intrusion_detection() == payload


# ──────────────────────────────────────────────────────────────────────────────
# PUT endpoint methods
# ──────────────────────────────────────────────────────────────────────────────


class TestPutEndpoints:
    # put_device_service_state --------------------------------------------------
    def test_put_device_service_state_url(self):
        api = _make_api()
        api._requests_session.put.return_value = _fake_response(None)
        api.put_device_service_state("hdm:ZigBee:abc", "SwitchActuator", {"@type": "switchActuatorState", "on": True})
        url = api._requests_session.put.call_args[0][0]
        assert url == f"{_API_ROOT}/devices/hdm:ZigBee:abc/services/SwitchActuator/state"

    def test_put_device_service_state_sends_body(self):
        api = _make_api()
        api._requests_session.put.return_value = _fake_response(None)
        state = {"@type": "switchActuatorState", "on": False}
        api.put_device_service_state("hdm:ZigBee:abc", "SwitchActuator", state)
        _, kwargs = api._requests_session.put.call_args
        assert json.loads(kwargs["data"]) == state

    def test_put_device_service_state_nok_raises(self):
        api = _make_api()
        api._requests_session.put.return_value = _fake_response(None, status_code=500)
        with pytest.raises(SHCSessionError):
            api.put_device_service_state("d", "s", {})

# ──────────────────────────────────────────────────────────────────────────────
# POST endpoint methods
# ──────────────────────────────────────────────────────────────────────────────


class TestPostEndpoints:
    # post_domain_action --------------------------------------------------------
    def test_post_domain_action_url(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(None)
        api.post_domain_action("intrusion/actions", {"@type": "arm"})
        url = api._requests_session.post.call_args[0][0]
        assert url == f"{_API_ROOT}/intrusion/actions"

    def test_post_domain_action_sends_data(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(None)
        data = {"@type": "disarm"}
        api.post_domain_action("intrusion/actions", data)
        _, kwargs = api._requests_session.post.call_args
        assert json.loads(kwargs["data"]) == data

    def test_post_domain_action_none_data(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(None)
        api.post_domain_action("intrusion/actions")
        _, kwargs = api._requests_session.post.call_args
        assert json.loads(kwargs["data"]) is None

    def test_post_domain_action_nok_raises(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(None, status_code=422)
        with pytest.raises(SHCSessionError):
            api.post_domain_action("intrusion/actions", {})


# ──────────────────────────────────────────────────────────────────────────────
# JSON-RPC long-polling methods
# ──────────────────────────────────────────────────────────────────────────────


def _rpc_response(method_result=None, error=None):
    """Build a fake JSON-RPC 2.0 response list."""
    envelope: dict = {"jsonrpc": "2.0"}
    if error is not None:
        envelope["error"] = error
    else:
        envelope["result"] = method_result
    return [envelope]


class TestLongPollingSubscribe:
    def test_posts_to_rpc_root(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response("poll-id-42")
        )
        api.long_polling_subscribe()
        url = api._requests_session.post.call_args[0][0]
        assert url == _RPC_ROOT

    def test_subscribe_method_in_body(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response("poll-id-42")
        )
        api.long_polling_subscribe()
        _, kwargs = api._requests_session.post.call_args
        sent = json.loads(kwargs["data"])
        assert sent[0]["method"] == "RE/subscribe"
        assert sent[0]["jsonrpc"] == "2.0"

    def test_subscribe_returns_result(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response("poll-id-99")
        )
        result = api.long_polling_subscribe()
        assert result == "poll-id-99"

    def test_subscribe_error_raises_jsonrpcerror(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response(error={"code": -32000, "message": "subscribe failed"})
        )
        with pytest.raises(JSONRPCError) as exc_info:
            api.long_polling_subscribe()
        assert exc_info.value.code == -32000
        assert exc_info.value.message == "subscribe failed"

    def test_subscribe_wrong_jsonrpc_version_raises(self):
        api = _make_api()
        bad_resp = [{"jsonrpc": "1.0", "result": "x"}]
        api._requests_session.post.return_value = _fake_response(bad_resp)
        with pytest.raises(SHCSessionError, match="JSON-RPC version"):
            api.long_polling_subscribe()

    def test_subscribe_empty_list_response_raises_shcsessionerror(self):
        """Regression: a malformed/empty JSON-RPC response (e.g. a proxy
        hiccup during an SHC reboot returning `[]`) must raise a handled
        SHCSessionError, not a bare IndexError."""
        api = _make_api()
        api._requests_session.post.return_value = _fake_response([])
        with pytest.raises(SHCSessionError, match="Malformed JSON-RPC response"):
            api.long_polling_subscribe()

    def test_subscribe_non_list_response_raises_shcsessionerror(self):
        """A JSON object instead of a list must raise a handled
        SHCSessionError, not a bare AttributeError from result[0].get(...)."""
        api = _make_api()
        api._requests_session.post.return_value = _fake_response({"jsonrpc": "2.0"})
        with pytest.raises(SHCSessionError, match="Malformed JSON-RPC response"):
            api.long_polling_subscribe()


class TestLongPollingPoll:
    def test_posts_to_rpc_root(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response([{"result": "event"}])
        )
        api.long_polling_poll("poll-id-42")
        url = api._requests_session.post.call_args[0][0]
        assert url == _RPC_ROOT

    def test_poll_method_and_params_in_body(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response([])
        )
        api.long_polling_poll("poll-id-42", wait_seconds=15)
        _, kwargs = api._requests_session.post.call_args
        sent = json.loads(kwargs["data"])
        assert sent[0]["method"] == "RE/longPoll"
        assert sent[0]["params"] == ["poll-id-42", 15]

    def test_poll_timeout_is_wait_plus_5(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response([])
        )
        api.long_polling_poll("pid", wait_seconds=20)
        _, kwargs = api._requests_session.post.call_args
        assert kwargs["timeout"] == 25

    def test_poll_returns_result(self):
        events = [{"path": "/devices/d1"}]
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response(events)
        )
        result = api.long_polling_poll("pid")
        assert result == events

    def test_poll_error_raises_jsonrpcerror(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response(error={"code": -32001, "message": "poll failed"})
        )
        with pytest.raises(JSONRPCError) as exc_info:
            api.long_polling_poll("pid")
        assert exc_info.value.code == -32001

    def test_poll_wrong_jsonrpc_version_raises(self):
        api = _make_api()
        bad_resp = [{"jsonrpc": "1.0", "result": []}]
        api._requests_session.post.return_value = _fake_response(bad_resp)
        with pytest.raises(SHCSessionError, match="JSON-RPC version"):
            api.long_polling_poll("pid")

    def test_poll_default_wait_seconds_30(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response([])
        )
        api.long_polling_poll("pid")
        _, kwargs = api._requests_session.post.call_args
        sent = json.loads(kwargs["data"])
        assert sent[0]["params"][1] == 30


class TestLongPollingUnsubscribe:
    def test_posts_to_rpc_root(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response("ok")
        )
        api.long_polling_unsubscribe("poll-id-42")
        url = api._requests_session.post.call_args[0][0]
        assert url == _RPC_ROOT

    def test_unsubscribe_method_and_params(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response("ok")
        )
        api.long_polling_unsubscribe("poll-id-42")
        _, kwargs = api._requests_session.post.call_args
        sent = json.loads(kwargs["data"])
        assert sent[0]["method"] == "RE/unsubscribe"
        assert sent[0]["params"] == ["poll-id-42"]

    def test_unsubscribe_returns_result(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response("ok")
        )
        result = api.long_polling_unsubscribe("pid")
        assert result == "ok"

    def test_unsubscribe_error_raises_jsonrpcerror(self):
        api = _make_api()
        api._requests_session.post.return_value = _fake_response(
            _rpc_response(error={"code": -32002, "message": "unsubscribe failed"})
        )
        with pytest.raises(JSONRPCError) as exc_info:
            api.long_polling_unsubscribe("pid")
        assert exc_info.value.code == -32002

    def test_unsubscribe_wrong_jsonrpc_version_raises(self):
        api = _make_api()
        bad_resp = [{"jsonrpc": "BAD", "result": "x"}]
        api._requests_session.post.return_value = _fake_response(bad_resp)
        with pytest.raises(SHCSessionError, match="JSON-RPC version"):
            api.long_polling_unsubscribe("pid")


# ──────────────────────────────────────────────────────────────────────────────
# JSONRPCError class
# ──────────────────────────────────────────────────────────────────────────────


class TestJSONRPCError:
    def test_code_property(self):
        err = JSONRPCError(-32000, "server error")
        assert err.code == -32000

    def test_message_property(self):
        err = JSONRPCError(-32000, "server error")
        assert err.message == "server error"

    def test_str_representation(self):
        err = JSONRPCError(-32001, "parse error")
        s = str(err)
        assert "-32001" in s
        assert "parse error" in s

    def test_is_exception(self):
        err = JSONRPCError(0, "x")
        assert isinstance(err, Exception)


# ──────────────────────────────────────────────────────────────────────────────
# HostNameIgnoringAdapter
# ──────────────────────────────────────────────────────────────────────────────


class TestSessionRequestRetry:
    """#281: one transparent retry on a bare ConnectionError (RemoteDisconnected)."""

    def _conn_err(self):
        import requests as req_mod
        return req_mod.exceptions.ConnectionError(
            "('Connection aborted.', RemoteDisconnected('Remote end closed "
            "connection without response'))"
        )

    def test_get_retries_once_then_succeeds(self):
        api = _make_api()
        ok = _fake_response([{"@type": "device", "id": "d1"}])
        api._requests_session.get.side_effect = [self._conn_err(), ok]
        result = api._get_api_result_or_fail(f"{_API_ROOT}/devices")
        assert result == [{"@type": "device", "id": "d1"}]
        assert api._requests_session.get.call_count == 2

    def test_put_retries_once_then_succeeds(self):
        api = _make_api()
        api._requests_session.put.side_effect = [self._conn_err(), _fake_response(None)]
        api._put_api_or_fail(f"{_API_ROOT}/x", {"on": True})
        assert api._requests_session.put.call_count == 2

    def test_post_retries_once_then_succeeds(self):
        api = _make_api()
        api._requests_session.post.side_effect = [
            self._conn_err(),
            _fake_response(_rpc_response("poll-id-1")),
        ]
        result = api.long_polling_subscribe()
        assert result == "poll-id-1"
        assert api._requests_session.post.call_count == 2

    def test_reraises_when_retry_also_fails(self):
        import requests as req_mod
        api = _make_api()
        api._requests_session.get.side_effect = [self._conn_err(), self._conn_err()]
        with pytest.raises(req_mod.exceptions.ConnectionError):
            api._get_api_result_or_fail(f"{_API_ROOT}/devices")
        assert api._requests_session.get.call_count == 2

    def test_no_retry_on_first_success(self):
        api = _make_api()
        api._requests_session.get.return_value = _fake_response([])
        api._get_api_result_or_fail(f"{_API_ROOT}/devices")
        assert api._requests_session.get.call_count == 1


class TestSSLVerifyOption:
    """#264: opt-in skip of SHC server-certificate verification."""

    def _build(self, ssl_verify=True):
        with patch("boschshcpy.api.requests.Session") as mock_sess_cls, \
             patch("urllib3.disable_warnings"), \
             patch("boschshcpy.api.importlib.resources.files") as mock_files:
            mock_files.return_value.__truediv__ = (
                lambda self, name: "/fake/tls_ca_chain.pem"
            )
            mock_sess = MagicMock()
            mock_sess_cls.return_value = mock_sess
            api = SHCAPI(_IP, "/cert.pem", "/key.pem", ssl_verify=ssl_verify)
            return api, mock_sess

    def test_verify_true_uses_ca_chain(self):
        _, sess = self._build(ssl_verify=True)
        assert sess.verify == "/fake/tls_ca_chain.pem"

    def test_verify_false_disables_verification(self):
        _, sess = self._build(ssl_verify=False)
        assert sess.verify is False

    def test_default_is_verify_on(self):
        _, sess = self._build()
        assert sess.verify == "/fake/tls_ca_chain.pem"

    def test_client_cert_unaffected_when_verify_off(self):
        _, sess = self._build(ssl_verify=False)
        assert sess.cert == ("/cert.pem", "/key.pem")


class TestHostNameIgnoringAdapter:
    def test_assert_hostname_false(self):
        from boschshcpy.api import HostNameIgnoringAdapter
        from requests.packages.urllib3.poolmanager import PoolManager

        adapter = HostNameIgnoringAdapter()
        captured = {}

        original_pm = PoolManager

        def capturing_pm(**kw):
            captured.update(kw)
            return original_pm(**kw)

        with patch("boschshcpy.api.PoolManager", side_effect=capturing_pm):
            adapter.init_poolmanager(connections=2, maxsize=5)

        assert captured.get("assert_hostname") is False
        assert captured["num_pools"] == 2
        assert captured["maxsize"] == 5
