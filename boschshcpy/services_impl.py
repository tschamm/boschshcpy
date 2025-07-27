from enum import Enum

from .device_service import SHCDeviceService


class TemperatureOffsetService(SHCDeviceService):
    @property
    def offset(self) -> float:
        return float(self.state["offset"] if "offset" in self.state else 0.0)

    @offset.setter
    def offset(self, value: float):
        self.put_state_element("offset", value)

    @property
    def step_size(self) -> float:
        return float(self.state["stepSize"] if "stepSize" in self.state else 0.0)

    @property
    def min_offset(self) -> float:
        return float(self.state["minOffset"] if "minOffset" in self.state else 0.0)

    @property
    def max_offset(self) -> float:
        return float(self.state["maxOffset"] if "maxOffset" in self.state else 0.0)

    def summary(self):
        super().summary()
        print(f"    TemperatureOffset        : {self.offset}")
        print(f"    stepSize                 : {self.step_size}")
        print(f"    minOffset                : {self.min_offset}")
        print(f"    maxOffset                : {self.max_offset}")


class TemperatureLevelService(SHCDeviceService):
    @property
    def temperature(self) -> float:
        return float(self.state["temperature"] if "temperature" in self.state else 0.0)

    def summary(self):
        super().summary()
        print(f"    Temperature              : {self.temperature}")


class HumidityLevelService(SHCDeviceService):
    @property
    def humidity(self) -> float:
        return float(self.state["humidity"] if "humidity" in self.state else 0.0)

    def summary(self):
        super().summary()
        print(f"    Humidity              : {self.humidity}")


class RoomClimateControlService(SHCDeviceService):
    class OperationMode(Enum):
        AUTOMATIC = "AUTOMATIC"
        MANUAL = "MANUAL"

    @property
    def operation_mode(self) -> OperationMode:
        return self.OperationMode(self.state["operationMode"])

    @operation_mode.setter
    def operation_mode(self, value: OperationMode):
        self.put_state_element("operationMode", value.value)

    @property
    def setpoint_temperature(self) -> float:
        return float(self.state["setpointTemperature"])

    @setpoint_temperature.setter
    def setpoint_temperature(self, value: float):
        self.put_state_element("setpointTemperature", value)

    @property
    def setpoint_temperature_eco(self) -> float:
        return float(self.state["setpointTemperatureForLevelEco"])

    @property
    def setpoint_temperature_comfort(self) -> float:
        return float(self.state["setpointTemperatureForLevelComfort"])

    @property
    def ventilation_mode(self) -> bool:
        return self.state["ventilationMode"]

    @property
    def low(self) -> bool:
        return self.state["low"]

    @low.setter
    def low(self, value: bool):
        self.put_state_element("low", value)

    @property
    def boost_mode(self) -> bool:
        return self.state["boostMode"]

    @boost_mode.setter
    def boost_mode(self, value: bool):
        self.put_state_element("boostMode", value)

    @property
    def summer_mode(self) -> bool:
        return self.state["summerMode"]

    @summer_mode.setter
    def summer_mode(self, value: bool) -> bool:
        self.put_state_element("summerMode", value)

    @property
    def supports_boost_mode(self) -> bool:
        return self.state["supportsBoostMode"]

    @property
    def show_setpoint_temperature(self) -> bool:
        if "showSetpointTemperature" in self.state.keys():
            return self.state["showSetpointTemperature"]
        else:
            return False

    def summary(self):
        super().summary()
        print(f"    Operation Mode           : {self.operation_mode}")
        print(f"    Setpoint Temperature     : {self.setpoint_temperature}")
        print(f"    Setpoint Temperature ECO : {self.setpoint_temperature_eco}")
        print(f"    Setpoint Temperature CMF : {self.setpoint_temperature_comfort}")
        print(f"    Ventilation Mode         : {self.ventilation_mode}")
        print(f"    Low                      : {self.low}")
        print(f"    Boost Mode               : {self.boost_mode}")
        print(f"    Summer Mode              : {self.summer_mode}")
        print(f"    Supports Boost Mode      : {self.supports_boost_mode}")
        print(f"    Show Setpoint Temperature: {self.show_setpoint_temperature}")


