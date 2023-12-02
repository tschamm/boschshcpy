from __future__ import annotations

import logging
import typing

from .api import SHCAPI
from .device import SHCDevice
from .models_impl import (
    SUPPORTED_MODELS,
    SHCBatteryDevice,
    SHCCamera360,
    SHCCameraEyes,
    SHCClimateControl,
    SHCHeatingCircuit,
    SHCLight,
    SHCMotionDetector,
    SHCShutterContact,
    SHCShutterContact2,
    SHCShutterContact2Plus,
    SHCShutterControl,
    SHCMicromoduleBlinds,
    SHCMicromoduleRelay,
    SHCMicromoduleShutterControl,
    SHCLightControl,
    SHCLightSwitch,
    SHCLightSwitchBSM,
    SHCPresenceSimulationSystem,
    SHCSmartPlug,
    SHCSmartPlugCompact,
    SHCSmokeDetector,
    SHCSmokeDetectionSystem,
    SHCThermostat,
    SHCRoomThermostat2,
    SHCTwinguard,
    SHCUniversalSwitch,
    SHCWallThermostat,
    SHCWaterLeakageSensor,
    build,
)

logger = logging.getLogger("boschshcpy")


class SHCDeviceHelper:
    def __init__(self, api: SHCAPI) -> None:
        self._api = api
        self._devices_by_model: dict[str, dict[str, SHCDevice]] = {}
        for model in SUPPORTED_MODELS:
            self._devices_by_model[model] = {}

    def device_init(self, raw_device, device_services) -> SHCDevice:
        device_id = raw_device["id"]
        device_model = raw_device["deviceModel"]
        device = []
        if device_model in SUPPORTED_MODELS:
            device = build(
                api=self._api,
                raw_device=raw_device,
                raw_device_services=device_services,
            )
            self._devices_by_model[device_model][device_id] = device
        else:
            device = SHCDevice(
                api=self._api,
                raw_device=raw_device,
                raw_device_services=device_services,
            )

        return device

    @property
    def shutter_contacts(self) -> typing.Sequence[SHCShutterContact]:
        devices = []
        if "SWD" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWD"].values())
        return devices

    @property
    def shutter_contacts2(self) -> typing.Sequence[SHCShutterContact2]:
        devices = []
        if "SWD2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWD2"].values())
        if "SWD2_PLUS" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWD2_PLUS"].values())
        return devices

    @property
    def shutter_controls(self) -> typing.Sequence[SHCShutterControl]:
        devices = []
        if "BBL" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BBL"].values())
        return devices

    @property
    def micromodule_shutter_controls(
        self,
    ) -> typing.Sequence[SHCMicromoduleShutterControl]:
        devices = []
        if "MICROMODULE_SHUTTER" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_SHUTTER"].values())
        if "MICROMODULE_AWNING" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_AWNING"].values())
        return devices

    @property
    def micromodule_blinds(
        self,
    ) -> typing.Sequence[SHCMicromoduleBlinds]:
        devices = []
        if "MICROMODULE_BLINDS" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_BLINDS"].values())
        return devices

    @property
    def micromodule_relays(
        self,
    ) -> typing.Sequence[SHCMicromoduleRelay]:
        devices = []
        if "MICROMODULE_RELAY" in SUPPORTED_MODELS:
            for relay in self._devices_by_model["MICROMODULE_RELAY"].values():
                if relay.relay_type == SHCMicromoduleRelay.RelayType.SWITCH:
                    devices.extend([relay])
        return devices

    @property
    def micromodule_impulse_relays(
        self,
    ) -> typing.Sequence[SHCMicromoduleRelay]:
        devices = []
        if "MICROMODULE_RELAY" in SUPPORTED_MODELS:
            for relay in self._devices_by_model["MICROMODULE_RELAY"].values():
                if relay.relay_type == SHCMicromoduleRelay.RelayType.BUTTON:
                    devices.extend([relay])
        return devices

    @property
    def light_switches_bsm(self) -> typing.Sequence[SHCLightSwitchBSM]:
        devices = []
        if "BSM" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BSM"].values())
        return devices

    @property
    def micromodule_light_attached(self) -> typing.Sequence[SHCLightSwitch]:
        devices = []
        if "MICROMODULE_LIGHT_ATTACHED" in SUPPORTED_MODELS:
            devices.extend(
                self._devices_by_model["MICROMODULE_LIGHT_ATTACHED"].values()
            )
        return devices

    @property
    def micromodule_light_controls(self) -> typing.Sequence[SHCLightControl]:
        devices = []
        if "MICROMODULE_LIGHT_CONTROL" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_LIGHT_CONTROL"].values())
        return devices

    @property
    def smart_plugs(self) -> typing.Sequence[SHCSmartPlug]:
        if "PSM" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["PSM"].values())

    @property
    def smart_plugs_compact(self) -> typing.Sequence[SHCSmartPlugCompact]:
        if "PLUG_COMPACT" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["PLUG_COMPACT"].values())

    @property
    def smoke_detectors(self) -> typing.Sequence[SHCSmokeDetector]:
        devices = []
        if "SD" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SD"].values())
        if "SMOKE_DETECTOR2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SMOKE_DETECTOR2"].values())
        return devices

    @property
    def climate_controls(self) -> typing.Sequence[SHCClimateControl]:
        if "ROOM_CLIMATE_CONTROL" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["ROOM_CLIMATE_CONTROL"].values())

    @property
    def thermostats(self) -> typing.Sequence[SHCThermostat]:
        devices = []
        if "TRV" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["TRV"].values())
        if "TRV_GEN2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["TRV_GEN2"].values())
        return devices

    @property
    def wallthermostats(self) -> typing.Sequence[SHCWallThermostat]:
        devices = []
        if "THB" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["THB"].values())
        if "BWTH" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BWTH"].values())
        return devices

    @property
    def roomthermostats(self) -> typing.Sequence[SHCRoomThermostat2]:
        devices = []
        if "RTH2_BAT" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["RTH2_BAT"].values())
        if "RTH2_230" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["RTH2_230"].values())
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
        devices = []
        if "WRC2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["WRC2"].values())
        if "SWITCH2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWITCH2"].values())
        return devices

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
        if "WLS" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["WLS"].values())

    @property
    def presence_simulation_system(
        self,
    ) -> SHCPresenceSimulationSystem:
        if "PRESENCE_SIMULATION_SERVICE" not in SUPPORTED_MODELS:
            return None
        return (
            self._devices_by_model["PRESENCE_SIMULATION_SERVICE"][
                "presenceSimulationService"
            ]
            if "presenceSimulationService"
            in self._devices_by_model["PRESENCE_SIMULATION_SERVICE"]
            else None
        )

    @property
    def smoke_detection_system(self) -> SHCSmokeDetectionSystem:
        if "SMOKE_DETECTION_SYSTEM" not in SUPPORTED_MODELS:
            return None
        return (
            self._devices_by_model["SMOKE_DETECTION_SYSTEM"]["smokeDetectionSystem"]
            if "smokeDetectionSystem"
            in self._devices_by_model["SMOKE_DETECTION_SYSTEM"]
            else None
        )

    @property
    def heating_circuits(self) -> typing.Sequence[SHCHeatingCircuit]:
        if "HEATING_CIRCUIT" not in SUPPORTED_MODELS:
            return []
        return list(self._devices_by_model["HEATING_CIRCUIT"].values())
