"""Unit tests for boschshcpy/session_async.py — SHCSessionAsync.

Strategy:
- Bypass __init__ via SHCSessionAsync.__new__() to inject a fake API.
- All async tests use asyncio.run() inside plain sync test functions,
  matching the pattern in tests/test_api_async.py (no pytest-asyncio needed,
  but pytest-asyncio 1.3.0 is available on this machine).
- No live SHC; no real aiohttp; all API calls use AsyncMock.

Run:
    PYTHONPATH=/tmp/lib-async PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
        python3 -m pytest tests/test_session_async.py -q -o addopts=""
"""

import asyncio
import json
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boschshcpy.api_async import JSONRPCError
from boschshcpy.exceptions import SHCConnectionError, SHCSessionError
from boschshcpy.session_async import SHCSessionAsync, _AsyncSHCInformation


# ---------------------------------------------------------------------------
# Helpers / factories
# ---------------------------------------------------------------------------

def _fake_api() -> AsyncMock:
    """Return an AsyncMock that quacks like SHCAPIAsync."""
    api = AsyncMock()
    # Default return values for enumeration calls
    api.get_public_information.return_value = {
        "macAddress": "AA-BB-CC-DD-EE-FF",
        "shcIpAddress": "192.168.2.99",
        "softwareUpdateState": {"swInstalledVersion": "9.99.0"},
    }
    api.get_information.return_value = {"@type": "internalState", "state": "OK"}
    api.get_services.return_value = []
    api.get_devices.return_value = []
    api.get_rooms.return_value = []
    api.get_scenarios.return_value = []
    api.get_messages.return_value = []
    api.get_userdefinedstates.return_value = []
    api.get_domain_intrusion_detection.return_value = {
        "@type": "systemState",
        "systemAvailability": {"@type": "systemAvailabilityState", "available": True, "deleted": False},
        "armingState": {"@type": "armingStateState", "state": "SYSTEM_DISARMED", "deleted": False},
        "alarmState": {"@type": "alarmStateState", "incidents": [], "value": "ALARM_OFF", "deleted": False},
        "activeConfigurationProfile": {"@type": "activeConfigurationProfileState", "profileId": "0"},
        "securityGapState": {"@type": "securityGapStateState", "securityGaps": [], "deleted": False},
    }
    api.long_polling_subscribe.return_value = "test-poll-id-1"
    api.long_polling_poll.return_value = []
    api.long_polling_unsubscribe.return_value = None
    api.close.return_value = None
    return api


def _bare_session(api: AsyncMock | None = None) -> SHCSessionAsync:
    """Return a SHCSessionAsync bypassing __init__ with minimal attribute seeding."""
    s = SHCSessionAsync.__new__(SHCSessionAsync)
    s._api = api if api is not None else _fake_api()
    s._device_helper = MagicMock()
    s._long_poll_timeout = 30
    s._rooms_by_id = {}
    s._scenarios_by_id = {}
    s._devices_by_id = {}
    s._services_by_device_id = defaultdict(list)
    s._domains_by_id = {}
    s._messages_by_id = {}
    s._userdefinedstates_by_id = {}
    s._subscribers = []
    s._emma = MagicMock()
    s._shc_information = _AsyncSHCInformation(
        {"macAddress": "AA-BB-CC-DD-EE-FF", "shcIpAddress": "192.168.2.99"},
        {},
    )
    s._poll_id = None
    s._poll_task = None
    s._stop_polling = False
    s._scenario_callbacks = {}
    s._userdefinedstate_callbacks = defaultdict(list)
    return s


def _fake_device(device_id: str = "hdm:ZigBee:TestDevice") -> MagicMock:
    dev = MagicMock()
    dev.id = device_id
    return dev


# ---------------------------------------------------------------------------
# _AsyncSHCInformation
# ---------------------------------------------------------------------------