class HeatingCircuitService(SHCDeviceService):
    class OperationMode(Enum):
        AUTOMATIC = "AUTOMATIC"
        MANUAL = "MANUAL"

    @property
    def operation_mode(self) -> OperationMode:
        return self.OperationMode(self.state["operationMode"])

    @operation_mode.setter
    def operation_mode(self, value: OperationMode):
        self.put_state_element("operationMode", value.value)

    @property
    def setpoint_temperature(self) -> float:
        return float(self.state["setpointTemperature"])

    @setpoint_temperature.setter
    def setpoint_temperature(self, value: float):
        self.put_state_element("setpointTemperature", value)

    @property
    def setpoint_temperature_eco(self) -> float:
        return float(self.state["setpointTemperatureForLevelEco"])

    @setpoint_temperature_eco.setter
    def setpoint_temperature_eco(self, value: float):
        self.put_state_element("setpointTemperatureForLevelEco", value)

    @property
    def setpoint_temperature_comfort(self) -> float:
        return float(self.state["setpointTemperatureForLevelComfort"])

    @setpoint_temperature_comfort.setter
    def setpoint_temperature_comfort(self, value: float):
        self.put_state_element("setpointTemperatureForLevelComfort", value)

    @property
    def temperature_override_mode_active(self) -> bool:
        return self.state["temperatureOverrideModeActive"]

    @property
    def temperature_override_feature_enabled(self) -> bool:
        return self.state["temperatureOverrideFeatureEnabled"]

    @property
    def energy_saving_feature_enabled(self) -> bool:
        return self.state["energySavingFeatureEnabled"]

    @property
    def on(self) -> bool:
        return self.state["on"]

    def summary(self):
        super().summary()
        print(f"    Operation Mode             : {self.operation_mode}")
        print(f"    Setpoint Temperature       : {self.setpoint_temperature}")
        print(f"    Setpoint Temperature ECO   : {self.setpoint_temperature_eco}")
        print(f"    Setpoint Temperature CMF   : {self.setpoint_temperature_comfort}")
        print(
            f"    Temp Override Mode Active  : {self.temperature_override_mode_active}"
        )
        print(
            f"    Temp Override Feat Enabled : {self.temperature_override_feature_enabled}"
        )
        print(f"    Energy Saving Feat Enabled : {self.energy_saving_feature_enabled}")
        print(f"    On                         : {self.on}")


class SilentModeService(SHCDeviceService):
    class State(Enum):
        MODE_SILENT = "MODE_SILENT"
        MODE_NORMAL = "MODE_NORMAL"

    @property
    def mode(self) -> State:
        return self.State(self.state["mode"])


class ShutterContactService(SHCDeviceService):
    class State(Enum):
        CLOSED = "CLOSED"
        OPEN = "OPEN"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    Value                    : {self.value}")


class BypassService(SHCDeviceService):
    class State(Enum):
        BYPASS_INACTIVE = "BYPASS_INACTIVE"
        BYPASS_ACTIVE = "BYPASS_ACTIVE"
        UNKNOWN = "UNKNOWN"

    @property
    def value(self) -> State:
        return self.State(self.state["state"])

    def summary(self):
        super().summary()
        print(f"    State                    : {self.value}")


class VibrationSensorService(SHCDeviceService):
    class State(Enum):
        NO_VIBRATION = "NO_VIBRATION"
        VIBRATION_DETECTED = "VIBRATION_DETECTED"
        UNKNOWN = "UNKNOWN"

    class SensitivityState(Enum):
        VERY_HIGH = "VERY_HIGH"
        HIGH = "HIGH"
        MEDIUM = "MEDIUM"
        LOW = "LOW"
        VERY_LOW = "VERY_LOW"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    @property
    def enabled(self) -> bool:
        return self.state["enabled"]

    @property
    def sensitivity(self) -> SensitivityState:
        return self.SensitivityState(self.state["sensitivity"])

    def summary(self):
        super().summary()
        print(f"    Value                    : {self.value}")
        print(f"    Sensitivity              : {self.sensitivity}")
        print(f"    Enabled                  : {self.enabled}")


