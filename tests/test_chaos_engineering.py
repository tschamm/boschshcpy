"""Chaos-engineering tests for boschshcpy.

Fault-injection tests targeting the library's real failure surfaces: the
long-poll thread's exception handling, malformed/adversarial server
responses, concurrent mutation of the devices dict, and the async
client's connection-drop retry path. Nothing here touches a live SHC —
the SHC API layer is mocked/faked throughout.

Randomized cases use a fixed seed so failures are reproducible, not flaky.
"""

import json
import random
import threading
import time
from collections import defaultdict
from unittest.mock import MagicMock, patch

import pytest

from boschshcpy.api import JSONRPCError
from boschshcpy.exceptions import SHCConnectionError
from boschshcpy.session import SHCSession

CHAOS_SEED = 20260713


def _bare_session() -> SHCSession:
    """Same isolation strategy as test_session_unit.py: bypass __init__."""
    s = SHCSession.__new__(SHCSession)
    s._api = MagicMock()
    s._device_helper = MagicMock()
    s._poll_id = None
    s._shc_information = None
    s._zeroconf = None
    s._long_poll_timeout = 10
    s._rooms_by_id = {}
    s._scenarios_by_id = {}
    s._devices_by_id = {}
    s._services_by_device_id = defaultdict(list)
    s._devices_lock = threading.RLock()
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


def _capture_polling_closure(s: SHCSession):
    """Capture the real polling_thread_main closure without starting a thread."""
    with patch("boschshcpy.session.threading.Thread") as MockThread:
        mock_thread = MagicMock()
        MockThread.return_value = mock_thread
        s.start_polling()
    return MockThread.call_args.kwargs["target"]


# ---------------------------------------------------------------------------
# 1. Polling-loop exception chaos: fire a random mix of every failure mode
#    the loop is documented to handle, and confirm none of it ever escapes
#    the thread or corrupts the stop/poll-id bookkeeping.
# ---------------------------------------------------------------------------


class TestPollingLoopExceptionChaos:
    def _make_random_fault(self, rng: random.Random):
        """Return a zero-arg callable that raises one randomly-chosen fault."""
        choice = rng.choice(
            [
                "runtime_error",
                "rpc_unknown_poll_id",
                "rpc_other_code",
                "connection_error",
                "generic_exception",
                "false_return",
                "success",
            ]
        )

        def fault():
            if choice == "runtime_error":
                raise RuntimeError("simulated fatal shutdown condition")
            if choice == "rpc_unknown_poll_id":
                raise JSONRPCError(-32001, "unknown poll id")
            if choice == "rpc_other_code":
                raise JSONRPCError(rng.choice([-32000, -32700, 500]), "chaos rpc error")
            if choice == "connection_error":
                raise SHCConnectionError("simulated transport drop")
            if choice == "generic_exception":
                raise ValueError("simulated unexpected library bug")
            if choice == "false_return":
                return False
            return True

        return fault, choice

    def test_survives_randomized_fault_sequence(self):
        """Feed N random faults through the real loop body; it must never
        propagate an exception out of the thread target, and must stop
        cleanly the moment a fatal RuntimeError occurs (its documented
        contract) rather than looping forever or wedging.
        """
        rng = random.Random(CHAOS_SEED)
        s = _bare_session()

        outcomes = []
        call_count = [0]
        MAX_ITERATIONS = 200

        def fake_long_poll():
            call_count[0] += 1
            if call_count[0] > MAX_ITERATIONS:
                # Safety valve: a chaos sequence with no RuntimeError must
                # not spin forever in this test.
                s._stop_polling_thread = True
                return True
            fault, choice = self._make_random_fault(rng)
            outcomes.append(choice)
            return fault()

        s._long_poll = fake_long_poll
        target = _capture_polling_closure(s)
        s._stop_polling_thread = False

        with patch("boschshcpy.session.time.sleep"):
            # Must never raise, regardless of which random faults occurred.
            target()

        assert s._stop_polling_thread is True
        # Confirm the loop actually exercised a nontrivial, mixed fault mix
        # and didn't just get lucky and stop on iteration 1.
        assert len(outcomes) >= 1
        if len(outcomes) > 1:
            assert len(set(outcomes)) > 1, (
                f"expected a mixed fault sequence, got only {set(outcomes)}"
            )

    def test_generic_exception_backs_off_and_continues(self):
        """A non-RuntimeError, non-JSONRPCError exception (the 'unknown bug'
        case) must be swallowed with a backoff sleep — the thread keeps
        polling rather than dying, since a transient bug in one iteration
        shouldn't kill the whole integration's connectivity.
        """
        s = _bare_session()
        iterations = [0]

        def fake_long_poll():
            iterations[0] += 1
            if iterations[0] == 1:
                raise ValueError("boom")
            s._stop_polling_thread = True
            return True

        s._long_poll = fake_long_poll
        target = _capture_polling_closure(s)
        s._stop_polling_thread = False

        with patch("boschshcpy.session.time.sleep") as mock_sleep:
            target()

        mock_sleep.assert_any_call(15.0)
        assert iterations[0] == 2

    def test_repeated_unknown_poll_id_eventually_resubscribes(self):
        """Resubscribe storm: SHC keeps claiming 'unknown poll id' several
        times in a row (e.g. flapping session on the controller side).
        Loop must keep retrying (1s backoff) rather than crashing or
        wedging, and recover as soon as the fault clears.
        """
        s = _bare_session()
        attempts = [0]
        FLAPS = 5

        def fake_long_poll():
            attempts[0] += 1
            if attempts[0] <= FLAPS:
                return False  # simulates the -32001 branch already having run
            s._stop_polling_thread = True
            return True

        s._long_poll = fake_long_poll
        target = _capture_polling_closure(s)
        s._stop_polling_thread = False

        with patch("boschshcpy.session.time.sleep") as mock_sleep:
            target()

        assert attempts[0] == FLAPS + 1
        assert mock_sleep.call_count == FLAPS


