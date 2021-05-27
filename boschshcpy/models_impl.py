import asyncio
from enum import Enum, Flag, auto

from .device import SHCDevice
from .services_impl import (
    BatteryLevelService,
    BinarySwitchService,
    CameraLightService,
    HumidityLevelService,
    ShutterContactService,
    ShutterControlService,
    SurveillanceAlarmService,
    TemperatureLevelService,
    ValveTappetService,
    WaterLeakageSensorCheckService,
    WaterLeakageSensorService,
    WaterLeakageSensorTiltService,
)


class SHCBatteryDevice(SHCDevice):
    from .services_impl import BatteryLevelService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._batterylevel_service = self.device_service("BatteryLevel")

    @property
    def supports_batterylevel(self):
        return self._batterylevel_service is not None

    @property
    def batterylevel(self) -> BatteryLevelService.State:
        if self.supports_batterylevel:
            return self._batterylevel_service.warningLevel
        return BatteryLevelService.State.NOT_AVAILABLE

    async def async_update(self):
        if self.supports_batterylevel:
            await self._batterylevel_service.async_short_poll()


class SHCSmokeDetector(SHCBatteryDevice):
    from .services_impl import AlarmService, SmokeDetectorCheckService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._alarm_service = self.device_service("Alarm")
        self._smokedetectorcheck_service = self.device_service("SmokeDetectorCheck")

    @property
    def alarmstate(self) -> AlarmService.State:
        return self._alarm_service.value

    async def async_set_alarmstate(self, state: str):
        await self._alarm_service.async_put_state_element("value", state)

    @property
    def smokedetectorcheck_state(self) -> SmokeDetectorCheckService.State:
        return self._smokedetectorcheck_service.value

    def smoketest_requested(self):
        self._smokedetectorcheck_service.put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    async def async_update(self):
        await self._alarm_service.async_short_poll()
        await self._smokedetectorcheck_service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"SD SmokeDetector:")
        super().summary()


