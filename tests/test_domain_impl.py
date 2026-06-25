"""Isolation-safe tests for domain_impl.py — SHCIntrusionSystem + build().

No HA harness, no real network. __init__ is called directly with a fake API
and a hand-crafted raw_domain_state dict.
"""

import pytest
from unittest.mock import MagicMock, call

from boschshcpy.domain_impl import SHCIntrusionSystem, build


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_ids(
    api=None,
    arming_state="SYSTEM_DISARMED",
    alarm_state="ALARM_OFF",
    profile_id="0",
    available=True,
    root_device_id="hdm:root",
    incidents=None,
    security_gaps=None,
    remaining_time=30,
):
    if api is None:
        api = MagicMock()
    raw = {
        "systemAvailability": {"available": available},
        "armingState": {"state": arming_state, "remainingTimeUntilArmed": remaining_time},
        "alarmState": {"value": alarm_state, "incidents": incidents if incidents is not None else []},
        "activeConfigurationProfile": {"profileId": profile_id},
        "securityGapState": {"securityGaps": security_gaps if security_gaps is not None else []},
    }
    return SHCIntrusionSystem(api=api, raw_domain_state=raw, root_device_id=root_device_id)


# ===========================================================================
# 1. Static properties
# ===========================================================================

def test_ids_id():
    assert _make_ids().id == "/intrusion"


def test_ids_manufacturer():
    assert _make_ids().manufacturer == "BOSCH"


def test_ids_name():
    assert _make_ids().name == "Intrusion Detection System"


def test_ids_device_model():
    assert _make_ids().device_model == "IDS"


def test_ids_deleted():
    assert _make_ids().deleted is False


def test_ids_root_device_id():
    svc = _make_ids(root_device_id="hdm:root")
    assert svc.root_device_id == "hdm:root"


# ===========================================================================
# 2. system_availability
# ===========================================================================

def test_ids_system_available_true():
    assert _make_ids(available=True).system_availability is True


def test_ids_system_available_false():
    assert _make_ids(available=False).system_availability is False


# ===========================================================================
# 3. arming_state
# ===========================================================================

def test_ids_arming_state_disarmed():
    svc = _make_ids(arming_state="SYSTEM_DISARMED")
    assert svc.arming_state == SHCIntrusionSystem.ArmingState.SYSTEM_DISARMED


def test_ids_arming_state_armed():
    svc = _make_ids(arming_state="SYSTEM_ARMED")
    assert svc.arming_state == SHCIntrusionSystem.ArmingState.SYSTEM_ARMED


def test_ids_arming_state_arming():
    svc = _make_ids(arming_state="SYSTEM_ARMING")
    assert svc.arming_state == SHCIntrusionSystem.ArmingState.SYSTEM_ARMING


# ===========================================================================
# 4. remaining_time_until_armed
# ===========================================================================

def test_ids_remaining_time_when_arming():
    svc = _make_ids(arming_state="SYSTEM_ARMING", remaining_time=30)
    assert svc.remaining_time_until_armed == 30


def test_ids_remaining_time_when_not_arming():
    svc = _make_ids(arming_state="SYSTEM_DISARMED", remaining_time=30)
    assert svc.remaining_time_until_armed == 0


def test_ids_remaining_time_when_armed():
    svc = _make_ids(arming_state="SYSTEM_ARMED", remaining_time=99)
    assert svc.remaining_time_until_armed == 0


# ===========================================================================
# 5. alarm_state
# ===========================================================================

def test_ids_alarm_state_off():
    assert _make_ids(alarm_state="ALARM_OFF").alarm_state == SHCIntrusionSystem.AlarmState.ALARM_OFF


def test_ids_alarm_state_on():
    assert _make_ids(alarm_state="ALARM_ON").alarm_state == SHCIntrusionSystem.AlarmState.ALARM_ON


def test_ids_alarm_state_muted():
    assert _make_ids(alarm_state="ALARM_MUTED").alarm_state == SHCIntrusionSystem.AlarmState.ALARM_MUTED