# ---------------------------------------------------------------------------
# 2. Malformed / adversarial long-poll payload chaos: garbage from the SHC
#    (missing keys, wrong types, unknown @type, deeply nested junk) must
#    never crash _process_long_polling_poll_result.
# ---------------------------------------------------------------------------


class TestMalformedPollResultChaos:
    """Fuzz with plausible SHC-protocol chaos, not protocol violations.

    The SHC's long-poll wire format guarantees "@type" plus each type's own
    mandatory keys ("id"/"deviceId") — those are load-bearing per the
    official OpenAPI spec (API_GROUND_TRUTH), not something a compliant
    server would ever omit. Realistic chaos is: an unknown/new "@type" we
    don't handle yet, known mandatory keys present but holding unexpected
    *values* (a firmware bug, a partial/null field), or corrupted nested
    JSON inside "message" events — including a missing/malformed "@type"
    at any level, or a non-dict "arguments", now that
    _process_long_polling_poll_result guards both (see
    TestKnownGapRegressions below for the dedicated fix-confirmation
    tests).
    """

    def _random_garbage_result(self, rng: random.Random):
        known_types = [
            "DeviceServiceData",
            "message",
            "scenarioTriggered",
            "device",
            "userDefinedState",
            "link",
            "armingState",  # a DOMAIN_STATES member
        ]
        shape = rng.choice(
            [
                "unknown_type",
                "wrong_field_values",
                "nested_junk_with_at_type",
                "missing_at_type",
                "nested_missing_at_type",
                "non_dict_arguments",
                "non_string_device_service_data_model",
            ]
        )

        if shape == "unknown_type":
            return {"@type": f"totallyUnknownType{rng.randint(0, 999)}"}
        if shape == "wrong_field_values":
            device_id = rng.choice(["hdm:Device:1", "hdm:Device:unknown-to-session"])
            return {
                "@type": rng.choice(known_types),
                "id": device_id,
                "deviceId": device_id,
                "deleted": rng.choice(["not-a-bool", None, 1, True, False]),
            }
        if shape == "nested_junk_with_at_type":
            # embedded deviceServiceDataModel is garbage but still carries
            # a top-level "@type" key of its own.
            return {
                "@type": "message",
                "id": "msg-1",
                "arguments": {
                    "deviceServiceDataModel": json.dumps(
                        {"@type": rng.choice([None, "unknownNestedType", 123])}
                    )
                },
            }
        if shape == "missing_at_type":
            return rng.choice([{"deviceId": "hdm:Device:1"}, {"id": "x"}, {}])
        if shape == "nested_missing_at_type":
            return {
                "@type": "message",
                "id": "msg-1",
                "arguments": {
                    "deviceServiceDataModel": json.dumps(
                        rng.choice([{"nested": "no @type key"}, {}])
                    )
                },
            }
        if shape == "non_dict_arguments":
            return {
                "@type": "message",
                "id": "msg-1",
                "arguments": rng.choice([None, "not-a-dict", 42, [], True]),
            }
        # non_string_device_service_data_model
        return {
            "@type": "message",
            "id": "msg-1",
            "arguments": {
                "deviceServiceDataModel": rng.choice(
                    [123, ["not", "a", "string"], {"already": "a dict"}, "{{invalid"]
                )
            },
        }

    def test_survives_randomized_garbage_payloads(self):
        """DOMAIN_STATES membership check requires intrusion_system to expose
        .DOMAIN_STATES; wire a real-ish fake so 'armingState' garbage
        actually exercises that branch too.
        """
        rng = random.Random(CHAOS_SEED)
        s = _bare_session()
        s._devices_by_id["hdm:Device:1"] = MagicMock(id="hdm:Device:1")

        ids = MagicMock()
        ids.DOMAIN_STATES = {"armingState", "alarmState", "securityGapState"}
        s._domains_by_id["IDS"] = ids

        crashes = []
        for _ in range(300):
            payload = self._random_garbage_result(rng)
            try:
                s._process_long_polling_poll_result(payload)
            except Exception as exc:  # noqa: BLE001 -- this IS the assertion
                crashes.append((payload, repr(exc)))

        assert not crashes, (
            f"{len(crashes)}/300 garbage payloads crashed the poll processor, "
            f"e.g. {crashes[0]}"
        )