class SHCSmartPlug(SHCDevice):
    from .services_impl import (
        PowerMeterService,
        PowerSwitchProgramService,
        PowerSwitchService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._powerswitch_service = self.device_service("PowerSwitch")
        self._powerswitchprogram_service = self.device_service("PowerSwitchProgram")
        self._powermeter_service = self.device_service("PowerMeter")

    @property
    def state(self) -> PowerSwitchService.State:
        return self._powerswitch_service.value

    async def async_set_state(self, state: bool):
        await self._powerswitch_service.async_put_state_element(
            "switchState", "ON" if state else "OFF"
        )

    @property
    def energyconsumption(self) -> float:
        return self._powermeter_service.energyconsumption

    @property
    def powerconsumption(self) -> float:
        return self._powermeter_service.powerconsumption

    async def async_update(self):
        await self._powerswitch_service.async_short_poll()
        await self._powerswitchprogram_service.async_short_poll()
        await self._powermeter_service.async_short_poll()

    def summary(self):
        print(f"PSM/BSM SmartPlug:")
        super().summary()


class SHCSmartPlugCompact(SHCDevice):
    from .services_impl import (
        CommunicationQualityService,
        PowerMeterService,
        PowerSwitchProgramService,
        PowerSwitchService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._powerswitch_service = self.device_service("PowerSwitch")
        self._powerswitchprogram_service = self.device_service("PowerSwitchProgram")
        self._powermeter_service = self.device_service("PowerMeter")
        self._communicationquality_service = self.device_service("CommunicationQuality")

    @property
    def state(self) -> PowerSwitchService.State:
        return self._powerswitch_service.value

    async def async_set_state(self, state: bool):
        await self._powerswitch_service.async_put_state_element(
            "switchState", "ON" if state else "OFF"
        )

    @property
    def energyconsumption(self) -> float:
        return self._powermeter_service.energyconsumption

    @property
    def powerconsumption(self) -> float:
        return self._powermeter_service.powerconsumption

    @property
    def communicationquality(self) -> CommunicationQualityService.State:
        return self._communicationquality_service.value

    async def async_update(self):
        await self._powerswitch_service.async_short_poll()
        await self._powerswitchprogram_service.async_short_poll()
        await self._powermeter_service.async_short_poll()
        await self._communicationquality_service.async_short_poll()

    def summary(self):
        print(f"PLUG_COMPACT SmartPlugCompact:")
        super().summary()


class SHCShutterControl(SHCDevice):
    from .services_impl import ShutterControlService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._service = self.device_service("ShutterControl")

    @property
    def level(self) -> float:
        return self._service.level

    async def async_set_level(self, level):
        await self._service.async_put_state_element("level", level)

    async def async_stop(self):
        await self._service.async_put_state_element(
            "operationState", ShutterControlService.State.STOPPED.name
        )

    @property
    def operation_state(self) -> ShutterControlService.State:
        return self._service.value

    async def async_update(self):
        await self._service.async_short_poll()

    def summary(self):
        print(f"BBL ShutterControl:")
        super().summary()


class SHCShutterContact(SHCBatteryDevice):
    from .services_impl import ShutterContactService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._service = self.device_service("ShutterContact")

    @property
    def device_class(self) -> str:
        return self.profile

    @property
    def state(self) -> ShutterContactService.State:
        return self._service.value

    async def async_update(self):
        await self._service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"SWD ShutterContact:")
        super().summary()


class SHCCameraEyes(SHCDevice):
    from .services_impl import CameraLightService, CameraNotificationService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._cameranotification_service = self.device_service("CameraNotification")
        self._cameralight_service = self.device_service("CameraLight")

    @property
    def cameranotification(self) -> CameraNotificationService.State:
        return self._cameranotification_service.value

    async def async_set_cameranotification(self, state: bool):
        await self._cameranotification_service.async_put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    @property
    def cameralight(self) -> CameraLightService.State:
        return self._cameralight_service.value

    async def async_set_cameralight(self, state: bool):
        await self._cameralight_service.async_put_state_element(
            "value", "ON" if state else "OFF"
        )

    async def async_update(self):
        await self._cameralight_service.async_short_poll()
        await self._cameranotification_service.async_short_poll()

    def summary(self):
        print(f"CAMERA_EYES CameraEyes:")
        super().summary()


class SHCCamera360(SHCDevice):
    from .services_impl import CameraNotificationService, PrivacyModeService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._privacymode_service = self.device_service("PrivacyMode")
        self._cameranotification_service = self.device_service("CameraNotification")

    @property
    def privacymode(self) -> PrivacyModeService.State:
        return self._privacymode_service.value

    async def async_set_privacymode(self, state: bool):
        await self._privacymode_service.async_put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    @property
    def cameranotification(self) -> CameraNotificationService.State:
        return self._cameranotification_service.value

    async def async_set_cameranotification(self, state: bool):
        await self._cameranotification_service.async_put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    async def async_update(self):
        await self._cameranotification_service.async_short_poll()
        await self._privacymode_service.async_short_poll()

    def summary(self):
        print(f"CAMERA_360 Camera360:")
        super().summary()


class SHCThermostat(SHCBatteryDevice):
    from .services_impl import TemperatureLevelService, ValveTappetService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._temperaturelevel_service = self.device_service("TemperatureLevel")
        self._valvetappet_service = self.device_service("ValveTappet")

    @property
    def position(self) -> int:
        return self._valvetappet_service.position

    @property
    def valvestate(self) -> ValveTappetService.State:
        return self._valvetappet_service.value

    @property
    def temperature(self) -> float:
        return self._temperaturelevel_service.temperature

    async def async_update(self):
        await self._temperaturelevel_service.async_short_poll()
        await self._valvetappet_service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"TRV Thermostat:")
        super().summary()


class SHCClimateControl(SHCDevice):
    from .services_impl import RoomClimateControlService, TemperatureLevelService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._temperaturelevel_service = self.device_service("TemperatureLevel")
        self._roomclimatecontrol_service = self.device_service("RoomClimateControl")

    @property
    def setpoint_temperature(self) -> float:
        return self._roomclimatecontrol_service.setpoint_temperature

    async def async_set_setpoint_temperature(self, temperature: float):
        await self._roomclimatecontrol_service.async_set_setpoint_temperature(
            temperature
        )

    @property
    def operation_mode(self) -> RoomClimateControlService.OperationMode:
        return self._roomclimatecontrol_service.operation_mode

    async def async_set_operation_mode(
        self, mode: RoomClimateControlService.OperationMode
    ):
        await self._roomclimatecontrol_service.async_set_operation_mode(mode)

    @property
    def boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.boost_mode

    async def async_set_boost_mode(self, value: bool):
        await self._roomclimatecontrol_service.async_set_boost_mode(value)

    @property
    def supports_boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.supports_boost_mode

    @property
    def low(self) -> bool:
        return self._roomclimatecontrol_service.low

    async def async_set_low(self, value: bool):
        await self._roomclimatecontrol_service.async_set_low(value)

    @property
    def summer_mode(self) -> bool:
        return self._roomclimatecontrol_service.summer_mode

    async def async_set_summer_mode(self, value: bool):
        await self._roomclimatecontrol_service.async_set_summer_mode(value)

    @property
    def temperature(self) -> float:
        return self._temperaturelevel_service.temperature

    async def async_update(self):
        await self._temperaturelevel_service.async_short_poll()
        await self._roomclimatecontrol_service.async_short_poll()

    def summary(self):
        print(f"ROOM_CLIMATE_CONTROL:")
        super().summary()


