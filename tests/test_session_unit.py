"""
Unit tests for boschshcpy/session.py.

Isolation strategy:
- Bypass __init__ via SHCSession.__new__(SHCSession) to avoid network/FS
- Inject fake API (SimpleNamespace / MagicMock)
- No real threads started; polling thread logic tested via extracted closures
- All JSON-RPC payloads match the shapes used in session.py branching logic
"""

import json
import threading
from collections import defaultdict
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from boschshcpy.api import JSONRPCError
from boschshcpy.exceptions import SHCSessionError
from boschshcpy.session import SHCSession


# ---------------------------------------------------------------------------
# Helpers / factories
# ---------------------------------------------------------------------------

def _bare_session() -> SHCSession:
    """Return a SHCSession bypassing __init__ with minimal attribute seeding."""
    s = SHCSession.__new__(SHCSession)
    s._api = MagicMock()
    s._device_helper = MagicMock()
    s._poll_id = None
    s._shc_information = None
    s._zeroconf = None
    s._rooms_by_id = {}
    s._scenarios_by_id = {}
    s._devices_by_id = {}
    s._services_by_device_id = defaultdict(list)
    s._domains_by_id = {}
    s._messages_by_id = {}
    s._userdefinedstates_by_id = {}
    s._subscribers = []
    s._emma = MagicMock()
    s._polling_thread = None
    s._stop_polling_thread = False
    s.reset_connection_listener = None
    s._scenario_callbacks = {}
    s._userdefinedstate_callbacks = defaultdict(list)
    return s


def _fake_device(device_id: str = "hdm:Device:1"):
    dev = MagicMock()
    dev.id = device_id
    return dev


def _fake_intrusion(types=None):
    ids = MagicMock()
    ids.DOMAIN_STATES = {
        "armingState",
        "alarmState",
        "securityGapState",
        "activeConfigurationProfile",
        "systemAvailability",
    }
    ids.process_long_polling_poll_result = MagicMock()
    return ids


# ---------------------------------------------------------------------------
# Properties & simple accessors
# ---------------------------------------------------------------------------

class TestPropertyAccessors:
    def test_api_property(self):
        s = _bare_session()
        assert s.api is s._api

    def test_device_helper_property(self):
        s = _bare_session()
        assert s.device_helper is s._device_helper

    def test_devices_returns_list_copy(self):
        s = _bare_session()
        dev = _fake_device("hdm:1")
        s._devices_by_id["hdm:1"] = dev
        result = s.devices
        assert isinstance(result, list)
        assert dev in result

    def test_device_by_id(self):
        s = _bare_session()
        dev = _fake_device("hdm:X")
        s._devices_by_id["hdm:X"] = dev
        assert s.device("hdm:X") is dev

    def test_rooms_returns_list(self):
        s = _bare_session()
        room = MagicMock()
        s._rooms_by_id["r1"] = room
        assert room in s.rooms

    def test_room_by_id(self):
        s = _bare_session()
        room = MagicMock()
        s._rooms_by_id["r1"] = room
        assert s.room("r1") is room

    def test_room_none_returns_fallback(self):
        s = _bare_session()
        s._api._api_root = "https://fake:8444/smarthome"
        with patch("boschshcpy.session.SHCRoom") as mock_room:
            mock_room.return_value = "fallback"
            result = s.room(None)
        assert result == "fallback"

    def test_scenarios_list(self):
        s = _bare_session()
        sc = MagicMock()
        s._scenarios_by_id["sc1"] = sc
        assert sc in s.scenarios

    def test_scenario_by_id(self):
        s = _bare_session()
        sc = MagicMock()
        s._scenarios_by_id["sc1"] = sc
        assert s.scenario("sc1") is sc

    def test_scenario_names(self):
        s = _bare_session()
        sc = MagicMock()
        sc.name = "Away"
        s._scenarios_by_id["sc1"] = sc
        assert "Away" in s.scenario_names

    def test_messages_list(self):
        s = _bare_session()
        msg = MagicMock()
        s._messages_by_id["m1"] = msg
        assert msg in s.messages

    def test_userdefinedstates_list(self):
        s = _bare_session()
        uds = MagicMock()
        s._userdefinedstates_by_id["u1"] = uds
        assert uds in s.userdefinedstates

    def test_userdefinedstate_by_id(self):
        s = _bare_session()
        uds = MagicMock()
        s._userdefinedstates_by_id["u1"] = uds
        assert s.userdefinedstate("u1") is uds

    def test_information_property(self):
        s = _bare_session()
        info = MagicMock()
        s._shc_information = info
        assert s.information is info

    def test_intrusion_system_property(self):
        s = _bare_session()
        ids = _fake_intrusion()
        s._domains_by_id["IDS"] = ids
        assert s.intrusion_system is ids

    def test_emma_property(self):
        s = _bare_session()
        emma = MagicMock()
        s._emma = emma
        assert s.emma is emma