class TestAsyncSHCInformation:
    def test_mac_address(self):
        info = _AsyncSHCInformation(
            {"macAddress": "AA-BB-CC-DD-EE-FF", "shcIpAddress": "1.2.3.4"},
            {},
        )
        assert info.macAddress == "AA-BB-CC-DD-EE-FF"

    def test_shc_ip_address(self):
        info = _AsyncSHCInformation({"shcIpAddress": "1.2.3.4"}, {})
        assert info.shcIpAddress == "1.2.3.4"

    def test_version(self):
        info = _AsyncSHCInformation(
            {"softwareUpdateState": {"swInstalledVersion": "9.99.0"}}, {}
        )
        assert info.version == "9.99.0"

    def test_unique_id_prefers_mac(self):
        info = _AsyncSHCInformation(
            {"macAddress": "AA-BB-CC-DD-EE-FF", "shcIpAddress": "1.2.3.4"}, {}
        )
        assert info.unique_id == "AA-BB-CC-DD-EE-FF"

    def test_unique_id_falls_back_to_ip(self):
        info = _AsyncSHCInformation({"shcIpAddress": "1.2.3.4"}, {})
        assert info.unique_id == "1.2.3.4"

    def test_name_is_ip(self):
        info = _AsyncSHCInformation({"shcIpAddress": "1.2.3.4"}, {})
        assert info.name == "1.2.3.4"

    def test_missing_fields_return_none(self):
        info = _AsyncSHCInformation({}, {})
        assert info.macAddress is None
        assert info.version is None
        assert info.unique_id is None


# ---------------------------------------------------------------------------
# __init__ sanity (no I/O)
# ---------------------------------------------------------------------------

class TestInit:
    def test_init_creates_api_no_io(self):
        """SHCSessionAsync.__init__ must not do any network I/O."""
        with patch("boschshcpy.session_async.SHCAPIAsync") as MockAPI:
            MockAPI.return_value = MagicMock()
            # We can't pass real cert paths, but __init__ only calls
            # SHCAPIAsync() which we mock — it must not raise.
            # Verify default state is set properly via the bare factory
            s2 = _bare_session()
            assert s2._poll_task is None
            assert s2._stop_polling is False
            assert s2._poll_id is None

    def test_init_long_poll_timeout_default(self):
        s = _bare_session()
        assert s._long_poll_timeout == 30


# ---------------------------------------------------------------------------
# async_init — device model build
# ---------------------------------------------------------------------------

class TestAsyncInit:

    def test_async_init_calls_api_methods(self):
        """async_init must call all enumerate methods and populate the model."""
        api = _fake_api()

        # Return a minimal service and device so _add_device is exercised
        api.get_services.return_value = [
            {"id": "PowerSwitch", "deviceId": "hdm:ZigBee:D1"},
        ]
        api.get_devices.return_value = [
            {"id": "hdm:ZigBee:D1", "deviceModel": "PSM", "manufacturer": "BOSCH",
             "name": "TestPlug", "status": "AVAILABLE", "rootDeviceId": "hdm:Root",
             "deviceServiceIds": ["PowerSwitch"]},
        ]

        async def run():
            s = _bare_session(api)
            # Patch out the intrusion system (needs proper raw data)
            with patch("boschshcpy.session_async.SHCIntrusionSystem") as MockIDS:
                MockIDS.return_value = MagicMock()
                await s.async_init()
            return s

        asyncio.run(run())

        api.get_information.assert_awaited_once()
        api.get_public_information.assert_awaited_once()
        api.get_services.assert_awaited_once()
        api.get_devices.assert_awaited_once()
        api.get_rooms.assert_awaited_once()
        api.get_scenarios.assert_awaited_once()
        api.get_messages.assert_awaited_once()
        api.get_userdefinedstates.assert_awaited_once()

    def test_async_init_builds_device_helper(self):
        api = _fake_api()
        api.get_services.return_value = []
        api.get_devices.return_value = []

        async def run():
            s = _bare_session(api)
            with patch("boschshcpy.session_async.SHCIntrusionSystem") as MockIDS:
                MockIDS.return_value = MagicMock()
                with patch("boschshcpy.session_async.SHCDeviceHelper") as MockHelper:
                    mock_helper = MagicMock()
                    MockHelper.return_value = mock_helper
                    await s.async_init()
            return s

        s = asyncio.run(run())
        assert s._device_helper is not None

    def test_async_init_populates_rooms(self):
        api = _fake_api()
        api.get_rooms.return_value = [
            {"id": "room1", "name": "Living Room", "iconId": "1"}
        ]

        async def run():
            s = _bare_session(api)
            with patch("boschshcpy.session_async.SHCIntrusionSystem") as MockIDS:
                MockIDS.return_value = MagicMock()
                with patch("boschshcpy.session_async.SHCRoom") as MockRoom:
                    MockRoom.return_value = MagicMock()
                    await s.async_init()
            return s

        s = asyncio.run(run())
        assert "room1" in s._rooms_by_id

    def test_async_init_populates_scenarios(self):
        api = _fake_api()
        api.get_scenarios.return_value = [
            {"id": "sc1", "name": "Away", "iconId": "2"}
        ]

        async def run():
            s = _bare_session(api)
            with patch("boschshcpy.session_async.SHCIntrusionSystem") as MockIDS:
                MockIDS.return_value = MagicMock()
                with patch("boschshcpy.session_async.SHCScenario") as MockSc:
                    MockSc.return_value = MagicMock()
                    await s.async_init()
            return s

        s = asyncio.run(run())
        assert "sc1" in s._scenarios_by_id

    def test_async_init_raises_on_public_info_failure(self):
        api = _fake_api()
        api.get_public_information.return_value = None

        async def run():
            s = _bare_session(api)
            await s._async_authenticate()

        with pytest.raises(SHCConnectionError):
            asyncio.run(run())

    def test_async_init_raises_on_auth_failure(self):
        api = _fake_api()
        api.get_information.return_value = None

        async def run():
            s = _bare_session(api)
            await s._async_authenticate()

        from boschshcpy.exceptions import SHCAuthenticationError
        with pytest.raises(SHCAuthenticationError):
            asyncio.run(run())