class SHCWallThermostat(SHCBatteryDevice):
    from .services_impl import HumidityLevelService, TemperatureLevelService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._temperaturelevel_service = self.device_service("TemperatureLevel")
        self._humiditylevel_service = self.device_service("HumidityLevel")

    @property
    def temperature(self) -> float:
        return self._temperaturelevel_service.temperature

    @property
    def humidity(self) -> float:
        return self._humiditylevel_service.humidity

    async def async_update(self):
        await self._temperaturelevel_service.async_short_poll()
        await self._humiditylevel_service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"THB/BWTH Wall Thermostat:")
        super().summary()


class SHCUniversalSwitch(SHCBatteryDevice):
    from .services_impl import KeypadService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._keypad_service = self.device_service("Keypad")

    @property
    def keycode(self) -> int:
        return self._keypad_service.keyCode

    @property
    def keyname(self) -> KeypadService.KeyState:
        return self._keypad_service.keyName

    @property
    def eventtype(self) -> KeypadService.KeyEvent:
        return self._keypad_service.eventType

    @property
    def eventtimestamp(self) -> int:
        return self._keypad_service.eventTimestamp

    async def async_update(self):
        await self._keypad_service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"WRC2 Universal Switch:")
        super().summary()


class SHCMotionDetector(SHCBatteryDevice):
    from .services_impl import LatestMotionService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._service = self.device_service("LatestMotion")

    @property
    def latestmotion(self) -> str:
        return self._service.latestMotionDetected

    async def async_update(self):
        await self._service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"MD Motion Detector:")
        super().summary()


class SHCTwinguard(SHCBatteryDevice):
    from .services_impl import AirQualityLevelService, SmokeDetectorCheckService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._airqualitylevel_service = self.device_service("AirQualityLevel")
        self._smokedetectorcheck_service = self.device_service("SmokeDetectorCheck")

    @property
    def description(self) -> str:
        return self._airqualitylevel_service.description

    @property
    def combined_rating(self) -> AirQualityLevelService.RatingState:
        return self._airqualitylevel_service.combinedRating

    @property
    def temperature(self) -> int:
        return self._airqualitylevel_service.temperature

    @property
    def temperature_rating(self) -> AirQualityLevelService.RatingState:
        return self._airqualitylevel_service.temperatureRating

    @property
    def humidity(self) -> int:
        return self._airqualitylevel_service.humidity

    @property
    def humidity_rating(self) -> AirQualityLevelService.RatingState:
        return self._airqualitylevel_service.humidityRating

    @property
    def purity(self) -> int:
        return self._airqualitylevel_service.purity

    @property
    def purity_rating(self) -> AirQualityLevelService.RatingState:
        return self._airqualitylevel_service.purityRating

    @property
    def smokedetectorcheck_state(self) -> SmokeDetectorCheckService.State:
        return self._smokedetectorcheck_service.value

    def smoketest_requested(self):
        self._smokedetectorcheck_service.put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    async def async_update(self):
        await self._airqualitylevel_service.async_short_poll()
        await self._smokedetectorcheck_service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"TWINGUARD:")
        super().summary()


class SHCSmokeDetectionSystem(SHCDevice):
    from .services_impl import SurveillanceAlarmService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._surveillancealarm_service = self.device_service("SurveillanceAlarm")

    @property
    def alarm(self) -> SurveillanceAlarmService.State:
        return self._surveillancealarm_service.value

    async def async_update(self):
        await self._surveillancealarm_service.async_short_poll()

    def summary(self):
        print(f"SMOKE_DETECTION_SYSTEM:")
        super().summary()


