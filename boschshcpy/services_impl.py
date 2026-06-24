import logging
from enum import Enum

from .device_service import SHCDeviceService

logger = logging.getLogger("boschshcpy")


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
    def setpoint_temperature_eco(self) -> float | None:
        value = self.state.get("setpointTemperatureForLevelEco")
        return float(value) if value is not None else None

    @property
    def setpoint_temperature_comfort(self) -> float | None:
        value = self.state.get("setpointTemperatureForLevelComfort")
        return float(value) if value is not None else None

    @property
    def ventilation_mode(self) -> bool:
        return self.state.get("ventilationMode", False)

    @property
    def low(self) -> bool:
        return self.state.get("low", False)

    @low.setter
    def low(self, value: bool):
        self.put_state_element("low", value)

    @property
    def supports_low(self) -> bool:
        # The eco/reduced "low" field is only present on rooms that expose it.
        return "low" in self.state

    @property
    def supports_eco(self) -> bool:
        # True only when the controller sends a dedicated eco setpoint, meaning
        # the room implements the ECO/COMFORT level model with a temperature
        # schedule.  Devices that have "low" but no eco setpoint (e.g. floor
        # heating via SHC-II) do not support an eco temperature preset.
        return "setpointTemperatureForLevelEco" in self.state

    @property
    def boost_mode(self) -> bool:
        return self.state.get("boostMode", False)

    @boost_mode.setter
    def boost_mode(self, value: bool):
        self.put_state_element("boostMode", value)

    @property
    def summer_mode(self) -> bool:
        return self.state.get("summerMode", False)

    @summer_mode.setter
    def summer_mode(self, value: bool) -> bool:
        self.put_state_element("summerMode", value)

    @property
    def room_control_mode(self) -> str:
        return self.state.get("roomControlMode", "HEATING")

    @room_control_mode.setter
    def room_control_mode(self, value: str):
        self.put_state_element("roomControlMode", value)

    @property
    def cooling_mode(self) -> bool:
        return self.room_control_mode == "COOLING"

    @cooling_mode.setter
    def cooling_mode(self, value: bool):
        self.room_control_mode = "COOLING" if value else "HEATING"

    @property
    def supports_cooling(self) -> bool:
        # FALLBACK heuristic only. The reliable discriminator is the dedicated
        # `ThermostatSupportedControlMode` service (see
        # ThermostatSupportedControlModeService + SHCClimateControl.supports_cooling);
        # this field-presence check is used only when a device does not expose it.
        # Field-presence is imperfect: reporter @jumlu (#67) had radiator rooms with
        # no `roomControlMode` key, but newer firmware (#334) adds the key with value
        # HEATING even to heating-only rooms, so this heuristic can false-positive
        # there. That firmware exposes ThermostatSupportedControlMode, which the model
        # prefers — so the false-positive only affects hypothetical devices that have
        # the key but lack the capability service.
        return "roomControlMode" in self.state

    @property
    def supports_boost_mode(self) -> bool:
        return self.state.get("supportsBoostMode", False)

    @property
    def show_setpoint_temperature(self) -> bool:
        return self.state.get("showSetpointTemperature", False)

    @property
    def has_demand(self) -> bool:
        return bool(self.state.get("hasDemand", False))

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
        print(f"    Room Control Mode        : {self.room_control_mode}")
        print(f"    Cooling Mode             : {self.cooling_mode}")
        print(f"    Supports Cooling         : {self.supports_cooling}")
        print(f"    Supports Boost Mode      : {self.supports_boost_mode}")
        print(f"    Show Setpoint Temperature: {self.show_setpoint_temperature}")


class ThermostatSupportedControlModeService(SHCDeviceService):
    # Per-room capability service on the virtual `roomClimateControl_hz_*`
    # device. Advertises which control modes the room genuinely supports,
    # e.g. ["HEATING", "OFF"] for a radiator room vs
    # ["COOLING", "HEATING", "OFF"] for a chiller/floor-heating room.
    # This is the reliable cooling discriminator (#70/#304/#330/#334) —
    # the `roomControlMode` field of RoomClimateControl is present even on
    # heating-only rooms on newer firmware, so field-presence is unreliable.
    @property
    def supported_control_modes(self) -> list:
        return self.state.get("supportedControlModes", [])

    @property
    def supports_cooling(self) -> bool:
        return "COOLING" in self.supported_control_modes

    def summary(self):
        super().summary()
        print(f"    Supported Control Modes  : {self.supported_control_modes}")


class HeatingCircuitService(SHCDeviceService):
    class OperationMode(Enum):
        AUTOMATIC = "AUTOMATIC"
        MANUAL = "MANUAL"

    class HeatingType(Enum):
        RADIATOR = "RADIATOR"
        CONVECTOR = "CONVECTOR"
        FLOOR = "FLOOR"
        AIRHEATING = "AIRHEATING"
        FANCOIL = "FANCOIL"
        UNKNOWN = "UNKNOWN"

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
    def setpoint_temperature_eco(self) -> float | None:
        value = self.state.get("setpointTemperatureForLevelEco")
        return float(value) if value is not None else None

    @setpoint_temperature_eco.setter
    def setpoint_temperature_eco(self, value: float):
        self.put_state_element("setpointTemperatureForLevelEco", value)

    @property
    def setpoint_temperature_comfort(self) -> float | None:
        value = self.state.get("setpointTemperatureForLevelComfort")
        return float(value) if value is not None else None

    @setpoint_temperature_comfort.setter
    def setpoint_temperature_comfort(self, value: float):
        self.put_state_element("setpointTemperatureForLevelComfort", value)

    @property
    def temperature_override_mode_active(self) -> bool:
        return self.state.get("temperatureOverrideModeActive", False)

    @property
    def temperature_override_feature_enabled(self) -> bool:
        return self.state.get("temperatureOverrideFeatureEnabled", False)

    @property
    def energy_saving_feature_enabled(self) -> bool:
        return self.state.get("energySavingFeatureEnabled", False)

    @property
    def on(self) -> bool:
        return self.state.get("on", False)

    @property
    def heating_type(self):
        raw = self.state.get("heatingType")
        if raw is None:
            return None
        try:
            return self.HeatingType(raw)
        except ValueError:
            return self.HeatingType.UNKNOWN

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
        print(f"    Heating Type               : {self.heating_type}")


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
        VALVE_ADAPTION_REQUESTED = "VALVE_ADAPTION_REQUESTED"
        RANGE_TOO_BIG = "RANGE_TOO_BIG"
        RANGE_TOO_SMALL = "RANGE_TOO_SMALL"
        RUN_TO_START_POSITION = "RUN_TO_START_POSITION"
        START_POSITION_REQUESTED = "START_POSITION_REQUESTED"
        IN_START_POSITION = "IN_START_POSITION"
        NOT_AVAILABLE = "NOT_AVAILABLE"
        NO_VALVE_BODY_ERROR = "NO_VALVE_BODY_ERROR"
        NO_MOTOR_ERROR = "NO_MOTOR_ERROR"
        VALVE_TOO_TIGHT = "VALVE_TOO_TIGHT"
        FIX_MOTOR_LOGIC_REQUESTED = "FIX_MOTOR_LOGIC_REQUESTED"
        FIX_MOTOR_LOGIC_IN_PROGRESS = "FIX_MOTOR_LOGIC_IN_PROGRESS"
        FIX_MOTOR_LOGIC_SUCCESSFUL = "FIX_MOTOR_LOGIC_SUCCESSFUL"
        ERROR = "ERROR"
        UNKNOWN = "UNKNOWN"

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
        return int(self.state.get("automaticPowerOffTime", 0))

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

    @property
    def energyyield(self) -> float:
        # #331: Smart Plug [+M] in Mini-PV mode reports PV production as a
        # separate energyYield (Wh). Older Zigbee plugs / firmware omit the
        # field → return None so the HA layer can skip the yield entities.
        value = self.state.get("energyYield")
        return None if value is None else float(value)

    def summary(self):
        super().summary()
        print(f"    powerConsumption         : {self.powerconsumption}")
        print(f"    energyConsumption        : {self.energyconsumption}")
        print(f"    energyYield              : {self.energyyield}")


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

    @value.setter
    def value(self, state: State):
        self.put_state_element("operationMode", state.value)

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
        # Smoke Detector II reports/accepts the *_REQUESTED variants on its
        # writable Alarm service (SmokeDetector-II spec AlarmState enum). They are
        # both the WRITE values AND the GET read-back values — without them
        # AlarmService.value would raise ValueError on every poll (#174).
        INTRUSION_ALARM_ON_REQUESTED = "INTRUSION_ALARM_ON_REQUESTED"
        INTRUSION_ALARM_OFF_REQUESTED = "INTRUSION_ALARM_OFF_REQUESTED"

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
        # Shutter Control I (old model) does not report an operationState at all
        # — only Shutter Control II does. Per the Bosch API spec (Shutter-local
        # vs Shutter-II), treat its absence as STOPPED so consumers that read
        # operation_state on every update don't crash with a KeyError.
        if "operationState" not in self.state:
            return self.State.STOPPED
        return self.State(self.state["operationState"])

    @property
    def calibrated(self) -> bool:
        # Shutter Control I does not expose `calibrated`; default to False.
        return self.state.get("calibrated", False)

    @property
    def level(self) -> float:
        # Shutter Control I reports level as a STRING ("0.000".."1.000"); Shutter
        # Control II as a number. Coerce to float so position math works for both.
        return float(self.state.get("level", 0.0))

    def summary(self):
        super().summary()
        print(f"    operationState           : {self.operation_state}")
        print(f"    Level                    : {self.level}")
        print(f"    Calibrated               : {self.calibrated}")


