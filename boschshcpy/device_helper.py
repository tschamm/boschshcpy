import typing
import logging

from .device import SHCDevice
from .shutter_contact import SHCShutterContact
from .shutter_control import SHCShutterControl

MODEL_MAPPING = {
    "SWD": "ShutterContact",
    "BBL": "ShutterControl"
    }

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
        if device_model in SUPPORTED_MODELS:
            if device_model == 'SWD':
                device = SHCShutterContact(
                    api=self._api, raw_device=raw_device)
            elif device_model == 'BBL':
                device = SHCShutterControl(
                    api=self._api, raw_device=raw_device)
            else:
                device = SHCDevice(api=self._api, raw_device=raw_device)
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
