"""Additional unit tests for boschshcpy/session_async.py to raise coverage to ≥95%.

Targets the following previously-uncovered lines:
  100-138  SHCSessionAsync.__init__ (real constructor path)
  184      _async_enumerate_services continue branch (unsupported service id)
  226-234  _async_add_new_device (full method)
  256-258  _async_enumerate_messages loop body
  264-268  _async_enumerate_userdefinedstates loop body
  326-327  stop_polling except Exception branch (task raises non-CancelledError)
  388-400  _poll_loop resubscribe short-poll refresh path
  426-433  _poll_loop JSONRPCError non-(-32001) path
  592      room() with non-None room_id
  672-676  _AsyncSHCInformation.summary()

Strategy: asyncio.run() inside plain sync test functions — no pytest-asyncio.

Run:
    PYTHONPATH=/tmp/lib-async PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \\
        python3 -m pytest tests/test_session_async_more.py -q -o addopts=""
"""

import asyncio
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boschshcpy.api_async import JSONRPCError
from boschshcpy.session_async import SHCSessionAsync, _AsyncSHCInformation


# ---------------------------------------------------------------------------
# Helpers (mirror what test_session_async.py uses, kept self-contained)
# ---------------------------------------------------------------------------

def _fake_api() -> AsyncMock:
    api = AsyncMock()
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
        "systemAvailability": {
            "@type": "systemAvailabilityState",
            "available": True,
            "deleted": False,
        },
        "armingState": {
            "@type": "armingStateState",
            "state": "SYSTEM_DISARMED",
            "deleted": False,
        },
        "alarmState": {
            "@type": "alarmStateState",
            "incidents": [],
            "value": "ALARM_OFF",
            "deleted": False,
        },
        "activeConfigurationProfile": {
            "@type": "activeConfigurationProfileState",
            "profileId": "0",
        },
        "securityGapState": {
            "@type": "securityGapStateState",
            "securityGaps": [],
            "deleted": False,
        },
    }
    api.long_polling_subscribe.return_value = "test-poll-id-1"
    api.long_polling_poll.return_value = []
    api.long_polling_unsubscribe.return_value = None
    api.close.return_value = None
    return api


def _bare_session(api: AsyncMock | None = None) -> SHCSessionAsync:
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
    dev.async_update = AsyncMock()
    return dev


# ---------------------------------------------------------------------------
# Lines 100-138: SHCSessionAsync.__init__ (real constructor)
# ---------------------------------------------------------------------------

class TestRealInit:
    """Tests that exercise the real __init__ path (lines 100-138)."""

    def test_real_init_sets_default_long_poll_timeout(self):
        with patch("boschshcpy.session_async.SHCAPIAsync") as MockAPI:
            MockAPI.return_value = MagicMock()
            s = SHCSessionAsync("1.2.3.4", "/cert.pem", "/key.pem")
        assert s._long_poll_timeout == 30

    def test_real_init_passes_long_poll_timeout(self):
        with patch("boschshcpy.session_async.SHCAPIAsync") as MockAPI:
            MockAPI.return_value = MagicMock()
            s = SHCSessionAsync("1.2.3.4", "/cert.pem", "/key.pem", long_poll_timeout=60)
        assert s._long_poll_timeout == 60

    def test_real_init_creates_api(self):
        with patch("boschshcpy.session_async.SHCAPIAsync") as MockAPI:
            mock_api_instance = MagicMock()
            MockAPI.return_value = mock_api_instance
            s = SHCSessionAsync("1.2.3.4", "/cert.pem", "/key.pem")
        assert s._api is mock_api_instance
        MockAPI.assert_called_once_with(
            controller_ip="1.2.3.4",
            certificate="/cert.pem",
            key="/key.pem",
            external_session=None,
            ssl_context=None,
        )

    def test_real_init_passes_external_session(self):
        fake_session = MagicMock()
        with patch("boschshcpy.session_async.SHCAPIAsync") as MockAPI:
            MockAPI.return_value = MagicMock()
            SHCSessionAsync(
                "1.2.3.4", "/cert.pem", "/key.pem", external_session=fake_session
            )
        MockAPI.assert_called_once_with(
            controller_ip="1.2.3.4",
            certificate="/cert.pem",
            key="/key.pem",
            external_session=fake_session,
            ssl_context=None,
        )

    def test_real_init_device_helper_is_none(self):
        with patch("boschshcpy.session_async.SHCAPIAsync") as MockAPI:
            MockAPI.return_value = MagicMock()
            s = SHCSessionAsync("1.2.3.4", "/cert.pem", "/key.pem")
        assert s._device_helper is None

    def test_real_init_state_is_clean(self):
        with patch("boschshcpy.session_async.SHCAPIAsync") as MockAPI:
            MockAPI.return_value = MagicMock()
            s = SHCSessionAsync("1.2.3.4", "/cert.pem", "/key.pem")
        assert s._poll_id is None
        assert s._poll_task is None
        assert s._stop_polling is False
        assert s._shc_information is None
        assert s._emma is None
        assert s._devices_by_id == {}
        assert s._rooms_by_id == {}
        assert s._scenarios_by_id == {}
        assert s._messages_by_id == {}
        assert s._userdefinedstates_by_id == {}
        assert s._subscribers == []
        assert s._scenario_callbacks == {}


