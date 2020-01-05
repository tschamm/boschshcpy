from enum import Enum
from .device_service import BSHLocalDeviceService


class TemperatureLevelService(BSHLocalDeviceService):
    @property
    def temperature(self) -> float:
        return float(self.state["temperature"])

    def summary(self):
        super().summary()
        print(f"    Temperature              : {self.temperature}")


class RoomClimateControlService(BSHLocalDeviceService):
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


class ShutterContactService(BSHLocalDeviceService):
    class State(Enum):
        CLOSED = "CLOSED"
        OPEN = "OPEN"

    @property
    def value(self) -> State:
        return self.State(self.state["value"])

    def summary(self):
        super().summary()
        print(f"    Value                    : {self.value}")


class ValveTappetService(BSHLocalDeviceService):
    @property
    def position(self) -> int:
        return int(self.state["position"])

    def summary(self):
        super().summary()
        print(f"    Position                 : {self.position}")


SERVICE_MAPPING = {"TemperatureLevel": TemperatureLevelService,
                   "RoomClimateControl": RoomClimateControlService,
                   "ShutterContact": ShutterContactService,
                   "ValveTappet": ValveTappetService}

SUPPORTED_DEVICE_SERVICE_IDS = SERVICE_MAPPING.keys()


def build(api, raw_device_service):
    device_service_id = raw_device_service["id"]
    assert device_service_id in SUPPORTED_DEVICE_SERVICE_IDS, "Device service is supported"
    return SERVICE_MAPPING[device_service_id](api=api, raw_device_service=raw_device_service)