# ---------------------------------------------------------------------------
# subscribe / scenario callbacks / userdefinedstate callbacks
# ---------------------------------------------------------------------------

class TestSubscriptions:
    def test_subscribe_appends(self):
        s = _bare_session()
        cb_tuple = (MagicMock, lambda x: None)
        s.subscribe(cb_tuple)
        assert cb_tuple in s._subscribers

    def test_subscribe_scenario_callback(self):
        s = _bare_session()
        cb = MagicMock()
        s.subscribe_scenario_callback("sc1", cb)
        assert s._scenario_callbacks["sc1"] is cb

    def test_unsubscribe_scenario_callback(self):
        s = _bare_session()
        s._scenario_callbacks["sc1"] = MagicMock()
        s.unsubscribe_scenario_callback("sc1")
        assert "sc1" not in s._scenario_callbacks

    def test_unsubscribe_scenario_callback_missing_key_noop(self):
        s = _bare_session()
        # Should not raise
        s.unsubscribe_scenario_callback("nonexistent")

    def test_subscribe_userdefinedstate_callback(self):
        s = _bare_session()
        cb = MagicMock()
        s.subscribe_userdefinedstate_callback("u1", cb)
        assert cb in s._userdefinedstate_callbacks["u1"]

    def test_subscribe_userdefinedstate_multiple_callbacks(self):
        s = _bare_session()
        cb1, cb2 = MagicMock(), MagicMock()
        s.subscribe_userdefinedstate_callback("u1", cb1)
        s.subscribe_userdefinedstate_callback("u1", cb2)
        assert s._userdefinedstate_callbacks["u1"] == [cb1, cb2]

    def test_unsubscribe_userdefinedstate_callbacks(self):
        s = _bare_session()
        s._userdefinedstate_callbacks["u1"] = [MagicMock()]
        s.unsubscribe_userdefinedstate_callbacks("u1")
        assert "u1" not in s._userdefinedstate_callbacks


# ---------------------------------------------------------------------------
# _long_poll: subscribe + poll
# ---------------------------------------------------------------------------

class TestLongPoll:
    def test_long_poll_subscribes_when_no_poll_id(self):
        s = _bare_session()
        s._api.long_polling_subscribe.return_value = "poll-1"
        s._api.long_polling_poll.return_value = []
        s._long_poll()
        s._api.long_polling_subscribe.assert_called_once()
        assert s._poll_id == "poll-1"

    def test_long_poll_does_not_resubscribe_when_poll_id_set(self):
        s = _bare_session()
        s._poll_id = "existing-id"
        s._api.long_polling_poll.return_value = []
        s._long_poll()
        s._api.long_polling_subscribe.assert_not_called()
        assert s._poll_id == "existing-id"

    def test_long_poll_returns_true_on_success(self):
        s = _bare_session()
        s._poll_id = "pid"
        s._api.long_polling_poll.return_value = []
        assert s._long_poll() is True

    def test_long_poll_passes_results_to_processor(self):
        s = _bare_session()
        s._poll_id = "pid"
        result = {"@type": "DeviceServiceData", "deviceId": "hdm:X"}
        s._api.long_polling_poll.return_value = [result]
        dev = MagicMock()
        s._devices_by_id["hdm:X"] = dev
        s._long_poll()
        dev.process_long_polling_poll_result.assert_called_once_with(result)

    def test_long_poll_invalidates_poll_id_on_rpc_error_32001(self):
        s = _bare_session()
        s._poll_id = "stale"
        s._api.long_polling_subscribe.return_value = "new-id"
        err = JSONRPCError(-32001, "UNKNOWN_POLLID")
        s._api.long_polling_poll.side_effect = err
        result = s._long_poll()
        assert result is False
        assert s._poll_id is None

    def test_long_poll_reraises_other_rpc_errors(self):
        s = _bare_session()
        s._poll_id = "pid"
        err = JSONRPCError(-32600, "Invalid Request")
        s._api.long_polling_poll.side_effect = err
        with pytest.raises(JSONRPCError) as exc_info:
            s._long_poll()
        assert exc_info.value.code == -32600

    def test_long_poll_passes_wait_seconds(self):
        s = _bare_session()
        s._poll_id = "pid"
        s._api.long_polling_poll.return_value = []
        s._long_poll(wait_seconds=30)
        s._api.long_polling_poll.assert_called_once_with("pid", 30)


# ---------------------------------------------------------------------------
# _maybe_unsubscribe
# ---------------------------------------------------------------------------

class TestMaybeUnsubscribe:
    def test_unsubscribes_when_poll_id_set(self):
        s = _bare_session()
        s._poll_id = "pid"
        s._maybe_unsubscribe()
        s._api.long_polling_unsubscribe.assert_called_once_with("pid")
        assert s._poll_id is None

    def test_noop_when_no_poll_id(self):
        s = _bare_session()
        s._poll_id = None
        s._maybe_unsubscribe()
        s._api.long_polling_unsubscribe.assert_not_called()


