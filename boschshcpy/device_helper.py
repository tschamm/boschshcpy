import logging
import typing

from .device import SHCDevice
from .models_impl import (
    SUPPORTED_MODELS,
    SHCBatteryDevice,
    SHCCamera360,
    SHCCameraEyes,
    SHCClimateControl,
    SHCLight,
    SHCMotionDetector,
    SHCShutterContact,
    SHCShutterControl,
    SHCSmartPlug,
    SHCSmartPlugCompact,
    SHCSmokeDetector,
    SHCSmokeDetectionSystem,
    SHCThermostat,
    SHCTwinguard,
    SHCUniversalSwitch,
    SHCWallThermostat,
    SHCWaterLeakageSensor,
    build,
)

logger = logging.getLogger("boschshcpy")


class SHCDeviceHelper:
    def __init__(self, api):
        self._api = api
        self._devices_by_model = {}
        for model in SUPPORTED_MODELS:
            self._devices_by_model[model] = {}

    def device_init(self, raw_device):
        device_id = raw_device["id"]
        device_model = raw_device["deviceModel"]
        device = []
        if device_model in SUPPORTED_MODELS:
            device = build(api=self._api, raw_device=raw_device)
            self._devices_by_model[device_model][device_id] = device
        else:
            device = SHCDevice(api=self._api, raw_device=raw_device)

        return device

    @property
    def shutter_contacts(self) -> typing.Sequence[SHCShutterContact]:
        if "SWD" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["SWD"].values())

    @property
    def shutter_controls(self) -> typing.Sequence[SHCShutterControl]:
        if "BBL" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["BBL"].values())

    @property
    def smart_plugs(self) -> typing.Sequence[SHCSmartPlug]:
        devices = []
        if "PSM" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["PSM"].values())
        if "BSM" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BSM"].values())
        return devices

    @property
    def smart_plugs_compact(self) -> typing.Sequence[SHCSmartPlugCompact]:
        if "PLUG_COMPACT" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model['PLUG_COMPACT'].values())

    @property
    def smoke_detectors(self) -> typing.Sequence[SHCSmokeDetector]:
        if "SD" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["SD"].values())

    @property
    def climate_controls(self) -> typing.Sequence[SHCClimateControl]:
        if "ROOM_CLIMATE_CONTROL" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["ROOM_CLIMATE_CONTROL"].values())

    @property
    def thermostats(self) -> typing.Sequence[SHCThermostat]:
        if "TRV" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["TRV"].values())

    @property
    def wallthermostats(self) -> typing.Sequence[SHCWallThermostat]:
        devices = []
        if "THB" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["THB"].values())
        if "BWTH" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BWTH"].values())
        return devices

    @property
    def motion_detectors(self) -> typing.Sequence[SHCMotionDetector]:
        if "MD" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["MD"].values())

    @property
    def twinguards(self) -> typing.Sequence[SHCTwinguard]:
        if "TWINGUARD" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["TWINGUARD"].values())

    @property
    def universal_switches(self) -> typing.Sequence[SHCUniversalSwitch]:
        if "WRC2" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["WRC2"].values())

    @property
    def camera_eyes(self) -> typing.Sequence[SHCCameraEyes]:
        if "CAMERA_EYES" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["CAMERA_EYES"].values())

    @property
    def camera_360(self) -> typing.Sequence[SHCCamera360]:
        if "CAMERA_360" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["CAMERA_360"].values())

    @property
    def ledvance_lights(self) -> typing.Sequence[SHCLight]:
        if "LEDVANCE_LIGHT" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["LEDVANCE_LIGHT"].values())

    @property
    def hue_lights(self) -> typing.Sequence[SHCLight]:
        if "HUE_LIGHT" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["HUE_LIGHT"].values())

    @property
    def water_leakage_detectors(self) -> typing.Sequence[SHCWaterLeakageSensor]:
        if "WATER_LEAKAGE_SENSOR" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["WATER_LEAKAGE_SENSOR"].values())

    @property
    def smoke_detection_system(self) -> typing.Sequence[SHCSmokeDetectionSystem]:
        if "SMOKE_DETECTION_SYSTEM" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["SMOKE_DETECTION_SYSTEM"].values())