class TestKnownGapRegressions:
    """Regression tests for the 3 gaps this chaos suite originally found
    (all one underlying pattern in _process_long_polling_poll_result:
    trusting the SHC's message shape more than verifying it). APK
    decompile of the official Bosch app (classes13.dex) found
    "deviceServiceDataModel" referenced only as a likely Moshi/Gson
    @Json(name=...) field annotation, not behind any visible defensive
    check — no evidence either way that the SHC ever actually sends these
    shapes, so these were fixed as cheap, behavior-preserving guards
    rather than chasing further live confirmation.
    """

    def test_missing_at_type_key_no_longer_raises(self):
        """A poll result with no "@type" key at all is now ignored, like
        any other unrecognized type, instead of raising KeyError.
        """
        s = _bare_session()
        s._process_long_polling_poll_result({"deviceId": "hdm:Device:1"})  # no raise

    def test_missing_at_type_reachable_via_embedded_message_no_longer_raises(self):
        """Same fix, reached via the "message" branch's recursion into an
        embedded deviceServiceDataModel JSON blob lacking "@type".
        """
        s = _bare_session()
        payload = {
            "@type": "message",
            "id": "msg-1",
            "arguments": {
                "deviceServiceDataModel": json.dumps({"nested": "no @type key"})
            },
        }
        s._process_long_polling_poll_result(payload)  # no raise

    def test_non_dict_arguments_on_message_type_no_longer_raises(self):
        """ "arguments" present but not a dict (a partially-populated or
        corrupted message envelope) is now ignored instead of raising
        TypeError from the `in` check.
        """
        s = _bare_session()
        payload = {"@type": "message", "id": "msg-1", "arguments": None}
        s._process_long_polling_poll_result(payload)  # no raise

    def test_well_formed_message_with_device_service_data_still_recurses(self):
        """Guard against a too-broad fix: a genuinely well-formed embedded
        deviceServiceDataModel must still be processed, not silently
        swallowed by the new isinstance/`.get()` guards.
        """
        s = _bare_session()
        device = MagicMock(id="hdm:Device:1")
        s._devices_by_id["hdm:Device:1"] = device
        payload = {
            "@type": "message",
            "id": "msg-1",
            "arguments": {
                "deviceServiceDataModel": json.dumps(
                    {"@type": "DeviceServiceData", "deviceId": "hdm:Device:1"}
                )
            },
        }
        s._process_long_polling_poll_result(payload)
        device.process_long_polling_poll_result.assert_called_once()

    def test_message_without_arguments_still_stored_as_message(self):
        """Guard against a too-broad fix: the pre-existing 'message without
        arguments' case (boot/firmware update) must still be stored via
        SHCMessage, not accidentally swallowed.
        """
        s = _bare_session()
        payload = {"@type": "message", "id": "msg-1", "messageCode": {"name": "X"}}
        s._process_long_polling_poll_result(payload)
        assert "msg-1" in s._messages_by_id

    def test_non_string_device_service_data_model_no_longer_raises(self):
        """Found by a second-pass bughunt on the fix above: the guard
        checked "deviceServiceDataModel" was present and "arguments" was a
        dict, but never validated the field's own value was a JSON string.
        A non-string value (int/list/dict) raised TypeError straight out of
        json.loads; malformed JSON text raised json.JSONDecodeError. Both
        are now caught and the malformed embedded model is ignored.
        """
        s = _bare_session()
        for bad_value in (
            123,
            ["not", "a", "string"],
            {"already": "a dict"},
            "not valid json {{",
        ):
            payload = {
                "@type": "message",
                "id": "msg-1",
                "arguments": {"deviceServiceDataModel": bad_value},
            }
            s._process_long_polling_poll_result(payload)  # no raise

    def test_known_device_id_with_delete_flag_variants_never_crash(self):
        """Specifically fuzz the device-delete branch (real production
        incident class: a device disappearing mid-poll) with truthy/falsy/
        garbage 'deleted' values.
        """
        s = _bare_session()
        device = MagicMock()
        device.id = "hdm:Device:chaos"
        s._devices_by_id["hdm:Device:chaos"] = device
        s._services_by_device_id["hdm:Device:chaos"] = [{"id": "svc"}]

        for deleted_value in (True, False, None, "true", 1, 0, [], {}):
            s._devices_by_id.setdefault("hdm:Device:chaos", device)
            s._services_by_device_id.setdefault("hdm:Device:chaos", [{"id": "svc"}])
            payload = {
                "@type": "device",
                "id": "hdm:Device:chaos",
                "deleted": deleted_value,
            }
            s._process_long_polling_poll_result(payload)  # must not raise