# ---------------------------------------------------------------------------
# _process_long_polling_poll_result — all branches
# ---------------------------------------------------------------------------

class TestProcessLongPollingPollResult:

    # --- DeviceServiceData ---

    def test_device_service_data_known_device(self):
        s = _bare_session()
        dev = MagicMock()
        s._devices_by_id["hdm:D1"] = dev
        raw = {"@type": "DeviceServiceData", "deviceId": "hdm:D1"}
        s._process_long_polling_poll_result(raw)
        dev.process_long_polling_poll_result.assert_called_once_with(raw)

    def test_device_service_data_unknown_device_skipped(self):
        s = _bare_session()
        raw = {"@type": "DeviceServiceData", "deviceId": "hdm:Unknown"}
        # No exception; no device touched
        s._process_long_polling_poll_result(raw)

    # --- message ---

    def test_message_with_device_service_data_model(self):
        s = _bare_session()
        inner = {"@type": "DeviceServiceData", "deviceId": "hdm:D2"}
        dev = MagicMock()
        s._devices_by_id["hdm:D2"] = dev
        raw = {
            "@type": "message",
            "id": "msg1",
            "arguments": {"deviceServiceDataModel": json.dumps(inner)},
        }
        s._process_long_polling_poll_result(raw)
        dev.process_long_polling_poll_result.assert_called_once_with(inner)

    def test_message_without_device_service_data_stores_message(self):
        s = _bare_session()
        raw = {
            "@type": "message",
            "id": "msg2",
            "arguments": {},
            "messageCode": {"name": "TILT", "category": "WARNING"},
            "sourceType": "DEVICE",
            "timestamp": 12345,
            "flags": [],
        }
        with patch("boschshcpy.session.SHCMessage") as MockMsg:
            mock_inst = MagicMock()
            MockMsg.return_value = mock_inst
            s._process_long_polling_poll_result(raw)
        assert "msg2" in s._messages_by_id

    # --- scenarioTriggered ---

    def test_scenario_triggered_calls_specific_callback(self):
        s = _bare_session()
        cb = MagicMock()
        s._scenario_callbacks["sc1"] = cb
        raw = {"@type": "scenarioTriggered", "id": "sc1"}
        s._process_long_polling_poll_result(raw)
        cb.assert_called_once_with(raw)

    def test_scenario_triggered_calls_shc_legacy_callback(self):
        s = _bare_session()
        cb = MagicMock()
        s._scenario_callbacks["shc"] = cb
        raw = {"@type": "scenarioTriggered", "id": "sc99"}
        s._process_long_polling_poll_result(raw)
        cb.assert_called_once_with(raw)

    def test_scenario_triggered_both_callbacks(self):
        s = _bare_session()
        cb1, cb2 = MagicMock(), MagicMock()
        s._scenario_callbacks["sc1"] = cb1
        s._scenario_callbacks["shc"] = cb2
        raw = {"@type": "scenarioTriggered", "id": "sc1"}
        s._process_long_polling_poll_result(raw)
        cb1.assert_called_once_with(raw)
        cb2.assert_called_once_with(raw)

    def test_scenario_triggered_no_callback_no_error(self):
        s = _bare_session()
        raw = {"@type": "scenarioTriggered", "id": "sc_none"}
        s._process_long_polling_poll_result(raw)  # must not raise

    # --- device: update existing ---

    def test_device_update_existing(self):
        s = _bare_session()
        dev = MagicMock()
        s._devices_by_id["hdm:D3"] = dev
        raw = {"@type": "device", "id": "hdm:D3"}
        s._process_long_polling_poll_result(raw)
        dev.update_raw_information.assert_called_once_with(raw)

    def test_device_deleted_removes_from_dicts(self):
        s = _bare_session()
        dev = MagicMock()
        s._devices_by_id["hdm:D4"] = dev
        s._services_by_device_id["hdm:D4"].append("svc")
        raw = {"@type": "device", "id": "hdm:D4", "deleted": True}
        s._process_long_polling_poll_result(raw)
        assert "hdm:D4" not in s._devices_by_id
        assert "hdm:D4" not in s._services_by_device_id

    def test_device_deleted_false_keeps_device(self):
        s = _bare_session()
        dev = MagicMock()
        s._devices_by_id["hdm:D5"] = dev
        raw = {"@type": "device", "id": "hdm:D5", "deleted": False}
        s._process_long_polling_poll_result(raw)
        assert "hdm:D5" in s._devices_by_id

    def test_device_new_calls_add_device_and_subscriber_callback(self):
        s = _bare_session()
        new_dev = MagicMock()
        new_dev.__class__ = MagicMock  # isinstance always True against MagicMock
        s._device_helper.device_init.return_value = new_dev
        raw = {"@type": "device", "id": "hdm:NEW", "deviceServiceIds": ["svc1"]}

        # Mock _add_device to inject the new device
        captured = {}

        def fake_add_device(raw_device, update_services=False):
            captured["called_with"] = raw_device
            s._devices_by_id["hdm:NEW"] = new_dev
            return new_dev

        s._add_device = fake_add_device

        cb = MagicMock()
        s._subscribers.append((object, cb))  # isinstance(new_dev, object) is True
        s._process_long_polling_poll_result(raw)
        assert captured["called_with"] is raw
        cb.assert_called_once_with(new_dev)

    def test_device_new_no_subscriber_no_crash(self):
        s = _bare_session()

        def fake_add_device(raw_device, update_services=False):
            return MagicMock()

        s._add_device = fake_add_device
        raw = {"@type": "device", "id": "hdm:NEWX"}
        s._process_long_polling_poll_result(raw)  # no subscribers, must not raise

    # --- intrusion domain states ---

    def test_domain_state_dispatched_to_intrusion_system(self):
        s = _bare_session()
        ids = _fake_intrusion()
        s._domains_by_id["IDS"] = ids
        raw = {"@type": "armingState", "state": "SYSTEM_DISARMED"}
        s._process_long_polling_poll_result(raw)
        ids.process_long_polling_poll_result.assert_called_once_with(raw)

    def test_domain_state_skipped_when_no_intrusion_system(self):
        s = _bare_session()
        s._domains_by_id["IDS"] = None
        raw = {"@type": "alarmState", "state": "ALARM_OFF"}
        s._process_long_polling_poll_result(raw)  # must not raise

    def test_all_domain_state_types_dispatched(self):
        from boschshcpy.domain_impl import SHCIntrusionSystem

        s = _bare_session()
        ids = _fake_intrusion()
        s._domains_by_id["IDS"] = ids
        for dtype in SHCIntrusionSystem.DOMAIN_STATES:
            raw = {"@type": dtype}
            s._process_long_polling_poll_result(raw)
        assert ids.process_long_polling_poll_result.call_count == len(
            SHCIntrusionSystem.DOMAIN_STATES
        )

    # --- userDefinedState ---

    def test_userdefinedstate_update_existing(self):
        s = _bare_session()
        uds = MagicMock()
        s._userdefinedstates_by_id["u1"] = uds
        raw = {"@type": "userDefinedState", "id": "u1", "name": "At Home", "state": True, "deleted": False}
        s._process_long_polling_poll_result(raw)
        uds.update_raw_information.assert_called_once_with(raw)

    def test_userdefinedstate_existing_fires_callbacks(self):
        s = _bare_session()
        uds = MagicMock()
        s._userdefinedstates_by_id["u1"] = uds
        cb = MagicMock()
        s._userdefinedstate_callbacks["u1"].append(cb)
        raw = {"@type": "userDefinedState", "id": "u1", "name": "x", "state": True, "deleted": False}
        s._process_long_polling_poll_result(raw)
        cb.assert_called_once()

    def test_userdefinedstate_new_stored_and_subscriber_called(self):
        s = _bare_session()
        info_mock = MagicMock()
        s._shc_information = info_mock

        raw = {
            "@type": "userDefinedState",
            "id": "u99",
            "name": "New State",
            "state": False,
            "deleted": False,
        }

        with patch("boschshcpy.session.SHCUserDefinedState") as MockUDS:
            new_uds = MagicMock()
            MockUDS.return_value = new_uds
            cb = MagicMock()
            # subscriber for any object type
            s._subscribers.append((object, cb))
            s._process_long_polling_poll_result(raw)

        assert "u99" in s._userdefinedstates_by_id
        cb.assert_called_once_with(new_uds)

    def test_userdefinedstate_no_callback_no_crash(self):
        s = _bare_session()
        uds = MagicMock()
        s._userdefinedstates_by_id["u2"] = uds
        # No callbacks registered for u2
        raw = {"@type": "userDefinedState", "id": "u2", "name": "x", "state": True, "deleted": False}
        s._process_long_polling_poll_result(raw)  # must not raise

    # --- link / emma ---

    def test_link_emma_applink_calls_update_emma_data(self):
        s = _bare_session()
        emma = MagicMock()
        s._emma = emma
        raw = {"@type": "link", "id": "com.bosch.tt.emma.applink", "data": {}}
        s._process_long_polling_poll_result(raw)
        emma.update_emma_data.assert_called_once_with(raw)

    def test_link_other_id_no_update(self):
        s = _bare_session()
        emma = MagicMock()
        s._emma = emma
        raw = {"@type": "link", "id": "some.other.link"}
        s._process_long_polling_poll_result(raw)
        emma.update_emma_data.assert_not_called()

    def test_unknown_type_no_crash(self):
        s = _bare_session()
        raw = {"@type": "futureUnknownType", "id": "x"}
        s._process_long_polling_poll_result(raw)  # must not raise