class BlindsControlService(SHCDeviceService):
    class BlindsType(Enum):
        DEGREE_90 = "DEGREE_90"
        DEGREE_180 = "DEGREE_180"
        DEGREE_360 = "DEGREE_360"
        EXTERIOR_BLINDS = "EXTERIOR_BLINDS"

    @property
    def current_angle(self) -> float:
        return self.state.get("currentAngle", 0.0)

    @property
    def target_angle(self) -> float:
        return self.state.get("targetAngle", 0.0)

    @target_angle.setter
    def target_angle(self, value: float):
        self.put_state_element("targetAngle", value)

    @property
    def blinds_type(self):
        raw = self.state.get("blindsType")
        if raw is None:
            return None
        return self.BlindsType(raw)

    def summary(self):
        super().summary()
        print(f"    currentAngle              : {self.current_angle}")
        print(f"    targetAngle               : {self.target_angle}")


class BlindsSceneControlService(SHCDeviceService):
    @property
    def level(self) -> float:
        return self.state.get("level", 0.0)

    @level.setter
    def level(self, value: float):
        # Spec requires both level + angle in the BlindsSceneControl PUT.
        self.put_state({"level": value, "angle": self.angle})

    @property
    def angle(self) -> float:
        return self.state.get("angle", 0.0)

    @angle.setter
    def angle(self, value: float):
        # Spec requires both level + angle in the BlindsSceneControl PUT.
        self.put_state({"angle": value, "level": self.level})

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


class CameraAmbientLightService(CameraLightService):
    pass


class CameraFrontLightService(CameraLightService):
    pass


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
        if "instantOfLastImpulse" not in self.state:
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
        UNDEFINED_BUTTON = "UNDEFINED_BUTTON"

    class KeyEvent(Enum):
        PRESS_SHORT = "PRESS_SHORT"
        PRESS_LONG = "PRESS_LONG"
        PRESS_LONG_RELEASED = "PRESS_LONG_RELEASED"
        SWITCH_ON = "SWITCH_ON"
        SWITCH_OFF = "SWITCH_OFF"

    @property
    def keyCode(self) -> int:
        return self.state["keyCode"] if "keyCode" in self.state else 0

    @property
    def keyName(self) -> KeyState:
        if "keyName" not in self.state:
            return None
        return self.KeyState(self.state["keyName"])

    @property
    def eventType(self) -> KeyEvent:
        if "eventType" not in self.state:
            return None
        return self.KeyEvent(self.state["eventType"])

    @eventType.setter
    def eventType(self, value: KeyEvent):
        self.state["eventType"] = value.value

    @property
    def eventTimestamp(self) -> int:
        if "eventTimestamp" not in self.state:
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


class DetectionTestService(SHCDeviceService):
    # GET state values (detectionState reported by the controller).
    class DetectionState(Enum):
        DETECTION_TEST_STARTED = "DETECTION_TEST_STARTED"
        DETECTION_TEST_STOPPED = "DETECTION_TEST_STOPPED"
        DETECTION_TEST_UNKNOWN = "DETECTION_TEST_UNKNOWN"

    # PUT request values (detectionState accepted by the controller). Same key,
    # different enum vocabulary — see the MotionDetector OpenAPI spec
    # (/services/DetectionTest/state PUT: "Start or stop a walk test").
    class DetectionStateRequest(Enum):
        DETECTION_STATE_START = "DETECTION_STATE_START"
        DETECTION_STATE_STOP = "DETECTION_STATE_STOP"

    @property
    def detection_state(self) -> "DetectionTestService.DetectionState":
        raw = self.state.get("detectionState")
        if raw is None:
            return self.DetectionState.DETECTION_TEST_UNKNOWN
        try:
            return self.DetectionState(raw)
        except ValueError:
            return self.DetectionState.DETECTION_TEST_UNKNOWN

    def set_detection_state_request(
        self, value: "DetectionTestService.DetectionStateRequest"
    ):
        # Write to detectionStateRequest, NOT detectionState. detectionState is
        # the read-only reported state (DETECTION_TEST_STARTED/STOPPED); the
        # controller rejects a write to it with 503 SERVICE_INVOCATION_FAILED
        # (hass#325). The APK capability dump confirms a separate request field
        # detectionStateRequest (START/STOP) — same split as WalkTest's
        # walkState / walkStateRequest. (Bosch's own OpenAPI spec is wrong here.)
        self.put_state_element("detectionStateRequest", value.value)

    async def async_set_detection_state_request(
        self, value: "DetectionTestService.DetectionStateRequest"
    ):
        await self.async_put_state_element("detectionStateRequest", value.value)

    def summary(self):
        super().summary()
        print(f"    detectionState           : {self.detection_state}")


