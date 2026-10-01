from boschshcpy.services_impl import SurveillanceAlarmService


def _service(value):
    svc = SurveillanceAlarmService.__new__(SurveillanceAlarmService)
    svc._raw_state = {"value": value}
    return svc


def test_pre_alarm_is_reported_not_folded_into_off():
    assert (
        _service("PRE_ALARM").value is SurveillanceAlarmService.State.PRE_ALARM
    )


def test_unknown_value_still_falls_back_to_off():
    assert (
        _service("SOMETHING_NEW").value is SurveillanceAlarmService.State.ALARM_OFF
    )