# ---------------------------------------------------------------------------
# start_polling / stop_polling
# ---------------------------------------------------------------------------

class TestPollingLifecycle:
    def test_start_polling_raises_when_already_polling(self):
        s = _bare_session()
        s._polling_thread = MagicMock()  # already set
        with pytest.raises(SHCSessionError):
            s.start_polling()

    def test_stop_polling_raises_when_not_polling(self):
        s = _bare_session()
        s._polling_thread = None
        with pytest.raises(SHCSessionError):
            s.stop_polling()

    def test_start_polling_creates_thread(self):
        s = _bare_session()
        s._api.long_polling_subscribe.return_value = "pid"
        # Make the polling loop exit immediately
        s._stop_polling_thread = False

        started_events = []

        original_thread_init = threading.Thread.__init__

        with patch("boschshcpy.session.threading.Thread") as MockThread:
            mock_thread = MagicMock()
            MockThread.return_value = mock_thread
            s.start_polling()
            MockThread.assert_called_once()
            mock_thread.start.assert_called_once()

        assert s._polling_thread is mock_thread

    def test_stop_polling_joins_thread_and_unsubscribes(self):
        s = _bare_session()
        mock_thread = MagicMock()
        s._polling_thread = mock_thread
        s._poll_id = "pid"
        s._stop_polling_thread = False

        s.stop_polling()

        assert s._stop_polling_thread is True
        mock_thread.join.assert_called_once()
        s._api.long_polling_unsubscribe.assert_called_once_with("pid")
        assert s._poll_id is None
        assert s._polling_thread is None

    def test_stop_polling_clears_poll_id(self):
        s = _bare_session()
        mock_thread = MagicMock()
        s._polling_thread = mock_thread
        s._poll_id = None  # Already unsubscribed
        s.stop_polling()
        # unsubscribe NOT called since poll_id was None
        s._api.long_polling_unsubscribe.assert_not_called()
        assert s._polling_thread is None


