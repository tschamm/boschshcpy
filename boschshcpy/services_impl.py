from enum import Enum
from .device_service import SHCDeviceService


class TemperatureLevelService(SHCDeviceService):
    @property
    def temperature(self) -> float:
        return float(self.state["temperature"])

    def summary(self):
        super().summary()
        print(f"    Temperature              : {self.temperature}")


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


class ValveTappetService(SHCDeviceService):
    @property
    def position(self) -> int:
        return int(self.state["position"])

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


class SmokeDetectorCheckService(SHCDeviceService):
    class State(Enum):
        NONE = "NONE"
        SMOKE_TEST_OK = "SMOKE_TEST_OK"

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
        self._curr_level = self.state["level"]
        self._last_level = self.state["level"]

    @property
    def value(self) -> State:
        if self._curr_level != self.level:
            self._last_level = self._curr_level
            self._curr_level = self.level
        if self.state["operationState"] == "MOVING" and self.level < self._last_level:
            return self.State("CLOSING")
        elif self.state["operationState"] == "MOVING" and self.level > self._last_level:
            return self.State("OPENING")
        else:
            return self.State(self.state["operationState"])

    @property
    def calibrated(self) -> bool:
        return self.state["calibrated"]

    @property
    def level(self) -> float:
        return self.state["level"]

    def summary(self):
        super().summary()
        print(f"    operationState           : {self.value}")
        print(f"    Level                    : {self.level}")
        print(f"    Calibrated               : {self.calibrated}")

class CameraLightService(SHCDeviceService):
    class State(Enum):
        ON = "ON"
        OFF = "OFF"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class PrivacyModeService(SHCDeviceService):
    class State(Enum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class CameraNotificationService(SHCDeviceService):
    class State(Enum):
        ENABLED = "ENABLED"
        DISABLED = "DISABLED"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")


class IntrusionDetectionControlService(SHCDeviceService):
    class State(Enum):
        SYSTEM_DISARMED = "SYSTEM_DISARMED"
        SYSTEM_ARMING = "SYSTEM_ARMING"
        SYSTEM_ARMED = "SYSTEM_ARMED"
        MUTE_ALARM = "MUTE_ALARM"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])
    
    @property
    def armActivationDelayTime(self) -> int:
        return self.state["armActivationDelayTime"]

    @property
    def alarmActivationDelayTime(self) -> int:
        return self.state["alarmActivationDelayTime"]

    def summary(self):
        super().summary()
        print(f"    value                    : {self.value}")
        print(f"    armActivationDelayTime   : {self.armActivationDelayTime}")
        print(f"    alarmActivationDelayTime : {self.alarmActivationDelayTime}")



SERVICE_MAPPING = {"TemperatureLevel": TemperatureLevelService,
                   "RoomClimateControl": RoomClimateControlService,
                   "ShutterContact": ShutterContactService,
                   "ValveTappet": ValveTappetService,
                   "PowerSwitch": PowerSwitchService,
                   "PowerMeter": PowerMeterService,
                   "Routing": RoutingService,
                   "PowerSwitchProgram": PowerSwitchProgramService,
                   "BinarySwitch": BinarySwitchService,
                   "SmokeDetectorCheck": SmokeDetectorCheckService,
                   "Alarm": AlarmService,
                   "ShutterControl": ShutterControlService,
                   "CameraLight": CameraLightService,
                   "PrivacyMode": PrivacyModeService,
                   "CameraNotification": CameraNotificationService,
                   "IntrusionDetectionControl": IntrusionDetectionControlService}
# Todo: implement BatteryLevelService

SUPPORTED_DEVICE_SERVICE_IDS = SERVICE_MAPPING.keys()


def build(api, raw_device_service):
    device_service_id = raw_device_service["id"]
    assert device_service_id in SUPPORTED_DEVICE_SERVICE_IDS, "Device service is supported"
    return SERVICE_MAPPING[device_service_id](api=api, raw_device_service=raw_device_service)
