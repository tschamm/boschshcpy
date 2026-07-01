from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any


class SHCIntrusionSystem:
    DOMAIN_STATES = {
        "armingState",
        "alarmState",
        "securityGapState",
        "activeConfigurationProfile",
        "systemAvailability",
    }

    class ArmingState(Enum):
        SYSTEM_DISARMED = "SYSTEM_DISARMED"
        SYSTEM_ARMED = "SYSTEM_ARMED"
        SYSTEM_ARMING = "SYSTEM_ARMING"

    class AlarmState(Enum):
        ALARM_OFF = "ALARM_OFF"
        ALARM_ON = "ALARM_ON"
        ALARM_MUTED = "ALARM_MUTED"
        PRE_ALARM = "PRE_ALARM"
        UNKNOWN = "UNKNOWN"

    class Profile(Enum):
        FULL_PROTECTION = 0
        PARTIAL_PROTECTION = 1
        CUSTOM_PROTECTION = 2
        # IDS supports additional custom profiles beyond these 3 built-ins
        # (profileId is a string per OpenAPI, not restricted to 0/1/2) — an
        # unrecognized id must not be silently mis-reported as an existing
        # profile (see active_configuration_profile below).
        UNKNOWN = -1

    def __init__(
        self, api: Any, raw_domain_state: dict[str, Any], root_device_id: str | None
    ) -> None:
        self._api = api
        # None of SystemStateData's sub-objects are in the OpenAPI "required"
        # list (IntrusionDetectionSystem-local-openapi-v3.yml has no
        # `required:` block at all) — the SHC is free to omit any of them.
        # This is on the hot poll path (short_poll below runs periodically),
        # so an unguarded KeyError here would take down live polling, not
        # just startup.
        self._raw_system_availability: dict[str, Any] = raw_domain_state.get(
            "systemAvailability", {}
        )
        self._raw_arming_state: dict[str, Any] = raw_domain_state.get("armingState", {})
        self._raw_alarm_state: dict[str, Any] = raw_domain_state.get("alarmState", {})
        self._raw_active_configuration_profile: dict[str, Any] = raw_domain_state.get(
            "activeConfigurationProfile", {}
        )
        self._raw_security_gap_state: dict[str, Any] = raw_domain_state.get(
            "securityGapState", {"securityGaps": []}
        )
        self._root_device_id = root_device_id

        self._callbacks: dict[Any, Callable[[], None]] = {}

    @property
    def id(self) -> str:
        return "/intrusion"

    @property
    def manufacturer(self) -> str:
        return "BOSCH"

    @property
    def name(self) -> str:
        return "Intrusion Detection System"

    @property
    def root_device_id(self) -> str | None:
        return self._root_device_id

    @property
    def device_model(self) -> str:
        return "IDS"

    @property
    def deleted(self) -> bool:
        return False

    @property
    def system_availability(self) -> bool:
        return bool(self._raw_system_availability.get("available", False))

    @property
    def arming_state(self) -> ArmingState:
        try:
            return self.ArmingState(self._raw_arming_state["state"])
        except (KeyError, ValueError):
            return self.ArmingState.SYSTEM_DISARMED

    @property
    def remaining_time_until_armed(self) -> int:
        if self.arming_state == self.ArmingState.SYSTEM_ARMING:
            return int(self._raw_arming_state.get("remainingTimeUntilArmed", 0))
        return 0

    @property
    def alarm_state(self) -> AlarmState:
        try:
            return self.AlarmState(self._raw_alarm_state["value"])
        except (KeyError, ValueError):
            return self.AlarmState.ALARM_OFF

    @property
    def alarm_state_incidents(self) -> list[Any]:
        return list(self._raw_alarm_state.get("incidents", []))

    @property
    def active_configuration_profile(self) -> Profile:
        try:
            return self.Profile(
                int(self._raw_active_configuration_profile.get("profileId", -1))
            )
        except (ValueError, KeyError, TypeError):
            # A custom/unrecognized profile must not be reported as
            # FULL_PROTECTION — that would misrepresent which profile is
            # actually armed (security-relevant: alarm_control_panel.py
            # derives ARMED_AWAY/ARMED_HOME/ARMED_CUSTOM_BYPASS from this).
            return self.Profile.UNKNOWN

    @property
    def security_gaps(self) -> list[Any]:
        return list(self._raw_security_gap_state.get("securityGaps", []))

    def subscribe_callback(self, entity: Any, callback: Callable[[], None]) -> None:
        self._callbacks[entity] = callback

    def unsubscribe_callback(self, entity: Any) -> None:
        self._callbacks.pop(entity, None)

    def summary(self) -> None:
        print(f"  Domain:                  {self.id}")
        print(f"    System Availability:   {self.system_availability}")
        print(f"    Arming State:          {self.arming_state}")
        print(f"    Alarm State:           {self.alarm_state}")

    def arm(self) -> None:
        self._api.post_domain_action("intrusion/actions/arm")

    async def async_arm(self) -> None:
        """Async write: arm the intrusion system (default profile)."""
        await self._api.post_domain_action("intrusion/actions/arm")

    def arm_full_protection(self) -> None:
        data = {"@type": "armRequest", "profileId": "0"}
        self._api.post_domain_action("intrusion/actions/arm", data)

    async def async_arm_full_protection(self) -> None:
        """Async write: arm with full protection (profile 0)."""
        data = {"@type": "armRequest", "profileId": "0"}
        await self._api.post_domain_action("intrusion/actions/arm", data)

    def arm_partial_protection(self) -> None:
        data = {"@type": "armRequest", "profileId": "1"}
        self._api.post_domain_action("intrusion/actions/arm", data)

    async def async_arm_partial_protection(self) -> None:
        """Async write: arm with partial protection (profile 1)."""
        data = {"@type": "armRequest", "profileId": "1"}
        await self._api.post_domain_action("intrusion/actions/arm", data)

    def arm_individual_protection(self) -> None:
        data = {"@type": "armRequest", "profileId": "2"}
        self._api.post_domain_action("intrusion/actions/arm", data)

    async def async_arm_individual_protection(self) -> None:
        """Async write: arm with individual (custom) protection (profile 2)."""
        data = {"@type": "armRequest", "profileId": "2"}
        await self._api.post_domain_action("intrusion/actions/arm", data)

    def disarm(self) -> None:
        self._api.post_domain_action("intrusion/actions/disarm")

    async def async_disarm(self) -> None:
        """Async write: disarm the intrusion system."""
        await self._api.post_domain_action("intrusion/actions/disarm")

    def mute(self) -> None:
        self._api.post_domain_action("intrusion/actions/mute")

    async def async_mute(self) -> None:
        """Async write: mute the active alarm."""
        await self._api.post_domain_action("intrusion/actions/mute")

    def short_poll(self) -> None:
        raw_domain_state = self._api.get_domain_intrusion_detection()
        # Same missing-field tolerance as __init__ — this runs periodically,
        # so an unguarded KeyError here would repeatedly break live polling
        # rather than just failing once at startup.
        self._raw_system_availability = raw_domain_state.get("systemAvailability", {})
        self._raw_arming_state = raw_domain_state.get("armingState", {})
        self._raw_alarm_state = raw_domain_state.get("alarmState", {})
        self._raw_active_configuration_profile = raw_domain_state.get(
            "activeConfigurationProfile", {}
        )
        self._raw_security_gap_state = raw_domain_state.get(
            "securityGapState", {"securityGaps": []}
        )

    def process_long_polling_poll_result(self, raw_result: dict[str, Any]) -> None:
        if raw_result.get("@type") == "armingState":
            self._raw_arming_state = raw_result
        if raw_result.get("@type") == "alarmState":
            self._raw_alarm_state = raw_result
        if raw_result.get("@type") == "systemAvailability":
            self._raw_system_availability = raw_result
        if raw_result.get("@type") == "activeConfigurationProfile":
            self._raw_active_configuration_profile = raw_result
        if raw_result.get("@type") == "securityGapState":
            self._raw_security_gap_state = raw_result

        for fn in list(self._callbacks.values()):
            fn()


MODEL_MAPPING = {"IDS": SHCIntrusionSystem}

SUPPORTED_DOMAINS = MODEL_MAPPING.keys()


def build(
    api: Any,
    domain_model: str,
    raw_domain_state: dict[str, Any],
    root_device_id: str | None,
) -> SHCIntrusionSystem:
    if domain_model not in SUPPORTED_DOMAINS:
        raise ValueError(f"Unsupported domain model: {domain_model!r}")
    return MODEL_MAPPING[domain_model](
        api=api, raw_domain_state=raw_domain_state, root_device_id=root_device_id
    )