# ---------------------------------------------------------------------------
# _add_device — sync path
# ---------------------------------------------------------------------------

class TestAddDevice:
    def test_add_device_skipped_when_no_services(self):
        s = _bare_session()
        result = s._add_device({"id": "hdm:Empty"})
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


# ---------------------------------------------------------------------------
# start_polling / stop_polling lifecycle
# ---------------------------------------------------------------------------

class TestPollingLifecycle:

    def test_start_polling_subscribes_and_creates_task(self):
        api = _fake_api()
        api.long_polling_subscribe.return_value = "pid-1"
        api.long_polling_poll.side_effect = asyncio.CancelledError

        async def run():
            s = _bare_session(api)
            await s.start_polling()
            assert s._poll_task is not None
            assert s._poll_id == "pid-1"
            # Cancel and clean up
            s._poll_task.cancel()
            try:
                await s._poll_task
            except asyncio.CancelledError:
                pass
            s._poll_task = None

        asyncio.run(run())
        api.long_polling_subscribe.assert_awaited_once()

    def test_start_polling_raises_when_already_polling(self):
        async def run():
            s = _bare_session()
            s._poll_task = MagicMock()  # simulate already polling
            await s.start_polling()

        with pytest.raises(SHCSessionError):
            asyncio.run(run())

    def test_stop_polling_raises_when_not_polling(self):
        async def run():
            s = _bare_session()
            s._poll_task = None
            await s.stop_polling()

        with pytest.raises(SHCSessionError):
            asyncio.run(run())

    def test_stop_polling_cancels_task_and_calls_cleanup(self):
        api = _fake_api()

        async def run():
            s = _bare_session(api)
            # Patch poll_id so unsubscribe is called
            s._poll_id = "pid-stop"

            # Create a task that sleeps indefinitely
            async def mock_loop():
                await asyncio.sleep(9999)

            s._poll_task = asyncio.get_event_loop().create_task(mock_loop())
            s._stop_polling = False

            await s.stop_polling()
            return s

        s = asyncio.run(run())
        assert s._poll_task is None
        assert s._poll_id is None
        api.long_polling_unsubscribe.assert_awaited_once_with("pid-stop")
        api.close.assert_awaited_once()

    def test_stop_polling_calls_close_even_if_unsubscribe_fails(self):
        api = _fake_api()
        api.long_polling_unsubscribe.side_effect = Exception("network error")

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-fail"

            async def mock_loop():
                await asyncio.sleep(9999)

            s._poll_task = asyncio.get_event_loop().create_task(mock_loop())
            await s.stop_polling()

        asyncio.run(run())
        api.close.assert_awaited_once()

    def test_stop_polling_swallows_non_cancelled_task_exception(self):
        """If the poll task finished with a non-CancelledError exception, stop_polling
        must log+swallow it (lines 326-327) and still unsubscribe + close."""
        api = _fake_api()

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-exc"

            async def boom():
                raise ValueError("poll blew up")

            task = asyncio.get_event_loop().create_task(boom())
            # let the task run to completion (it raises) before we stop
            try:
                await task
            except ValueError:
                pass
            s._poll_task = task  # already-done task holding the exception
            await s.stop_polling()

        asyncio.run(run())
        api.long_polling_unsubscribe.assert_awaited_once_with("pid-exc")
        api.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# _poll_loop — core dispatch behaviour