# ---------------------------------------------------------------------------
# Line 184: _async_enumerate_services — unsupported service id is skipped
# ---------------------------------------------------------------------------

class TestEnumerateServices:
    def test_enumerate_services_skips_unsupported_ids(self):
        """Services with IDs not in SUPPORTED_DEVICE_SERVICE_IDS must be skipped."""
        api = _fake_api()
        api.get_services.return_value = [
            {"id": "UNSUPPORTED_XYZ_SERVICE", "deviceId": "hdm:D1"},
        ]

        async def run():
            s = _bare_session(api)
            await s._async_enumerate_services()
            return s

        s = asyncio.run(run())
        # The unsupported service must NOT have been added to any device
        assert len(s._services_by_device_id) == 0

    def test_enumerate_services_keeps_supported_ids(self):
        """Services with supported IDs must be kept."""
        from boschshcpy.services_impl import SUPPORTED_DEVICE_SERVICE_IDS
        supported_id = next(iter(SUPPORTED_DEVICE_SERVICE_IDS))
        api = _fake_api()
        api.get_services.return_value = [
            {"id": supported_id, "deviceId": "hdm:D1"},
            {"id": "UNSUPPORTED_GARBAGE", "deviceId": "hdm:D1"},
        ]

        async def run():
            s = _bare_session(api)
            await s._async_enumerate_services()
            return s

        s = asyncio.run(run())
        # Only the supported one must be kept
        assert len(s._services_by_device_id["hdm:D1"]) == 1
        assert s._services_by_device_id["hdm:D1"][0]["id"] == supported_id


# ---------------------------------------------------------------------------
# Lines 226-234: _async_add_new_device
# ---------------------------------------------------------------------------

class TestAsyncAddNewDevice:
    def test_async_add_new_device_fetches_services(self):
        """_async_add_new_device must call get_device_services and populate."""
        from boschshcpy.services_impl import SUPPORTED_DEVICE_SERVICE_IDS
        supported_id = next(iter(SUPPORTED_DEVICE_SERVICE_IDS))

        api = _fake_api()
        api.get_device_services.return_value = [
            {"id": supported_id, "deviceId": "hdm:NEW"},
            {"id": "UNSUPPORTED", "deviceId": "hdm:NEW"},
        ]

        fake_dev = _fake_device("hdm:NEW")

        async def run():
            s = _bare_session(api)
            s._device_helper.device_init.return_value = fake_dev
            result = await s._async_add_new_device({"id": "hdm:NEW"})
            return s, result

        s, result = asyncio.run(run())
        api.get_device_services.assert_awaited_once_with("hdm:NEW")
        # Only the supported service must be in services_by_device_id
        assert len(s._services_by_device_id["hdm:NEW"]) == 1
        assert s._services_by_device_id["hdm:NEW"][0]["id"] == supported_id
        assert result is fake_dev

    def test_async_add_new_device_clears_stale_services(self):
        """_async_add_new_device must discard any cached services for the device first."""
        api = _fake_api()
        api.get_device_services.return_value = []

        async def run():
            s = _bare_session(api)
            # Seed stale services
            s._services_by_device_id["hdm:STALE"].append({"id": "OldSvc"})
            result = await s._async_add_new_device({"id": "hdm:STALE"})
            return s, result

        s, result = asyncio.run(run())
        # Should have been cleared (no supported services returned)
        assert len(s._services_by_device_id["hdm:STALE"]) == 0
        # _add_device returns None when no services
        assert result is None

    def test_async_add_new_device_no_supported_services_returns_none(self):
        """When get_device_services returns only unsupported IDs, _add_device returns None."""
        api = _fake_api()
        api.get_device_services.return_value = [
            {"id": "TOTALLY_UNSUPPORTED", "deviceId": "hdm:X"},
        ]

        async def run():
            s = _bare_session(api)
            return await s._async_add_new_device({"id": "hdm:X"})

        result = asyncio.run(run())
        assert result is None


# ---------------------------------------------------------------------------
# Lines 256-258: _async_enumerate_messages loop body
# ---------------------------------------------------------------------------