class ValveTappetService(SHCDeviceService):
    class State(Enum):
        VALVE_ADAPTION_SUCCESSFUL = "VALVE_ADAPTION_SUCCESSFUL"
        VALVE_ADAPTION_IN_PROGRESS = "VALVE_ADAPTION_IN_PROGRESS"
        RANGE_TOO_BIG = "RANGE_TOO_BIG"
        RUN_TO_START_POSITION = "RUN_TO_START_POSITION"
        IN_START_POSITION = "IN_START_POSITION"
        NOT_AVAILABLE = "NOT_AVAILABLE"
        NO_VALVE_BODY_ERROR = "NO_VALVE_BODY_ERROR"
        VALVE_TOO_TIGHT = "VALVE_TOO_TIGHT"

    @property
    def position(self) -> int:
        return int(self.state["position"])

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    Position                 : {self.position}")


class PowerSwitchService(SHCDeviceService):
    class State(Enum):
        ON = "ON"
        OFF = "OFF"

    @property
    def value(self) -> State:
        return self.State(self.state["switchState"])

    @property
    def powerofftime(self) -> int:
        return int(self.state["automaticPowerOffTime"])

    def summary(self):
        super().summary()
        print(f"    switchState              : {self.value}")
        print(f"    automaticPowerOffTime    : {self.powerofftime}")


class PowerMeterService(SHCDeviceService):
    @property
    def powerconsumption(self) -> float:
        return float(self.state["powerConsumption"])

    @property
    def energyconsumption(self) -> float:
        return float(self.state["energyConsumption"])

    def summary(self):
        super().summary()
        print(f"    powerConsumption         : {self.powerconsumption}")
        print(f"    energyConsumption        : {self.energyconsumption}")


