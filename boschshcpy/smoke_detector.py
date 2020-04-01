from enum import Enum
from .device import SHCDevice


class SHCSmokeDetector(SHCDevice):
    class AlarmState(Enum):
        INTRUSION_ALARM_ON_REQUESTED = "INTRUSION_ALARM_ON_REQUESTED"
        INTRUSION_ALARM_OFF_REQUESTED = "INTRUSION_ALARM_OFF_REQUESTED"
        MUTE_SECONDARY_ALARM_REQUESTED = "MUTE_SECONDARY_ALARM_REQUESTED"

    def __init__(self, api, raw_device):
        super().__init__(api, raw_device)

        self._service = self.device_service('Alarm')

    def set_alarmstate(self, state: AlarmState):
        self._service.put_state_element('state', state.name)

    def summary(self):
        print(f"SD SmokeDetector:")
        super().summary()