# ---------------------------------------------------------------------------
# 3. Concurrency chaos: real threads racing device add/update/delete against
#    concurrent `.devices` reads under the real RLock. Regression target is
#    the documented "dictionary changed size during iteration" failure mode.
# ---------------------------------------------------------------------------


class TestConcurrentMutationChaos:
    def test_single_mutator_vs_concurrent_readers_never_corrupt_or_deadlock(self):
        """Matches the DOCUMENTED production threading model (session.py's
        own comment on _devices_lock): exactly ONE thread (the
        SHCPollingThread) ever adds/updates/deletes devices; other threads
        (HA's executor) only ever read via `.devices`/`.device()`
        concurrently. This is the actual invariant the RLock protects —
        multiple concurrent *writers* is a different, not-applicable
        architecture and isn't this library's contract.
        """
        s = _bare_session()
        s._device_helper.device_init.side_effect = lambda raw, services: MagicMock(
            id=raw["id"]
        )

        stop = threading.Event()
        errors: list[BaseException] = []
        N_DEVICES = 40
        DURATION_S = 1.5

        def writer():
            rng = random.Random(CHAOS_SEED)
            try:
                while not stop.is_set():
                    device_id = f"hdm:Device:{rng.randint(0, N_DEVICES - 1)}"
                    op = rng.choice(["add", "update", "delete"])
                    if op == "add":
                        s._add_device({"id": device_id}, update_services=False)
                        with s._devices_lock:
                            s._services_by_device_id[device_id] = [{"id": "svc"}]
                    elif op == "update":
                        with s._devices_lock:
                            exists = device_id in s._devices_by_id
                        if exists:
                            s._process_long_polling_poll_result(
                                {"@type": "device", "id": device_id}
                            )
                    else:  # delete
                        s._process_long_polling_poll_result(
                            {"@type": "device", "id": device_id, "deleted": True}
                        )
            except BaseException as exc:  # noqa: BLE001 -- this IS the assertion
                errors.append(exc)

        def reader():
            try:
                while not stop.is_set():
                    # .devices snapshots under the lock; iterate it fully,
                    # the exact pattern that used to race a concurrent
                    # dict mutation ("dictionary changed size during
                    # iteration") before the RLock was introduced.
                    for device in s.devices:
                        _ = device.id
            except BaseException as exc:  # noqa: BLE001 -- this IS the assertion
                errors.append(exc)

        threads = [threading.Thread(target=writer, daemon=True)] + [
            threading.Thread(target=reader, daemon=True) for _ in range(6)
        ]

        for t in threads:
            t.start()
        time.sleep(DURATION_S)
        stop.set()
        for t in threads:
            t.join(timeout=5)
            assert not t.is_alive(), "chaos thread did not exit — possible deadlock"

        assert not errors, f"concurrent access raised: {errors[:3]!r}"