# ---------------------------------------------------------------------------
# Polling thread internal logic (white-box: extract the closure)
# ---------------------------------------------------------------------------

class TestPollingThreadLogic:
    """Exercise the inner polling_thread_main closure without real threads."""

    def _capture_polling_closure(self, s: SHCSession):
        """Capture the closure by intercepting Thread creation."""
        captured = {}
        original_start_polling = SHCSession.start_polling

        with patch("boschshcpy.session.threading.Thread") as MockThread:
            mock_thread = MagicMock()
            MockThread.return_value = mock_thread

            def capture_target(*args, **kwargs):
                target = kwargs.get("target") or args[0] if args else None
                # Thread(target=fn, name=...) pattern
                call_kwargs = MockThread.call_args
                captured["target"] = call_kwargs.kwargs.get("target") or call_kwargs.args[0] if call_kwargs.args else None
                return mock_thread

            MockThread.side_effect = capture_target
            s.start_polling()

        # Re-extract via call_args
        thread_call = MockThread.call_args
        target = thread_call.kwargs.get("target")
        return target

    def test_polling_loop_calls_long_poll(self):
        s = _bare_session()
        call_count = [0]

        def fake_long_poll():
            call_count[0] += 1
            s._stop_polling_thread = True  # exit after one iteration
            return True

        s._long_poll = fake_long_poll

        target = self._capture_polling_closure(s)
        s._stop_polling_thread = False
        target()
        assert call_count[0] == 1

    def test_polling_loop_sleeps_on_false_return(self):
        s = _bare_session()
        iterations = [0]

        def fake_long_poll():
            iterations[0] += 1
            if iterations[0] >= 2:
                s._stop_polling_thread = True
            return False

        s._long_poll = fake_long_poll

        target = self._capture_polling_closure(s)
        s._stop_polling_thread = False
        with patch("boschshcpy.session.time.sleep") as mock_sleep:
            target()
        # sleep(1.0) called for each False return (iterations=1 before stop)
        mock_sleep.assert_any_call(1.0)

    def test_polling_loop_runtime_error_stops_thread(self):
        s = _bare_session()
        s._poll_id = "pid"

        def fake_long_poll():
            raise RuntimeError("expected shutdown")

        s._long_poll = fake_long_poll

        target = self._capture_polling_closure(s)
        s._stop_polling_thread = False
        target()  # must not raise
        assert s._stop_polling_thread is True

    def test_polling_loop_runtime_error_attempts_unsubscribe(self):
        s = _bare_session()
        s._poll_id = "pid"
        unsubscribe_called = [False]

        def fake_long_poll():
            raise RuntimeError("shutdown")

        def fake_unsubscribe():
            unsubscribe_called[0] = True

        s._long_poll = fake_long_poll
        s._maybe_unsubscribe = fake_unsubscribe

        target = self._capture_polling_closure(s)
        s._stop_polling_thread = False
        target()
        assert unsubscribe_called[0] is True

    def test_polling_loop_runtime_error_unsubscribe_fails_logged(self):
        """Lines 280-281: unsubscribe raises inside RuntimeError handler — logged, not re-raised."""
        s = _bare_session()
        s._poll_id = "pid"

        def fake_long_poll():
            raise RuntimeError("shutdown")

        def fake_unsubscribe_fails():
            raise OSError("connection refused")

        s._long_poll = fake_long_poll
        s._maybe_unsubscribe = fake_unsubscribe_fails

        target = self._capture_polling_closure(s)
        s._stop_polling_thread = False
        target()  # must NOT raise despite unsubscribe failure
        assert s._stop_polling_thread is True

    def test_polling_loop_exception_waits_15s(self):
        s = _bare_session()
        iterations = [0]

        def fake_long_poll():
            iterations[0] += 1
            if iterations[0] == 1:
                raise ValueError("transient error")
            s._stop_polling_thread = True
            return True

        s._long_poll = fake_long_poll

        target = self._capture_polling_closure(s)
        s._stop_polling_thread = False
        with patch("boschshcpy.session.time.sleep") as mock_sleep:
            target()
        mock_sleep.assert_any_call(15.0)


