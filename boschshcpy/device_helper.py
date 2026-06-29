from __future__ import annotations

import logging
import typing
from typing import Any, cast

from .api import SHCAPI
from .device import SHCDevice
from .models_impl import SHCBatteryDevice  # noqa: F401  (re-export via __init__)
from .models_impl import SHCShutterContact2Plus  # noqa: F401  (re-export via __init__)
from .models_impl import SHCThermostatGen2  # noqa: F401  (re-export via __init__)
from .models_impl import (
    SUPPORTED_MODELS,
    SHCCamera360,
    SHCCameraEyes,
    SHCCameraOutdoorGen2,
    SHCClimateControl,
    SHCHeatingCircuit,
    SHCLight,
    SHCMotionDetector,
    SHCMotionDetector2,
    SHCShutterContact,
    SHCShutterContact2,
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
    SHCOutdoorSiren,
    SHCThermostat,
    SHCRoomThermostat2,
    SHCTwinguard,
    SHCUniversalSwitch,
    SHCWallThermostat,
    SHCWaterLeakageSensor,
    SHCMicromoduleDimmer,
    build,
)

logger = logging.getLogger("boschshcpy")

__all__ = [
    "SHCBatteryDevice",
    "SHCCamera360",
    "SHCCameraEyes",
    "SHCCameraOutdoorGen2",
    "SHCClimateControl",
    "SHCDeviceHelper",
    "SHCHeatingCircuit",
    "SHCLight",
    "SHCMotionDetector",
    "SHCMotionDetector2",
    "SHCShutterContact",
    "SHCShutterContact2",
    "SHCShutterContact2Plus",
    "SHCShutterControl",
    "SHCMicromoduleBlinds",
    "SHCMicromoduleDimmer",
    "SHCMicromoduleShutterControl",
    "SHCMicromoduleRelay",
    "SHCLightControl",
    "SHCLightSwitch",
    "SHCLightSwitchBSM",
    "SHCPresenceSimulationSystem",
    "SHCSmartPlug",
    "SHCSmartPlugCompact",
    "SHCSmokeDetector",
    "SHCSmokeDetectionSystem",
    "SHCOutdoorSiren",
    "SHCThermostat",
    "SHCThermostatGen2",
    "SHCRoomThermostat2",
    "SHCTwinguard",
    "SHCUniversalSwitch",
    "SHCWallThermostat",
    "SHCWaterLeakageSensor",
]


