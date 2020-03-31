from enum import Enum
from .device import SHCDevice

class SHCShutterContact(SHCDevice):
    class DeviceClass(Enum):
        GENERIC = "GENERIC"
        ENTRANCE_DOOR = "ENTRANCE_DOOR"
        REGULAR_WINDOW = "REGULAR_WINDOW"
        FRENCH_WINDOW = "FRENCH_WINDOW"

    def __init__(self, api, raw_device):
        super().__init__(api, raw_device)

    @property
    def device_class(self) -> DeviceClass:
        return self.DeviceClass(self.profile)

    def summary(self):
        print(f"SWD ShutterContact:")
        super().summary()