class LatestTamperService(SHCDeviceService):
    @property
    def tamper_protection_enabled(self) -> bool:
        return self.state["tamperProtectionEnabled"]

    @tamper_protection_enabled.setter
    def tamper_protection_enabled(self, value: bool):
        self.put_state_element("tamperProtectionEnabled", bool(value))

    async def async_set_tamper_protection_enabled(self, value: bool):
        await self.async_put_state_element("tamperProtectionEnabled", bool(value))

    def reset_tampered_state(self):
        """POST operation/resetTamperedState — confirm the device is back in place."""
        self._api.post_device_service_operation(
            self.device_id.replace("#", "%23"), self.id, "resetTamperedState"
        )

    async def async_reset_tampered_state(self):
        """Async counterpart to reset_tampered_state."""
        await self._api.post_device_service_operation(
            self.device_id.replace("#", "%23"), self.id, "resetTamperedState"
        )

    @property
    def was_tampered(self) -> bool:
        return self.state["wasTampered"]

    @property
    def last_tamper_time(self) -> str:
        return (
            self.state["lastTamperTime"]
            if "lastTamperTime" in self.state
            else "n/a"
        )

    def summary(self):
        super().summary()
        print(f"    tamperProtectionEnabled  : {self.tamper_protection_enabled}")
        print(f"    wasTampered              : {self.was_tampered}")
        print(f"    lastTamperTime           : {self.last_tamper_time}")


class PollControlService(SHCDeviceService):
    class PollControlState(Enum):
        LONG = "LONG"
        SHORT = "SHORT"
        UNKNOWN = "UNKNOWN"

    @property
    def longPollInterval(self) -> PollControlState:
        raw = self.state.get("longPollInterval")
        if raw is None:
            return self.PollControlState.UNKNOWN
        try:
            return self.PollControlState(raw)
        except ValueError:
            return self.PollControlState.UNKNOWN

    @longPollInterval.setter
    def longPollInterval(self, value: "PollControlService.PollControlState"):
        # Spec only accepts SHORT / LONG for writes.
        self.put_state_element("longPollInterval", value.value)

    async def async_set_long_poll_interval(
        self, value: "PollControlService.PollControlState"
    ):
        await self.async_put_state_element("longPollInterval", value.value)

    def summary(self):
        super().summary()
        print(f"    longPollInterval         : {self.longPollInterval}")


class PirSensorConfigurationService(SHCDeviceService):
    class MotionSensitivity(Enum):
        HIGH = "HIGH"
        MIDDLE = "MIDDLE"
        LOW = "LOW"
        UNKNOWN = "UNKNOWN"

    @property
    def motionSensitivity(self) -> MotionSensitivity:
        return self.MotionSensitivity(self.state["motionSensitivity"])

    def summary(self):
        super().summary()
        print(f"    motionSensitivity        : {self.motionSensitivity}")


class OccupancyDetectionService(SHCDeviceService):
    @property
    def isOccupied(self) -> bool:
        return self.state["isOccupied"]

    @property
    def lastOccupancyChangeTime(self) -> str:
        return (
            self.state["lastOccupancyChangeTime"]
            if "lastOccupancyChangeTime" in self.state
            else "n/a"
        )

    @property
    def last_occupancy_change_time(self):
        return self.state.get("lastOccupancyChangeTime")

    def summary(self):
        super().summary()
        print(f"    isOccupied                : {self.isOccupied}")
        print(f"    lastOccupancyChangeTime   : {self.lastOccupancyChangeTime}")


class PetImmunityService(SHCDeviceService):
    @property
    def enabled(self) -> bool:
        return self.state["enabled"]

    @enabled.setter
    def enabled(self, value: bool):
        self.put_state_element("enabled", value)

    def summary(self):
        super().summary()
        print(f"    enabled                  : {self.enabled}")


class SmartSensitivityControlService(SHCDeviceService):
    class SmartSensitivityContext(Enum):
        SECURITY = "SECURITY"
        COMFORT = "COMFORT"
        UNKNOWN = "UNKNOWN"

    # APK: SmartSensitivitySetting.manualLevel / automaticLevel type is MotionSensitivity
    class MotionSensitivity(Enum):
        HIGH = "HIGH"
        MIDDLE = "MIDDLE"
        LOW = "LOW"
        UNKNOWN = "UNKNOWN"

    @property
    def enabled(self) -> bool:
        return bool(self.state.get("enabled", False))

    @enabled.setter
    def enabled(self, value: bool):
        self.put_state_element("enabled", value)

    @property
    def sensitivities(self) -> list:
        return self.state.get("sensitivities", [])

    def get_sensitivity(self, context: "SmartSensitivityControlService.SmartSensitivityContext"):
        """Return the sensitivity dict for the given context, or None if not found."""
        ctx_value = context.value if hasattr(context, "value") else context
        for entry in self.sensitivities:
            if entry.get("context") == ctx_value:
                return entry
        return None

    def set_enabled(self, value: bool):
        self.put_state_element("enabled", value)

    async def async_set_enabled(self, value: bool):
        await self.async_put_state_element("enabled", value)

    def set_manual_level(
        self,
        context: "SmartSensitivityControlService.SmartSensitivityContext",
        level: "SmartSensitivityControlService.MotionSensitivity",
    ):
        """Set manualLevel (MotionSensitivity enum) for the given context.

        APK: manualLevel and automaticLevel are MotionSensitivity enum strings
        (HIGH/MIDDLE/LOW/UNKNOWN). automaticLevel is read-only from the SHC;
        it is round-tripped in the PUT payload unchanged from the state dict.
        """
        ctx_value = context.value if hasattr(context, "value") else context
        level_value = level.value if hasattr(level, "value") else level
        updated = []
        for entry in self.sensitivities:
            if entry.get("context") == ctx_value:
                entry = {**entry, "manualLevel": level_value}
            updated.append(entry)
        self.put_state({"enabled": self.enabled, "sensitivities": updated})

    async def async_set_manual_level(
        self,
        context: "SmartSensitivityControlService.SmartSensitivityContext",
        level: "SmartSensitivityControlService.MotionSensitivity",
    ):
        """Async version of set_manual_level."""
        ctx_value = context.value if hasattr(context, "value") else context
        level_value = level.value if hasattr(level, "value") else level
        updated = []
        for entry in self.sensitivities:
            if entry.get("context") == ctx_value:
                entry = {**entry, "manualLevel": level_value}
            updated.append(entry)
        await self.async_put_state({"enabled": self.enabled, "sensitivities": updated})

    def summary(self):
        super().summary()
        print(f"    enabled                  : {self.enabled}")
        print(f"    sensitivities            : {self.sensitivities}")


