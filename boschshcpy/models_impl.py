from enum import Enum, Flag, auto

from .device import SHCDevice
from .services_impl import (
    BatteryLevelService,
    BinarySwitchService,
    CameraLightService,
    HumidityLevelService,
    RoutingService,
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

    def update(self):
        if self.supports_batterylevel:
            self._batterylevel_service.short_poll()


class SHCSmokeDetector(SHCBatteryDevice):
    from .services_impl import AlarmService, SmokeDetectorCheckService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._alarm_service = self.device_service("Alarm")
        self._smokedetectorcheck_service = self.device_service("SmokeDetectorCheck")

    @property
    def alarmstate(self) -> AlarmService.State:
        return self._alarm_service.value

    @alarmstate.setter
    def alarmstate(self, state: str):
        self._alarm_service.put_state_element("value", state)

    @property
    def smokedetectorcheck_state(self) -> SmokeDetectorCheckService.State:
        return self._smokedetectorcheck_service.value

    def smoketest_requested(self):
        self._smokedetectorcheck_service.put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    def update(self):
        self._alarm_service.short_poll()
        self._smokedetectorcheck_service.short_poll()
        super().update()

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
        self._routing_service = self.device_service("Routing")
        self._powerswitchprogram_service = self.device_service("PowerSwitchProgram")
        self._powermeter_service = self.device_service("PowerMeter")

    @property
    def state(self) -> PowerSwitchService.State:
        return self._powerswitch_service.value

    @state.setter
    def state(self, state: bool):
        self._powerswitch_service.put_state_element(
            "switchState", "ON" if state else "OFF"
        )

    @property
    def routing(self) -> RoutingService.State:
        return self._routing_service.value

    @routing.setter
    def routing(self, state: bool):
        self._routing_service.put_state_element(
            "routingState", "ENABLED" if state else "DISABLED"
        )

    @property
    def energyconsumption(self) -> float:
        return self._powermeter_service.energyconsumption

    @property
    def powerconsumption(self) -> float:
        return self._powermeter_service.powerconsumption

    def update(self):
        self._powerswitch_service.short_poll()
        self._powerswitchprogram_service.short_poll()
        self._powermeter_service.short_poll()

    def summary(self):
        print(f"PSM SmartPlug:")
        super().summary()


class SHCSmartPlugCompact(SHCDevice):
    from .services_impl import (
        PowerMeterService,
        PowerSwitchProgramService,
        PowerSwitchService,
        CommunicationQualityService,
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

    @state.setter
    def state(self, state: bool):
        self._powerswitch_service.put_state_element(
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

    def update(self):
        self._powerswitch_service.short_poll()
        self._powerswitchprogram_service.short_poll()
        self._powermeter_service.short_poll()
        self._communicationquality_service.short_poll()

    def summary(self):
        print(f"PLUG_COMPACT SmartPlugCompact:")
        super().summary()


class SHCLightSwitch(SHCDevice):
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

    @state.setter
    def state(self, state: bool):
        self._powerswitch_service.put_state_element(
            "switchState", "ON" if state else "OFF"
        )

    @property
    def energyconsumption(self) -> float:
        return self._powermeter_service.energyconsumption

    @property
    def powerconsumption(self) -> float:
        return self._powermeter_service.powerconsumption

    def update(self):
        self._powerswitch_service.short_poll()
        self._powerswitchprogram_service.short_poll()
        self._powermeter_service.short_poll()

    def summary(self):
        print(f"BSM LightSwitch:")
        super().summary()


class SHCShutterControl(SHCDevice):
    from .services_impl import ShutterControlService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._service = self.device_service("ShutterControl")

    @property
    def level(self) -> float:
        return self._service.level

    @level.setter
    def level(self, level):
        self._service.put_state_element("level", level)

    def stop(self):
        self._service.put_state_element(
            "operationState", ShutterControlService.State.STOPPED.name
        )

    @property
    def operation_state(self) -> ShutterControlService.State:
        return self._service.value

    def update(self):
        self._service.short_poll()

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

    def update(self):
        self._service.short_poll()
        super().update()

    def summary(self):
        print(f"SWD ShutterContact:")
        super().summary()


class SHCCameraEyes(SHCDevice):
    from .services_impl import (
        CameraLightService,
        CameraNotificationService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._cameranotification_service = self.device_service("CameraNotification")
        self._cameralight_service = self.device_service("CameraLight")

    @property
    def cameranotification(self) -> CameraNotificationService.State:
        return self._cameranotification_service.value

    @cameranotification.setter
    def cameranotification(self, state: bool):
        self._cameranotification_service.put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    @property
    def cameralight(self) -> CameraLightService.State:
        return self._cameralight_service.value

    @cameralight.setter
    def cameralight(self, state: bool):
        self._cameralight_service.put_state_element("value", "ON" if state else "OFF")

    def update(self):
        self._cameralight_service.short_poll()
        self._cameranotification_service.short_poll()

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

    @privacymode.setter
    def privacymode(self, state: bool):
        self._privacymode_service.put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    @property
    def cameranotification(self) -> CameraNotificationService.State:
        return self._cameranotification_service.value

    @cameranotification.setter
    def cameranotification(self, state: bool):
        self._cameranotification_service.put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    def update(self):
        self._cameranotification_service.short_poll()
        self._privacymode_service.short_poll()

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

    def update(self):
        self._temperaturelevel_service.short_poll()
        self._valvetappet_service.short_poll()
        super().update()

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

    @setpoint_temperature.setter
    def setpoint_temperature(self, temperature: float):
        self._roomclimatecontrol_service.setpoint_temperature = temperature

    @property
    def operation_mode(self) -> RoomClimateControlService.OperationMode:
        return self._roomclimatecontrol_service.operation_mode

    @operation_mode.setter
    def operation_mode(self, mode: RoomClimateControlService.OperationMode):
        self._roomclimatecontrol_service.operation_mode = mode

    @property
    def boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.boost_mode

    @boost_mode.setter
    def boost_mode(self, value: bool):
        self._roomclimatecontrol_service.boost_mode = value

    @property
    def supports_boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.supports_boost_mode

    @property
    def low(self) -> bool:
        return self._roomclimatecontrol_service.low

    @low.setter
    def low(self, value: bool):
        self._roomclimatecontrol_service.low = value

    @property
    def summer_mode(self) -> bool:
        return self._roomclimatecontrol_service.summer_mode

    @summer_mode.setter
    def summer_mode(self, value: bool):
        self._roomclimatecontrol_service.summer_mode = value

    @property
    def temperature(self) -> float:
        return self._temperaturelevel_service.temperature

    def update(self):
        self._temperaturelevel_service.short_poll()
        self._roomclimatecontrol_service.short_poll()

    def summary(self):
        print(f"ROOM_CLIMATE_CONTROL:")
        super().summary()


class SHCHeatingCircuit(SHCDevice):
    from .services_impl import HeatingCircuitService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._heating_circuit_service = self.device_service("HeatingCircuit")

    @property
    def setpoint_temperature(self) -> float:
        return self._heating_circuit_service.setpoint_temperature

    @setpoint_temperature.setter
    def setpoint_temperature(self, temperature: float):
        self._heating_circuit_service.setpoint_temperature = temperature

    @property
    def operation_mode(self) -> HeatingCircuitService.OperationMode:
        return self._heating_circuit_service.operation_mode

    @operation_mode.setter
    def operation_mode(self, mode: HeatingCircuitService.OperationMode):
        self._heating_circuit_service.operation_mode = mode

    @property
    def temperature_override_mode_active(self) -> bool:
        return self._heating_circuit_service.temperature_override_mode_active

    @property
    def temperature_override_feature_enabled(self) -> bool:
        return self._heating_circuit_service.temperature_override_feature_enabled

    @property
    def energy_saving_feature_enabled(self) -> bool:
        return self._heating_circuit_service.energy_saving_feature_enabled

    @property
    def on(self) -> bool:
        return self._heating_circuit_service.on

    def update(self):
        self._heating_circuit_service.short_poll()

    def summary(self):
        print(f"HEATING_CIRCUIT:")
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

    def update(self):
        self._temperaturelevel_service.short_poll()
        self._humiditylevel_service.short_poll()
        super().update()

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

    def update(self):
        self._keypad_service.short_poll()
        super().update()

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

    def update(self):
        self._service.short_poll()
        super().update()

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

    def update(self):
        self._airqualitylevel_service.short_poll()
        self._smokedetectorcheck_service.short_poll()
        super().update()

    def summary(self):
        print(f"TWINGUARD:")
        super().summary()


class SHCSmokeDetectionSystem(SHCDevice):
    from .services_impl import SurveillanceAlarmService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._surveillancealarm_service = self.device_service("SurveillanceAlarm")
        # self._smokedetectioncontrol_service = self.device_service("SmokeDetectionControl")

    @property
    def alarm(self) -> SurveillanceAlarmService.State:
        return self._surveillancealarm_service.value

    def update(self):
        self._surveillancealarm_service.short_poll()
        # self._smokedetectioncontrol_service.short_poll()

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

    @state.setter
    def state(self, state: bool):
        self._binaryswitch_service.put_state_element("on", True if state else False)

    @property
    def brightness(self) -> int:
        if (
            self._capabilities & self.Capabilities.BRIGHTNESS
        ) == self.Capabilities.BRIGHTNESS:
            return self._multilevelswitch_service.value
        return 0

    @brightness.setter
    def brightness(self, state: int):
        if (
            self._capabilities & self.Capabilities.BRIGHTNESS
        ) == self.Capabilities.BRIGHTNESS:
            self._multilevelswitch_service.put_state_element("level", state)

    @property
    def color(self) -> int:
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            return self._huecolortemperature_service.value
        return 0

    @color.setter
    def color(self, state: int):
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            self._huecolortemperature_service.put_state_element(
                "colorTemperature", state
            )

    @property
    def rgb(self) -> int:
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            return self._hsbcoloractuator_service.value
        return 0

    @rgb.setter
    def rgb(self, state: int):
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            self._hsbcoloractuator_service.put_state_element("rgb", state)

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

    def update(self):
        self._binaryswitch_service.short_poll()
        if (
            self._capabilities & self.Capabilities.BRIGHTNESS
        ) == self.Capabilities.BRIGHTNESS:
            self._multilevelswitch_service.short_poll()
        if (
            self._capabilities & self.Capabilities.COLOR_TEMP
        ) == self.Capabilities.COLOR_TEMP:
            self._huecolortemperature_service.short_poll()
        if (
            self._capabilities & self.Capabilities.COLOR_HSB
        ) == self.Capabilities.COLOR_HSB:
            self._hsbcoloractuator_service.short_poll()

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

    def update(self):
        self._leakage_service.short_poll()
        self._tilt_service.short_poll()
        self._sensor_check_service.short_poll()
        super().update()

    def summary(self):
        print(f"WLS:")
        super().summary()


MODEL_MAPPING = {
    "SWD": SHCShutterContact,
    "BBL": SHCShutterControl,
    "PSM": SHCSmartPlug,
    "BSM": SHCLightSwitch,
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
    "HEATING_CIRCUIT": SHCHeatingCircuit,
}

SUPPORTED_MODELS = MODEL_MAPPING.keys()


def build(api, raw_device, raw_device_services):
    device_model = raw_device["deviceModel"]
    assert device_model in SUPPORTED_MODELS, "Device model is supported"
    return MODEL_MAPPING[device_model](
        api=api, raw_device=raw_device, raw_device_services=raw_device_services
    )