# ---------------------------------------------------------------------------
# _add_device
# ---------------------------------------------------------------------------

class TestAddDevice:
    def test_add_device_skipped_when_no_services(self):
        s = _bare_session()
        raw = {"id": "hdm:Empty"}
        # No services → should return None and skip
        result = s._add_device(raw)
        assert result is None
        assert "hdm:Empty" not in s._devices_by_id

    def test_add_device_with_services(self):
        s = _bare_session()
        raw = {"id": "hdm:D1"}
        s._services_by_device_id["hdm:D1"].append({"id": "svc", "deviceId": "hdm:D1"})
        fake_dev = MagicMock()
        s._device_helper.device_init.return_value = fake_dev
        result = s._add_device(raw)
        assert result is fake_dev
        assert s._devices_by_id["hdm:D1"] is fake_dev

    def test_add_device_update_services_fetches_api(self):
        s = _bare_session()
        raw = {"id": "hdm:D2"}
        svc = {"id": "CameraLive", "deviceId": "hdm:D2"}
        s._api.get_device_services.return_value = [svc]

        # SUPPORTED_DEVICE_SERVICE_IDS is a set — patch via the module attribute
        import boschshcpy.session as session_mod
        original = session_mod.SUPPORTED_DEVICE_SERVICE_IDS
        try:
            session_mod.SUPPORTED_DEVICE_SERVICE_IDS = {"CameraLive"}
            fake_dev = MagicMock()
            s._device_helper.device_init.return_value = fake_dev
            result = s._add_device(raw, update_services=True)
        finally:
            session_mod.SUPPORTED_DEVICE_SERVICE_IDS = original

        s._api.get_device_services.assert_called_once_with("hdm:D2")
        assert result is fake_dev

    def test_add_device_update_services_clears_old_services(self):
        s = _bare_session()
        raw = {"id": "hdm:D3"}
        s._services_by_device_id["hdm:D3"].append("old_svc")
        s._api.get_device_services.return_value = []  # no new services

        result = s._add_device(raw, update_services=True)
        # Old services cleared, none added → skipped
        assert result is None


# ---------------------------------------------------------------------------
# _enumerate_* helpers (isolated)
# ---------------------------------------------------------------------------

