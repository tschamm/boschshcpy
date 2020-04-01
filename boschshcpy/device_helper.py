import typing
import logging

from .device import SHCDevice
from .shutter_contact import SHCShutterContact
from .shutter_control import SHCShutterControl
from .smart_plug import SHCSmartPlug
from .smoke_detector import SHCSmokeDetector
from .camera_eyes import SHCCameraEyes

MODEL_MAPPING = {
    "SWD": "ShutterContact",
    "BBL": "ShutterControl",
    "PSM": "SmartPlug",
    "SD": "SmokeDetector",
    "CAMERA_EYES": "CameraEyes",
}
    # "WRC2": "UniversalSwitchFlex",
    # "BSM": "LightControl",
    # "MD": "MotionDetector"

SUPPORTED_MODELS = MODEL_MAPPING.keys()

logger = logging.getLogger("boschshcpy")


class SHCDeviceHelper:
    def __init__(self, api):
        self._api = api
        self._devices_by_model = {}
        for model in SUPPORTED_MODELS:
            self._devices_by_model[model] = {}

    def device_init(self, raw_device):
        device_id = raw_device['id']
        device_model = raw_device['deviceModel']

        device = None
        switcher = {
            'SWD': lambda: SHCShutterContact(api=self._api, raw_device=raw_device),
            'BBL': lambda: SHCShutterControl(api=self._api, raw_device=raw_device),
            'PSM': lambda: SHCSmartPlug(api=self._api, raw_device=raw_device),
            'SD': lambda: SHCSmokeDetector(api=self._api, raw_device=raw_device),
            'CAMERA_EYES': lambda: SHCCameraEyes(api=self._api, raw_device=raw_device)
        }
        if device_model in switcher and device_model in SUPPORTED_MODELS:
            device = switcher[device_model]()
            self._devices_by_model[device_model][device_id] = device
        else:
            device = SHCDevice(api=self._api, raw_device=raw_device)

        return device

    @property
    def devices_by_model(self, model):
        if model not in SUPPORTED_MODELS:
            return {}
        return self._devices_by_model[model]

    @property
    def shutter_contacts(self) -> typing.Sequence[SHCShutterContact]:
        return list(self._devices_by_model['SWD'].values())

    @property
    def shutter_controls(self) -> typing.Sequence[SHCShutterControl]:
        return list(self._devices_by_model['BBL'].values())

    @property
    def smart_plugs(self) -> typing.Sequence[SHCSmartPlug]:
        return list(self._devices_by_model['PSM'].values())

    @property
    def smoke_detectors(self) -> typing.Sequence[SHCSmokeDetector]:
        return list(self._devices_by_model['SD'].values())

    @property
    def camera_eyes(self) -> typing.Sequence[SHCCameraEyes]:
        return list(self._devices_by_model['CAMERA_EYES'].values())