class TestEnumerateMessages:
    def test_enumerate_messages_populates_dict(self):
        api = _fake_api()
        api.get_messages.return_value = [
            {"id": "msg-001", "@type": "message", "sourceType": "DEVICE"},
            {"id": "msg-002", "@type": "message", "sourceType": "DEVICE"},
        ]

        async def run():
            s = _bare_session(api)
            with patch("boschshcpy.session_async.SHCMessage") as MockMsg:
                MockMsg.side_effect = lambda api, raw_message: MagicMock(id=raw_message["id"])
                await s._async_enumerate_messages()
                return s

        s = asyncio.run(run())
        assert "msg-001" in s._messages_by_id
        assert "msg-002" in s._messages_by_id


# ---------------------------------------------------------------------------
# Lines 264-268: _async_enumerate_userdefinedstates loop body
# ---------------------------------------------------------------------------

class TestEnumerateUserDefinedStates:
    def test_enumerate_userdefinedstates_populates_dict(self):
        api = _fake_api()
        api.get_userdefinedstates.return_value = [
            {"id": "uds-1", "name": "Vacation", "state": False, "deleted": False},
            {"id": "uds-2", "name": "Night", "state": True, "deleted": False},
        ]

        async def run():
            s = _bare_session(api)
            with patch("boschshcpy.session_async.SHCUserDefinedState") as MockUDS:
                def make_uds(api, info, raw_state):
                    m = MagicMock()
                    m.id = raw_state["id"]
                    return m
                MockUDS.side_effect = make_uds
                await s._async_enumerate_userdefinedstates()
                return s

        s = asyncio.run(run())
        assert "uds-1" in s._userdefinedstates_by_id
        assert "uds-2" in s._userdefinedstates_by_id


# ---------------------------------------------------------------------------
# Lines 326-327: stop_polling except Exception branch
# ---------------------------------------------------------------------------

class TestStopPollingExceptionBranch:
    def test_stop_polling_handles_non_cancelled_task_exception(self):
        """If the poll task raises a non-CancelledError, stop_polling must log and continue."""
        api = _fake_api()

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-exc"
            s._stop_polling = False

            # Create a task that raises a plain Exception (not CancelledError)
            # when cancelled, to exercise the except Exception branch in stop_polling.
            async def mock_loop_raises():
                try:
                    await asyncio.sleep(9999)
                except asyncio.CancelledError:
                    raise RuntimeError("Task raised RuntimeError instead of re-raising")

            s._poll_task = asyncio.get_event_loop().create_task(mock_loop_raises())
            # stop_polling should handle this gracefully (log and continue)
            await s.stop_polling()
            return s

        s = asyncio.run(run())
        assert s._poll_task is None
        api.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# Lines 388-400: _poll_loop resubscribe short-poll refresh path
# ---------------------------------------------------------------------------