class TestEnumerateHelpers:
    def test_enumerate_services_filters_unsupported(self):
        s = _bare_session()
        s._api.get_services.return_value = [
            {"id": "SupportedService", "deviceId": "hdm:D1"},
            {"id": "UnsupportedService", "deviceId": "hdm:D2"},
        ]
        import boschshcpy.session as session_mod
        original = session_mod.SUPPORTED_DEVICE_SERVICE_IDS
        try:
            session_mod.SUPPORTED_DEVICE_SERVICE_IDS = {"SupportedService"}
            s._enumerate_services()
        finally:
            session_mod.SUPPORTED_DEVICE_SERVICE_IDS = original
        assert "hdm:D1" in s._services_by_device_id
        assert "hdm:D2" not in s._services_by_device_id

    def test_enumerate_rooms_populates_dict(self):
        s = _bare_session()
        raw_room = {"id": "room1", "name": "Living Room", "iconId": "1"}
        s._api.get_rooms.return_value = [raw_room]
        with patch("boschshcpy.session.SHCRoom") as MockRoom:
            mock_inst = MagicMock()
            MockRoom.return_value = mock_inst
            s._enumerate_rooms()
        assert "room1" in s._rooms_by_id

    def test_enumerate_scenarios_populates_dict(self):
        s = _bare_session()
        raw_sc = {"id": "sc1", "name": "Away", "iconId": "2"}
        s._api.get_scenarios.return_value = [raw_sc]
        with patch("boschshcpy.session.SHCScenario") as MockScenario:
            mock_inst = MagicMock()
            MockScenario.return_value = mock_inst
            s._enumerate_scenarios()
        assert "sc1" in s._scenarios_by_id

    def test_enumerate_messages_populates_dict(self):
        s = _bare_session()
        raw_msg = {
            "id": "msg1",
            "messageCode": {"name": "TILT", "category": "WARNING"},
            "sourceType": "DEVICE",
            "timestamp": 9999,
            "flags": [],
            "arguments": {},
        }
        s._api.get_messages.return_value = [raw_msg]
        with patch("boschshcpy.session.SHCMessage") as MockMsg:
            mock_inst = MagicMock()
            MockMsg.return_value = mock_inst
            s._enumerate_messages()
        assert "msg1" in s._messages_by_id

    def test_enumerate_userdefinedstates_populates_dict(self):
        s = _bare_session()
        info = MagicMock()
        s._shc_information = info
        raw_state = {"id": "uds1", "name": "At Home", "state": True, "deleted": False}
        s._api.get_userdefinedstates.return_value = [raw_state]
        with patch("boschshcpy.session.SHCUserDefinedState") as MockUDS:
            mock_inst = MagicMock()
            MockUDS.return_value = mock_inst
            s._enumerate_userdefinedstates()
        assert "uds1" in s._userdefinedstates_by_id

    def test_enumerate_devices_calls_add_device(self):
        s = _bare_session()
        raw1 = {"id": "hdm:D1"}
        raw2 = {"id": "hdm:D2"}
        s._api.get_devices.return_value = [raw1, raw2]
        added = []

        def fake_add_device(raw, update_services=False):
            added.append(raw["id"])
            return MagicMock()

        s._add_device = fake_add_device
        s._enumerate_devices()
        assert "hdm:D1" in added
        assert "hdm:D2" in added

    def test_add_device_update_services_skips_unsupported(self):
        """Line 82: the continue branch inside update_services loop."""
        s = _bare_session()
        raw = {"id": "hdm:D9"}
        # one unsupported + one supported service
        import boschshcpy.session as session_mod
        original = session_mod.SUPPORTED_DEVICE_SERVICE_IDS
        try:
            session_mod.SUPPORTED_DEVICE_SERVICE_IDS = {"GoodSvc"}
            s._api.get_device_services.return_value = [
                {"id": "BadSvc", "deviceId": "hdm:D9"},
                {"id": "GoodSvc", "deviceId": "hdm:D9"},
            ]
            fake_dev = MagicMock()
            s._device_helper.device_init.return_value = fake_dev
            result = s._add_device(raw, update_services=True)
        finally:
            session_mod.SUPPORTED_DEVICE_SERVICE_IDS = original

        # Only GoodSvc should have been added
        assert len(s._services_by_device_id["hdm:D9"]) == 1
        assert s._services_by_device_id["hdm:D9"][0]["id"] == "GoodSvc"
        assert result is fake_dev


# ---------------------------------------------------------------------------
# _initialize_domains / _initialize_emma
# ---------------------------------------------------------------------------

class TestInitializeHelpers:
    def test_initialize_domains_creates_intrusion_system(self):
        s = _bare_session()
        info = MagicMock()
        info.macAddress = "AA:BB:CC:DD:EE:FF"
        s._shc_information = info
        s._api.get_domain_intrusion_detection.return_value = {"state": "ACTIVE"}

        with patch("boschshcpy.session.SHCIntrusionSystem") as MockIDS:
            mock_ids = MagicMock()
            MockIDS.return_value = mock_ids
            s._initialize_domains()

        assert s._domains_by_id["IDS"] is mock_ids
        MockIDS.assert_called_once_with(
            s._api,
            {"state": "ACTIVE"},
            "AA:BB:CC:DD:EE:FF",
        )

    def test_initialize_emma_creates_emma(self):
        s = _bare_session()
        info = MagicMock()
        s._shc_information = info

        with patch("boschshcpy.session.SHCEmma") as MockEmma:
            mock_emma = MagicMock()
            MockEmma.return_value = mock_emma
            s._initialize_emma()

        assert s._emma is mock_emma
        MockEmma.assert_called_once_with(s._api, info, None)

    def test_enumerate_all_calls_all_steps(self):
        s = _bare_session()
        steps = []
        s.authenticate = lambda: steps.append("authenticate")
        s._enumerate_services = lambda: steps.append("services")
        s._enumerate_devices = lambda: steps.append("devices")
        s._enumerate_rooms = lambda: steps.append("rooms")
        s._enumerate_scenarios = lambda: steps.append("scenarios")
        s._enumerate_messages = lambda: steps.append("messages")
        s._enumerate_userdefinedstates = lambda: steps.append("userdefinedstates")
        s._initialize_domains = lambda: steps.append("domains")
        s._initialize_emma = lambda: steps.append("emma")
        s._enumerate_all()
        assert steps == [
            "authenticate",
            "services",
            "devices",
            "rooms",
            "scenarios",
            "messages",
            "userdefinedstates",
            "domains",
            "emma",
        ]