class SHCLight(SHCDevice):
    from .services_impl import (
        BinarySwitchService,
        HSBColorActuatorService,
        HueColorTemperatureService,
        MultiLevelSwitchService,
    )

    class Capabilities(Flag):
        BRIGHTNESS = auto()
        COLOR_TEMP = auto()
        COLOR_HSB = auto()

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._binaryswitch_service = self.device_service("BinarySwitch")
        self._multilevelswitch_service = self.device_service("MultiLevelSwitch")
        self._huecolortemperature_service = self.device_service("HueColorTemperature")
        self._hsbcoloractuator_service = self.device_service("HSBColorActuator")

        self._capabilities = self.Capabilities(0)
        if self._multilevelswitch_service:
            self._capabilities |= self.Capabilities.BRIGHTNESS
        if self._huecolortemperature_service:
            self._capabilities |= self.Capabilities.COLOR_TEMP
        if self._hsbcoloractuator_service:
            self._capabilities |= self.Capabilities.COLOR_HSB

    @property
    def state(self) -> bool:
        return self._binaryswitch_service.value

    async def async_set_state(self, state: bool):
        await self._binaryswitch_service.async_put_state_element(
            "on", True if state else False
        )

    @property
    def brightness(self) -> int:
        if (
            self._capabilities & self.Capabilities.BRIGHTNESS
        ) == self.Capabilities.BRIGHTNESS:
            return self._multilevelswitch_service.value
        return 0

    async def async_set_brightness(self, state: int):
        if (
            self._capabilities & self.Capabilities.BRIGHTNESS
        ) == self.Capabilities.BRIGHTNESS:
            await self._multilevelswitch_service.async_put_state_element("level", state)

    @property
    def color(self) -> int:
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            return self._huecolortemperature_service.value
        return 0

    async def async_set_color(self, state: int):
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            await self._huecolortemperature_service.async_put_state_element(
                "colorTemperature", state
            )

    @property
    def rgb(self) -> int:
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            return self._hsbcoloractuator_service.value
        return 0

    async def async_set_rgb(self, state: int):
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            await self._hsbcoloractuator_service.async_put_state_element("rgb", state)

    @property
    def min_color_temperature(self) -> int:
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            return self._huecolortemperature_service.min_value
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            return self._hsbcoloractuator_service.min_value
        return 0

    @property
    def max_color_temperature(self) -> int:
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            return self._huecolortemperature_service.max_value
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            return self._hsbcoloractuator_service.max_value
        return 0

    @property
    def supports_brightness(self) -> bool:
        return (
            self._capabilities & self.Capabilities.BRIGHTNESS
        ) == self.Capabilities.BRIGHTNESS

    @property
    def supports_color_temp(self) -> bool:
        return (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP

    @property
    def supports_color_hsb(self) -> bool:
        return (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB

    async def async_update(self):
        await self._binaryswitch_service.async_short_poll()
        if (
            self._capabilities & self.Capabilities.BRIGHTNESS
        ) == self.Capabilities.BRIGHTNESS:
            await self._multilevelswitch_service.async_short_poll()
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            await self._huecolortemperature_service.async_short_poll()
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            await self._hsbcoloractuator_service.async_short_poll()

    def summary(self):
        print(f"HUE/LEDVANCE Light:")
        print(f"  Capabilities               : {self._capabilities}")
        super().summary()


class SHCWaterLeakageSensor(SHCBatteryDevice):
    from .services_impl import WaterLeakageSensorService, WaterLeakageSensorTiltService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._leakage_service = self.device_service("WaterLeakageSensor")
        self._tilt_service = self.device_service("WaterLeakageSensorTilt")
        self._sensor_check_service = self.device_service("WaterLeakageSensorCheck")

    @property
    def leakage_state(self) -> WaterLeakageSensorService.State:
        return self._leakage_service.value

    @property
    def acoustic_signal_state(self) -> WaterLeakageSensorTiltService.State:
        return self._tilt_service.acousticSignalState

    @property
    def push_notification_state(self) -> WaterLeakageSensorTiltService.State:
        return self._tilt_service.pushNotificationState

    @property
    def sensor_check_state(self) -> str:
        return self._sensor_check_service.value

    async def async_update(self):
        await self._leakage_service.async_short_poll()
        await self._tilt_service.async_short_poll()
        await self._sensor_check_service.async_short_poll()
        await super().async_update()

    def summary(self):
        print(f"WLS:")
        super().summary()


MODEL_MAPPING = {
    "SWD": SHCShutterContact,
    "BBL": SHCShutterControl,
    "PSM": SHCSmartPlug,
    "BSM": SHCSmartPlug,
    "PLUG_COMPACT": SHCSmartPlugCompact,
    "SD": SHCSmokeDetector,
    "CAMERA_EYES": SHCCameraEyes,
    "CAMERA_360": SHCCamera360,
    "ROOM_CLIMATE_CONTROL": SHCClimateControl,
    "TRV": SHCThermostat,
    "THB": SHCWallThermostat,
    "BWTH": SHCWallThermostat,
    "WRC2": SHCUniversalSwitch,
    "MD": SHCMotionDetector,
    "TWINGUARD": SHCTwinguard,
    "SMOKE_DETECTION_SYSTEM": SHCSmokeDetectionSystem,
    "LEDVANCE_LIGHT": SHCLight,
    "HUE_LIGHT": SHCLight,
    "WLS": SHCWaterLeakageSensor,
}

SUPPORTED_MODELS = MODEL_MAPPING.keys()


def build(api, raw_device, raw_device_services):
    device_model = raw_device["deviceModel"]
    assert device_model in SUPPORTED_MODELS, "Device model is supported"
    return MODEL_MAPPING[device_model](
        api=api, raw_device=raw_device, raw_device_services=raw_device_services
    )