class WalkTestService(SHCDeviceService):
    class WalkState(Enum):
        WALK_TEST_STARTED = "WALK_TEST_STARTED"
        WALK_TEST_STOPPED = "WALK_TEST_STOPPED"  # APK: WalkTestState.WalkState
        UNKNOWN = "UNKNOWN"

    class WalkStateRequest(Enum):
        WALK_STATE_START = "WALK_STATE_START"
        WALK_STATE_STOP = "WALK_STATE_STOP"  # APK: WalkTestState.WalkStateRequest
        UNKNOWN = "UNKNOWN"

    class PetImmunityState(Enum):
        PET_IMMUNITY_ENABLED = "PET_IMMUNITY_ENABLED"
        PET_IMMUNITY_DISABLED = "PET_IMMUNITY_DISABLED"  # APK: WalkTestState.PetImmunityState
        UNKNOWN = "UNKNOWN"

    @property
    def walk_state(self) -> "WalkTestService.WalkState":
        raw = self.state.get("walkState")
        if raw is None:
            return self.WalkState.UNKNOWN
        try:
            return self.WalkState(raw)
        except ValueError:
            return self.WalkState.UNKNOWN

    @property
    def walk_state_request(self) -> "WalkTestService.WalkStateRequest":
        raw = self.state.get("walkStateRequest")
        if raw is None:
            return self.WalkStateRequest.UNKNOWN
        try:
            return self.WalkStateRequest(raw)
        except ValueError:
            return self.WalkStateRequest.UNKNOWN

    @walk_state_request.setter
    def walk_state_request(self, value: "WalkTestService.WalkStateRequest"):
        self.put_state_element("walkStateRequest", value.value)

    @property
    def pet_immunity_state(self) -> "WalkTestService.PetImmunityState":
        raw = self.state.get("petImmunityState")
        if raw is None:
            return self.PetImmunityState.UNKNOWN
        try:
            return self.PetImmunityState(raw)
        except ValueError:
            return self.PetImmunityState.UNKNOWN

    def set_walk_state_request(self, value: "WalkTestService.WalkStateRequest"):
        self.put_state_element("walkStateRequest", value.value)

    async def async_set_walk_state_request(self, value: "WalkTestService.WalkStateRequest"):
        await self.async_put_state_element("walkStateRequest", value.value)

    def summary(self):
        super().summary()
        print(f"    walkState                : {self.walk_state}")
        print(f"    walkStateRequest         : {self.walk_state_request}")
        print(f"    petImmunityState         : {self.pet_immunity_state}")


class SmokeSensitivityService(SHCDeviceService):
    class SmokeSensitivityLevel(Enum):
        HIGH = "HIGH"
        MIDDLE = "MIDDLE"
        LOW = "LOW"
        UNKNOWN = "UNKNOWN"

    @property
    def smoke_sensitivity(self) -> "SmokeSensitivityService.SmokeSensitivityLevel":
        raw = self.state.get("smokeSensitivity")
        if raw is None:
            return None
        try:
            return self.SmokeSensitivityLevel(raw)
        except ValueError:
            return self.SmokeSensitivityLevel.UNKNOWN

    @smoke_sensitivity.setter
    def smoke_sensitivity(self, value: "SmokeSensitivityService.SmokeSensitivityLevel"):
        self.put_state_element("smokeSensitivity", value.value)

    @property
    def pre_alarm_enabled(self) -> bool:
        return bool(self.state.get("preAlarmEnabled", False))

    @pre_alarm_enabled.setter
    def pre_alarm_enabled(self, value: bool):
        self.put_state_element("preAlarmEnabled", value)

    def set_smoke_sensitivity(self, value: "SmokeSensitivityService.SmokeSensitivityLevel"):
        self.put_state_element("smokeSensitivity", value.value)

    async def async_set_smoke_sensitivity(
        self, value: "SmokeSensitivityService.SmokeSensitivityLevel"
    ):
        await self.async_put_state_element("smokeSensitivity", value.value)

    def set_pre_alarm_enabled(self, value: bool):
        self.put_state_element("preAlarmEnabled", value)

    async def async_set_pre_alarm_enabled(self, value: bool):
        await self.async_put_state_element("preAlarmEnabled", value)

    def summary(self):
        super().summary()
        print(f"    smokeSensitivity         : {self.smoke_sensitivity}")
        print(f"    preAlarmEnabled          : {self.pre_alarm_enabled}")


class TwinguardNightlyPromiseService(SHCDeviceService):
    @property
    def nightly_promise_enabled(self) -> bool:
        return bool(self.state.get("nightlyPromiseEnabled", False))

    @nightly_promise_enabled.setter
    def nightly_promise_enabled(self, value: bool):
        self.put_state_element("nightlyPromiseEnabled", value)

    def set_nightly_promise_enabled(self, value: bool):
        self.put_state_element("nightlyPromiseEnabled", value)

    async def async_set_nightly_promise_enabled(self, value: bool):
        await self.async_put_state_element("nightlyPromiseEnabled", value)

    def summary(self):
        super().summary()
        print(f"    nightlyPromiseEnabled    : {self.nightly_promise_enabled}")


class EnergySavingModeService(SHCDeviceService):
    @property
    def energy_saving_mode_enabled(self) -> bool:
        return bool(self.state.get("energySavingModeEnabled", False))

    @energy_saving_mode_enabled.setter
    def energy_saving_mode_enabled(self, value: bool):
        self.put_state_element("energySavingModeEnabled", value)

    @property
    def power_threshold(self):
        return self.state.get("powerThreshold")

    @power_threshold.setter
    def power_threshold(self, value):
        self.put_state_element("powerThreshold", value)

    @property
    def enter_duration_seconds(self) -> int:
        return int(self.state.get("enterDurationSeconds", 0))

    @enter_duration_seconds.setter
    def enter_duration_seconds(self, value: int):
        self.put_state_element("enterDurationSeconds", value)

    def set_energy_saving_mode_enabled(self, value: bool):
        self.put_state_element("energySavingModeEnabled", value)

    async def async_set_energy_saving_mode_enabled(self, value: bool):
        await self.async_put_state_element("energySavingModeEnabled", value)

    def set_power_threshold(self, value):
        self.put_state_element("powerThreshold", value)

    async def async_set_power_threshold(self, value):
        await self.async_put_state_element("powerThreshold", value)

    def set_enter_duration_seconds(self, value: int):
        self.put_state_element("enterDurationSeconds", value)

    async def async_set_enter_duration_seconds(self, value: int):
        await self.async_put_state_element("enterDurationSeconds", value)

    def summary(self):
        super().summary()
        print(f"    energySavingModeEnabled  : {self.energy_saving_mode_enabled}")
        print(f"    powerThreshold           : {self.power_threshold}")
        print(f"    enterDurationSeconds     : {self.enter_duration_seconds}")


class LedBrightnessConfigurationService(SHCDeviceService):
    @property
    def brightness(self):
        return self.state.get("brightness")

    @brightness.setter
    def brightness(self, value):
        self.put_state_element("brightness", value)

    @property
    def max_brightness(self):
        return self.state.get("maxBrightness")

    @property
    def min_brightness(self):
        return self.state.get("minBrightness")

    @property
    def step_size(self):
        return self.state.get("stepSize")

    def set_brightness(self, value):
        self.put_state_element("brightness", value)

    async def async_set_brightness(self, value):
        await self.async_put_state_element("brightness", value)

    def summary(self):
        super().summary()
        print(f"    brightness               : {self.brightness}")
        print(f"    maxBrightness            : {self.max_brightness}")
        print(f"    minBrightness            : {self.min_brightness}")
        print(f"    stepSize                 : {self.step_size}")