# ---------------------------------------------------------------------------
# rawscan
# ---------------------------------------------------------------------------

class TestRawscan:
    def test_rawscan_devices(self):
        s = _bare_session()
        s._api.get_devices.return_value = ["dev1"]
        assert s.rawscan(command="devices") == ["dev1"]

    def test_rawscan_device(self):
        s = _bare_session()
        s._api.get_device.return_value = {"id": "hdm:1"}
        result = s.rawscan(command="device", device_id="hdm:1")
        s._api.get_device.assert_called_once_with(device_id="hdm:1")
        assert result == {"id": "hdm:1"}

    def test_rawscan_services(self):
        s = _bare_session()
        s._api.get_services.return_value = []
        assert s.rawscan(command="services") == []

    def test_rawscan_device_services(self):
        s = _bare_session()
        s._api.get_device_services.return_value = [{"id": "svc1"}]
        result = s.rawscan(command="device_services", device_id="hdm:1")
        s._api.get_device_services.assert_called_once_with(device_id="hdm:1")

    def test_rawscan_device_service(self):
        s = _bare_session()
        s._api.get_device_service.return_value = {"id": "svc1"}
        result = s.rawscan(command="device_service", device_id="hdm:1", service_id="svc1")
        s._api.get_device_service.assert_called_once_with(device_id="hdm:1", service_id="svc1")

    def test_rawscan_rooms(self):
        s = _bare_session()
        s._api.get_rooms.return_value = []
        assert s.rawscan(command="rooms") == []

    def test_rawscan_scenarios(self):
        s = _bare_session()
        s._api.get_scenarios.return_value = []
        assert s.rawscan(command="scenarios") == []

    def test_rawscan_messages(self):
        s = _bare_session()
        s._api.get_messages.return_value = []
        assert s.rawscan(command="messages") == []

    def test_rawscan_info(self):
        s = _bare_session()
        s._api.get_information.return_value = {"version": "1.0"}
        assert s.rawscan(command="info") == {"version": "1.0"}

    def test_rawscan_information_alias(self):
        s = _bare_session()
        s._api.get_information.return_value = {"version": "2.0"}
        assert s.rawscan(command="information") == {"version": "2.0"}

    def test_rawscan_public_information(self):
        s = _bare_session()
        s._api.get_public_information.return_value = {"pub": "data"}
        assert s.rawscan(command="public_information") == {"pub": "data"}

    def test_rawscan_intrusion_detection(self):
        s = _bare_session()
        s._api.get_domain_intrusion_detection.return_value = {"ids": True}
        assert s.rawscan(command="intrusion_detection") == {"ids": True}

    def test_rawscan_unknown_command_returns_none(self):
        s = _bare_session()
        assert s.rawscan(command="not_a_real_command") is None

    def test_rawscan_commands_list(self):
        s = _bare_session()
        cmds = s.rawscan_commands
        assert "devices" in cmds
        assert "intrusion_detection" in cmds
        assert len(cmds) == 12


# ---------------------------------------------------------------------------
# authenticate / mdns_info
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_authenticate_creates_shc_information(self):
        s = _bare_session()
        with patch("boschshcpy.session.SHCInformation") as MockInfo:
            mock_info = MagicMock()
            MockInfo.return_value = mock_info
            s.authenticate()
        assert s._shc_information is mock_info

    def test_mdns_info_returns_new_information(self):
        s = _bare_session()
        with patch("boschshcpy.session.SHCInformation") as MockInfo:
            mock_info = MagicMock()
            MockInfo.return_value = mock_info
            result = s.mdns_info()
        assert result is mock_info
        # Must pass authenticate=False
        call_kwargs = MockInfo.call_args.kwargs
        assert call_kwargs.get("authenticate") is False


# ---------------------------------------------------------------------------
# Poll-id resubscribe integration: False return → next call resubscribes
# ---------------------------------------------------------------------------

class TestPollIdResubscribeCycle:
    def test_after_invalidation_next_long_poll_resubscribes(self):
        s = _bare_session()
        s._poll_id = "stale-id"

        # First call: -32001 → invalidate
        err = JSONRPCError(-32001, "UNKNOWN_POLLID")
        s._api.long_polling_poll.side_effect = err
        result1 = s._long_poll()
        assert result1 is False
        assert s._poll_id is None

        # Second call: subscribe succeeds + poll returns empty
        s._api.long_polling_subscribe.return_value = "fresh-id"
        s._api.long_polling_poll.side_effect = None
        s._api.long_polling_poll.return_value = []
        result2 = s._long_poll()
        assert result2 is True
        assert s._poll_id == "fresh-id"
        s._api.long_polling_subscribe.assert_called_once()