class TestPollLoopResubscribeRefresh:
    def test_poll_loop_resubscribe_refreshes_devices(self):
        """After resubscribe, _poll_loop must async-short-poll all devices."""
        api = _fake_api()

        # First call: poll_id is None → resubscribe, then poll returns empty
        # Second call: CancelledError to exit
        subscribe_calls = [0]

        async def fake_subscribe():
            subscribe_calls[0] += 1
            return f"pid-resub-{subscribe_calls[0]}"

        api.long_polling_subscribe.side_effect = fake_subscribe

        poll_calls = [0]

        async def fake_poll(poll_id, timeout):
            poll_calls[0] += 1
            if poll_calls[0] == 1:
                return []  # empty — triggers the resubscribe refresh path
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            # poll_id is None → triggers resubscribe on the first iteration
            s._poll_id = None

            # Add two fake devices whose async_update() we can track
            dev1 = _fake_device("hdm:D1")
            dev2 = _fake_device("hdm:D2")
            s._devices_by_id["hdm:D1"] = dev1
            s._devices_by_id["hdm:D2"] = dev2

            with patch("boschshcpy.session_async.asyncio.sleep", new_callable=AsyncMock):
                s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
                try:
                    await asyncio.wait_for(s._poll_task, timeout=3.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                s._poll_task = None

            return dev1, dev2

        dev1, dev2 = asyncio.run(run())
        # Both devices must have been async-updated with fire_callbacks=True
        dev1.async_update.assert_called_once_with(fire_callbacks=True)
        dev2.async_update.assert_called_once_with(fire_callbacks=True)

    def test_poll_loop_resubscribe_refresh_device_update_error_is_logged(self):
        """A failing device.update() during refresh must be caught, not crash the loop."""
        api = _fake_api()

        subscribe_calls = [0]

        async def fake_subscribe():
            subscribe_calls[0] += 1
            return f"pid-err-{subscribe_calls[0]}"

        api.long_polling_subscribe.side_effect = fake_subscribe

        poll_calls = [0]

        async def fake_poll(poll_id, timeout):
            poll_calls[0] += 1
            if poll_calls[0] == 1:
                return []
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            s._poll_id = None
            dev = _fake_device("hdm:Err")
            s._devices_by_id["hdm:Err"] = dev

            # async_update() raises an exception
            dev.async_update.side_effect = ConnectionError("SHC unreachable")

            with patch("boschshcpy.session_async.asyncio.sleep", new_callable=AsyncMock):
                s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
                try:
                    await asyncio.wait_for(s._poll_task, timeout=3.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                s._poll_task = None

        # Must not raise — exception in device.update() is caught and logged
        asyncio.run(run())


# ---------------------------------------------------------------------------
# Lines 426-433: _poll_loop JSONRPCError non-(-32001) path
# ---------------------------------------------------------------------------

class TestPollLoopJSONRPCNon32001:
    def test_poll_loop_non_32001_jsonrpc_error_backs_off(self):
        """A JSONRPCError with code != -32001 must log + sleep _BACKOFF_OTHER_ERROR."""
        api = _fake_api()

        error_calls = [0]

        async def fake_poll(poll_id, timeout):
            error_calls[0] += 1
            if error_calls[0] == 1:
                raise JSONRPCError(-32600, "Invalid Request")
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        sleep_calls = []

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-jsonrpc"

            async def fake_sleep(seconds):
                sleep_calls.append(seconds)

            with patch("boschshcpy.session_async.asyncio.sleep", side_effect=fake_sleep):
                s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
                try:
                    await asyncio.wait_for(s._poll_task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                s._poll_task = None

        asyncio.run(run())
        # Must have slept with _BACKOFF_OTHER_ERROR (15.0)
        from boschshcpy.session_async import _BACKOFF_OTHER_ERROR
        assert _BACKOFF_OTHER_ERROR in sleep_calls

    def test_poll_loop_non_32001_does_not_invalidate_poll_id(self):
        """A non-(-32001) JSONRPCError must NOT invalidate poll_id."""
        api = _fake_api()

        error_calls = [0]

        async def fake_poll(poll_id, timeout):
            error_calls[0] += 1
            if error_calls[0] == 1:
                raise JSONRPCError(-32700, "Parse error")
            raise asyncio.CancelledError

        api.long_polling_poll.side_effect = fake_poll

        async def run():
            s = _bare_session(api)
            s._poll_id = "pid-stays-valid"

            with patch("boschshcpy.session_async.asyncio.sleep", new_callable=AsyncMock):
                s._poll_task = asyncio.get_event_loop().create_task(s._poll_loop())
                try:
                    await asyncio.wait_for(s._poll_task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                s._poll_task = None
            return s

        s = asyncio.run(run())
        # poll_id must NOT have been set to None (only -32001 does that)
        assert s._poll_id == "pid-stays-valid"


# ---------------------------------------------------------------------------
# Line 592: room() with a non-None room_id
# ---------------------------------------------------------------------------

class TestRoomAccessor:
    def test_room_by_id_returns_correct_room(self):
        s = _bare_session()
        room = MagicMock()
        s._rooms_by_id["r42"] = room
        assert s.room("r42") is room

    def test_room_by_id_raises_for_missing_room(self):
        s = _bare_session()
        with pytest.raises(KeyError):
            s.room("does-not-exist")

    def test_room_none_returns_fallback(self):
        s = _bare_session()
        with patch("boschshcpy.session_async.SHCRoom") as MockRoom:
            MockRoom.return_value = "fallback"
            result = s.room(None)
        assert result == "fallback"


# ---------------------------------------------------------------------------
# Lines 672-676: _AsyncSHCInformation.summary()
# ---------------------------------------------------------------------------

class TestAsyncSHCInformationSummary:
    def test_summary_prints_fields(self, capsys):
        info = _AsyncSHCInformation(
            {
                "macAddress": "AA-BB-CC-DD-EE-FF",
                "shcIpAddress": "192.168.2.99",
                "softwareUpdateState": {"swInstalledVersion": "9.99.0"},
            },
            {},
        )
        info.summary()
        captured = capsys.readouterr()
        assert "AsyncSHCInformation" in captured.out
        assert "192.168.2.99" in captured.out
        assert "AA-BB-CC-DD-EE-FF" in captured.out
        assert "9.99.0" in captured.out

    def test_summary_handles_missing_fields(self, capsys):
        info = _AsyncSHCInformation({}, {})
        info.summary()  # must not raise
        captured = capsys.readouterr()
        assert "AsyncSHCInformation" in captured.out
        assert "None" in captured.out
