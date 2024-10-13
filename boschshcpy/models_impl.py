from enum import Enum, Flag, auto

from .device import SHCDevice


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
        return self.BatteryLevelService.State.NOT_AVAILABLE


class _CommunicationQuality(SHCDevice):
    from .services_impl import (
        CommunicationQualityService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._communicationquality_service = self.device_service("CommunicationQuality")

    @property
    def communicationquality(self) -> CommunicationQualityService.State:
        return self._communicationquality_service.value


class _PowerMeter(SHCDevice):
    from .services_impl import (
        PowerMeterService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._powermeter_service = self.device_service("PowerMeter")

    @property
    def energyconsumption(self) -> float:
        return self._powermeter_service.energyconsumption

    @property
    def powerconsumption(self) -> float:
        return self._powermeter_service.powerconsumption


class _ChildProtection(SHCDevice):
    from .services_impl import (
        ChildProtectionService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._childprotection_service = self.device_service("ChildProtection")

    @property
    def child_lock(self) -> bool:
        return self._childprotection_service.childLockActive

    @child_lock.setter
    def child_lock(self, state: bool):
        self._childprotection_service.put_state_element("childLockActive", state)


class _Thermostat(SHCDevice):
    from .services_impl import (
        ThermostatService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._thermostat_service = self.device_service("Thermostat")

    @property
    def child_lock(self) -> ThermostatService.State:
        return self._thermostat_service.childLock

    @child_lock.setter
    def child_lock(self, state: bool):
        self._thermostat_service.put_state_element(
            "childLock", "ON" if state else "OFF"
        )


class _PowerSwitch(SHCDevice):
    from .services_impl import (
        PowerSwitchService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._powerswitch_service = self.device_service("PowerSwitch")

    @property
    def switchstate(self) -> PowerSwitchService.State:
        return self._powerswitch_service.value

    @switchstate.setter
    def switchstate(self, state: bool):
        self._powerswitch_service.put_state_element(
            "switchState", "ON" if state else "OFF"
        )


class _PowerSwitchProgram(SHCDevice):
    from .services_impl import (
        PowerSwitchProgramService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._powerswitchprogram_service = self.device_service("PowerSwitchProgram")

    # To be implemented


class _TemperatureLevel(SHCDevice):
    from .services_impl import TemperatureLevelService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._temperaturelevel_service = self.device_service("TemperatureLevel")

    @property
    def temperature(self) -> float:
        return self._temperaturelevel_service.temperature


class _HumidityLevel(SHCDevice):
    from .services_impl import HumidityLevelService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._humiditylevel_service = self.device_service("HumidityLevel")

    @property
    def humidity(self) -> float:
        return self._humiditylevel_service.humidity


class _TemperatureOffset(SHCDevice):
    from .services_impl import (
        TemperatureOffsetService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._temperatureoffset_service = self.device_service("TemperatureOffset")

    @property
    def offset(self) -> float:
        return self._temperatureoffset_service.offset

    @offset.setter
    def offset(self, value: float):
        self._temperatureoffset_service.offset = value

    @property
    def step_size(self) -> float:
        return self._temperatureoffset_service.step_size

    @property
    def min_offset(self) -> float:
        return self._temperatureoffset_service.min_offset

    @property
    def max_offset(self) -> float:
        return self._temperatureoffset_service.max_offset


class _SilentMode(SHCDevice):
    from .services_impl import (
        SilentModeService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._silentmode_service = self.device_service("SilentMode")

    @property
    def supports_silentmode(self):
        return self._silentmode_service is not None

    @property
    def silentmode(self) -> SilentModeService.State:
        if self.supports_silentmode:
            return self._silentmode_service.mode

    @silentmode.setter
    def silentmode(self, state: bool):
        if self.supports_silentmode:
            self._silentmode_service.put_state_element(
                "mode", "MODE_SILENT" if state else "MODE_NORMAL"
            )


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


class SHCSmartPlug(_PowerMeter, _PowerSwitch, _PowerSwitchProgram):
    from .services_impl import (
        RoutingService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._routing_service = self.device_service("Routing")

    @property
    def routing(self) -> RoutingService.State:
        return self._routing_service.value

    @routing.setter
    def routing(self, state: bool):
        self._routing_service.put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )


class SHCSmartPlugCompact(
    _CommunicationQuality, _PowerMeter, _PowerSwitch, _PowerSwitchProgram
):
    pass


class SHCLightSwitch(_ChildProtection, _PowerSwitch, _PowerSwitchProgram):
    pass


class SHCLightSwitchBSM(SHCLightSwitch, _PowerMeter):
    pass


class SHCLightControl(_CommunicationQuality, _PowerMeter):
    pass


class SHCMicromoduleRelay(
    _CommunicationQuality, _ChildProtection, _PowerSwitch, _PowerSwitchProgram
):
    from .services_impl import (
        ImpulseSwitchService,
    )

    class RelayType(Enum):
        BUTTON = "BUTTON"
        SWITCH = "SWITCH"

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._impulseswitch_service = self.device_service("ImpulseSwitch")

    @property
    def relay_type(self) -> RelayType:
        return (
            self.RelayType.BUTTON
            if self.profile == "GENERIC"
            else self.RelayType.SWITCH
        )

    def trigger_impulse_state(self):
        if self._impulseswitch_service:
            self._impulseswitch_service.put_state_element("impulseState", True)

    @property
    def instant_of_last_impulse(self) -> str:
        if self._impulseswitch_service:
            return self._impulseswitch_service.instant_of_last_impulse


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
        self._service.put_state_element("operationState", "STOPPED")

    @property
    def operation_state(self) -> ShutterControlService.State:
        return self._service.value


class SHCMicromoduleShutterControl(
    SHCShutterControl, _CommunicationQuality, _ChildProtection, _PowerMeter
):
    pass


class SHCMicromoduleBlinds(SHCMicromoduleShutterControl):
    from .services_impl import BlindsControlService, BlindsSceneControlService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._blindscontrol_service = self.device_service("BlindsControl")
        self._blindsscenecontrol_service = self.device_service("BlindsSceneControl")

    @property
    def current_angle(self) -> float:
        return self._blindscontrol_service.current_angle

    @property
    def target_angle(self) -> float:
        return self._blindscontrol_service.target_angle

    @target_angle.setter
    def target_angle(self, value: float):
        self._blindscontrol_service.target_angle = value

    @property
    def blinds_level(self) -> float:
        return self._blindsscenecontrol_service.level

    @blinds_level.setter
    def blinds_level(self, level: float):
        self._blindsscenecontrol_service.level = level

    @property
    def blinds_type(self) -> BlindsControlService.BlindsType:
        return self._blindscontrol_service.blinds_type

    def stop_blinds(self):
        self._api.put_shading_shutters_stop(self.id)


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


class SHCShutterContact2(SHCShutterContact, _CommunicationQuality):
    from .services_impl import BypassService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._bypass_service = self.device_service("Bypass")

    @property
    def bypass(self) -> BypassService.State:
        return self._bypass_service.value

    @bypass.setter
    def bypass(self, state: bool):
        self._bypass_service.put_state_element(
            "state", "BYPASS_ACTIVE" if state else "BYPASS_INACTIVE"
        )


class SHCShutterContact2Plus(SHCShutterContact2):
    from .services_impl import VibrationSensorService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._vibrationsensor_service = self.device_service("VibrationSensor")

    @property
    def vibrationsensor(self) -> VibrationSensorService.State:
        return self._vibrationsensor_service.value

    @property
    def enabled(self) -> bool:
        return self._vibrationsensor_service.enabled

    @enabled.setter
    def enabled(self, state: bool):
        self._vibrationsensor_service.put_state_element("enabled", state)

    @property
    def sensitivity(self) -> VibrationSensorService.SensitivityState:
        return self._vibrationsensor_service.sensitivity

    @sensitivity.setter
    def sensitivity(self, state: VibrationSensorService.SensitivityState):
        self._vibrationsensor_service.put_state_element("sensitivity", state.name)


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
            "value", "DISABLED" if state else "ENABLED"
        )

    @property
    def cameranotification(self) -> CameraNotificationService.State:
        if self._cameranotification_service:
            return self._cameranotification_service.value

    @cameranotification.setter
    def cameranotification(self, state: bool):
        if self._cameranotification_service:
            self._cameranotification_service.put_state_element(
                "value", "ENABLED" if state else "DISABLED"
            )


class SHCCameraEyes(SHCCamera360):
    from .services_impl import (
        CameraLightService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._cameralight_service = self.device_service("CameraLight")

    @property
    def cameralight(self) -> CameraLightService.State:
        if self._cameralight_service:
            return self._cameralight_service.value

    @cameralight.setter
    def cameralight(self, state: bool):
        if self._cameralight_service:
            self._cameralight_service.put_state_element(
                "value", "ON" if state else "OFF"
            )


class SHCThermostat(
    SHCBatteryDevice,
    _CommunicationQuality,
    _SilentMode,
    _Thermostat,
    _TemperatureLevel,
    _TemperatureOffset,
):
    from .services_impl import (
        ValveTappetService,
        TemperatureOffsetService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._valvetappet_service = self.device_service("ValveTappet")

    @property
    def position(self) -> int:
        return self._valvetappet_service.position

    @property
    def valvestate(self) -> ValveTappetService.State:
        return self._valvetappet_service.value


class SHCClimateControl(_TemperatureLevel):
    from .services_impl import RoomClimateControlService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
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


class SHCWallThermostat(SHCBatteryDevice, _TemperatureLevel, _HumidityLevel):
    pass


class SHCRoomThermostat2(
    SHCWallThermostat,
    _CommunicationQuality,
    _Thermostat,
    _TemperatureOffset,
):
    pass


class SHCUniversalSwitch(SHCBatteryDevice):
    from .services_impl import KeypadService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._keypad_service = self.device_service("Keypad")

    @property
    def keystates(self) -> dict[str]:
        return ["LOWER_BUTTON", "UPPER_BUTTON"]

    @property
    def eventtypes(self) -> Enum:
        return self._keypad_service.KeyEvent

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


class SHCUniversalSwitch2(SHCUniversalSwitch):
    from .services_impl import KeypadService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

    @property
    def keystates(self) -> dict[str]:
        return [
            "LOWER_LEFT_BUTTON",
            "LOWER_RIGHT_BUTTON",
            "UPPER_LEFT_BUTTON",
            "UPPER_RIGHT_BUTTON",
        ]


class SHCMotionDetector(SHCBatteryDevice):
    from .services_impl import LatestMotionService, MultiLevelSensorService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._service = self.device_service("LatestMotion")
        self._multi_level_sensor_service = self.device_service("MultiLevelSensor")

    @property
    def latestmotion(self) -> str:
        return self._service.latestMotionDetected

    @property
    def illuminance(self) -> str:
        return self._multi_level_sensor_service.illuminance


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


class SHCSmokeDetectionSystem(SHCDevice):
    from .services_impl import SurveillanceAlarmService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._surveillancealarm_service = self.device_service("SurveillanceAlarm")
        # self._smokedetectioncontrol_service = self.device_service("SmokeDetectionControl")

    @property
    def alarm(self) -> SurveillanceAlarmService.State:
        return self._surveillancealarm_service.value


class SHCPresenceSimulationSystem(SHCDevice):
    from .services_impl import PresenceSimulationConfigurationService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._presencesimulationconfiguration_service = self.device_service(
            "PresenceSimulationConfiguration"
        )

    @property
    def enabled(self) -> bool:
        return self._presencesimulationconfiguration_service.enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._presencesimulationconfiguration_service.enabled = value


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
    def binarystate(self) -> bool:
        return self._binaryswitch_service.value

    @binarystate.setter
    def binarystate(self, state: bool):
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


class SHCMicromoduleDimmer(
    SHCLight, _CommunicationQuality, _ChildProtection, _PowerSwitch
):
    # from .services_impl import (
    #     # Services TBD:
    #     # ElectricalFaultsService,
    #     # DimmerConfiguration,
    #     # SwitchConfiguration,
    # )

    @property
    def binarystate(self) -> bool:
        if self._powerswitch_service:
            return self._powerswitch_service.value == self.PowerSwitchService.State.ON

    @binarystate.setter
    def binarystate(self, state: bool):
        if self._powerswitch_service:
            self._powerswitch_service.put_state_element(
                "switchState", "ON" if state else "OFF"
            )


MODEL_MAPPING = {
    "SWD": SHCShutterContact,
    "SWD2": SHCShutterContact2,
    "SWD2_PLUS": SHCShutterContact2Plus,
    "BBL": SHCShutterControl,
    "MICROMODULE_AWNING": SHCMicromoduleShutterControl,
    "MICROMODULE_SHUTTER": SHCMicromoduleShutterControl,
    "PSM": SHCSmartPlug,
    "BSM": SHCLightSwitchBSM,
    "MICROMODULE_BLINDS": SHCMicromoduleBlinds,
    "MICROMODULE_LIGHT_ATTACHED": SHCLightSwitch,
    "MICROMODULE_LIGHT_CONTROL": SHCLightControl,
    "MICROMODULE_RELAY": SHCMicromoduleRelay,
    "PLUG_COMPACT": SHCSmartPlugCompact,
    "SD": SHCSmokeDetector,
    "SMOKE_DETECTOR2": SHCSmokeDetector,
    "CAMERA_EYES": SHCCameraEyes,
    "CAMERA_360": SHCCamera360,
    "ROOM_CLIMATE_CONTROL": SHCClimateControl,
    "TRV": SHCThermostat,
    "TRV_GEN2": SHCThermostat,
    "THB": SHCWallThermostat,
    "BWTH": SHCWallThermostat,
    "BWTH24": SHCWallThermostat,
    "RTH2_BAT": SHCRoomThermostat2,
    "RTH2_230": SHCRoomThermostat2,
    "WRC2": SHCUniversalSwitch,
    "SWITCH2": SHCUniversalSwitch2,
    "MD": SHCMotionDetector,
    "PRESENCE_SIMULATION_SERVICE": SHCPresenceSimulationSystem,
    "TWINGUARD": SHCTwinguard,
    "SMOKE_DETECTION_SYSTEM": SHCSmokeDetectionSystem,
    "LEDVANCE_LIGHT": SHCLight,
    "HUE_LIGHT": SHCLight,
    "WLS": SHCWaterLeakageSensor,
    "HEATING_CIRCUIT": SHCHeatingCircuit,
    "MICROMODULE_DIMMER": SHCMicromoduleDimmer,
}

SUPPORTED_MODELS = MODEL_MAPPING.keys()


def build(api, raw_device, raw_device_services) -> SHCDevice:
    device_model = raw_device["deviceModel"]
    assert device_model in SUPPORTED_MODELS, "Device model is supported"
    return MODEL_MAPPING[device_model](
        api=api, raw_device=raw_device, raw_device_services=raw_device_services
    )