class SHCDeviceHelper:
    def __init__(self, api: SHCAPI) -> None:
        self._api = api
        self._devices_by_model: dict[str, dict[str, SHCDevice]] = {}
        for model in SUPPORTED_MODELS:
            self._devices_by_model[model] = {}

    def device_init(self, raw_device: dict[str, Any], device_services: list[dict[str, Any]]) -> SHCDevice:
        device_id = str(raw_device["id"])
        device_model = str(raw_device["deviceModel"])
        device: SHCDevice
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
        devices: list[SHCDevice] = []
        if "SWD" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWD"].values())
        return cast(typing.Sequence[SHCShutterContact], devices)

    @property
    def shutter_contacts2(self) -> typing.Sequence[SHCShutterContact2]:
        devices: list[SHCDevice] = []
        if "SWD2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWD2"].values())
        if "SWD2_PLUS" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWD2_PLUS"].values())
        if "SWD2_DUAL" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWD2_DUAL"].values())
        return cast(typing.Sequence[SHCShutterContact2], devices)

    @property
    def shutter_controls(self) -> typing.Sequence[SHCShutterControl]:
        devices: list[SHCDevice] = []
        if "BBL" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BBL"].values())
        return cast(typing.Sequence[SHCShutterControl], devices)

    @property
    def micromodule_shutter_controls(
        self,
    ) -> typing.Sequence[SHCMicromoduleShutterControl]:
        devices: list[SHCDevice] = []
        if "MICROMODULE_SHUTTER" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_SHUTTER"].values())
        if "MICROMODULE_AWNING" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_AWNING"].values())
        return cast(typing.Sequence[SHCMicromoduleShutterControl], devices)

    @property
    def micromodule_blinds(
        self,
    ) -> typing.Sequence[SHCMicromoduleBlinds]:
        devices: list[SHCDevice] = []
        if "MICROMODULE_BLINDS" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_BLINDS"].values())
        return cast(typing.Sequence[SHCMicromoduleBlinds], devices)

    @property
    def micromodule_relays(
        self,
    ) -> typing.Sequence[SHCMicromoduleRelay]:
        devices: list[SHCMicromoduleRelay] = []
        if "MICROMODULE_RELAY" in SUPPORTED_MODELS:
            for relay in self._devices_by_model["MICROMODULE_RELAY"].values():
                relay_typed = cast(SHCMicromoduleRelay, relay)
                if relay_typed.relay_type == SHCMicromoduleRelay.RelayType.SWITCH:
                    devices.append(relay_typed)
        return devices

    @property
    def micromodule_impulse_relays(
        self,
    ) -> typing.Sequence[SHCMicromoduleRelay]:
        devices: list[SHCMicromoduleRelay] = []
        if "MICROMODULE_RELAY" in SUPPORTED_MODELS:
            for relay in self._devices_by_model["MICROMODULE_RELAY"].values():
                relay_typed = cast(SHCMicromoduleRelay, relay)
                if relay_typed.relay_type == SHCMicromoduleRelay.RelayType.BUTTON:
                    devices.append(relay_typed)
        return devices

    @property
    def light_switches_bsm(self) -> typing.Sequence[SHCLightSwitchBSM]:
        devices: list[SHCDevice] = []
        if "BSM" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BSM"].values())
        return cast(typing.Sequence[SHCLightSwitchBSM], devices)

    @property
    def micromodule_light_attached(self) -> typing.Sequence[SHCLightSwitch]:
        devices: list[SHCDevice] = []
        if "MICROMODULE_LIGHT_ATTACHED" in SUPPORTED_MODELS:
            devices.extend(
                self._devices_by_model["MICROMODULE_LIGHT_ATTACHED"].values()
            )
        return cast(typing.Sequence[SHCLightSwitch], devices)

    @property
    def micromodule_light_controls(self) -> typing.Sequence[SHCLightControl]:
        devices: list[SHCDevice] = []
        if "MICROMODULE_LIGHT_CONTROL" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["MICROMODULE_LIGHT_CONTROL"].values())
        return cast(typing.Sequence[SHCLightControl], devices)

    @property
    def smart_plugs(self) -> typing.Sequence[SHCSmartPlug]:
        if "PSM" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCSmartPlug], list(self._devices_by_model["PSM"].values()))

    @property
    def smart_plugs_compact(self) -> typing.Sequence[SHCSmartPlugCompact]:
        devices: list[SHCDevice] = []
        if "PLUG_COMPACT" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["PLUG_COMPACT"].values())
        if "PLUG_COMPACT_DUAL" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["PLUG_COMPACT_DUAL"].values())
        return cast(typing.Sequence[SHCSmartPlugCompact], devices)

    @property
    def smoke_detectors(self) -> typing.Sequence[SHCSmokeDetector]:
        devices: list[SHCDevice] = []
        if "SD" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SD"].values())
        if "SMOKE_DETECTOR2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SMOKE_DETECTOR2"].values())
        return cast(typing.Sequence[SHCSmokeDetector], devices)

    @property
    def climate_controls(self) -> typing.Sequence[SHCClimateControl]:
        if "ROOM_CLIMATE_CONTROL" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCClimateControl], list(self._devices_by_model["ROOM_CLIMATE_CONTROL"].values()))

    @property
    def thermostats(self) -> typing.Sequence[SHCThermostat]:
        devices: list[SHCDevice] = []
        if "TRV" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["TRV"].values())
        if "TRV_GEN2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["TRV_GEN2"].values())
        if "TRV_GEN2_DUAL" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["TRV_GEN2_DUAL"].values())
        return cast(typing.Sequence[SHCThermostat], devices)

    @property
    def wallthermostats(self) -> typing.Sequence[SHCWallThermostat]:
        devices: list[SHCDevice] = []
        if "THB" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["THB"].values())
        if "BWTH" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BWTH"].values())
        if "BWTH24" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["BWTH24"].values())
        return cast(typing.Sequence[SHCWallThermostat], devices)

    @property
    def roomthermostats(self) -> typing.Sequence[SHCRoomThermostat2]:
        devices: list[SHCDevice] = []
        if "RTH2_BAT" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["RTH2_BAT"].values())
        if "RTH2_230" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["RTH2_230"].values())
        return cast(typing.Sequence[SHCRoomThermostat2], devices)

    @property
    def motion_detectors(self) -> typing.Sequence[SHCMotionDetector]:
        if "MD" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCMotionDetector], list(self._devices_by_model["MD"].values()))

    @property
    def motion_detectors2(self) -> typing.Sequence[SHCMotionDetector2]:
        if "MD2" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCMotionDetector2], list(self._devices_by_model["MD2"].values()))

    @property
    def twinguards(self) -> typing.Sequence[SHCTwinguard]:
        if "TWINGUARD" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCTwinguard], list(self._devices_by_model["TWINGUARD"].values()))

    @property
    def universal_switches(self) -> typing.Sequence[SHCUniversalSwitch]:
        devices: list[SHCDevice] = []
        if "WRC2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["WRC2"].values())
        if "SWITCH2" in SUPPORTED_MODELS:
            devices.extend(self._devices_by_model["SWITCH2"].values())
        return cast(typing.Sequence[SHCUniversalSwitch], devices)

    @property
    def camera_eyes(self) -> typing.Sequence[SHCCameraEyes]:
        if "CAMERA_EYES" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCCameraEyes], list(self._devices_by_model["CAMERA_EYES"].values()))

    @property
    def camera_360(self) -> typing.Sequence[SHCCamera360]:
        if "CAMERA_360" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCCamera360], list(self._devices_by_model["CAMERA_360"].values()))

    @property
    def camera_outdoor_gen2(self) -> typing.Sequence[SHCCameraOutdoorGen2]:
        if "CAMERA_OUTDOOR_GEN2" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCCameraOutdoorGen2], list(self._devices_by_model["CAMERA_OUTDOOR_GEN2"].values()))

    @property
    def ledvance_lights(self) -> typing.Sequence[SHCLight]:
        if "LEDVANCE_LIGHT" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCLight], list(self._devices_by_model["LEDVANCE_LIGHT"].values()))

    @property
    def hue_lights(self) -> typing.Sequence[SHCLight]:
        if "HUE_LIGHT" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCLight], list(self._devices_by_model["HUE_LIGHT"].values()))

    @property
    def water_leakage_detectors(self) -> typing.Sequence[SHCWaterLeakageSensor]:
        if "WLS" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCWaterLeakageSensor], list(self._devices_by_model["WLS"].values()))

    @property
    def presence_simulation_system(
        self,
    ) -> SHCPresenceSimulationSystem | None:
        if "PRESENCE_SIMULATION_SERVICE" not in SUPPORTED_MODELS:
            return None
        return cast(
            SHCPresenceSimulationSystem | None,
            self._devices_by_model["PRESENCE_SIMULATION_SERVICE"].get(
                "presenceSimulationService"
            ),
        )

    @property
    def smoke_detection_system(self) -> SHCSmokeDetectionSystem | None:
        if "SMOKE_DETECTION_SYSTEM" not in SUPPORTED_MODELS:
            return None
        return cast(
            SHCSmokeDetectionSystem | None,
            self._devices_by_model["SMOKE_DETECTION_SYSTEM"].get(
                "smokeDetectionSystem"
            ),
        )

    @property
    def heating_circuits(self) -> typing.Sequence[SHCHeatingCircuit]:
        if "HEATING_CIRCUIT" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCHeatingCircuit], list(self._devices_by_model["HEATING_CIRCUIT"].values()))

    @property
    def micromodule_dimmers(self) -> typing.Sequence[SHCMicromoduleDimmer]:
        if "MICROMODULE_DIMMER" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCMicromoduleDimmer], list(self._devices_by_model["MICROMODULE_DIMMER"].values()))

    @property
    def outdoor_sirens(self) -> typing.Sequence[SHCOutdoorSiren]:
        if "OUTDOOR_SIREN" not in SUPPORTED_MODELS:
            return []
        return cast(typing.Sequence[SHCOutdoorSiren], list(self._devices_by_model["OUTDOOR_SIREN"].values()))