class PowerSwitchConfigurationService(SHCDeviceService):
    class StateAfterPowerOutage(Enum):
        OFF = "OFF"
        ON = "ON"
        LAST_STATE = "LAST_STATE"
        UNKNOWN = "UNKNOWN"

    @property
    def state_after_power_outage(self) -> "PowerSwitchConfigurationService.StateAfterPowerOutage":
        raw = self.state.get("stateAfterPowerOutage")
        if raw is None:
            return None
        try:
            return self.StateAfterPowerOutage(raw)
        except ValueError:
            return self.StateAfterPowerOutage.UNKNOWN

    @state_after_power_outage.setter
    def state_after_power_outage(
        self, value: "PowerSwitchConfigurationService.StateAfterPowerOutage"
    ):
        self.put_state_element("stateAfterPowerOutage", value.value)

    @property
    def supported_states_after_power_outage(self) -> list:
        return self.state.get("supportedStatesAfterPowerOutage", [])

    def set_state_after_power_outage(
        self, value: "PowerSwitchConfigurationService.StateAfterPowerOutage"
    ):
        self.put_state_element("stateAfterPowerOutage", value.value)

    async def async_set_state_after_power_outage(
        self, value: "PowerSwitchConfigurationService.StateAfterPowerOutage"
    ):
        await self.async_put_state_element("stateAfterPowerOutage", value.value)

    def summary(self):
        super().summary()
        print(f"    stateAfterPowerOutage            : {self.state_after_power_outage}")
        print(
            f"    supportedStatesAfterPowerOutage  : {self.supported_states_after_power_outage}"
        )


class PowerSwitchWarningService(SHCDeviceService):
    @property
    def warning_suppressed(self) -> bool:
        return bool(self.state.get("warningSuppressed", False))

    @warning_suppressed.setter
    def warning_suppressed(self, value: bool):
        self.put_state_element("warningSuppressed", value)

    def set_warning_suppressed(self, value: bool):
        self.put_state_element("warningSuppressed", value)

    async def async_set_warning_suppressed(self, value: bool):
        await self.async_put_state_element("warningSuppressed", value)

    def summary(self):
        super().summary()
        print(f"    warningSuppressed        : {self.warning_suppressed}")


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

    @property
    def comfortZone(self) -> dict:
        return self.state.get("comfortZone", {})

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
        print("    not yet implemented!")


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
        if not faults or not faults.get("entries"):
            return self.State("OK")
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


class DisplayConfiguration(SHCDeviceService):
    @property
    def display_brightness(self):
        return self.state.get("displayBrightness")

    @display_brightness.setter
    def display_brightness(self, value):
        self.put_state_element("displayBrightness", value)

    @property
    def display_brightness_max(self):
        return self.state.get("displayBrightnessMax")

    @property
    def display_brightness_min(self):
        return self.state.get("displayBrightnessMin")

    @property
    def display_brightness_step_size(self):
        return self.state.get("displayBrightnessStepSize")

    @property
    def display_on_time(self):
        return self.state.get("displayOnTime")

    @display_on_time.setter
    def display_on_time(self, value):
        self.put_state_element("displayOnTime", value)

    @property
    def display_on_time_max(self):
        return self.state.get("displayOnTimeMax")

    @property
    def display_on_time_min(self):
        return self.state.get("displayOnTimeMin")

    @property
    def display_on_time_step_size(self):
        return self.state.get("displayOnTimeStepSize")

    @property
    def humidity_warning_enabled(self):
        v = self.state.get("humidityWarningEnabled")
        return None if v is None else bool(v)

    @humidity_warning_enabled.setter
    def humidity_warning_enabled(self, value: bool):
        self.put_state_element("humidityWarningEnabled", value)

    def set_displayBrightness(self, value):
        self.put_state_element("displayBrightness", value)

    async def async_set_displayBrightness(self, value):
        await self.async_put_state_element("displayBrightness", value)

    def set_displayOnTime(self, value):
        self.put_state_element("displayOnTime", value)

    async def async_set_displayOnTime(self, value):
        await self.async_put_state_element("displayOnTime", value)

    def set_humidityWarningEnabled(self, value: bool):
        self.put_state_element("humidityWarningEnabled", value)

    async def async_set_humidityWarningEnabled(self, value: bool):
        await self.async_put_state_element("humidityWarningEnabled", value)

    def summary(self):
        super().summary()
        print(f"    displayBrightness        : {self.display_brightness}")
        print(f"    displayOnTime            : {self.display_on_time}")
        print(f"    humidityWarningEnabled   : {self.humidity_warning_enabled}")


class DisplayDirection(SHCDeviceService):
    class Direction(Enum):
        NORMAL = "NORMAL"
        REVERSED = "REVERSED"
        UNKNOWN = "UNKNOWN"

    @property
    def direction(self) -> "DisplayDirection.Direction":
        raw = self.state.get("direction")
        if raw is None:
            return None
        try:
            return self.Direction(raw)
        except ValueError:
            return self.Direction.UNKNOWN

    @direction.setter
    def direction(self, value: "DisplayDirection.Direction"):
        self.put_state_element("direction", value.value)

    def set_direction(self, value: "DisplayDirection.Direction"):
        self.put_state_element("direction", value.value)

    async def async_set_direction(self, value: "DisplayDirection.Direction"):
        await self.async_put_state_element("direction", value.value)

    def summary(self):
        super().summary()
        print(f"    direction                : {self.direction}")


class DisplayedTemperatureConfiguration(SHCDeviceService):
    class DisplayedTemperature(Enum):
        SETPOINT = "SETPOINT"
        MEASURED = "MEASURED"
        UNKNOWN = "UNKNOWN"

    @property
    def displayed_temperature(self) -> "DisplayedTemperatureConfiguration.DisplayedTemperature":
        raw = self.state.get("displayedTemperature")
        if raw is None:
            return None
        try:
            return self.DisplayedTemperature(raw)
        except ValueError:
            return self.DisplayedTemperature.UNKNOWN

    @displayed_temperature.setter
    def displayed_temperature(
        self, value: "DisplayedTemperatureConfiguration.DisplayedTemperature"
    ):
        self.put_state_element("displayedTemperature", value.value)

    def set_displayedTemperature(
        self, value: "DisplayedTemperatureConfiguration.DisplayedTemperature"
    ):
        self.put_state_element("displayedTemperature", value.value)

    async def async_set_displayedTemperature(
        self, value: "DisplayedTemperatureConfiguration.DisplayedTemperature"
    ):
        await self.async_put_state_element("displayedTemperature", value.value)

    def summary(self):
        super().summary()
        print(f"    displayedTemperature     : {self.displayed_temperature}")