class RoutingService(SHCDeviceService):
    class State(Enum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class PowerSwitchProgramService(SHCDeviceService):
    class State(Enum):
        MANUAL = "MANUAL"
        AUTOMATIC = "AUTOMATIC"

    @property
    def value(self) -> State:
        return self.State(self.state["operationMode"])

    def summary(self):
        super().summary()
        print(f"    operationMode            : {self.value}")


class BinarySwitchService(SHCDeviceService):
    @property
    def value(self) -> bool:
        return self.state["on"]

    def summary(self):
        super().summary()
        print(f"    switchState              : {self.value}")


class MultiLevelSwitchService(SHCDeviceService):
    @property
    def value(self) -> int:
        return self.state["level"]

    def summary(self):
        super().summary()
        print(f"    multiLevelSwitchState    : {self.value}")


class MultiLevelSensorService(SHCDeviceService):
    @property
    def illuminance(self) -> int:
        return self.state["illuminance"]

    def summary(self):
        super().summary()
        print(f"    multiLevelSensorState    : {self.illuminance}")


class HueColorTemperatureService(SHCDeviceService):
    @property
    def value(self) -> int:
        return self.state["colorTemperature"]

    @property
    def min_value(self) -> int:
        return self.state["colorTemperatureRange"]["minCt"]

    @property
    def max_value(self) -> int:
        return self.state["colorTemperatureRange"]["maxCt"]

    def summary(self):
        super().summary()
        print(f"    colorTemperature         : {self.value}")
        print(f"    minColorTemperature      : {self.min_value}")
        print(f"    maxColorTemperature      : {self.max_value}")


class HSBColorActuatorService(SHCDeviceService):
    @property
    def value(self) -> int:
        return self.state["rgb"]

    @property
    def gamut(self) -> str:
        return self.state["gamut"]

    @property
    def min_value(self) -> int:
        return self.state["colorTemperatureRange"]["minCt"]

    @property
    def max_value(self) -> int:
        return self.state["colorTemperatureRange"]["maxCt"]

    def summary(self):
        super().summary()
        print(f"    rgb                      : {self.value}")
        print(f"    gamut                    : {self.gamut}")
        print(f"    minColorTemperature      : {self.min_value}")
        print(f"    maxColorTemperature      : {self.max_value}")


class SmokeDetectorCheckService(SHCDeviceService):
    class State(Enum):
        NONE = "NONE"
        SMOKE_TEST_OK = "SMOKE_TEST_OK"
        SMOKE_TEST_REQUESTED = "SMOKE_TEST_REQUESTED"
        SMOKE_TEST_FAILED = "SMOKE_TEST_FAILED"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    smokeDetectorCheckState  : {self.value}")


class AlarmService(SHCDeviceService):
    class State(Enum):
        IDLE_OFF = "IDLE_OFF"
        INTRUSION_ALARM = "INTRUSION_ALARM"
        SECONDARY_ALARM = "SECONDARY_ALARM"
        PRIMARY_ALARM = "PRIMARY_ALARM"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    alarmState               : {self.value}")


class ShutterControlService(SHCDeviceService):
    class State(Enum):
        STOPPED = "STOPPED"
        MOVING = "MOVING"
        CALIBRATING = "CALIBRATING"
        OPENING = "OPENING"
        CLOSING = "CLOSING"

    def __init__(self, api, raw_device_service):
        super().__init__(api=api, raw_device_service=raw_device_service)

    @property
    def operation_state(self) -> State:
        return self.State(self.state["operationState"])

    @property
    def calibrated(self) -> bool:
        return self.state["calibrated"]

    @property
    def level(self) -> float:
        return self.state["level"]

    def summary(self):
        super().summary()
        print(f"    operationState           : {self.operation_state}")
        print(f"    Level                    : {self.level}")
        print(f"    Calibrated               : {self.calibrated}")


class BlindsControlService(SHCDeviceService):
    class BlindsType(Enum):
        DEGREE_90 = "DEGREE_90"
        DEGREE_180 = "DEGREE_180"

    @property
    def current_angle(self) -> float:
        return self.state["currentAngle"]

    @property
    def target_angle(self) -> float:
        return self.state["targetAngle"]

    @target_angle.setter
    def target_angle(self, value: float):
        self.put_state_element("targetAngle", value)

    @property
    def blinds_type(self) -> BlindsType:
        return self.state["blindsType"]

    def summary(self):
        super().summary()
        print(f"    currentAngle              : {self.current_angle}")
        print(f"    targetAngle               : {self.target_angle}")


class BlindsSceneControlService(SHCDeviceService):
    @property
    def level(self) -> float:
        return self.state["level"]

    @level.setter
    def level(self, value: float):
        self.put_state_element("level", value)

    @property
    def angle(self) -> float:
        return self.state["angle"]

    @angle.setter
    def angle(self, value: float):
        self.put_state_element("angle", value)

    def summary(self):
        super().summary()
        print(f"    level              : {self.level}")
        print(f"    angle               : {self.angle}")


class CameraLightService(SHCDeviceService):
    class State(Enum):
        ON = "ON"
        OFF = "OFF"
        NONE = "NONE"

    @property
    def value(self) -> State:
        return self.State(self.state["value"] if "value" in self.state else "NONE")

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class PrivacyModeService(SHCDeviceService):
    class State(Enum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    @property
    def value(self) -> State:
        return self.State(self.state["value"] if "value" in self.state else "DISABLED")

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class CameraNotificationService(SHCDeviceService):
    class State(Enum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    @property
    def value(self) -> State:
        return self.State(self.state["value"] if "value" in self.state else "DISABLED")

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class ChildProtectionService(SHCDeviceService):
    @property
    def childLockActive(self) -> bool:
        return self.state["childLockActive"]

    def summary(self):
        super().summary()
        print(f"    childLockActive                    : {self.childLockActive}")


class ImpulseSwitchService(SHCDeviceService):
    @property
    def impulse_state(self) -> bool:
        return self.state["impulseState"]

    @property
    def impulse_length(self) -> int:
        return self.state["impulseLength"]

    @property
    def instant_of_last_impulse(self) -> str:
        if not "instantOfLastImpulse" in self.state:
            return None
        return self.state["instantOfLastImpulse"]


class KeypadService(SHCDeviceService):
    class KeyState(Enum):
        LOWER_BUTTON = "LOWER_BUTTON"
        LOWER_LEFT_BUTTON = "LOWER_LEFT_BUTTON"
        LOWER_RIGHT_BUTTON = "LOWER_RIGHT_BUTTON"
        UPPER_BUTTON = "UPPER_BUTTON"
        UPPER_LEFT_BUTTON = "UPPER_LEFT_BUTTON"
        UPPER_RIGHT_BUTTON = "UPPER_RIGHT_BUTTON"

    class KeyEvent(Enum):
        PRESS_SHORT = "PRESS_SHORT"
        PRESS_LONG = "PRESS_LONG"
        PRESS_LONG_RELEASED = "PRESS_LONG_RELEASED"

    @property
    def keyCode(self) -> int:
        return self.state["keyCode"] if "keyCode" in self.state else 0

    @property
    def keyName(self) -> KeyState:
        if not "keyName" in self.state:
            return None
        return self.KeyState(self.state["keyName"])

    @property
    def eventType(self) -> KeyEvent:
        if not "eventType" in self.state:
            return None
        return self.KeyEvent(self.state["eventType"])

    @property
    def eventTimestamp(self) -> int:
        if not "eventTimestamp" in self.state:
            return 0
        return self.state["eventTimestamp"]

    def summary(self):
        super().summary()
        print(f"    keyCode                  : {self.keyCode}")
        print(f"    keyName                  : {self.keyName}")
        print(f"    eventType                : {self.eventType}")
        print(f"    eventTimestamp           : {self.eventTimestamp}")


class LatestMotionService(SHCDeviceService):
    @property
    def latestMotionDetected(self) -> str:
        return (
            self.state["latestMotionDetected"]
            if "latestMotionDetected" in self.state
            else "n/a"
        )

    def summary(self):
        super().summary()
        print(f"    latestMotionDetected     : {self.latestMotionDetected}")


class AirQualityLevelService(SHCDeviceService):
    class RatingState(Enum):
        GOOD = "GOOD"
        MEDIUM = "MEDIUM"
        BAD = "BAD"

    @property
    def combinedRating(self) -> RatingState:
        return self.RatingState(self.state["combinedRating"])

    @property
    def description(self) -> str:
        return self.state["description"]

    @property
    def temperature(self) -> int:
        return self.state["temperature"]

    @property
    def temperatureRating(self) -> RatingState:
        return self.RatingState(self.state["temperatureRating"])

    @property
    def humidity(self) -> int:
        return self.state["humidity"]

    @property
    def humidityRating(self) -> RatingState:
        return self.RatingState(self.state["humidityRating"])

    @property
    def purity(self) -> int:
        return self.state["purity"]

    @property
    def purityRating(self) -> RatingState:
        return self.RatingState(self.state["purityRating"])

    def summary(self):
        super().summary()
        print(f"    combinedRating           : {self.combinedRating}")
        print(f"    description              : {self.description}")
        print(f"    temperature              : {self.temperature}")
        print(f"    temperatureRating        : {self.temperatureRating}")
        print(f"    humidity                 : {self.humidity}")
        print(f"    humidityRating           : {self.humidityRating}")
        print(f"    purity                   : {self.purity}")
        print(f"    purityRating             : {self.purityRating}")


class SurveillanceAlarmService(SHCDeviceService):
    class State(Enum):
        ALARM_OFF = "ALARM_OFF"
        ALARM_ON = "ALARM_ON"
        ALARM_MUTED = "ALARM_MUTED"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class SmokeDetectionControlService(SHCDeviceService):
    def summary(self):
        super().summary()
        print(f"    not yet implemented!")


class BatteryLevelService(SHCDeviceService):
    class State(Enum):
        LOW_BATTERY = "LOW_BATTERY"
        CRITICAL_LOW = "CRITICAL_LOW"
        CRITICALLY_LOW_BATTERY = "CRITICALLY_LOW_BATTERY"
        OK = "OK"
        NOT_AVAILABLE = "NOT_AVAILABLE"

    @property
    def warningLevel(self) -> State:
        faults = (
            self._raw_device_service["faults"]
            if "faults" in self._raw_device_service
            else None
        )
        if not faults:
            return self.State("OK")
        assert len(faults["entries"]) == 1
        assert "type" in faults["entries"][0]
        return self.State(faults["entries"][0]["type"])

    def summary(self):
        super().summary()
        print(f"    warningLevel             : {self.warningLevel}")


class ThermostatService(SHCDeviceService):
    class State(Enum):
        ON = "ON"
        OFF = "OFF"

    @property
    def childLock(self) -> State:
        return self.State(self.state["childLock"])

    def summary(self):
        super().summary()
        print(f"    childLock                : {self.childLock}")


class CommunicationQualityService(SHCDeviceService):
    class State(Enum):
        BAD = "BAD"
        GOOD = "GOOD"
        MEDIUM = "MEDIUM"
        NORMAL = "NORMAL"
        UNKNOWN = "UNKNOWN"
        FETCHING = "FETCHING"

    @property
    def value(self) -> State:
        return self.State(self.state["quality"])

    def summary(self):
        super().summary()
        print(f"    quality                  : {self.value}")


class WaterLeakageSensorService(SHCDeviceService):
    class State(Enum):
        LEAKAGE_DETECTED = "LEAKAGE_DETECTED"
        NO_LEAKAGE = "NO_LEAKAGE"

    @property
    def value(self) -> State:
        return self.State(self.state["state"])

    def summary(self):
        super().summary()
        print(f"    waterLeakageSensorState  : {self.value}")


class WaterLeakageSensorTiltService(SHCDeviceService):
    class State(Enum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    @property
    def pushNotificationState(self) -> State:
        return self.State(self.state["pushNotificationState"])

    @property
    def acousticSignalState(self) -> State:
        return self.State(self.state["acousticSignalState"])

    def summary(self):
        super().summary()
        print(f"    pushNotificationState    : {self.pushNotificationState}")
        print(f"    acousticSignalState      : {self.acousticSignalState}")


class WaterLeakageSensorCheckService(SHCDeviceService):
    @property
    def value(self) -> str:
        return self.state["result"]

    def summary(self):
        super().summary()
        print(f"    waterLeakageSensorCheck  : {self.value}")


class PresenceSimulationConfigurationService(SHCDeviceService):
    @property
    def enabled(self) -> bool:
        return self.state["enabled"]

    @enabled.setter
    def enabled(self, value: bool):
        self.put_state_element("enabled", value)

    def summary(self):
        super().summary()
        print(f"    presenceSimulationConfigurationState  : {self.enabled}")


SERVICE_MAPPING = {
    "AirQualityLevel": AirQualityLevelService,
    "Alarm": AlarmService,
    "BatteryLevel": BatteryLevelService,
    "BinarySwitch": BinarySwitchService,
    "BlindsControl": BlindsControlService,
    "BlindsSceneControl": BlindsSceneControlService,
    "Bypass": BypassService,
    "CameraLight": CameraLightService,
    "CameraNotification": CameraNotificationService,
    "ChildProtection": ChildProtectionService,
    "CommunicationQuality": CommunicationQualityService,
    "HeatingCircuit": HeatingCircuitService,
    "HSBColorActuator": HSBColorActuatorService,
    "HueColorTemperature": HueColorTemperatureService,
    "HumidityLevel": HumidityLevelService,
    "ImpulseSwitch": ImpulseSwitchService,
    "Keypad": KeypadService,
    "LatestMotion": LatestMotionService,
    "MultiLevelSwitch": MultiLevelSwitchService,
    "MultiLevelSensor": MultiLevelSensorService,
    "PowerMeter": PowerMeterService,
    "PowerSwitch": PowerSwitchService,
    "PowerSwitchProgram": PowerSwitchProgramService,
    "PresenceSimulationConfiguration": PresenceSimulationConfigurationService,
    "PrivacyMode": PrivacyModeService,
    "RoomClimateControl": RoomClimateControlService,
    "Routing": RoutingService,
    "ShutterContact": ShutterContactService,
    "ShutterControl": ShutterControlService,
    "SilentMode": SilentModeService,
    "SmokeDetectorCheck": SmokeDetectorCheckService,
    "SurveillanceAlarm": SurveillanceAlarmService,
    "TemperatureLevel": TemperatureLevelService,
    "TemperatureOffset": TemperatureOffsetService,
    "Thermostat": ThermostatService,
    "ValveTappet": ValveTappetService,
    "VibrationSensor": VibrationSensorService,
    "WaterLeakageSensor": WaterLeakageSensorService,
    "WaterLeakageSensorTilt": WaterLeakageSensorTiltService,
    "WaterLeakageSensorCheck": WaterLeakageSensorCheckService,
}

#    "SmokeDetectionControl": SmokeDetectionControlService,
#    "ElectricalFaults": ElectricalFaultsService,
#    "SwitchConfiguration": SwitchConfigurationService,
#    "Linking": LinkingService,

SUPPORTED_DEVICE_SERVICE_IDS = SERVICE_MAPPING.keys()


def build(api, raw_device_service):
    device_service_id = raw_device_service["id"]
    assert (
        device_service_id in SUPPORTED_DEVICE_SERVICE_IDS
    ), "Device service is supported"
    return SERVICE_MAPPING[device_service_id](
        api=api, raw_device_service=raw_device_service
    )