def test_ids_alarm_state_pre_alarm():
    assert _make_ids(alarm_state="PRE_ALARM").alarm_state == SHCIntrusionSystem.AlarmState.PRE_ALARM


# ===========================================================================
# 6. alarm_state_incidents
# ===========================================================================

def test_ids_alarm_state_incidents_empty():
    assert _make_ids().alarm_state_incidents == []


def test_ids_alarm_state_incidents_with_items():
    items = [{"x": 1}, {"x": 2}]
    svc = _make_ids(incidents=items)
    assert svc.alarm_state_incidents == items


# ===========================================================================
# 7. active_configuration_profile
# ===========================================================================

def test_ids_profile_full():
    svc = _make_ids(profile_id="0")
    assert svc.active_configuration_profile == SHCIntrusionSystem.Profile.FULL_PROTECTION


def test_ids_profile_partial():
    svc = _make_ids(profile_id="1")
    assert svc.active_configuration_profile == SHCIntrusionSystem.Profile.PARTIAL_PROTECTION


def test_ids_profile_custom():
    svc = _make_ids(profile_id="2")
    assert svc.active_configuration_profile == SHCIntrusionSystem.Profile.CUSTOM_PROTECTION


# ===========================================================================
# 8. security_gaps
# ===========================================================================

def test_ids_security_gaps_empty():
    assert _make_ids().security_gaps == []


def test_ids_security_gaps_with_item():
    gaps = [{"id": "gap1"}]
    svc = _make_ids(security_gaps=gaps)
    assert svc.security_gaps == gaps


# ===========================================================================
# 9. subscribe / unsubscribe callback
# ===========================================================================

def test_ids_subscribe_callback():
    svc = _make_ids()
    cb = MagicMock()
    svc.subscribe_callback("entity1", cb)
    assert "entity1" in svc._callbacks
    assert svc._callbacks["entity1"] is cb


def test_ids_unsubscribe_callback():
    svc = _make_ids()
    cb = MagicMock()
    svc.subscribe_callback("entity1", cb)
    svc.unsubscribe_callback("entity1")
    assert "entity1" not in svc._callbacks


def test_ids_unsubscribe_nonexistent_does_not_raise():
    svc = _make_ids()
    svc.unsubscribe_callback("nonexistent")  # must not raise


# ===========================================================================
# 10. arm actions
# ===========================================================================

def test_ids_arm():
    api = MagicMock()
    svc = _make_ids(api=api)
    svc.arm()
    api.post_domain_action.assert_called_once_with("intrusion/actions/arm")


def test_ids_arm_full_protection():
    api = MagicMock()
    svc = _make_ids(api=api)
    svc.arm_full_protection()
    api.post_domain_action.assert_called_once_with(
        "intrusion/actions/arm", {"@type": "armRequest", "profileId": "0"}
    )


def test_ids_arm_partial_protection():
    api = MagicMock()
    svc = _make_ids(api=api)
    svc.arm_partial_protection()
    api.post_domain_action.assert_called_once_with(
        "intrusion/actions/arm", {"@type": "armRequest", "profileId": "1"}
    )


def test_ids_arm_individual_protection():
    api = MagicMock()
    svc = _make_ids(api=api)
    svc.arm_individual_protection()
    api.post_domain_action.assert_called_once_with(
        "intrusion/actions/arm", {"@type": "armRequest", "profileId": "2"}
    )


def test_ids_disarm():
    api = MagicMock()
    svc = _make_ids(api=api)
    svc.disarm()
    api.post_domain_action.assert_called_once_with("intrusion/actions/disarm")


def test_ids_mute():
    api = MagicMock()
    svc = _make_ids(api=api)
    svc.mute()
    api.post_domain_action.assert_called_once_with("intrusion/actions/mute")


# ===========================================================================
# 11. short_poll
# ===========================================================================

def _full_raw(arming_state="SYSTEM_ARMED"):
    return {
        "systemAvailability": {"available": True},
        "armingState": {"state": arming_state, "remainingTimeUntilArmed": 0},
        "alarmState": {"value": "ALARM_OFF", "incidents": []},
        "activeConfigurationProfile": {"profileId": "0"},
        "securityGapState": {"securityGaps": []},
    }


