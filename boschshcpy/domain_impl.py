from enum import Enum

from .api import SHCAPI


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

    class Profile(Enum):
        FULL_PROTECTION = 0
        PARTIAL_PROTECTION = 1
        CUSTOM_PROTECTION = 2

    def __init__(self, api: SHCAPI, raw_domain_state):
        self._api = api
        self._raw_system_availability = raw_domain_state["systemAvailability"]
        self._raw_arming_state = raw_domain_state["armingState"]
        self._raw_alarm_state = raw_domain_state["alarmState"]
        self._raw_active_configuration_profile = raw_domain_state[
            "activeConfigurationProfile"
        ]
        self._raw_security_gap_state = raw_domain_state["securityGapState"]

        self._callbacks = {}

    @property
    def id(self):
        return "/intrusion"

    @property
    def manufacturer(self):
        return "BOSCH"

    @property
    def name(self):
        return "Intrusion Detection System"

    @property
    def device_model(self):
        return "IDS"

    @property
    def system_availability(self) -> bool:
        return self._raw_system_availability["available"]

    @property
    def arming_state(self) -> ArmingState:
        return self.ArmingState(self._raw_arming_state["state"])

    @property
    def remaining_time_until_armed(self) -> int:
        if self.arming_state == self.ArmingState.SYSTEM_ARMING:
            return self._raw_arming_state["remainingTimeUntilArmed"]
        return 0

    @property
    def alarm_state(self) -> AlarmState:
        return self.AlarmState(self._raw_alarm_state["value"])

    @property
    def alarm_state_incidents(self):
        return self._raw_alarm_state["incidents"]

    @property
    def active_configuration_profile(self) -> Profile:
        return self.Profile(int(self._raw_active_configuration_profile["profileId"]))

    @property
    def security_gaps(self):
        return self._raw_security_gap_state["securityGaps"]

    def subscribe_callback(self, entity, callback):
        self._callbacks[entity] = callback

    def unsubscribe_callback(self, entity):
        self._callbacks.pop(entity, None)

    def summary(self):
        print(f"  Domain:                  {self.id}")
        print(f"    System Availability:   {self.system_availability}")
        print(f"    Arming State:          {self.arming_state}")
        print(f"    Alarm State:           {self.alarm_state}")

    def arm(self):
        result = self._api.post_domain_action("intrusion/actions/arm")

    def arm_full_protection(self):
        data = {"@type": "armRequest", "profileId": "0"}
        result = self._api.post_domain_action("intrusion/actions/arm", data)

    def arm_partial_protection(self):
        data = {"@type": "armRequest", "profileId": "1"}
        result = self._api.post_domain_action("intrusion/actions/arm", data)

    def arm_individual_protection(self):
        data = {"@type": "armRequest", "profileId": "2"}
        self._api.post_domain_action("intrusion/actions/arm", data)

    def disarm(self):
        self._api.post_domain_action("intrusion/actions/disarm")

    def mute(self):
        self._api.post_domain_action("intrusion/actions/mute")

    def short_poll(self):
        raw_domain_state = self._api.get_domain_intrusion_detection()
        self._raw_system_availability = raw_domain_state["systemAvailability"]
        self._raw_arming_state = raw_domain_state["armingState"]
        self._raw_alarm_state = raw_domain_state["alarmState"]
        self._raw_active_configuration_profile = raw_domain_state[
            "activeConfigurationProfile"
        ]
        self._raw_security_gap_state = raw_domain_state["securityGapState"]

    def process_long_polling_poll_result(self, raw_result):
        if raw_result["@type"] == "armingState":
            self._raw_arming_state = raw_result
        if raw_result["@type"] == "alarmState":
            self._raw_alarm_state = raw_result
        if raw_result["@type"] == "systemAvailability":
            self._raw_system_availability = raw_result
        if raw_result["@type"] == "activeConfigurationProfile":
            self._raw_active_configuration_profile = raw_result
        if raw_result["@type"] == "securityGapState":
            self._raw_security_gap_state = raw_result

        for callback in self._callbacks:
            self._callbacks[callback]()


MODEL_MAPPING = {"IDS": SHCIntrusionSystem}

SUPPORTED_DOMAINS = MODEL_MAPPING.keys()


def build(api, domain_model, raw_domain_state):
    assert domain_model in SUPPORTED_DOMAINS, "Domain model is supported"
    return MODEL_MAPPING[domain_model](api=api, raw_domain_state=raw_domain_state)
