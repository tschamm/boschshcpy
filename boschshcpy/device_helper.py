import logging
import typing

from .device import SHCDevice
from .models_impl import (SUPPORTED_MODELS, SHCCameraEyes,
                          SHCIntrusionDetectionSystem, SHCShutterContact,
                          SHCShutterControl, SHCSmartPlug, SHCSmokeDetector,
                          SHCThermostat, SHCUniversalSwitch, SHCMotionDetector)

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
            'BSM': lambda: SHCSmartPlug(api=self._api, raw_device=raw_device),
            'SD': lambda: SHCSmokeDetector(api=self._api, raw_device=raw_device),
            'TRV': lambda: SHCThermostat(api=self._api, raw_device=raw_device),
            'MD': lambda: SHCMotionDetector(api=self._api, raw_device=raw_device),
            'WRC2': lambda: SHCUniversalSwitch(api=self._api, raw_device=raw_device),
            'CAMERA_EYES': lambda: SHCCameraEyes(api=self._api, raw_device=raw_device),
            'INTRUSION_DETECTION_SYSTEM': lambda: SHCIntrusionDetectionSystem(api=self._api, raw_device=raw_device),
        }
        if device_model in switcher and device_model in SUPPORTED_MODELS:
            device = switcher[device_model]()
            self._devices_by_model[device_model][device_id] = device
        else:
            device = SHCDevice(api=self._api, raw_device=raw_device)

        return device

    @property
    def shutter_contacts(self) -> typing.Sequence[SHCShutterContact]:
        if 'SWD' not in SUPPORTED_MODELS: 
            return []
        return list(self._devices_by_model['SWD'].values())

    @property
    def shutter_controls(self) -> typing.Sequence[SHCShutterControl]:
        if 'BBL' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['BBL'].values())

    @property
    def smart_plugs(self) -> typing.Sequence[SHCSmartPlug]:
        if 'PSM' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['PSM'].values())

    @property
    def light_controls(self) -> typing.Sequence[SHCSmartPlug]:
        if 'BSM' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['BSM'].values())

    @property
    def smoke_detectors(self) -> typing.Sequence[SHCSmokeDetector]:
        if 'SD' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['SD'].values())

    @property
    def thermostats(self) -> typing.Sequence[SHCThermostat]:
        if 'TRV' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['TRV'].values())

    @property
    def motion_detectors(self) -> typing.Sequence[SHCMotionDetector]:
        if 'MD' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['MD'].values())

    @property
    def universal_switches(self) -> typing.Sequence[SHCUniversalSwitch]:
        if 'WRC2' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['WRC'].values())

    @property
    def camera_eyes(self) -> typing.Sequence[SHCCameraEyes]:
        if 'CAMERA_EYES' not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['CAMERA_EYES'].values())

    @property
    def intrusion_detection_system(self) -> SHCIntrusionDetectionSystem:
        if 'INTRUSION_DETECTION_SYSTEM' not in SUPPORTED_MODELS:
            return None
        return list(self._devices_by_model['INTRUSION_DETECTION_SYSTEM'].values())[0]