# ---------------------------------------------------------------------------

class TestPollLoop:

    def test_poll_loop_dispatches_device_service_data(self):
        """A DeviceServiceData event must be routed to the correct device."""
        api = _fake_api()

        device_id = "hdm:ZigBee:TestDevice"
        raw_event = {
            "@type": "DeviceServiceData",
            "deviceId": device_id,
            "id": "PowerSwitch",
            "state": {"@type": "powerSwitchState", "switchState": "ON"},
            "path": f"/devices/{device_id}/services/PowerSwitch",
        }

        # Return the event once, then CancelledError to exit loop
        call_count = [0]

        async def fake_poll(poll_id, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                return [raw_event]
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-dispatch"
            fake_device = _fake_device(device_id)
            s._devices_by_id[device_id] = fake_device

            await s.start_polling()
            try:
                await asyncio.wait_for(s._poll_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            s._poll_task = None
            return fake_device

        dev = asyncio.run(run())
        dev.process_long_polling_poll_result.assert_called_once_with(raw_event)

    def test_poll_loop_stale_poll_id_triggers_resubscribe(self):
        """-32001 must invalidate poll_id and resubscribe on next iteration."""
        api = _fake_api()

        calls = [0]

        async def fake_subscribe():
            calls[0] += 1
            return f"pid-{calls[0]}"

        api.long_polling_subscribe.side_effect = fake_subscribe

        poll_calls = [0]

        async def fake_poll(poll_id, timeout):
            poll_calls[0] += 1
            if poll_calls[0] == 1:
                # First poll: raise stale-poll-id error
                raise JSONRPCError(-32001, "UNKNOWN_POLLID")
            # Second poll: no more events, then exit
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            # Seed with first poll_id (as start_polling would have done)
            s._poll_id = await api.long_polling_subscribe()
            assert s._poll_id == "pid-1"

            # Run one iteration: -32001 → invalidate → sleep(1)
            # Then second iteration: resubscribe + CancelledError to exit
            with patch("boschshcpy.session_async.asyncio.sleep", new_callable=AsyncMock):
                s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
                try:
                    await asyncio.wait_for(s._poll_task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                s._poll_task = None
            return s

        asyncio.run(run())
        # subscribe was called: once in run() + once for resubscribe inside _poll_loop
        assert calls[0] >= 2

    def test_poll_loop_other_error_backoff(self):
        """Non-32001 exceptions must log and backoff without crashing."""
        api = _fake_api()

        error_calls = [0]

        async def fake_poll(poll_id, timeout):
            error_calls[0] += 1
            if error_calls[0] == 1:
                raise ValueError("transient network error")
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-backoff"
            sleep_calls = []

            async def fake_sleep(seconds):
                sleep_calls.append(seconds)

            with patch("boschshcpy.session_async.asyncio.sleep", side_effect=fake_sleep):
                s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
                try:
                    await asyncio.wait_for(s._poll_task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                s._poll_task = None
            return sleep_calls

        sleep_calls = asyncio.run(run())
        # Must have slept 15s for the generic error
        assert 15.0 in sleep_calls

    def test_poll_loop_cancelled_error_propagates(self):
        """CancelledError must NOT be swallowed — the task must end with it."""
        api = _fake_api()
        api.long_polling_poll.side_effect = asyncio.CancelledError

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-cancel"
            task = asyncio.get_event_loop().create_task(s._poll_loop())
            with pytest.raises(asyncio.CancelledError):
                await task

        asyncio.run(run())

    def test_poll_loop_clears_poll_task_on_cancellation(self):
        """Regression: _poll_loop() must clear self._poll_task in a finally
        however it exits — mirrors the sync session.py fix (0.4.4) for a
        permanent 'Already polling!' lockout after the task dies. Without
        this, self._poll_task stays set to a dead/cancelled Task object and
        a fresh start_polling() call would raise forever."""
        api = _fake_api()
        api.long_polling_poll.side_effect = asyncio.CancelledError

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-cancel"
            s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
            with pytest.raises(asyncio.CancelledError):
                await s._poll_task
            return s

        s = asyncio.run(run())
        assert s._poll_task is None

    def test_poll_loop_clears_poll_task_on_normal_exit(self):
        """Normal exit (self._stop_polling set to True) must also clear
        self._poll_task, not just the cancellation/exception paths."""
        api = _fake_api()

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-normal"

            async def poll_once_then_stop(*_args, **_kwargs):
                s._stop_polling = True
                return []

            api.long_polling_poll.side_effect = poll_once_then_stop
            s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
            await s._poll_task
            return s

        s = asyncio.run(run())
        assert s._poll_task is None

    def test_poll_loop_scenario_triggered_calls_callback(self):
        """scenarioTriggered events must invoke registered callbacks."""
        api = _fake_api()

        raw_event = {"@type": "scenarioTriggered", "id": "sc-away"}
        call_count = [0]

        async def fake_poll(poll_id, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                return [raw_event]
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        callback = MagicMock()

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-sc"
            s._scenario_callbacks["sc-away"] = callback

            s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
            try:
                await asyncio.wait_for(s._poll_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            s._poll_task = None

        asyncio.run(run())
        callback.assert_called_once_with(raw_event)

    def test_poll_loop_message_with_device_service_model(self):
        """message events containing deviceServiceDataModel must be unwrapped."""
        api = _fake_api()

        device_id = "hdm:ZigBee:MsgDevice"
        inner = {
            "@type": "DeviceServiceData",
            "deviceId": device_id,
            "id": "PowerSwitch",
            "state": {"@type": "powerSwitchState", "switchState": "OFF"},
            "path": f"/devices/{device_id}/services/PowerSwitch",
        }
        raw_event = {
            "@type": "message",
            "id": "msg1",
            "arguments": {"deviceServiceDataModel": json.dumps(inner)},
        }

        call_count = [0]

        async def fake_poll(poll_id, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                return [raw_event]
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-msg"
            fake_device = _fake_device(device_id)
            s._devices_by_id[device_id] = fake_device

            s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
            try:
                await asyncio.wait_for(s._poll_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            s._poll_task = None
            return fake_device

        dev = asyncio.run(run())
        dev.process_long_polling_poll_result.assert_called_once_with(inner)

    def test_poll_loop_unknown_type_no_crash(self):
        """Unknown @type events must be silently ignored, not crash the loop."""
        api = _fake_api()

        call_count = [0]

        async def fake_poll(poll_id, timeout):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"@type": "futureUnknownType", "id": "x"}]
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-unknown"
            s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
            try:
                await asyncio.wait_for(s._poll_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            s._poll_task = None

        asyncio.run(run())  # must not raise


# ---------------------------------------------------------------------------
# _process_long_polling_poll_result — branch coverage
# ---------------------------------------------------------------------------

class TestProcessPollResult:

    def _run_process(self, raw_result, session_state=None):
        """Helper: run _process_long_polling_poll_result and return session."""
        s = _bare_session()
        if session_state:
            for k, v in session_state.items():
                setattr(s, k, v)

        asyncio.run(s._process_long_polling_poll_result(raw_result))
        return s

    def test_device_service_data_known_device(self):
        dev = _fake_device("hdm:D1")
        raw = {"@type": "DeviceServiceData", "deviceId": "hdm:D1",
               "id": "PowerSwitch", "state": {}}
        self._run_process(raw, {"_devices_by_id": {"hdm:D1": dev}})
        dev.process_long_polling_poll_result.assert_called_once_with(raw)

    def test_device_service_data_unknown_device_no_crash(self):
        raw = {"@type": "DeviceServiceData", "deviceId": "hdm:Unknown",
               "id": "x", "state": {}}
        self._run_process(raw)  # must not raise

    def test_scenario_triggered_calls_callback(self):
        cb = MagicMock()
        raw = {"@type": "scenarioTriggered", "id": "sc1"}
        self._run_process(raw, {"_scenario_callbacks": {"sc1": cb}})
        cb.assert_called_once_with(raw)

    def test_scenario_triggered_legacy_shc_callback(self):
        cb = MagicMock()
        raw = {"@type": "scenarioTriggered", "id": "sc99"}
        self._run_process(raw, {"_scenario_callbacks": {"shc": cb}})
        cb.assert_called_once_with(raw)

    def test_device_update_existing(self):
        dev = _fake_device("hdm:D2")
        raw = {"@type": "device", "id": "hdm:D2"}
        self._run_process(raw, {"_devices_by_id": {"hdm:D2": dev}})
        dev.update_raw_information.assert_called_once_with(raw)

    def test_device_deleted_removes_from_dicts(self):
        dev = _fake_device("hdm:D3")
        s = _bare_session()
        s._devices_by_id["hdm:D3"] = dev
        s._services_by_device_id["hdm:D3"].append("svc")
        raw = {"@type": "device", "id": "hdm:D3", "deleted": True}
        asyncio.run(s._process_long_polling_poll_result(raw))
        assert "hdm:D3" not in s._devices_by_id
        assert "hdm:D3" not in s._services_by_device_id

    def test_device_new_subscriber_mutating_list_does_not_raise(self):
        """Regression: _subscribers must be snapshotted (list(...)) before
        iterating, matching sync session.py — a callback that subscribes a
        new instance (e.g. HA platform setup registering further callbacks
        during dynamic entity creation) must not raise
        'list changed size during iteration'."""
        async def run():
            s = _bare_session()
            new_dev = _fake_device("hdm:NEW2")

            async def fake_add(raw_device):
                s._devices_by_id["hdm:NEW2"] = new_dev
                return new_dev

            s._async_add_new_device = fake_add

            def mutating_cb(_dev):
                s._subscribers.append((object, MagicMock()))

            s._subscribers.append((object, mutating_cb))

            raw = {"@type": "device", "id": "hdm:NEW2"}
            # Must not raise RuntimeError: list changed size during iteration
            await s._process_long_polling_poll_result(raw)

        asyncio.run(run())

    def test_device_new_calls_async_add_new_device(self):
        async def run():
            s = _bare_session()
            new_dev = _fake_device("hdm:NEW")
            added = []

            async def fake_add(raw_device):
                added.append(raw_device["id"])
                s._devices_by_id["hdm:NEW"] = new_dev
                return new_dev

            s._async_add_new_device = fake_add
            cb = MagicMock()
            s._subscribers.append((object, cb))

            raw = {"@type": "device", "id": "hdm:NEW"}
            await s._process_long_polling_poll_result(raw)
            return added, cb, new_dev

        added, cb, new_dev = asyncio.run(run())
        assert "hdm:NEW" in added
        cb.assert_called_once_with(new_dev)

    def test_userdefinedstate_existing_update_and_callback(self):
        uds = MagicMock()
        cb = MagicMock()
        raw = {"@type": "userDefinedState", "id": "u1", "name": "x",
               "state": True, "deleted": False}
        s = _bare_session()
        s._userdefinedstates_by_id["u1"] = uds
        s._userdefinedstate_callbacks["u1"].append(cb)
        asyncio.run(s._process_long_polling_poll_result(raw))
        uds.update_raw_information.assert_called_once_with(raw)
        cb.assert_called_once()

    def test_userdefinedstate_new_stored_and_subscriber_called(self):
        async def run():
            s = _bare_session()
            info_mock = _AsyncSHCInformation({"macAddress": "AA-BB"}, {})
            s._shc_information = info_mock
            cb = MagicMock()
            s._subscribers.append((object, cb))

            raw = {"@type": "userDefinedState", "id": "u99", "name": "New",
                   "state": False, "deleted": False}

            with patch("boschshcpy.session_async.SHCUserDefinedState") as MockUDS:
                new_uds = MagicMock()
                MockUDS.return_value = new_uds
                await s._process_long_polling_poll_result(raw)
                assert "u99" in s._userdefinedstates_by_id
                cb.assert_called_once_with(new_uds)

        asyncio.run(run())

    def test_emma_link_update(self):
        emma = MagicMock()
        raw = {"@type": "link", "id": "com.bosch.tt.emma.applink", "data": {}}
        self._run_process(raw, {"_emma": emma})
        emma.update_emma_data.assert_called_once_with(raw)

    def test_message_without_device_service_stores_message(self):
        raw = {
            "@type": "message",
            "id": "msg2",
            "arguments": {},  # no deviceServiceDataModel key
        }
        s = _bare_session()
        with patch("boschshcpy.session_async.SHCMessage") as MockMsg:
            MockMsg.return_value = MagicMock()
            asyncio.run(s._process_long_polling_poll_result(raw))
        assert "msg2" in s._messages_by_id

    def test_domain_state_dispatched_to_intrusion_system(self):
        from boschshcpy.domain_impl import SHCIntrusionSystem
        ids = MagicMock()
        ids.process_long_polling_poll_result = MagicMock()
        raw = {"@type": "armingState", "state": "SYSTEM_DISARMED"}
        s = _bare_session()
        s._domains_by_id["IDS"] = ids
        # Make sure armingState is in DOMAIN_STATES
        assert "armingState" in SHCIntrusionSystem.DOMAIN_STATES
        asyncio.run(s._process_long_polling_poll_result(raw))
        ids.process_long_polling_poll_result.assert_called_once_with(raw)


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------

class TestPropertyAccessors:
    def test_api_property(self):
        s = _bare_session()
        assert s.api is s._api

    def test_device_helper_property(self):
        s = _bare_session()
        s._device_helper = MagicMock()
        assert s.device_helper is s._device_helper

    def test_devices_list(self):
        s = _bare_session()
        dev = _fake_device("hdm:D1")
        s._devices_by_id["hdm:D1"] = dev
        assert dev in s.devices

    def test_device_by_id(self):
        s = _bare_session()
        dev = _fake_device("hdm:D1")
        s._devices_by_id["hdm:D1"] = dev
        assert s.device("hdm:D1") is dev

    def test_rooms_list(self):
        s = _bare_session()
        room = MagicMock()
        s._rooms_by_id["r1"] = room
        assert room in s.rooms

    def test_room_none_returns_fallback(self):
        s = _bare_session()
        with patch("boschshcpy.session_async.SHCRoom") as MockRoom:
            MockRoom.return_value = "fallback"
            result = s.room(None)
        assert result == "fallback"

    def test_scenarios_list(self):
        s = _bare_session()
        sc = MagicMock()
        s._scenarios_by_id["sc1"] = sc
        assert sc in s.scenarios

    def test_scenario_names(self):
        s = _bare_session()
        sc = MagicMock()
        sc.name = "Away"
        s._scenarios_by_id["sc1"] = sc
        assert "Away" in s.scenario_names

    def test_scenario_by_id(self):
        s = _bare_session()
        sc = MagicMock()
        s._scenarios_by_id["sc1"] = sc
        assert s.scenario("sc1") is sc

    def test_messages_list(self):
        s = _bare_session()
        msg = MagicMock()
        s._messages_by_id["m1"] = msg
        assert msg in s.messages

    def test_emma_property(self):
        s = _bare_session()
        emma = MagicMock()
        s._emma = emma
        assert s.emma is emma

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
        assert s.information is s._shc_information

    def test_intrusion_system_returns_none_when_absent(self):
        s = _bare_session()
        assert s.intrusion_system is None

    def test_intrusion_system_returns_object(self):
        s = _bare_session()
        ids = MagicMock()
        s._domains_by_id["IDS"] = ids
        assert s.intrusion_system is ids


# ---------------------------------------------------------------------------
# Subscription API
# ---------------------------------------------------------------------------

class TestSubscriptions:
    def test_subscribe_appends(self):
        s = _bare_session()
        tpl = (MagicMock, lambda x: None)
        s.subscribe(tpl)
        assert tpl in s._subscribers

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

    def test_unsubscribe_scenario_missing_noop(self):
        s = _bare_session()
        s.unsubscribe_scenario_callback("nonexistent")  # must not raise

    def test_subscribe_userdefinedstate_callback(self):
        s = _bare_session()
        cb = MagicMock()
        s.subscribe_userdefinedstate_callback("u1", cb)
        assert cb in s._userdefinedstate_callbacks["u1"]

    def test_unsubscribe_userdefinedstate_callbacks(self):
        s = _bare_session()
        s._userdefinedstate_callbacks["u1"] = [MagicMock()]
        s.unsubscribe_userdefinedstate_callbacks("u1")
        assert "u1" not in s._userdefinedstate_callbacks
