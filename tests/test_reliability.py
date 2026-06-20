"""Tests for reliability fixes (urllib3 pool size, log levels, ValveTappet enum)."""

from boschshcpy.services_impl import ValveTappetService


def test_valvetappet_no_motor_error_member():
    # REGRESSION #243: the Bosch firmware reports NO_MOTOR_ERROR on a motor
    # error; the enum lacked it, so ValveTappetService.State(value) raised
    # ValueError and killed the valve/sensor entity.
    assert ValveTappetService.State("NO_MOTOR_ERROR") is ValveTappetService.State.NO_MOTOR_ERROR


def test_valvetappet_known_members_still_parse():
    for value in ("NO_VALVE_BODY_ERROR", "IN_START_POSITION", "NOT_AVAILABLE"):
        assert ValveTappetService.State(value).value == value


def test_pool_maxsize_set_on_adapter():
    # #56: the HTTPS adapter must set pool_maxsize (>10) so the long-poll thread
    # plus on-demand reads don't exhaust the default pool of 10.
    import inspect

    from boschshcpy import api

    src = inspect.getsource(api.SHCAPI.__init__)
    assert "pool_maxsize=" in src