def test_ids_short_poll_updates_state():
    api = MagicMock()
    api.get_domain_intrusion_detection.return_value = _full_raw(arming_state="SYSTEM_ARMED")
    svc = _make_ids(api=api, arming_state="SYSTEM_DISARMED")
    assert svc.arming_state == SHCIntrusionSystem.ArmingState.SYSTEM_DISARMED
    svc.short_poll()
    api.get_domain_intrusion_detection.assert_called_once()
    assert svc.arming_state == SHCIntrusionSystem.ArmingState.SYSTEM_ARMED


def test_ids_short_poll_updates_alarm_state():
    api = MagicMock()
    new_raw = _full_raw()
    new_raw["alarmState"] = {"value": "ALARM_ON", "incidents": []}
    api.get_domain_intrusion_detection.return_value = new_raw
    svc = _make_ids(api=api, alarm_state="ALARM_OFF")
    svc.short_poll()
    assert svc.alarm_state == SHCIntrusionSystem.AlarmState.ALARM_ON


# ===========================================================================
# 12. process_long_polling_poll_result
# ===========================================================================

def test_ids_process_arming_state():
    svc = _make_ids(arming_state="SYSTEM_DISARMED")
    svc.process_long_polling_poll_result(
        {"@type": "armingState", "state": "SYSTEM_ARMED", "remainingTimeUntilArmed": 0}
    )
    assert svc.arming_state == SHCIntrusionSystem.ArmingState.SYSTEM_ARMED


def test_ids_process_alarm_state():
    svc = _make_ids(alarm_state="ALARM_OFF")
    svc.process_long_polling_poll_result(
        {"@type": "alarmState", "value": "ALARM_ON", "incidents": []}
    )
    assert svc.alarm_state == SHCIntrusionSystem.AlarmState.ALARM_ON


def test_ids_process_system_availability():
    svc = _make_ids(available=True)
    svc.process_long_polling_poll_result(
        {"@type": "systemAvailability", "available": False}
    )
    assert svc.system_availability is False


def test_ids_process_active_config_profile():
    svc = _make_ids(profile_id="0")
    svc.process_long_polling_poll_result(
        {"@type": "activeConfigurationProfile", "profileId": "2"}
    )
    assert svc.active_configuration_profile == SHCIntrusionSystem.Profile.CUSTOM_PROTECTION


def test_ids_process_security_gap_state():
    svc = _make_ids()
    new_gaps = [{"id": "gap42"}]
    svc.process_long_polling_poll_result(
        {"@type": "securityGapState", "securityGaps": new_gaps}
    )
    assert svc.security_gaps == new_gaps


def test_ids_process_unknown_type_no_crash():
    svc = _make_ids()
    # Must not raise even for an unrecognised @type
    svc.process_long_polling_poll_result({"@type": "unknownFutureThing", "data": 42})


def test_ids_process_callbacks_called():
    svc = _make_ids()
    cb = MagicMock()
    svc.subscribe_callback("entity1", cb)
    svc.process_long_polling_poll_result(
        {"@type": "armingState", "state": "SYSTEM_ARMED", "remainingTimeUntilArmed": 0}
    )
    cb.assert_called_once()


def test_ids_process_multiple_callbacks_all_called():
    svc = _make_ids()
    cb1, cb2 = MagicMock(), MagicMock()
    svc.subscribe_callback("e1", cb1)
    svc.subscribe_callback("e2", cb2)
    svc.process_long_polling_poll_result(
        {"@type": "alarmState", "value": "ALARM_OFF", "incidents": []}
    )
    cb1.assert_called_once()
    cb2.assert_called_once()


def test_ids_process_unsubscribed_callback_not_called():
    svc = _make_ids()
    cb = MagicMock()
    svc.subscribe_callback("entity1", cb)
    svc.unsubscribe_callback("entity1")
    svc.process_long_polling_poll_result(
        {"@type": "armingState", "state": "SYSTEM_ARMED", "remainingTimeUntilArmed": 0}
    )
    cb.assert_not_called()


