from enum import Enum
from .api import SHCAPI

class SHCIntrusionDetectionDomain:
    class ArmingState(Enum):
        SYSTEM_DISARMED = "SYSTEM_DISARMED"
        SYSTEM_ARMED = "SYSTEM_ARMED"
        SYSTEM_ARMING = "SYSTEM_ARMING"

    class AlarmState(Enum):
        ALARM_OFF = "ALARM_OFF"
        ALARM_ON = "ALARM_ON"
        ALARM_MUTED = "ALARM_MUTED"

    def __init__(self, api: SHCAPI, raw_domain_state):
        self._api = api
        self._raw_domain_state = raw_domain_state

        self._callbacks = {}

    @property
    def id(self):
        return "Intrusion Detection"

    @property
    def system_availability(self) -> bool:
        return self._raw_domain_state["systemAvailability"]["available"]

    @property
    def arming_state(self) -> ArmingState:
        return self.ArmingState(self._raw_domain_state["armingState"]["state"])

    @property
    def alarm_state(self) -> AlarmState:
        return self.AlarmState(self._raw_domain_state["alarmState"]["value"])

    @property
    def alarm_state_incidents(self):
        return self._raw_domain_state["alarmState"]["incidents"]

    @property
    def active_configuration_profile(self):
        return self._raw_domain_state["activeConfigurationProfile"]["profileId"]

    @property
    def security_gap_state(self):
        return self._raw_domain_state["securityGapState"]["securityGaps"]

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
        result = self._api.post_domain_action("intrusion/action/arm")
        print(result)

    def arm_full_protection(self):
        data = {
        	"@type": "armRequest",
	        "profileId": "0"
        }
        result = self._api.post_domain_action("intrusion/action/arm", data)
        print(result)

    def arm_partial_protection(self):
        data = {
        	"@type": "armRequest",
	        "profileId": "1"
        }
        result = self._api.post_domain_action("intrusion/action/arm", data)
        print(result)

    def arm_individual_protection(self):
        data = {
        	"@type": "armRequest",
	        "profileId": "2"
        }
        result = self._api.post_domain_action("intrusion/action/arm", data)
        print(result)

    def disarm(self):
        result = self._api.post_domain_action("intrusion/action/disarm")
        print(result)

    def mute(self):
        result = self._api.post_domain_action("intrusion/action/mute")
        print(result)

    def short_poll(self):
        self._raw_domain_state = self._api.get_domain_intrusion_detection()

    def process_long_polling_poll_result(self, raw_result):
        assert raw_result["@type"] == "systemState"
        self._raw_domain_state = raw_result  # Update device service data

        for callback in self._callbacks:
            self._callbacks[callback]()

MODEL_MAPPING = {
    "intrusion": SHCIntrusionDetectionDomain
}

SUPPORTED_DOMAINS = MODEL_MAPPING.keys()


def build(api, domain_model, raw_domain_state):
    assert domain_model in SUPPORTED_DOMAINS, "Domain model is supported"
    return MODEL_MAPPING[domain_model](api=api, raw_domain_state=raw_domain_state)
