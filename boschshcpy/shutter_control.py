from enum import Enum
from .device import SHCDevice


class SHCShutterControl(SHCDevice):
    def __init__(self, api, raw_device):
        super().__init__(api, raw_device=raw_device)
        
        self._service = self.device_service('ShutterControl')

    def set_level(self, level):
        self._service.put_state_element('level', level)

    @property
    def level(self) -> float:
        self._service.short_poll()
        return self._service.level

    def set_stopped(self):
        self._service.put_state_element('operationState', 'STOPPED')

    def summary(self):
        print(f"BBL ShutterControl:")
        super().summary()