class TerminalConfiguration(SHCDeviceService):
    class Type(Enum):
        NOT_CONNECTED = "NOT_CONNECTED"
        FLOOR_SENSOR_CONNECTED = "FLOOR_SENSOR_CONNECTED"
        FLOOR_SENSOR_USED_FOR_REGULATION = "FLOOR_SENSOR_USED_FOR_REGULATION"
        FLOOR_SENSOR_DISPLAYED = "FLOOR_SENSOR_DISPLAYED"
        FLOOR_SENSOR_DISPLAYED_AND_USED_FOR_REGULATION = (
            "FLOOR_SENSOR_DISPLAYED_AND_USED_FOR_REGULATION"
        )
        VOLT_FREE_SENSOR_CONNECTED = "VOLT_FREE_SENSOR_CONNECTED"
        VOLT_FREE_SENSOR_CONNECTED_AND_USED_FOR_OPERATION = (
            "VOLT_FREE_SENSOR_CONNECTED_AND_USED_FOR_OPERATION"
        )
        OUTDOOR_SENSOR_CONNECTED = "OUTDOOR_SENSOR_CONNECTED"
        UNKNOWN = "UNKNOWN"

    @property
    def type(self) -> "TerminalConfiguration.Type":
        raw = self.state.get("type")
        if raw is None:
            return None
        try:
            return self.Type(raw)
        except ValueError:
            return self.Type.UNKNOWN

    @type.setter
    def type(self, value: "TerminalConfiguration.Type"):
        self.put_state_element("type", value.value)

    @property
    def supported_types(self) -> list:
        return self.state.get("supportedTypes", [])

    @property
    def temperature(self):
        return self.state.get("temperature")

    def set_type(self, value: "TerminalConfiguration.Type"):
        self.put_state_element("type", value.value)

    async def async_set_type(self, value: "TerminalConfiguration.Type"):
        await self.async_put_state_element("type", value.value)

    def summary(self):
        super().summary()
        print(f"    type                     : {self.type}")
        print(f"    supportedTypes           : {self.supported_types}")
        print(f"    temperature              : {self.temperature}")


class WallThermostatConfiguration(SHCDeviceService):
    class ValveType(Enum):
        NORMALLY_CLOSE = "NORMALLY_CLOSE"
        NORMALLY_OPEN = "NORMALLY_OPEN"
        UNKNOWN = "UNKNOWN"

    class HeaterType(Enum):
        FLOOR_HEATING = "FLOOR_HEATING"
        FLOOR_HEATING_LOW_ENERGY = "FLOOR_HEATING_LOW_ENERGY"
        RADIATOR = "RADIATOR"
        CONVECTOR_PASSIVE = "CONVECTOR_PASSIVE"
        CONVECTOR_ACTIVE = "CONVECTOR_ACTIVE"
        UNKNOWN = "UNKNOWN"

    @property
    def valve_type(self) -> "WallThermostatConfiguration.ValveType":
        raw = self.state.get("valveType")
        if raw is None:
            return None
        try:
            return self.ValveType(raw)
        except ValueError:
            return self.ValveType.UNKNOWN

    @valve_type.setter
    def valve_type(self, value: "WallThermostatConfiguration.ValveType"):
        self.put_state_element("valveType", value.value)

    @property
    def heater_type(self) -> "WallThermostatConfiguration.HeaterType":
        raw = self.state.get("heaterType")
        if raw is None:
            return None
        try:
            return self.HeaterType(raw)
        except ValueError:
            return self.HeaterType.UNKNOWN

    @heater_type.setter
    def heater_type(self, value: "WallThermostatConfiguration.HeaterType"):
        self.put_state_element("heaterType", value.value)

    def set_valveType(self, value: "WallThermostatConfiguration.ValveType"):
        self.put_state_element("valveType", value.value)

    async def async_set_valveType(self, value: "WallThermostatConfiguration.ValveType"):
        await self.async_put_state_element("valveType", value.value)

    def set_heaterType(self, value: "WallThermostatConfiguration.HeaterType"):
        self.put_state_element("heaterType", value.value)

    async def async_set_heaterType(self, value: "WallThermostatConfiguration.HeaterType"):
        await self.async_put_state_element("heaterType", value.value)

    def summary(self):
        super().summary()
        print(f"    valveType                : {self.valve_type}")
        print(f"    heaterType               : {self.heater_type}")


class SwitchConfiguration(SHCDeviceService):
    class SwitchType(Enum):
        NONE = "NONE"
        PUSHBUTTON = "PUSHBUTTON"
        SWITCH = "SWITCH"
        NO_SWITCH = "NO_SWITCH"
        UNKNOWN = "UNKNOWN"

    class ActuatorType(Enum):
        NORMALLY_CLOSED = "NORMALLY_CLOSED"
        NORMALLY_OPEN = "NORMALLY_OPEN"
        UNSUPPORTED = "UNSUPPORTED"
        UNKNOWN = "UNKNOWN"

    class OutputMode(Enum):
        ATTACHED = "ATTACHED"
        DETACHED = "DETACHED"
        DETACHED_SHORT_PRESS = "DETACHED_SHORT_PRESS"
        DETACHED_LONG_PRESS = "DETACHED_LONG_PRESS"
        UNSUPPORTED = "UNSUPPORTED"
        UNKNOWN = "UNKNOWN"

    @property
    def switch_type(self) -> "SwitchConfiguration.SwitchType":
        raw = self.state.get("switchType")
        if raw is None:
            return None
        try:
            return self.SwitchType(raw)
        except ValueError:
            return self.SwitchType.UNKNOWN

    @switch_type.setter
    def switch_type(self, value: "SwitchConfiguration.SwitchType"):
        self.put_state_element("switchType", value.value)

    @property
    def swap_inputs(self) -> bool:
        return bool(self.state.get("swapInputs", False))

    @swap_inputs.setter
    def swap_inputs(self, value: bool):
        self.put_state_element("swapInputs", value)

    @property
    def swap_outputs(self) -> bool:
        return bool(self.state.get("swapOutputs", False))

    @swap_outputs.setter
    def swap_outputs(self, value: bool):
        self.put_state_element("swapOutputs", value)

    @property
    def actuator_type(self) -> "SwitchConfiguration.ActuatorType":
        raw = self.state.get("actuatorType")
        if raw is None:
            return None
        try:
            return self.ActuatorType(raw)
        except ValueError:
            return self.ActuatorType.UNKNOWN

    @actuator_type.setter
    def actuator_type(self, value: "SwitchConfiguration.ActuatorType"):
        self.put_state_element("actuatorType", value.value)

    @property
    def output_mode(self) -> "SwitchConfiguration.OutputMode":
        raw = self.state.get("outputMode")
        if raw is None:
            return None
        try:
            return self.OutputMode(raw)
        except ValueError:
            return self.OutputMode.UNKNOWN

    @output_mode.setter
    def output_mode(self, value: "SwitchConfiguration.OutputMode"):
        self.put_state_element("outputMode", value.value)

    @property
    def supports_swap_outputs(self):
        return self.state.get("supportsSwapOutputs")

    @property
    def supported_output_modes(self) -> list:
        return self.state.get("supportedOutputModes", [])

    def set_switchType(self, value: "SwitchConfiguration.SwitchType"):
        self.put_state_element("switchType", value.value)

    async def async_set_switchType(self, value: "SwitchConfiguration.SwitchType"):
        await self.async_put_state_element("switchType", value.value)

    def set_swapInputs(self, value: bool):
        self.put_state_element("swapInputs", value)

    async def async_set_swapInputs(self, value: bool):
        await self.async_put_state_element("swapInputs", value)

    def set_swapOutputs(self, value: bool):
        self.put_state_element("swapOutputs", value)

    async def async_set_swapOutputs(self, value: bool):
        await self.async_put_state_element("swapOutputs", value)

    def set_actuatorType(self, value: "SwitchConfiguration.ActuatorType"):
        self.put_state_element("actuatorType", value.value)

    async def async_set_actuatorType(self, value: "SwitchConfiguration.ActuatorType"):
        await self.async_put_state_element("actuatorType", value.value)

    def set_outputMode(self, value: "SwitchConfiguration.OutputMode"):
        self.put_state_element("outputMode", value.value)

    async def async_set_outputMode(self, value: "SwitchConfiguration.OutputMode"):
        await self.async_put_state_element("outputMode", value.value)

    def summary(self):
        super().summary()
        print(f"    switchType               : {self.switch_type}")
        print(f"    swapInputs               : {self.swap_inputs}")
        print(f"    swapOutputs              : {self.swap_outputs}")
        print(f"    actuatorType             : {self.actuator_type}")
        print(f"    outputMode               : {self.output_mode}")
        print(f"    supportsSwapOutputs      : {self.supports_swap_outputs}")
        print(f"    supportedOutputModes     : {self.supported_output_modes}")


