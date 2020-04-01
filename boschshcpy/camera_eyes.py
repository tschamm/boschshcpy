from enum import Enum
from .device import SHCDevice
from .services_impl import CameraLightService


class SHCCameraEyes(SHCDevice):
    def __init__(self, api, raw_device):
        super().__init__(api, raw_device)

        self._privacymode_service = self.device_service('PrivacyMode')
        self._cameranotification_service = self.device_service('CameraNotification')
        self._cameralight_service = self.device_service('CameraLight')

    def set_privacymode(self, state: bool):
        self._privacymode_service.put_state_element(
            'value', "ENABLED" if state else "DISABLED")

    def set_cameranotification(self, state: bool):
        self._cameranotification_service.put_state_element(
            'value', "ENABLED" if state else "DISABLED")

    def set_cameralight(self, state: bool):
        self._cameralight_service.put_state_element(
            'value', "ON" if state else "OFF")
    
    @property
    def get_light_state(self) -> CameraLightService.State:
        self._cameralight_service.short_poll()
        return self._cameralight_service.value

    def summary(self):
        print(f"CAMERA_EYES CameraEyes:")
        super().summary()
