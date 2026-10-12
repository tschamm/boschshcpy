"""Polling lifecycle / per-result isolation regression tests (no hardware)."""

import json
import threading
import time


from test_session_unit import _bare_session


def _wire(s):
    s._api.long_polling_subscribe.return_value = "pid"
    s._api.long_polling_poll.return_value = []
    s._api.long_polling_unsubscribe.return_value = None


def test_restart_after_stop_polls_again():
    s = _bare_session()
    _wire(s)
    s._long_poll_timeout = 0
    s.start_polling()
    time.sleep(0.2)
    s.stop_polling()
    assert s._polling_thread is None
    s._api.long_polling_poll.reset_mock()
    s.start_polling()
    time.sleep(0.3)
    try:
        assert s._api.long_polling_poll.called
    finally:
        s.stop_polling()


def test_stop_keeps_handle_of_still_running_worker():
    s = _bare_session()
    s._long_poll_timeout = -10  # join(timeout=0)
    release = threading.Event()
    t = threading.Thread(target=release.wait, daemon=True)
    t.start()
    s._polling_thread = t
    s._poll_id = None
    s.stop_polling()
    assert s._polling_thread is t
    release.set()
    t.join()


def test_callback_runtimeerror_does_not_drop_batch():
    s = _bare_session()
    _wire(s)
    s._poll_id = "pid"
    seen = []

    def boom(_):
        raise RuntimeError("callback bug")

    s._scenario_callbacks = {"a": boom, "b": lambda r: seen.append(r)}
    s._api.long_polling_poll.return_value = [
        {"@type": "scenarioTriggered", "id": "a"},
        {"@type": "scenarioTriggered", "id": "b"},
    ]
    assert s._long_poll() is True
    assert len(seen) == 1


def test_non_dict_embedded_model_does_not_abort_batch():
    s = _bare_session()
    _wire(s)
    s._poll_id = "pid"
    seen = []
    s._scenario_callbacks = {"b": lambda r: seen.append(r)}
    msgs = [
        {
            "@type": "message",
            "id": str(i),
            "arguments": {"deviceServiceDataModel": json.dumps(v)},
        }
        for i, v in enumerate([None, [], 42])
    ]
    s._api.long_polling_poll.return_value = msgs + [
        {"@type": "scenarioTriggered", "id": "b"}
    ]
    assert s._long_poll() is True
    assert len(seen) == 1


def test_start_blocks_until_stop_cleanup_completes():
    """start_polling() racing a stop whose unsubscribe is still running must
    not spawn a second worker that the older stop then orphans."""
    s = _bare_session()
    _wire(s)
    s._long_poll_timeout = 0
    s.start_polling()
    time.sleep(0.2)
    first = s._polling_thread

    in_unsub = threading.Event()
    release = threading.Event()

    def slow_unsub(_pid):
        in_unsub.set()
        release.wait(5)

    s._api.long_polling_unsubscribe.side_effect = slow_unsub
    stopper = threading.Thread(target=s.stop_polling)
    stopper.start()
    assert in_unsub.wait(5)  # worker is gone, stop still cleaning up

    starter = threading.Thread(target=lambda: s.start_polling())
    starter.start()
    time.sleep(0.3)
    # start must still be waiting for stop cleanup
    assert starter.is_alive()
    release.set()
    stopper.join(5)
    starter.join(5)
    try:
        new = s._polling_thread
        assert new is not None and new is not first and new.is_alive()
        assert s._stop_polling_thread is False
    finally:
        s._api.long_polling_unsubscribe.side_effect = None
        s.stop_polling()


def test_poll_cond_is_per_session_instance():
    a = _bare_session()
    b = _bare_session()
    assert a._poll_cond is not b._poll_cond
    # stable on repeated access (lazy fallback for __new__-built doubles)
    assert a._poll_cond is a._poll_cond
    # one session holding its lifecycle lock must not block another
    done = threading.Event()
    with a._poll_cond:

        def other():
            with b._poll_cond:
                done.set()

        t = threading.Thread(target=other)
        t.start()
        assert done.wait(2)
        t.join(2)


def test_start_waits_for_full_cleanup_budget():
    """A valid slow cleanup (join + 30s unsubscribe) must not make
    start_polling raise; the wait is sized to the whole cleanup budget."""
    s = _bare_session()
    _wire(s)
    s._long_poll_timeout = 10
    s._poll_stopping = True
    seen = {}

    class Cond:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def wait_for(self, pred, timeout=None):
            seen["timeout"] = timeout
            s._poll_stopping = False
            return True

    s._poll_cond = Cond()
    s.start_polling()
    try:
        assert seen["timeout"] >= s._long_poll_timeout + 10 + 30
    finally:
        s._stop_polling_thread = True