class OutdoorSirenService(SHCDeviceService):
    """Outdoor Siren state + configuration.

    Alarm activation (acousticAlarmOn / visualAlarmOn) is read-only — the siren
    fires only as a consequence of the intrusion system. The only writable part
    is the configuration block, and a triggerTestAlarm operation. See
    OutdoorSiren-local-openapi-v3.yml.
    """

    class SoundLevel(Enum):
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"

    @property
    def acoustic_alarm_on(self) -> bool:
        return bool(self.state.get("acousticAlarmOn", False))

    @property
    def visual_alarm_on(self) -> bool:
        return bool(self.state.get("visualAlarmOn", False))

    @property
    def tamper_activated(self) -> bool:
        return bool(self.state.get("tamperActivated", False))

    @property
    def legacy_alarm(self) -> bool:
        return bool(self.state.get("legacyAlarm", False))

    @property
    def smart_alarm(self) -> bool:
        return bool(self.state.get("smartAlarm", False))

    @property
    def _config(self) -> dict:
        return self.state.get("outdoorSirenConfiguration", {}) or {}

    @property
    def alarm_duration(self) -> int:
        return int(self._config.get("alarmDuration", 0))

    @property
    def flash_duration(self) -> int:
        return int(self._config.get("flashDuration", 0))

    @property
    def alarm_delay(self) -> int:
        return int(self._config.get("alarmDelay", 0))

    @property
    def flash_delay(self) -> int:
        return int(self._config.get("flashDelay", 0))

    @property
    def sound_level(self) -> "OutdoorSirenService.SoundLevel":
        try:
            return self.SoundLevel(self._config.get("soundLevel", "MEDIUM"))
        except ValueError:
            return self.SoundLevel.MEDIUM

    def _merged_config(self, **overrides) -> dict:
        # The PUT requires the full configuration block (all 5 fields). Start
        # from the current config and override only the changed field.
        cfg = {
            "alarmDuration": self.alarm_duration,
            "flashDuration": self.flash_duration,
            "soundLevel": self.sound_level.value,
            "alarmDelay": self.alarm_delay,
            "flashDelay": self.flash_delay,
        }
        cfg.update(overrides)
        return cfg

    async def async_set_configuration(
        self,
        *,
        alarm_duration: int = None,
        flash_duration: int = None,
        sound_level: "OutdoorSirenService.SoundLevel" = None,
        alarm_delay: int = None,
        flash_delay: int = None,
    ):
        """Async write: update one or more configuration fields.

        Bosch requires the whole configuration block on every PUT, so unchanged
        fields are filled from the current state. If the current state has no
        configuration block yet (e.g. a partial push before the first full
        read), skip the write rather than PUT a block of zeros that would wipe
        the user's settings.
        """
        if not self._config:
            logger.warning(
                "OutdoorSiren %s: configuration not yet known, skipping write to "
                "avoid resetting siren settings",
                self.device_id,
            )
            return
        overrides = {}
        if alarm_duration is not None:
            overrides["alarmDuration"] = alarm_duration
        if flash_duration is not None:
            overrides["flashDuration"] = flash_duration
        if sound_level is not None:
            overrides["soundLevel"] = sound_level.value
        if alarm_delay is not None:
            overrides["alarmDelay"] = alarm_delay
        if flash_delay is not None:
            overrides["flashDelay"] = flash_delay
        await self.async_put_state_element(
            "outdoorSirenConfiguration", self._merged_config(**overrides)
        )

    async def async_trigger_test_alarm(
        self, sound_level: "OutdoorSirenService.SoundLevel" = None
    ):
        """Async: fire a short test alarm (operation/triggerTestAlarm)."""
        level = (sound_level or self.sound_level).value
        await self.async_post_operation("triggerTestAlarm", {"soundLevel": level})

    def summary(self):
        super().summary()
        print(f"    acousticAlarmOn          : {self.acoustic_alarm_on}")
        print(f"    visualAlarmOn            : {self.visual_alarm_on}")
        print(f"    tamperActivated          : {self.tamper_activated}")
        print(f"    soundLevel               : {self.sound_level}")
        print(f"    alarmDuration            : {self.alarm_duration}")
        print(f"    flashDuration            : {self.flash_duration}")


class OutdoorSirenPowerSupplyService(SHCDeviceService):
    """Outdoor Siren power-supply diagnostics (read-only)."""

    class ConfiguredPowerSupply(Enum):
        NONE = "NONE"
        AC = "AC"
        DC = "DC"
        UNKNOWN = "UNKNOWN"

    class MainPowerSupply(Enum):
        BATTERY = "BATTERY"
        SOLAR = "SOLAR"
        V12 = "V12"
        V230 = "V230"
        UNKNOWN = "UNKNOWN"

    class SolarChargingScore(Enum):
        BAD = "BAD"
        MEDIUM = "MEDIUM"
        GOOD = "GOOD"
        UNKNOWN = "UNKNOWN"

    @property
    def battery_percentage_remaining(self) -> int:
        return int(self.state.get("batteryPercentageRemaining", 0))

    @property
    def ac_dc_error(self) -> bool:
        return bool(self.state.get("acDcError", False))

    @property
    def battery_defect(self) -> bool:
        return bool(self.state.get("batteryDefect", False))

    @property
    def battery_temperature_abnormal(self) -> bool:
        return bool(self.state.get("batteryTemperatureAbnormal", False))

    @property
    def primary_power_supply_outage(self) -> bool:
        return bool(self.state.get("primaryPowerSupplyOutage", False))

    @property
    def solar_charging_current(self) -> int:
        return int(self.state.get("solarChargingCurrent", 0))

    @property
    def configured_power_supply(self) -> "OutdoorSirenPowerSupplyService.ConfiguredPowerSupply":
        try:
            return self.ConfiguredPowerSupply(self.state.get("configuredPowerSupply", "UNKNOWN"))
        except ValueError:
            return self.ConfiguredPowerSupply.UNKNOWN

    @property
    def main_power_supply(self) -> "OutdoorSirenPowerSupplyService.MainPowerSupply":
        try:
            return self.MainPowerSupply(self.state.get("mainPowerSupply", "UNKNOWN"))
        except ValueError:
            return self.MainPowerSupply.UNKNOWN

    @property
    def solar_charging_score(self) -> "OutdoorSirenPowerSupplyService.SolarChargingScore":
        try:
            return self.SolarChargingScore(self.state.get("solarChargingScore", "UNKNOWN"))
        except ValueError:
            return self.SolarChargingScore.UNKNOWN

    def summary(self):
        super().summary()
        print(f"    batteryPercentage        : {self.battery_percentage_remaining}")
        print(f"    mainPowerSupply          : {self.main_power_supply}")
        print(f"    solarChargingScore       : {self.solar_charging_score}")