# ---------------------------------------------------------------------------
# 4. Async retry-path chaos: randomized transient-failure sequences against
#    SHCAPIAsync._retry_once_on_connection_drop.
# ---------------------------------------------------------------------------


class TestAsyncRetryChaos:
    """All async tests use asyncio.run() inside plain sync test functions,
    matching the existing project convention (tests/test_session_async.py,
    tests/test_api_async.py) — no pytest-asyncio marker/config needed.
    """

    @staticmethod
    def _run_retry(attempt_sequence):
        """Drive _retry_once_on_connection_drop with a scripted sequence of
        outcomes for successive attempt() calls, using the real aiohttp
        exception types so the except-clauses genuinely match.
        """
        import asyncio

        import aiohttp

        from boschshcpy.api_async import SHCAPIAsync

        async def run():
            api = SHCAPIAsync.__new__(SHCAPIAsync)
            calls = {"n": 0}

            async def attempt():
                outcome = attempt_sequence[calls["n"]]
                calls["n"] += 1
                if outcome == "ok":
                    return "success"
                if outcome == "ssl":
                    raise aiohttp.ClientSSLError(MagicMock(), OSError("cert chaos"))
                if outcome == "timeout":
                    raise TimeoutError("chaos timeout")
                if outcome == "drop":
                    raise aiohttp.ClientConnectionError("chaos drop")
                raise AssertionError(f"unknown scripted outcome {outcome}")

            result = await api._retry_once_on_connection_drop(
                "https://chaos/api", attempt
            )
            return result, calls["n"]

        return asyncio.run(run())

    def test_single_drop_then_success_retries_once(self):
        result, n = self._run_retry(["drop", "ok"])
        assert result == "success"
        assert n == 2

    def test_double_drop_wraps_as_connection_error(self):
        with pytest.raises(SHCConnectionError):
            self._run_retry(["drop", "drop"])

    def test_drop_then_timeout_wraps_as_connection_error(self):
        with pytest.raises(SHCConnectionError):
            self._run_retry(["drop", "timeout"])

    def test_ssl_error_never_retried(self):
        """A cert/handshake failure must fail fast (raise immediately, not
        retry) — retrying it is pointless and would mask a real TLS
        misconfiguration. The scripted 'ok' second outcome must never be
        reached.
        """
        with pytest.raises(SHCConnectionError, match="SSLError"):
            self._run_retry(["ssl", "ok"])

    def test_randomized_first_attempt_outcomes_never_hang_or_crash_wrong(self):
        """Chaos-fuzz the first-attempt outcome; whatever happens, the
        helper must either return a value or raise SHCConnectionError —
        never a bare aiohttp/TimeoutError escaping to the caller (that
        would break every caller's `except SHCConnectionError` handling).
        """
        rng = random.Random(CHAOS_SEED)
        for _ in range(50):
            first = rng.choice(["ok", "ssl", "timeout", "drop"])
            second = rng.choice(["ok", "ssl", "timeout", "drop"])
            sequence = [first] if first == "ok" else [first, second]
            try:
                result, n = self._run_retry(sequence)
                assert result == "success"
            except SHCConnectionError:
                pass  # acceptable, documented outcome
            except Exception as exc:  # noqa: BLE001 -- this IS the assertion
                pytest.fail(
                    f"sequence {sequence} leaked an undocumented exception: {exc!r}"
                )
