"""
Tests for SHCSession.__init__ — covers lines 28-61 of session.py.

Isolation: patch SHCAPI + SHCDeviceHelper + SHCEmma so no disk/network access.
Style: mirrors test_session_unit.py. Does NOT duplicate its assertions.
"""

from collections import defaultdict
from unittest.mock import MagicMock, call, patch

import pytest

from boschshcpy.session import SHCSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patched_init(lazy=False, zeroconf=None):
    """
    Construct a real SHCSession via __init__ with all external deps patched.

    Returns (session, mock_api_instance, mock_api_class, mock_enumerate_all).
    """
    mock_api_instance = MagicMock()
    mock_api_class = MagicMock(return_value=mock_api_instance)

    mock_device_helper_instance = MagicMock()
    mock_device_helper_class = MagicMock(return_value=mock_device_helper_instance)

    mock_emma_instance = MagicMock()
    mock_emma_class = MagicMock(return_value=mock_emma_instance)

    enumerate_calls = []

    with patch("boschshcpy.session.SHCAPI", mock_api_class), \
         patch("boschshcpy.session.SHCDeviceHelper", mock_device_helper_class), \
         patch("boschshcpy.session.SHCEmma", mock_emma_class), \
         patch.object(SHCSession, "_enumerate_all",
                      lambda self: enumerate_calls.append("called")):
        session = SHCSession(
            controller_ip="192.0.2.1",
            certificate="/fake/cert.pem",
            key="/fake/key.pem",
            lazy=lazy,
            zeroconf=zeroconf,
        )

    return session, mock_api_instance, mock_api_class, enumerate_calls, \
           mock_device_helper_class, mock_device_helper_instance, \
           mock_emma_class, mock_emma_instance


# ---------------------------------------------------------------------------
# SHCAPI construction (lines 28-30)
# ---------------------------------------------------------------------------

class TestInitApiConstruction:
    def test_shcapi_called_with_correct_args(self):
        """SHCAPI called with controller_ip/certificate/key and verify_hostname=False."""
        _, _, mock_api_class, *_ = _patched_init(lazy=True)
        mock_api_class.assert_called_once_with(
            controller_ip="192.0.2.1",
            certificate="/fake/cert.pem",
            key="/fake/key.pem",
            verify_hostname=False,
            ssl_verify=True,
        )

    def test_api_attribute_is_shcapi_instance(self):
        """session._api must be the instance returned by SHCAPI(...)."""
        session, mock_api_instance, *_ = _patched_init(lazy=True)
        assert session._api is mock_api_instance

    def test_api_property_returns_same_instance(self):
        """session.api property (line 389) forwards _api."""
        session, mock_api_instance, *_ = _patched_init(lazy=True)
        assert session.api is mock_api_instance


# ---------------------------------------------------------------------------
# SHCDeviceHelper construction (line 31)
# ---------------------------------------------------------------------------

class TestInitDeviceHelper:
    def test_device_helper_called_with_api(self):
        """Line 31: SHCDeviceHelper(self._api)."""
        session, mock_api_instance, _, _enum, mock_dh_class, mock_dh_instance, *_ = \
            _patched_init(lazy=True)
        mock_dh_class.assert_called_once_with(mock_api_instance)

    def test_device_helper_attribute_set(self):
        """session._device_helper is the instance from SHCDeviceHelper(...)."""
        session, _, _, _enum, _, mock_dh_instance, *_ = _patched_init(lazy=True)
        assert session._device_helper is mock_dh_instance

    def test_device_helper_property_returns_instance(self):
        """session.device_helper property forwards _device_helper."""
        session, _, _, _enum, _, mock_dh_instance, *_ = _patched_init(lazy=True)
        assert session.device_helper is mock_dh_instance


# ---------------------------------------------------------------------------
# Scalar attribute initialisation (lines 34-48)
# ---------------------------------------------------------------------------