class KeypadTriggerService(SHCDeviceService):
    """Universal Switch II button->scenario mapping (read-only).

    Spec-grounded from the Bosch app (APK 10.33) DeviceServiceData catalog —
    keypadTriggerState{scenarioIdAssociations, switchType, idsToTrigger}. This
    service is NOT in the official local OpenAPI and has not yet been observed
    in a rawscan, so every field is defensively .get-guarded. It reports which
    scenarios a Universal Switch II key is wired to trigger; it is informational
    only (the actual press events arrive via the separate Keypad service).
    """

    @property
    def switch_type(self) -> str:
        return self.state.get("switchType")

    @property
    def scenario_id_associations(self) -> list:
        # Each entry maps a key (keyName/keyState) to a scenarioId. Shape is not
        # yet confirmed by a rawscan, so it is surfaced verbatim.
        return self.state.get("scenarioIdAssociations", []) or []

    @property
    def ids_to_trigger(self) -> list:
        return self.state.get("idsToTrigger", []) or []

    def summary(self):
        super().summary()
        print(f"    switchType               : {self.switch_type}")
        print(f"    scenarioIdAssociations   : {self.scenario_id_associations}")
        print(f"    idsToTrigger             : {self.ids_to_trigger}")


class SoftwareUpdateService(SHCDeviceService):
    """Per-device firmware update state (read-only).

    Mirrors the controller-level ShcInfo softwareUpdateState block (see
    SHCInformation, hass#186) but at the individual-device level. Like the
    controller case, the local API exposes no install action — updates are
    started from the Bosch app — so this is a read-only status surface only.
    Spec-grounded from APK 10.33; not yet confirmed in a per-device rawscan, so
    all access is .get/try-guarded and any device may or may not carry it.
    """

    class SwUpdateState(Enum):
        NO_UPDATE_AVAILABLE = "NO_UPDATE_AVAILABLE"
        UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
        DOWNLOADING = "DOWNLOADING"
        INSTALLING = "INSTALLING"
        UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
        UPDATE_SUCCESS = "UPDATE_SUCCESS"
        UPDATE_FAILED = "UPDATE_FAILED"
        UNKNOWN = "UNKNOWN"

    @property
    def sw_update_state(self) -> "SoftwareUpdateService.SwUpdateState":
        raw = self.state.get("swUpdateState")
        if raw is None:
            return self.SwUpdateState.UNKNOWN
        try:
            return self.SwUpdateState(raw)
        except ValueError:
            return self.SwUpdateState.UNKNOWN

    @property
    def sw_update_last_result(self) -> str:
        return self.state.get("swUpdateLastResult")

    @property
    def sw_update_available_version(self) -> str:
        return self.state.get("swUpdateAvailableVersion")

    @property
    def sw_installed_version(self) -> str:
        return self.state.get("swInstalledVersion")

    @property
    def automatic_updates_enabled(self) -> bool:
        return bool(self.state.get("automaticUpdatesEnabled", False))

    def summary(self):
        super().summary()
        print(f"    swUpdateState            : {self.sw_update_state}")
        print(f"    swInstalledVersion       : {self.sw_installed_version}")
        print(f"    swUpdateAvailableVersion : {self.sw_update_available_version}")


SERVICE_MAPPING = {
    "AirQualityLevel": AirQualityLevelService,
    "Alarm": AlarmService,
    "BatteryLevel": BatteryLevelService,
    "BinarySwitch": BinarySwitchService,
    "BlindsControl": BlindsControlService,
    "BlindsSceneControl": BlindsSceneControlService,
    "Bypass": BypassService,
    "CameraAmbientLight": CameraAmbientLightService,
    "CameraFrontLight": CameraFrontLightService,
    "CameraLight": CameraLightService,
    "CameraNotification": CameraNotificationService,
    "ChildProtection": ChildProtectionService,
    "CommunicationQuality": CommunicationQualityService,
    "DetectionTest": DetectionTestService,
    "DisplayConfiguration": DisplayConfiguration,
    "DisplayDirection": DisplayDirection,
    "DisplayedTemperatureConfiguration": DisplayedTemperatureConfiguration,
    "EnergySavingMode": EnergySavingModeService,
    "HeatingCircuit": HeatingCircuitService,
    "HSBColorActuator": HSBColorActuatorService,
    "HueColorTemperature": HueColorTemperatureService,
    "HumidityLevel": HumidityLevelService,
    "ImpulseSwitch": ImpulseSwitchService,
    "Keypad": KeypadService,
    "KeypadTrigger": KeypadTriggerService,
    "LatestMotion": LatestMotionService,
    "LatestTamper": LatestTamperService,
    "LedBrightnessConfiguration": LedBrightnessConfigurationService,
    "MultiLevelSensor": MultiLevelSensorService,
    "MultiLevelSwitch": MultiLevelSwitchService,
    "OccupancyDetection": OccupancyDetectionService,
    "OutdoorSiren": OutdoorSirenService,
    "OutdoorSirenPowerSupply": OutdoorSirenPowerSupplyService,
    "PetImmunity": PetImmunityService,
    "PirSensorConfiguration": PirSensorConfigurationService,
    "PollControl": PollControlService,
    "PowerMeter": PowerMeterService,
    "PowerSwitch": PowerSwitchService,
    "PowerSwitchConfiguration": PowerSwitchConfigurationService,
    "PowerSwitchProgram": PowerSwitchProgramService,
    "PowerSwitchWarning": PowerSwitchWarningService,
    "PresenceSimulationConfiguration": PresenceSimulationConfigurationService,
    "PrivacyMode": PrivacyModeService,
    "RoomClimateControl": RoomClimateControlService,
    "ThermostatSupportedControlMode": ThermostatSupportedControlModeService,
    "Routing": RoutingService,
    "ShutterContact": ShutterContactService,
    "ShutterControl": ShutterControlService,
    "SilentMode": SilentModeService,
    "SmartSensitivityControl": SmartSensitivityControlService,
    "SmokeSensitivity": SmokeSensitivityService,
    "SmokeDetectorCheck": SmokeDetectorCheckService,
    "SoftwareUpdate": SoftwareUpdateService,
    "SurveillanceAlarm": SurveillanceAlarmService,
    "SwitchConfiguration": SwitchConfiguration,
    "TemperatureLevel": TemperatureLevelService,
    "TemperatureOffset": TemperatureOffsetService,
    "TerminalConfiguration": TerminalConfiguration,
    "Thermostat": ThermostatService,
    "TwinguardNightlyPromise": TwinguardNightlyPromiseService,
    "ValveTappet": ValveTappetService,
    "VibrationSensor": VibrationSensorService,
    "WalkTest": WalkTestService,
    "WallThermostatConfiguration": WallThermostatConfiguration,
    "WaterLeakageSensor": WaterLeakageSensorService,
    "WaterLeakageSensorCheck": WaterLeakageSensorCheckService,
    "WaterLeakageSensorTilt": WaterLeakageSensorTiltService,
}

#    "SmokeDetectionControl": SmokeDetectionControlService,
#    "ElectricalFaults": ElectricalFaultsService,
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
