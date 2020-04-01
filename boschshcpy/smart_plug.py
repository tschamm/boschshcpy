from enum import Enum
from .device import SHCDevice

class SHCSmartPlug(SHCDevice):
    def __init__(self, api, raw_device):
        super().__init__(api, raw_device)

        self._service = self.device_service('PowerSwitch')

    def set_state(self, state: bool):
        self._service.put_state_element('state', state)

    def summary(self):
        print(f"PSM SmartPlug:")
        super().summary()