class TestInitAttributes:
    def setup_method(self):
        self.session, *_ = _patched_init(lazy=True)

    def test_poll_id_is_none(self):
        assert self.session._poll_id is None

    def test_shc_information_is_none(self):
        assert self.session._shc_information is None

    def test_zeroconf_none_when_not_passed(self):
        assert self.session._zeroconf is None

    def test_zeroconf_stored_when_passed(self):
        session, *_ = _patched_init(lazy=True, zeroconf="fake_zeroconf")
        assert session._zeroconf == "fake_zeroconf"

    def test_rooms_by_id_empty_dict(self):
        assert self.session._rooms_by_id == {}

    def test_scenarios_by_id_empty_dict(self):
        assert self.session._scenarios_by_id == {}

    def test_devices_by_id_empty_dict(self):
        assert self.session._devices_by_id == {}

    def test_services_by_device_id_is_defaultdict(self):
        s = self.session
        assert isinstance(s._services_by_device_id, defaultdict)
        # defaultdict(list): accessing unknown key returns []
        assert s._services_by_device_id["new_key"] == []

    def test_domains_by_id_empty_dict(self):
        assert self.session._domains_by_id == {}

    def test_messages_by_id_empty_dict(self):
        assert self.session._messages_by_id == {}

    def test_userdefinedstates_by_id_empty_dict(self):
        assert self.session._userdefinedstates_by_id == {}

    def test_subscribers_empty_list(self):
        assert self.session._subscribers == []


# ---------------------------------------------------------------------------
# SHCEmma construction (line 49)
# ---------------------------------------------------------------------------

class TestInitEmma:
    def test_emma_called_with_api(self):
        """Line 49: SHCEmma(self._api) — initial emma before enumerate."""
        session, mock_api_instance, _, _enum, _, _, mock_emma_class, _ = \
            _patched_init(lazy=True)
        # First call is from __init__ line 49 (lazy=True skips _initialize_emma)
        assert mock_emma_class.call_count >= 1
        first_call_args = mock_emma_class.call_args_list[0]
        assert first_call_args == call(mock_api_instance)

    def test_emma_attribute_set(self):
        """session._emma is the SHCEmma instance."""
        session, _, _, _enum, _, _, _, mock_emma_instance = _patched_init(lazy=True)
        assert session._emma is mock_emma_instance


# ---------------------------------------------------------------------------
# lazy flag — _enumerate_all (lines 51-52)
# ---------------------------------------------------------------------------

class TestInitLazyFlag:
    def test_enumerate_all_not_called_when_lazy(self):
        """lazy=True: _enumerate_all must NOT be called."""
        _, _, _, enum_calls, *_ = _patched_init(lazy=True)
        assert enum_calls == []

    def test_enumerate_all_called_when_not_lazy(self):
        """lazy=False (default): _enumerate_all MUST be called once."""
        _, _, _, enum_calls, *_ = _patched_init(lazy=False)
        assert enum_calls == ["called"]

    def test_default_lazy_is_false(self):
        """Default lazy=False means enumerate is triggered."""
        mock_api_class = MagicMock(return_value=MagicMock())
        enum_calls = []
        with patch("boschshcpy.session.SHCAPI", mock_api_class), \
             patch("boschshcpy.session.SHCDeviceHelper", MagicMock()), \
             patch("boschshcpy.session.SHCEmma", MagicMock()), \
             patch.object(SHCSession, "_enumerate_all",
                          lambda self: enum_calls.append("called")):
            SHCSession("192.0.2.1", "/cert", "/key")
        assert enum_calls == ["called"]


# ---------------------------------------------------------------------------
# Post-enumerate attributes (lines 54-61)
# ---------------------------------------------------------------------------

class TestInitPostEnumerateAttributes:
    def setup_method(self):
        self.session, *_ = _patched_init(lazy=True)

    def test_polling_thread_is_none(self):
        assert self.session._polling_thread is None

    def test_stop_polling_thread_is_false(self):
        assert self.session._stop_polling_thread is False

    def test_reset_connection_listener_is_none(self):
        assert self.session.reset_connection_listener is None

    def test_scenario_callbacks_empty_dict(self):
        assert self.session._scenario_callbacks == {}

    def test_userdefinedstate_callbacks_is_defaultdict(self):
        s = self.session
        assert isinstance(s._userdefinedstate_callbacks, defaultdict)
        assert s._userdefinedstate_callbacks["new_key"] == []