# ===========================================================================
# 13. build() function
# ===========================================================================

def test_domain_build_ids():
    # Regression (fixed): build() now forwards root_device_id to the model's __init__,
    # so it constructs a fully-initialised SHCIntrusionSystem without any patching.
    api = MagicMock()
    raw = _full_raw()
    result = build(
        api=api, domain_model="IDS", raw_domain_state=raw, root_device_id="hdm:root"
    )
    assert isinstance(result, SHCIntrusionSystem)
    assert result.root_device_id == "hdm:root"


def test_domain_build_unknown_raises():
    api = MagicMock()
    with pytest.raises(ValueError):
        build(
            api=api, domain_model="UNKNOWN", raw_domain_state={}, root_device_id="hdm:root"
        )


def test_domain_build_ids_model_mapping():
    """MODEL_MAPPING contains exactly 'IDS' and nothing else unexpected."""
    from boschshcpy.domain_impl import MODEL_MAPPING, SUPPORTED_DOMAINS
    assert "IDS" in SUPPORTED_DOMAINS
    assert MODEL_MAPPING["IDS"] is SHCIntrusionSystem


# ===========================================================================
# BUG 3 regression — bare Enum() calls raise ValueError on unknown values.
# All three properties (arming_state, alarm_state, active_configuration_profile)
# must return a safe default instead of crashing.
#
# Consumer (alarm_control_panel.py) impact analysis:
#   arming_state unknown  → default SYSTEM_DISARMED → panel shows DISARMED (safe)
#   alarm_state unknown   → default ALARM_OFF       → no false trigger (safe)
#   profile unknown       → default FULL_PROTECTION → ARMED_AWAY sub-state (safe,
#                           no worse than showing wrong sub-mode when already ARMED)
#
# alarm_state_incidents: spec marks "incidents" optional → KeyError fixed to .get([]).
# ===========================================================================

def test_ids_unknown_arming_state_returns_disarmed():
    """Regression: ValueError on ArmingState('UNKNOWN_FUTURE') → safe DISARMED."""
    svc = _make_ids()
    svc._raw_arming_state = {"state": "UNKNOWN_FUTURE_VALUE", "remainingTimeUntilArmed": 0}
    assert svc.arming_state == SHCIntrusionSystem.ArmingState.SYSTEM_DISARMED


def test_ids_unknown_alarm_state_returns_alarm_off():
    """Regression: ValueError on AlarmState('NEW_BOSCH_STATE') → safe ALARM_OFF."""
    svc = _make_ids()
    svc._raw_alarm_state = {"value": "NEW_BOSCH_STATE", "incidents": []}
    assert svc.alarm_state == SHCIntrusionSystem.AlarmState.ALARM_OFF


def test_ids_unknown_profile_returns_full_protection():
    """Regression: ValueError on Profile(int('99')) → safe FULL_PROTECTION."""
    svc = _make_ids()
    svc._raw_active_configuration_profile = {"profileId": "99"}
    assert svc.active_configuration_profile == SHCIntrusionSystem.Profile.FULL_PROTECTION


def test_ids_non_int_profile_returns_full_protection():
    """Regression: ValueError on Profile(int('custom')) → safe FULL_PROTECTION."""
    svc = _make_ids()
    svc._raw_active_configuration_profile = {"profileId": "custom"}
    assert svc.active_configuration_profile == SHCIntrusionSystem.Profile.FULL_PROTECTION


def test_ids_alarm_state_incidents_key_absent_no_keyerror():
    """Regression: KeyError on _raw_alarm_state['incidents'] when key absent."""
    svc = _make_ids()
    svc._raw_alarm_state = {"value": "ALARM_OFF"}  # no 'incidents' key
    assert svc.alarm_state_incidents == []


def test_ids_summary(capsys):
    svc = _make_ids()
    svc.summary()
    out = capsys.readouterr().out
    assert "Domain" in out
    assert "System Availability" in out
    assert "Arming State" in out
    assert "Alarm State" in out
