"""Smoke system and measurement-history endpoints (found in the Bosch app)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from test_api_async import _make_api as _make_async_api
from test_api_async import _make_mock_response, cert_and_key_paths  # noqa: F401
from test_api_sync import _API_ROOT, _fake_response
from test_api_sync import _make_api as _make_sync_api

from boschshcpy.exceptions import SHCSessionError

_ASYNC_ROOT = "https://192.0.2.1:8444/smarthome"

_STATE = {
    "@type": "smoke:SystemState",
    "systemAvailability": {"@type": "smoke:SystemAvailabilityState", "available": True},
}
_CONFIG = {
    "@type": "smoke:Configuration",
    "alarmActuatorGroups": [
        {"@type": "smoke:ActuatorGroup", "id": "g1", "deleted": False}
    ],
}
_PAGE = {
    "@type": "measurementsPage",
    "sensorId": "hdm:ZigBee:abc",
    "referenceTime": 1760000000,
    "interval": 86400,
    "intervalRounding": 3600,
    "times": [1759996400],
    "history": {"TEMPERATURE": [21.5]},
}


def _sync(body, status=200):
    api = _make_sync_api()
    api._requests_session.get.return_value = _fake_response(body, status)
    return api


def _url(api):
    return api._requests_session.get.call_args[0][0]


class TestSync:
    def test_smoke_system_state(self):
        api = _sync(_STATE)
        assert api.get_smoke_system_state() == _STATE
        assert _url(api) == f"{_API_ROOT}/smoke/states/system"

    def test_smoke_configuration(self):
        api = _sync(_CONFIG)
        assert api.get_smoke_configuration() == _CONFIG
        assert _url(api) == f"{_API_ROOT}/smoke/configuration"

    def test_measurements_page_url_and_result(self):
        api = _sync(_PAGE)
        result = api.get_measurements_page(
            "hdm:ZigBee:abc", 1760000000, 86400, 3600, 60
        )
        assert result == _PAGE
        assert _url(api) == (
            f"{_API_ROOT}/historicdata/page/hdm%3AZigBee%3Aabc"
            "?referenceTime=1760000000&interval=86400&rounding=3600&overlap=60"
        )

    def test_measurements_page_overlap_defaults_to_zero(self):
        api = _sync(_PAGE)
        api.get_measurements_page("s", 10, 20, 30)
        assert _url(api).endswith("&overlap=0")

    def test_measurements_page_quotes_hash_in_sensor_id(self):
        api = _sync(_PAGE)
        api.get_measurements_page("hdm:ZigBee:abc#2", 1, 2, 3)
        assert "/historicdata/page/hdm%3AZigBee%3Aabc%232?" in _url(api)

    @pytest.mark.parametrize(
        "call",
        [
            lambda a: a.get_smoke_system_state(),
            lambda a: a.get_smoke_configuration(),
            lambda a: a.get_measurements_page("s", 1, 2, 3),
        ],
    )
    def test_http_error_raises(self, call):
        with pytest.raises(SHCSessionError):
            call(_sync({"error": "x"}, status=404))


def _async_api(cert_and_key_paths, body):
    api = _make_async_api(cert_and_key_paths)
    api._session.get = MagicMock(return_value=_make_mock_response(body=body))
    return api


class TestAsync:
    def test_smoke_system_state(self, cert_and_key_paths):
        api = _async_api(cert_and_key_paths, _STATE)
        assert asyncio.run(api.get_smoke_system_state()) == _STATE
        assert api._session.get.call_args[0][0] == f"{_ASYNC_ROOT}/smoke/states/system"

    def test_smoke_configuration(self, cert_and_key_paths):
        api = _async_api(cert_and_key_paths, _CONFIG)
        assert asyncio.run(api.get_smoke_configuration()) == _CONFIG
        assert api._session.get.call_args[0][0] == f"{_ASYNC_ROOT}/smoke/configuration"

    def test_measurements_page(self, cert_and_key_paths):
        api = _async_api(cert_and_key_paths, _PAGE)
        result = asyncio.run(
            api.get_measurements_page("hdm:ZigBee:abc", 1760000000, 86400, 3600)
        )
        assert result == _PAGE
        assert api._session.get.call_args[0][0] == (
            f"{_ASYNC_ROOT}/historicdata/page/hdm%3AZigBee%3Aabc"
            "?referenceTime=1760000000&interval=86400&rounding=3600&overlap=0"
        )


class TestValidation:
    @pytest.mark.parametrize(
        "args",
        [
            ("", 1, 2, 3, 0),
            ("s", -1, 2, 3, 0),
            ("s", 1, 0, 3, 0),
            ("s", 1, 2, 0, 0),
            ("s", 1, 2, 3, -1),
            ("s", True, 2, 3, 0),
            ("s", 1.5, 2, 3, 0),
        ],
    )
    def test_bad_arguments_rejected_before_request(self, args):
        api = _sync(_PAGE)
        with pytest.raises(ValueError):
            api.get_measurements_page(*args)
        api._requests_session.get.assert_not_called()

    def test_async_bad_arguments_rejected(self, cert_and_key_paths):
        api = _async_api(cert_and_key_paths, _PAGE)
        with pytest.raises(ValueError):
            asyncio.run(api.get_measurements_page("s", 1, 0, 3))
        api._session.get.assert_not_called()
