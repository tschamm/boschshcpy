from __future__ import annotations

from enum import Enum, Flag, auto
from typing import Any

from .api import SHCAPI
from .device import SHCDevice
from .services_impl import (
    AirQualityLevelService,
    AlarmService,
    BatteryLevelService,
    BinarySwitchService,
    BlindsControlService,
    BlindsSceneControlService,
    BypassService,
    CameraAmbientLightService,
    CameraFrontLightService,
    CameraLightService,
    CameraNotificationService,
    ChildProtectionService,
    CommunicationQualityService,
    DetectionTestService,
    DimmerConfigurationService,
    DisplayConfiguration,
    DisplayDirection,
    DisplayedTemperatureConfiguration,
    EnergySavingModeService,
    HSBColorActuatorService,
    HeatingCircuitService,
    HueColorTemperatureService,
    HumidityLevelService,
    ImpulseSwitchService,
    KeypadService,
    KeypadTriggerService,
    LatestMotionService,
    LatestTamperService,
    LedBrightnessConfigurationService,
    MultiLevelSensorService,
    MultiLevelSwitchService,
    OccupancyDetectionService,
    OutdoorSirenPowerSupplyService,
    OutdoorSirenService,
    PetImmunityService,
    PirSensorConfigurationService,
    PollControlService,
    PowerMeterService,
    PowerSwitchConfigurationService,
    PowerSwitchProgramService,
    PowerSwitchService,
    PowerSwitchWarningService,
    PresenceSimulationConfigurationService,
    PrivacyModeService,
    RoomClimateControlService,
    RoutingService,
    ShutterContactService,
    ShutterControlService,
    SilentModeService,
    SmartSensitivityControlService,
    SmokeDetectorCheckService,
    SmokeSensitivityService,
    SurveillanceAlarmService,
    SwitchConfiguration,
    TemperatureLevelService,
    TemperatureOffsetService,
    TerminalConfiguration,
    ThermostatService,
    ThermostatSupportedControlModeService,
    TwinguardNightlyPromiseService,
    ValveTappetService,
    VibrationSensorService,
    WalkTestService,
    WallThermostatConfiguration,
    WaterLeakageSensorCheckService,
    WaterLeakageSensorService,
    WaterLeakageSensorTiltService,
)


class SHCBatteryDevice(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._batterylevel_service: BatteryLevelService | None = self.device_service(  # type: ignore[assignment]
            "BatteryLevel"
        )

    @property
    def supports_batterylevel(self) -> bool:
        return self._batterylevel_service is not None

    @property
    def batterylevel(self) -> BatteryLevelService.State:
        if self._batterylevel_service is not None:
            return self._batterylevel_service.warningLevel
        return BatteryLevelService.State.NOT_AVAILABLE


class _CommunicationQuality(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._communicationquality_service: CommunicationQualityService = (
            self.device_service(  # type: ignore[assignment]
                "CommunicationQuality"
            )
        )

    @property
    def communicationquality(self) -> CommunicationQualityService.State:
        return self._communicationquality_service.value


class _PowerMeter(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._powermeter_service: PowerMeterService = self.device_service(  # type: ignore[assignment]
            "PowerMeter"
        )

    @property
    def energyconsumption(self) -> float:
        return self._powermeter_service.energyconsumption

    @property
    def powerconsumption(self) -> float:
        return self._powermeter_service.powerconsumption

    @property
    def energy_yield(self) -> float:
        # #331: PV production (Wh) on Smart Plug [+M]; None when unsupported.
        return self._powermeter_service.energyyield  # type: ignore[return-value]

    @property
    def supports_energy_yield(self) -> bool:
        # True only when the controller actually reports an energyYield field
        # (Smart Plug [+M] in Mini-PV mode) — gates the HA yield entities.
        return self._powermeter_service.energyyield is not None


class _ChildProtection(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._childprotection_service: ChildProtectionService = self.device_service(  # type: ignore[assignment]
            "ChildProtection"
        )

    @property
    def child_lock(self) -> bool:
        return self._childprotection_service.childLockActive

    @child_lock.setter
    def child_lock(self, state: bool) -> None:
        self._childprotection_service.put_state_element("childLockActive", state)

    async def async_set_child_lock(self, state: bool) -> None:
        """Async write: set childLockActive on ChildProtection service."""
        await self._childprotection_service.async_put_state_element(
            "childLockActive", state
        )


class _Thermostat(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._thermostat_service: ThermostatService = self.device_service(  # type: ignore[assignment]
            "Thermostat"
        )

    @property
    def child_lock(self) -> ThermostatService.State:
        return self._thermostat_service.childLock

    @child_lock.setter
    def child_lock(self, state: bool) -> None:
        self._thermostat_service.put_state_element(
            "childLock", "ON" if state else "OFF"
        )

    async def async_set_child_lock(self, state: bool) -> None:
        """Async write: set childLock on Thermostat service."""
        await self._thermostat_service.async_put_state_element(
            "childLock", "ON" if state else "OFF"
        )


class _PowerSwitch(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._powerswitch_service: PowerSwitchService = self.device_service(  # type: ignore[assignment]
            "PowerSwitch"
        )

    @property
    def switchstate(self) -> PowerSwitchService.State:
        return self._powerswitch_service.value

    @switchstate.setter
    def switchstate(self, state: bool) -> None:
        self._powerswitch_service.put_state_element(
            "switchState", "ON" if state else "OFF"
        )

    async def async_set_switchstate(self, state: bool) -> None:
        """Async write: set switchState on PowerSwitch service."""
        await self._powerswitch_service.async_put_state_element(
            "switchState", "ON" if state else "OFF"
        )


class _PowerSwitchProgram(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._powerswitchprogram_service: PowerSwitchProgramService | None = (
            self.device_service(  # type: ignore[assignment]
                "PowerSwitchProgram"
            )
        )

    # To be implemented


class _TemperatureLevel(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._temperaturelevel_service: TemperatureLevelService | None = (
            self.device_service(  # type: ignore[assignment]
                "TemperatureLevel"
            )
        )

    @property
    def temperature(self) -> float | None:
        if self._temperaturelevel_service is None:
            return None
        return self._temperaturelevel_service.temperature


class _HumidityLevel(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._humiditylevel_service: HumidityLevelService | None = self.device_service(  # type: ignore[assignment]
            "HumidityLevel"
        )

    @property
    def supports_humidity(self) -> bool:
        return self._humiditylevel_service is not None

    @property
    def humidity(self) -> float | None:
        if self._humiditylevel_service is None:
            return None
        return self._humiditylevel_service.humidity


class _TemperatureOffset(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._temperatureoffset_service: TemperatureOffsetService | None = (
            self.device_service(  # type: ignore[assignment]
                "TemperatureOffset"
            )
        )

    @property
    def supports_temperature_offset(self) -> bool:
        return self._temperatureoffset_service is not None

    @property
    def offset(self) -> float:
        assert self._temperatureoffset_service is not None
        return self._temperatureoffset_service.offset

    @offset.setter
    def offset(self, value: float) -> None:
        assert self._temperatureoffset_service is not None
        self._temperatureoffset_service.offset = value

    async def async_set_offset(self, value: float) -> None:
        """Async write: set temperature offset."""
        assert self._temperatureoffset_service is not None
        await self._temperatureoffset_service.async_put_state_element("offset", value)

    @property
    def step_size(self) -> float:
        assert self._temperatureoffset_service is not None
        return self._temperatureoffset_service.step_size

    @property
    def min_offset(self) -> float:
        assert self._temperatureoffset_service is not None
        return self._temperatureoffset_service.min_offset

    @property
    def max_offset(self) -> float:
        assert self._temperatureoffset_service is not None
        return self._temperatureoffset_service.max_offset


class _SilentMode(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._silentmode_service: SilentModeService | None = self.device_service(  # type: ignore[assignment]
            "SilentMode"
        )

    @property
    def supports_silentmode(self) -> bool:
        return self._silentmode_service is not None

    @property
    def silentmode(self) -> SilentModeService.State | None:
        if self._silentmode_service is not None:
            return self._silentmode_service.mode
        return None

    @silentmode.setter
    def silentmode(self, state: bool) -> None:
        if self._silentmode_service is not None:
            self._silentmode_service.put_state_element(
                "mode", "MODE_SILENT" if state else "MODE_NORMAL"
            )

    async def async_set_silentmode(self, state: bool) -> None:
        """Async write: set silent mode."""
        if self._silentmode_service is not None:
            await self._silentmode_service.async_put_state_element(
                "mode", "MODE_SILENT" if state else "MODE_NORMAL"
            )


class SHCSmokeDetector(SHCBatteryDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)

        self._alarm_service: AlarmService = self.device_service("Alarm")  # type: ignore[assignment]
        self._smokedetectorcheck_service: SmokeDetectorCheckService = (
            self.device_service(  # type: ignore[assignment]
                "SmokeDetectorCheck"
            )
        )
        self._smoke_sensitivity_service: SmokeSensitivityService | None = (
            self.device_service(  # type: ignore[assignment]
                "SmokeSensitivity"
            )
        )

    @property
    def alarmstate(self) -> AlarmService.State:
        return self._alarm_service.value

    @alarmstate.setter
    def alarmstate(self, state: str) -> None:
        self._alarm_service.put_state_element("value", state)

    async def async_set_alarmstate(self, state: str) -> None:
        """Async write: set alarm state on Alarm service."""
        await self._alarm_service.async_put_state_element("value", state)

    @property
    def supports_intrusion_alarm(self) -> bool:
        """True for Smoke Detector II, which can sound/clear its intrusion alarm.

        The SD II Alarm service accepts a writable request value
        (INTRUSION_ALARM_ON_REQUESTED / INTRUSION_ALARM_OFF_REQUESTED), letting
        the detector act as a siren. Gen-1 SD exposes the Alarm service too but
        only as a read-only smoke state, so this is gated on the model id.
        """
        return (
            self.device_model == "SMOKE_DETECTOR2" and self._alarm_service is not None
        )

    @property
    def intrusion_alarm(self) -> bool:
        """True while the (SD II) intrusion alarm is sounding.

        SD II read-back states are IDLE_OFF / INTRUSION_ALARM_ON_REQUESTED /
        INTRUSION_ALARM_OFF_REQUESTED (SmokeDetector-II spec). Treat anything that
        is neither idle nor an explicit OFF request as active (also covers the
        gen-1 INTRUSION_ALARM/PRIMARY/SECONDARY members defensively).
        """
        if self._alarm_service is None:
            return False
        return self._alarm_service.value not in (
            AlarmService.State.IDLE_OFF,
            AlarmService.State.INTRUSION_ALARM_OFF_REQUESTED,
        )

    async def async_set_intrusion_alarm(self, active: bool = True) -> None:
        """Async write: sound (True) or clear (False) the SD II intrusion alarm.

        Bosch uses dedicated *_REQUESTED write values; the read-back state is
        INTRUSION_ALARM / IDLE_OFF (same request-vs-state split as DetectionTest,
        see #325). Writing the bare INTRUSION_ALARM_ON failed for reporters (#174).
        """
        value = (
            "INTRUSION_ALARM_ON_REQUESTED"
            if active
            else "INTRUSION_ALARM_OFF_REQUESTED"
        )
        await self._alarm_service.async_put_state_element("value", value)

    @property
    def smokedetectorcheck_state(self) -> SmokeDetectorCheckService.State:
        return self._smokedetectorcheck_service.value

    def smoketest_requested(self) -> None:
        self._smokedetectorcheck_service.put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    async def async_smoketest_requested(self) -> None:
        """Async write: request a smoke test."""
        await self._smokedetectorcheck_service.async_put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    @property
    def has_smoke_sensitivity_service(self) -> bool:
        return self._smoke_sensitivity_service is not None

    @property
    def smoke_sensitivity(self) -> SmokeSensitivityService.SmokeSensitivityLevel | None:
        if self._smoke_sensitivity_service is None:
            return None
        return self._smoke_sensitivity_service.smoke_sensitivity

    @smoke_sensitivity.setter
    def smoke_sensitivity(
        self, value: SmokeSensitivityService.SmokeSensitivityLevel
    ) -> None:
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.smoke_sensitivity = value

    async def async_set_smoke_sensitivity(
        self, value: SmokeSensitivityService.SmokeSensitivityLevel
    ) -> None:
        """Async write: set smoke sensitivity level (if service present)."""
        if self._smoke_sensitivity_service is not None:
            await self._smoke_sensitivity_service.async_set_smoke_sensitivity(value)

    @property
    def pre_alarm_enabled(self) -> bool:
        if self._smoke_sensitivity_service is None:
            return False
        return self._smoke_sensitivity_service.pre_alarm_enabled

    @pre_alarm_enabled.setter
    def pre_alarm_enabled(self, value: bool) -> None:
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.pre_alarm_enabled = value

    async def async_set_pre_alarm_enabled(self, value: bool) -> None:
        """Async write: enable/disable pre-alarm (if service present)."""
        if self._smoke_sensitivity_service is not None:
            await self._smoke_sensitivity_service.async_set_pre_alarm_enabled(value)

    @property
    def supports_smoke_sensitivity(self) -> bool:
        return self._smoke_sensitivity_service is not None


class SHCSmartPlug(_PowerMeter, _PowerSwitch, _PowerSwitchProgram):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)

        self._routing_service: RoutingService = self.device_service("Routing")  # type: ignore[assignment]
        self._energy_saving_mode_service: EnergySavingModeService | None = (
            self.device_service(  # type: ignore[assignment]
                "EnergySavingMode"
            )
        )
        self._led_brightness_configuration_service: (
            LedBrightnessConfigurationService | None
        ) = self.device_service(  # type: ignore[assignment]
            "LedBrightnessConfiguration"
        )
        self._power_switch_configuration_service: (
            PowerSwitchConfigurationService | None
        ) = self.device_service(  # type: ignore[assignment]
            "PowerSwitchConfiguration"
        )
        self._power_switch_warning_service: PowerSwitchWarningService | None = (
            self.device_service(  # type: ignore[assignment]
                "PowerSwitchWarning"
            )
        )

    @property
    def routing(self) -> RoutingService.State:
        return self._routing_service.value

    @routing.setter
    def routing(self, state: bool) -> None:
        self._routing_service.put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    async def async_set_routing(self, state: bool) -> None:
        """Async write: set routing on Routing service."""
        await self._routing_service.async_put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    @property
    def energy_saving_mode_enabled(self) -> bool:
        if self._energy_saving_mode_service is None:
            return False
        return self._energy_saving_mode_service.energy_saving_mode_enabled

    @energy_saving_mode_enabled.setter
    def energy_saving_mode_enabled(self, value: bool) -> None:
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.energy_saving_mode_enabled = value

    async def async_set_energy_saving_mode_enabled(self, value: bool) -> None:
        """Async write: enable/disable energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_energy_saving_mode_enabled(
                value
            )

    @property
    def power_threshold(self) -> float | None:
        if self._energy_saving_mode_service is None:
            return None
        return self._energy_saving_mode_service.power_threshold  # type: ignore[no-any-return]

    @power_threshold.setter
    def power_threshold(self, value: float) -> None:
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.power_threshold = value

    async def async_set_power_threshold(self, value: float) -> None:
        """Async write: set power threshold for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_power_threshold(value)

    @property
    def enter_duration_seconds(self) -> int:
        if self._energy_saving_mode_service is None:
            return 0
        return self._energy_saving_mode_service.enter_duration_seconds

    @enter_duration_seconds.setter
    def enter_duration_seconds(self, value: int) -> None:
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.enter_duration_seconds = value

    async def async_set_enter_duration_seconds(self, value: int) -> None:
        """Async write: set enter duration for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_enter_duration_seconds(
                value
            )

    @property
    def led_brightness(self) -> int | None:
        if self._led_brightness_configuration_service is None:
            return None
        return self._led_brightness_configuration_service.brightness

    @led_brightness.setter
    def led_brightness(self, value: int) -> None:
        if self._led_brightness_configuration_service is not None:
            self._led_brightness_configuration_service.brightness = value

    async def async_set_led_brightness(self, value: int) -> None:
        """Async write: set LED brightness."""
        if self._led_brightness_configuration_service is not None:
            await self._led_brightness_configuration_service.async_set_brightness(value)

    @property
    def state_after_power_outage(
        self,
    ) -> PowerSwitchConfigurationService.StateAfterPowerOutage | None:
        if self._power_switch_configuration_service is None:
            return None
        return self._power_switch_configuration_service.state_after_power_outage

    @state_after_power_outage.setter
    def state_after_power_outage(
        self, value: PowerSwitchConfigurationService.StateAfterPowerOutage
    ) -> None:
        if self._power_switch_configuration_service is not None:
            self._power_switch_configuration_service.state_after_power_outage = value

    async def async_set_state_after_power_outage(
        self, value: PowerSwitchConfigurationService.StateAfterPowerOutage
    ) -> None:
        """Async write: set state after power outage behavior."""
        if self._power_switch_configuration_service is not None:
            await self._power_switch_configuration_service.async_set_state_after_power_outage(
                value
            )

    @property
    def warning_suppressed(self) -> bool:
        if self._power_switch_warning_service is None:
            return False
        return self._power_switch_warning_service.warning_suppressed

    @warning_suppressed.setter
    def warning_suppressed(self, value: bool) -> None:
        if self._power_switch_warning_service is not None:
            self._power_switch_warning_service.warning_suppressed = value

    async def async_set_warning_suppressed(self, value: bool) -> None:
        """Async write: suppress/enable 'still on' warning."""
        if self._power_switch_warning_service is not None:
            await self._power_switch_warning_service.async_set_warning_suppressed(value)

    @property
    def supports_energy_saving_mode(self) -> bool:
        return self._energy_saving_mode_service is not None

    @property
    def supports_led_brightness(self) -> bool:
        return self._led_brightness_configuration_service is not None

    @property
    def supports_power_switch_configuration(self) -> bool:
        return self._power_switch_configuration_service is not None

    @property
    def supports_power_switch_warning(self) -> bool:
        return self._power_switch_warning_service is not None


class SHCSmartPlugCompact(
    _CommunicationQuality, _PowerMeter, _PowerSwitch, _PowerSwitchProgram
):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._energy_saving_mode_service: EnergySavingModeService | None = (
            self.device_service(  # type: ignore[assignment]
                "EnergySavingMode"
            )
        )
        self._led_brightness_configuration_service: (
            LedBrightnessConfigurationService | None
        ) = self.device_service(  # type: ignore[assignment]
            "LedBrightnessConfiguration"
        )
        self._power_switch_configuration_service: (
            PowerSwitchConfigurationService | None
        ) = self.device_service(  # type: ignore[assignment]
            "PowerSwitchConfiguration"
        )
        self._power_switch_warning_service: PowerSwitchWarningService | None = (
            self.device_service(  # type: ignore[assignment]
                "PowerSwitchWarning"
            )
        )

    @property
    def energy_saving_mode_enabled(self) -> bool:
        if self._energy_saving_mode_service is None:
            return False
        return self._energy_saving_mode_service.energy_saving_mode_enabled

    @energy_saving_mode_enabled.setter
    def energy_saving_mode_enabled(self, value: bool) -> None:
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.energy_saving_mode_enabled = value

    async def async_set_energy_saving_mode_enabled(self, value: bool) -> None:
        """Async write: enable/disable energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_energy_saving_mode_enabled(
                value
            )

    @property
    def power_threshold(self) -> float | None:
        if self._energy_saving_mode_service is None:
            return None
        return self._energy_saving_mode_service.power_threshold  # type: ignore[no-any-return]

    @power_threshold.setter
    def power_threshold(self, value: float) -> None:
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.power_threshold = value

    async def async_set_power_threshold(self, value: float) -> None:
        """Async write: set power threshold for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_power_threshold(value)

    @property
    def enter_duration_seconds(self) -> int:
        if self._energy_saving_mode_service is None:
            return 0
        return self._energy_saving_mode_service.enter_duration_seconds

    @enter_duration_seconds.setter
    def enter_duration_seconds(self, value: int) -> None:
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.enter_duration_seconds = value

    async def async_set_enter_duration_seconds(self, value: int) -> None:
        """Async write: set enter duration for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_enter_duration_seconds(
                value
            )

    @property
    def led_brightness(self) -> int | None:
        if self._led_brightness_configuration_service is None:
            return None
        return self._led_brightness_configuration_service.brightness

    @led_brightness.setter
    def led_brightness(self, value: int) -> None:
        if self._led_brightness_configuration_service is not None:
            self._led_brightness_configuration_service.brightness = value

    async def async_set_led_brightness(self, value: int) -> None:
        """Async write: set LED brightness."""
        if self._led_brightness_configuration_service is not None:
            await self._led_brightness_configuration_service.async_set_brightness(value)

    @property
    def state_after_power_outage(
        self,
    ) -> PowerSwitchConfigurationService.StateAfterPowerOutage | None:
        if self._power_switch_configuration_service is None:
            return None
        return self._power_switch_configuration_service.state_after_power_outage

    @state_after_power_outage.setter
    def state_after_power_outage(
        self, value: PowerSwitchConfigurationService.StateAfterPowerOutage
    ) -> None:
        if self._power_switch_configuration_service is not None:
            self._power_switch_configuration_service.state_after_power_outage = value

    async def async_set_state_after_power_outage(
        self, value: PowerSwitchConfigurationService.StateAfterPowerOutage
    ) -> None:
        """Async write: set state after power outage behavior."""
        if self._power_switch_configuration_service is not None:
            await self._power_switch_configuration_service.async_set_state_after_power_outage(
                value
            )

    @property
    def warning_suppressed(self) -> bool:
        if self._power_switch_warning_service is None:
            return False
        return self._power_switch_warning_service.warning_suppressed

    @warning_suppressed.setter
    def warning_suppressed(self, value: bool) -> None:
        if self._power_switch_warning_service is not None:
            self._power_switch_warning_service.warning_suppressed = value

    async def async_set_warning_suppressed(self, value: bool) -> None:
        """Async write: suppress/enable 'still on' warning."""
        if self._power_switch_warning_service is not None:
            await self._power_switch_warning_service.async_set_warning_suppressed(value)

    @property
    def supports_energy_saving_mode(self) -> bool:
        return self._energy_saving_mode_service is not None

    @property
    def supports_led_brightness(self) -> bool:
        return self._led_brightness_configuration_service is not None

    @property
    def supports_power_switch_configuration(self) -> bool:
        return self._power_switch_configuration_service is not None

    @property
    def supports_power_switch_warning(self) -> bool:
        return self._power_switch_warning_service is not None


class SHCLightSwitch(_ChildProtection, _PowerSwitch, _PowerSwitchProgram):
    pass


class SHCLightSwitchBSM(SHCLightSwitch, _PowerMeter):
    pass


class SHCLightControl(_CommunicationQuality, _PowerMeter):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._switch_config_service: SwitchConfiguration | None = self.device_service(  # type: ignore[assignment]
            "SwitchConfiguration"
        )
        # #282: Light Control II exposes a Keypad service when its physical
        # input is configured as a push-button that does NOT toggle the output.
        # The wall press then arrives as a Keypad event the user can react to.
        self._keypad_service: KeypadService | None = self.device_service("Keypad")  # type: ignore[assignment]

    @property
    def has_keypad(self) -> bool:
        return self._keypad_service is not None

    @property
    def keyname(self) -> KeypadService.KeyState | None:
        return (
            self._keypad_service.keyName if self._keypad_service is not None else None
        )

    @property
    def eventtype(self) -> KeypadService.KeyEvent | None:
        return (
            self._keypad_service.eventType if self._keypad_service is not None else None
        )

    @property
    def eventtimestamp(self) -> int:
        return (
            self._keypad_service.eventTimestamp
            if self._keypad_service is not None
            else 0
        )

    @property
    def switch_type(self) -> SwitchConfiguration.SwitchType | None:
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.switch_type

    @switch_type.setter
    def switch_type(self, value: SwitchConfiguration.SwitchType) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.switch_type = value

    async def async_set_switch_type(
        self, value: SwitchConfiguration.SwitchType
    ) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_switchType(value)

    @property
    def swap_inputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_inputs

    @swap_inputs.setter
    def swap_inputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.swap_inputs = value

    async def async_set_swap_inputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapInputs(value)

    @property
    def swap_outputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_outputs

    @swap_outputs.setter
    def swap_outputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.swap_outputs = value

    async def async_set_swap_outputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapOutputs(value)

    @property
    def actuator_type(self) -> SwitchConfiguration.ActuatorType | None:
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.actuator_type

    @actuator_type.setter
    def actuator_type(self, value: SwitchConfiguration.ActuatorType) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.actuator_type = value

    async def async_set_actuator_type(
        self, value: SwitchConfiguration.ActuatorType
    ) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_actuatorType(value)

    @property
    def output_mode(self) -> SwitchConfiguration.OutputMode | None:
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.output_mode

    @output_mode.setter
    def output_mode(self, value: SwitchConfiguration.OutputMode) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.output_mode = value

    async def async_set_output_mode(
        self, value: SwitchConfiguration.OutputMode
    ) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_outputMode(value)


class SHCMicromoduleRelay(
    _CommunicationQuality, _ChildProtection, _PowerSwitch, _PowerSwitchProgram
):
    class RelayType(Enum):
        BUTTON = "BUTTON"
        SWITCH = "SWITCH"

    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)

        self._impulseswitch_service: ImpulseSwitchService | None = self.device_service(  # type: ignore[assignment]
            "ImpulseSwitch"
        )
        self._switch_config_service: SwitchConfiguration | None = self.device_service(  # type: ignore[assignment]
            "SwitchConfiguration"
        )

    @property
    def relay_type(self) -> RelayType:
        return (
            self.RelayType.BUTTON
            if self._impulseswitch_service is not None
            else self.RelayType.SWITCH
        )

    def trigger_impulse_state(self) -> None:
        if self._impulseswitch_service:
            self._impulseswitch_service.put_state_element("impulseState", True)

    async def async_trigger_impulse_state(self) -> None:
        """Async write: trigger impulse relay."""
        if self._impulseswitch_service:
            await self._impulseswitch_service.async_put_state_element(
                "impulseState", True
            )

    @property
    def impulse_length(self) -> int | None:
        if self._impulseswitch_service is None:
            return None
        return self._impulseswitch_service.impulse_length

    @impulse_length.setter
    def impulse_length(self, impulse_length: int) -> None:
        if self._impulseswitch_service is None:
            return
        self._impulseswitch_service.put_state_element("impulseLength", impulse_length)

    async def async_set_impulse_length(self, impulse_length: int) -> None:
        """Async write: set impulse length (tenths of seconds)."""
        if self._impulseswitch_service is not None:
            await self._impulseswitch_service.async_put_state_element(
                "impulseLength", impulse_length
            )

    @property
    def instant_of_last_impulse(self) -> str | None:
        if self._impulseswitch_service:
            return self._impulseswitch_service.instant_of_last_impulse
        return None

    @property
    def switch_type(self) -> SwitchConfiguration.SwitchType | None:
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.switch_type

    @switch_type.setter
    def switch_type(self, value: SwitchConfiguration.SwitchType) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.switch_type = value

    async def async_set_switch_type(
        self, value: SwitchConfiguration.SwitchType
    ) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_switchType(value)

    @property
    def swap_inputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_inputs

    @swap_inputs.setter
    def swap_inputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.swap_inputs = value

    async def async_set_swap_inputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapInputs(value)

    @property
    def swap_outputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_outputs

    @swap_outputs.setter
    def swap_outputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.swap_outputs = value

    async def async_set_swap_outputs(self, value: bool) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapOutputs(value)

    @property
    def actuator_type(self) -> SwitchConfiguration.ActuatorType | None:
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.actuator_type

    @actuator_type.setter
    def actuator_type(self, value: SwitchConfiguration.ActuatorType) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.actuator_type = value

    async def async_set_actuator_type(
        self, value: SwitchConfiguration.ActuatorType
    ) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_actuatorType(value)

    @property
    def output_mode(self) -> SwitchConfiguration.OutputMode | None:
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.output_mode

    @output_mode.setter
    def output_mode(self, value: SwitchConfiguration.OutputMode) -> None:
        if self._switch_config_service is not None:
            self._switch_config_service.output_mode = value

    async def async_set_output_mode(
        self, value: SwitchConfiguration.OutputMode
    ) -> None:
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_outputMode(value)

    @property
    def supports_switch_configuration(self) -> bool:
        return self._switch_config_service is not None


class SHCShutterControl(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._service: ShutterControlService = self.device_service("ShutterControl")  # type: ignore[assignment]

    @property
    def level(self) -> float:
        return self._service.level

    @level.setter
    def level(self, level: float) -> None:
        self._service.put_state_element("level", level)

    async def async_set_level(self, level: float) -> None:
        """Async write: set cover position level (0.0 closed .. 1.0 open)."""
        await self._service.async_put_state_element("level", level)

    def stop(self) -> None:
        self._service.put_state_element("operationState", "STOPPED")

    async def async_stop(self) -> None:
        """Async write: stop the shutter/cover."""
        await self._service.async_put_state_element("operationState", "STOPPED")

    @property
    def operation_state(self) -> ShutterControlService.State:
        return self._service.operation_state


class SHCMicromoduleShutterControl(
    SHCShutterControl, _CommunicationQuality, _ChildProtection, _PowerMeter
):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._keypad_service: KeypadService | None = self.device_service("Keypad")  # type: ignore[assignment]

    @property
    def keystates(self) -> list[str]:
        return ["UNDEFINED_BUTTON"]

    @property
    def eventtypes(self) -> list[str]:
        return ["SWITCH_OFF", "SWITCH_ON"]

    @property
    def has_keypad(self) -> bool:
        # Some MICROMODULE_SHUTTER/BLINDS devices expose no Keypad service
        # (no physical wall switch wired). Callers must guard keypad access.
        return self._keypad_service is not None

    @property
    def keycode(self) -> int:
        return self._keypad_service.keyCode if self._keypad_service is not None else 0

    @property
    def keyname(self) -> KeypadService.KeyState | None:
        return (
            self._keypad_service.keyName if self._keypad_service is not None else None
        )

    @property
    def eventtype(self) -> KeypadService.KeyEvent | None:
        return (
            self._keypad_service.eventType if self._keypad_service is not None else None
        )

    @eventtype.setter
    def eventtype(self, value: KeypadService.KeyEvent) -> None:
        # No-op when the device has no Keypad service — eventType is only local
        # bookkeeping for the physical-switch direction logic (issue #318).
        if self._keypad_service is not None:
            self._keypad_service.eventType = value

    @property
    def eventtimestamp(self) -> int:
        return (
            self._keypad_service.eventTimestamp
            if self._keypad_service is not None
            else 0
        )


class SHCMicromoduleBlinds(SHCMicromoduleShutterControl):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._blindscontrol_service: BlindsControlService = self.device_service(  # type: ignore[assignment]
            "BlindsControl"
        )
        self._blindsscenecontrol_service: BlindsSceneControlService = (
            self.device_service(  # type: ignore[assignment]
                "BlindsSceneControl"
            )
        )

    @property
    def current_angle(self) -> float:
        return self._blindscontrol_service.current_angle

    @property
    def target_angle(self) -> float:
        return self._blindscontrol_service.target_angle

    @target_angle.setter
    def target_angle(self, value: float) -> None:
        self._blindscontrol_service.target_angle = value

    async def async_set_target_angle(self, value: float) -> None:
        """Async write: set blind slat angle (0.0..1.0)."""
        await self._blindscontrol_service.async_put_state_element("targetAngle", value)

    @property
    def blinds_level(self) -> float:
        return self._blindsscenecontrol_service.level

    @blinds_level.setter
    def blinds_level(self, level: float) -> None:
        self._blindsscenecontrol_service.level = level

    async def async_set_blinds_level(self, level: float) -> None:
        """Async write: set blinds position (0.0 closed .. 1.0 open).

        BlindsSceneControl requires both level + angle in the PUT body.
        """
        await self._blindsscenecontrol_service.async_put_state(
            {"level": level, "angle": self._blindsscenecontrol_service.angle}
        )

    @property
    def blinds_type(self) -> BlindsControlService.BlindsType | None:
        return self._blindscontrol_service.blinds_type

    def stop_blinds(self) -> None:
        # Spec-correct STOP: PUT ShutterControl/state operationState=STOPPED
        # (the old /shading/shutters/{id}/stop endpoint is not in the API).
        self._service.put_state_element("operationState", "STOPPED")

    async def async_stop_blinds(self) -> None:
        """Async write: stop the blinds (same endpoint as async_stop on parent)."""
        await self._service.async_put_state_element("operationState", "STOPPED")


class SHCShutterContact(SHCBatteryDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._service: ShutterContactService = self.device_service("ShutterContact")  # type: ignore[assignment]

    @property
    def device_class(self) -> str | None:
        return self.profile

    @property
    def state(self) -> ShutterContactService.State:
        return self._service.value


class SHCShutterContact2(SHCShutterContact, _CommunicationQuality):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._bypass_service: BypassService = self.device_service("Bypass")  # type: ignore[assignment]

    @property
    def bypass(self) -> BypassService.State:
        return self._bypass_service.value

    @bypass.setter
    def bypass(self, state: bool) -> None:
        self._bypass_service.put_state_element(
            "state", "BYPASS_ACTIVE" if state else "BYPASS_INACTIVE"
        )

    async def async_set_bypass(self, state: bool) -> None:
        """Async write: set bypass on Bypass service."""
        await self._bypass_service.async_put_state_element(
            "state", "BYPASS_ACTIVE" if state else "BYPASS_INACTIVE"
        )


class SHCShutterContact2Plus(SHCShutterContact2):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._vibrationsensor_service: VibrationSensorService = self.device_service(  # type: ignore[assignment]
            "VibrationSensor"
        )

    @property
    def vibrationsensor(self) -> VibrationSensorService.State:
        return self._vibrationsensor_service.value

    @property
    def enabled(self) -> bool:
        return self._vibrationsensor_service.enabled

    @enabled.setter
    def enabled(self, state: bool) -> None:
        self._vibrationsensor_service.put_state_element("enabled", state)

    async def async_set_vibration_enabled(self, state: bool) -> None:
        """Async write: enable/disable vibration sensor."""
        await self._vibrationsensor_service.async_put_state_element("enabled", state)

    @property
    def sensitivity(self) -> VibrationSensorService.SensitivityState:
        return self._vibrationsensor_service.sensitivity

    @sensitivity.setter
    def sensitivity(self, state: VibrationSensorService.SensitivityState) -> None:
        self._vibrationsensor_service.put_state_element("sensitivity", state.name)

    async def async_set_sensitivity(
        self, state: VibrationSensorService.SensitivityState
    ) -> None:
        """Async write: set vibration sensitivity."""
        await self._vibrationsensor_service.async_put_state_element(
            "sensitivity", state.name
        )


class SHCCamera360(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)

        self._privacymode_service: PrivacyModeService = self.device_service(  # type: ignore[assignment]
            "PrivacyMode"
        )
        self._cameranotification_service: CameraNotificationService | None = (
            self.device_service(  # type: ignore[assignment]
                "CameraNotification"
            )
        )

    @property
    def privacymode(self) -> PrivacyModeService.State:
        return self._privacymode_service.value

    @privacymode.setter
    def privacymode(self, state: bool) -> None:
        self._privacymode_service.put_state_element(
            "value", "DISABLED" if state else "ENABLED"
        )

    async def async_set_privacymode(self, state: bool) -> None:
        """Async write: set privacy mode (True = camera on/DISABLED, False = ENABLED)."""
        await self._privacymode_service.async_put_state_element(
            "value", "DISABLED" if state else "ENABLED"
        )

    @property
    def cameranotification(self) -> CameraNotificationService.State | None:
        if self._cameranotification_service:
            return self._cameranotification_service.value
        return None

    @cameranotification.setter
    def cameranotification(self, state: bool) -> None:
        if self._cameranotification_service:
            self._cameranotification_service.put_state_element(
                "value", "ENABLED" if state else "DISABLED"
            )

    async def async_set_cameranotification(self, state: bool) -> None:
        """Async write: enable/disable camera notification."""
        if self._cameranotification_service:
            await self._cameranotification_service.async_put_state_element(
                "value", "ENABLED" if state else "DISABLED"
            )


class SHCCameraEyes(SHCCamera360):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._cameralight_service: CameraLightService | None = self.device_service(  # type: ignore[assignment]
            "CameraLight"
        )

    @property
    def cameralight(self) -> CameraLightService.State | None:
        if self._cameralight_service:
            return self._cameralight_service.value
        return None

    @cameralight.setter
    def cameralight(self, state: bool) -> None:
        if self._cameralight_service:
            self._cameralight_service.put_state_element(
                "value", "ON" if state else "OFF"
            )

    async def async_set_cameralight(self, state: bool) -> None:
        """Async write: turn camera light on/off."""
        if self._cameralight_service:
            await self._cameralight_service.async_put_state_element(
                "value", "ON" if state else "OFF"
            )


class SHCCameraOutdoorGen2(SHCCamera360):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._cameraambientlight_service: CameraAmbientLightService | None = (
            self.device_service(  # type: ignore[assignment]
                "CameraAmbientLight"
            )
        )
        self._camerafrontlight_service: CameraFrontLightService | None = (
            self.device_service(  # type: ignore[assignment]
                "CameraFrontLight"
            )
        )

    @property
    def cameraambientlight(self) -> CameraAmbientLightService.State | None:
        if self._cameraambientlight_service:
            return self._cameraambientlight_service.value
        return None

    @cameraambientlight.setter
    def cameraambientlight(self, state: bool) -> None:
        if self._cameraambientlight_service:
            self._cameraambientlight_service.put_state_element(
                "value", "ON" if state else "OFF"
            )

    async def async_set_cameraambientlight(self, state: bool) -> None:
        """Async write: turn camera ambient light on/off."""
        if self._cameraambientlight_service:
            await self._cameraambientlight_service.async_put_state_element(
                "value", "ON" if state else "OFF"
            )

    @property
    def camerafrontlight(self) -> CameraFrontLightService.State | None:
        if self._camerafrontlight_service:
            return self._camerafrontlight_service.value
        return None

    @camerafrontlight.setter
    def camerafrontlight(self, state: bool) -> None:
        if self._camerafrontlight_service:
            self._camerafrontlight_service.put_state_element(
                "value", "ON" if state else "OFF"
            )

    async def async_set_camerafrontlight(self, state: bool) -> None:
        """Async write: turn camera front light on/off."""
        if self._camerafrontlight_service:
            await self._camerafrontlight_service.async_put_state_element(
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
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._valvetappet_service: ValveTappetService = self.device_service(
            "ValveTappet"
        )  # type: ignore[assignment]

    @property
    def position(self) -> int:
        return self._valvetappet_service.position

    @property
    def valvestate(self) -> ValveTappetService.State:
        return self._valvetappet_service.value


class SHCClimateControl(_TemperatureLevel):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._roomclimatecontrol_service: RoomClimateControlService = (
            self.device_service(  # type: ignore[assignment]
                "RoomClimateControl"
            )
        )
        self._supportedcontrolmode_service: (
            ThermostatSupportedControlModeService | None
        ) = self.device_service(  # type: ignore[assignment]
            "ThermostatSupportedControlMode"
        )

    @property
    def setpoint_temperature(self) -> float:
        return self._roomclimatecontrol_service.setpoint_temperature

    @setpoint_temperature.setter
    def setpoint_temperature(self, temperature: float) -> None:
        self._roomclimatecontrol_service.setpoint_temperature = temperature

    async def async_set_setpoint_temperature(self, temperature: float) -> None:
        """Async write: set target temperature."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "setpointTemperature", temperature
        )

    @property
    def operation_mode(self) -> RoomClimateControlService.OperationMode:
        return self._roomclimatecontrol_service.operation_mode

    @operation_mode.setter
    def operation_mode(self, mode: RoomClimateControlService.OperationMode) -> None:
        self._roomclimatecontrol_service.operation_mode = mode

    async def async_set_operation_mode(
        self, mode: RoomClimateControlService.OperationMode
    ) -> None:
        """Async write: set operation mode (AUTOMATIC/MANUAL)."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "operationMode", mode.value
        )

    @property
    def boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.boost_mode

    @boost_mode.setter
    def boost_mode(self, value: bool) -> None:
        self._roomclimatecontrol_service.boost_mode = value

    async def async_set_boost_mode(self, value: bool) -> None:
        """Async write: set boost mode."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "boostMode", value
        )

    @property
    def supports_boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.supports_boost_mode

    @property
    def low(self) -> bool:
        return self._roomclimatecontrol_service.low

    @low.setter
    def low(self, value: bool) -> None:
        self._roomclimatecontrol_service.low = value

    async def async_set_low(self, value: bool) -> None:
        """Async write: set ECO (low) mode."""
        await self._roomclimatecontrol_service.async_put_state_element("low", value)

    @property
    def supports_low(self) -> bool:
        return self._roomclimatecontrol_service.supports_low

    @property
    def supports_eco(self) -> bool:
        return self._roomclimatecontrol_service.supports_eco

    @property
    def summer_mode(self) -> bool:
        return self._roomclimatecontrol_service.summer_mode

    @summer_mode.setter
    def summer_mode(self, value: bool) -> None:
        self._roomclimatecontrol_service.summer_mode = value

    async def async_set_summer_mode(self, value: bool) -> None:
        """Async write: set summer mode (off-season / HVAC off)."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "summerMode", value
        )

    @property
    def room_control_mode(self) -> str:
        return self._roomclimatecontrol_service.room_control_mode

    @room_control_mode.setter
    def room_control_mode(self, value: str) -> None:
        self._roomclimatecontrol_service.room_control_mode = value

    async def async_set_room_control_mode(self, value: str) -> None:
        """Async write: set room control mode (HEATING/COOLING)."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "roomControlMode", value
        )

    @property
    def cooling_mode(self) -> bool:
        return self._roomclimatecontrol_service.cooling_mode

    @cooling_mode.setter
    def cooling_mode(self, value: bool) -> None:
        self._roomclimatecontrol_service.cooling_mode = value

    async def async_set_cooling_mode(self, value: bool) -> None:
        """Async write: set cooling mode (True=COOLING, False=HEATING)."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "roomControlMode", "COOLING" if value else "HEATING"
        )

    @property
    def supports_cooling(self) -> bool:
        # Prefer the dedicated capability service (#70/#304/#330/#334): it
        # advertises COOLING only on genuinely cool-capable rooms. Fall back to
        # the RoomClimateControl field-presence heuristic on older firmware /
        # devices that do not expose ThermostatSupportedControlMode.
        if self._supportedcontrolmode_service is not None:
            return self._supportedcontrolmode_service.supports_cooling
        return self._roomclimatecontrol_service.supports_cooling

    @property
    def supported_control_modes(self) -> list[Any]:
        if self._supportedcontrolmode_service is not None:
            return self._supportedcontrolmode_service.supported_control_modes
        return []

    @property
    def has_demand(self) -> bool:
        return self._roomclimatecontrol_service.has_demand


class SHCHeatingCircuit(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._heating_circuit_service: HeatingCircuitService = self.device_service(  # type: ignore[assignment]
            "HeatingCircuit"
        )

    @property
    def setpoint_temperature(self) -> float:
        return self._heating_circuit_service.setpoint_temperature

    @setpoint_temperature.setter
    def setpoint_temperature(self, temperature: float) -> None:
        self._heating_circuit_service.setpoint_temperature = temperature

    async def async_set_setpoint_temperature(self, temperature: float) -> None:
        """Async write: set HeatingCircuit setpoint temperature."""
        await self._heating_circuit_service.async_put_state_element(
            "setpointTemperature", temperature
        )

    @property
    def operation_mode(self) -> HeatingCircuitService.OperationMode:
        return self._heating_circuit_service.operation_mode

    @operation_mode.setter
    def operation_mode(self, mode: HeatingCircuitService.OperationMode) -> None:
        self._heating_circuit_service.operation_mode = mode

    async def async_set_operation_mode(
        self, mode: HeatingCircuitService.OperationMode
    ) -> None:
        """Async write: set HeatingCircuit operation mode (AUTOMATIC/MANUAL)."""
        await self._heating_circuit_service.async_put_state_element(
            "operationMode", mode.value
        )

    async def async_set_setpoint_temperature_eco(self, temperature: float) -> None:
        """Async write: set HeatingCircuit ECO setpoint temperature."""
        await self._heating_circuit_service.async_put_state_element(
            "setpointTemperatureForLevelEco", temperature
        )

    async def async_set_setpoint_temperature_comfort(self, temperature: float) -> None:
        """Async write: set HeatingCircuit comfort setpoint temperature."""
        await self._heating_circuit_service.async_put_state_element(
            "setpointTemperatureForLevelComfort", temperature
        )

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

    @property
    def heating_type(self) -> HeatingCircuitService.HeatingType | None:
        return self._heating_circuit_service.heating_type


class SHCWallThermostat(
    SHCBatteryDevice, _TemperatureLevel, _HumidityLevel, _Thermostat, _TemperatureOffset
):
    pass


class SHCThermostatGen2(SHCThermostat):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._display_config_service: DisplayConfiguration | None = self.device_service(  # type: ignore[assignment]
            "DisplayConfiguration"
        )
        self._display_direction_service: DisplayDirection | None = self.device_service(  # type: ignore[assignment]
            "DisplayDirection"
        )
        self._displayed_temp_service: DisplayedTemperatureConfiguration | None = (
            self.device_service(  # type: ignore[assignment]
                "DisplayedTemperatureConfiguration"
            )
        )
        self._wall_thermostat_config_service: WallThermostatConfiguration | None = (
            self.device_service(  # type: ignore[assignment]
                "WallThermostatConfiguration"
            )
        )

    @property
    def display_brightness(self) -> int | None:
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_brightness

    @display_brightness.setter
    def display_brightness(self, value: int) -> None:
        if self._display_config_service is not None:
            self._display_config_service.display_brightness = value

    async def async_set_display_brightness(self, value: int) -> None:
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayBrightness(value)

    @property
    def display_on_time(self) -> int | None:
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_on_time

    @display_on_time.setter
    def display_on_time(self, value: int) -> None:
        if self._display_config_service is not None:
            self._display_config_service.display_on_time = value

    async def async_set_display_on_time(self, value: int) -> None:
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayOnTime(value)

    @property
    def humidity_warning_enabled(self) -> bool | None:
        if self._display_config_service is None:
            return None
        return self._display_config_service.humidity_warning_enabled

    @humidity_warning_enabled.setter
    def humidity_warning_enabled(self, value: bool) -> None:
        if self._display_config_service is not None:
            self._display_config_service.humidity_warning_enabled = value

    async def async_set_humidity_warning_enabled(self, value: bool) -> None:
        if self._display_config_service is not None:
            await self._display_config_service.async_set_humidityWarningEnabled(value)

    @property
    def display_direction(self) -> DisplayDirection.Direction | None:
        if self._display_direction_service is None:
            return None
        return self._display_direction_service.direction

    @display_direction.setter
    def display_direction(self, value: DisplayDirection.Direction) -> None:
        if self._display_direction_service is not None:
            self._display_direction_service.direction = value

    async def async_set_display_direction(
        self, value: DisplayDirection.Direction
    ) -> None:
        if self._display_direction_service is not None:
            await self._display_direction_service.async_set_direction(value)

    @property
    def displayed_temperature(
        self,
    ) -> DisplayedTemperatureConfiguration.DisplayedTemperature | None:
        if self._displayed_temp_service is None:
            return None
        return self._displayed_temp_service.displayed_temperature

    @displayed_temperature.setter
    def displayed_temperature(
        self, value: DisplayedTemperatureConfiguration.DisplayedTemperature
    ) -> None:
        if self._displayed_temp_service is not None:
            self._displayed_temp_service.displayed_temperature = value

    async def async_set_displayed_temperature(
        self, value: DisplayedTemperatureConfiguration.DisplayedTemperature
    ) -> None:
        if self._displayed_temp_service is not None:
            await self._displayed_temp_service.async_set_displayedTemperature(value)

    @property
    def valve_type(self) -> WallThermostatConfiguration.ValveType | None:
        if self._wall_thermostat_config_service is None:
            return None
        return self._wall_thermostat_config_service.valve_type

    @valve_type.setter
    def valve_type(self, value: WallThermostatConfiguration.ValveType) -> None:
        if self._wall_thermostat_config_service is not None:
            self._wall_thermostat_config_service.valve_type = value

    async def async_set_valve_type(
        self, value: WallThermostatConfiguration.ValveType
    ) -> None:
        if self._wall_thermostat_config_service is not None:
            await self._wall_thermostat_config_service.async_set_valveType(value)

    @property
    def heater_type(self) -> WallThermostatConfiguration.HeaterType | None:
        if self._wall_thermostat_config_service is None:
            return None
        return self._wall_thermostat_config_service.heater_type

    @heater_type.setter
    def heater_type(self, value: WallThermostatConfiguration.HeaterType) -> None:
        if self._wall_thermostat_config_service is not None:
            self._wall_thermostat_config_service.heater_type = value

    async def async_set_heater_type(
        self, value: WallThermostatConfiguration.HeaterType
    ) -> None:
        if self._wall_thermostat_config_service is not None:
            await self._wall_thermostat_config_service.async_set_heaterType(value)

    @property
    def supports_display_configuration(self) -> bool:
        return self._display_config_service is not None

    @property
    def supports_display_direction(self) -> bool:
        return self._display_direction_service is not None

    @property
    def supports_displayed_temperature(self) -> bool:
        return self._displayed_temp_service is not None

    @property
    def supports_wall_thermostat_configuration(self) -> bool:
        return self._wall_thermostat_config_service is not None


class SHCRoomThermostat2(
    SHCWallThermostat,
    _CommunicationQuality,
    _Thermostat,
    _TemperatureOffset,
):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._display_config_service: DisplayConfiguration | None = self.device_service(  # type: ignore[assignment]
            "DisplayConfiguration"
        )
        self._display_direction_service: DisplayDirection | None = self.device_service(  # type: ignore[assignment]
            "DisplayDirection"
        )
        self._displayed_temp_service: DisplayedTemperatureConfiguration | None = (
            self.device_service(  # type: ignore[assignment]
                "DisplayedTemperatureConfiguration"
            )
        )
        self._terminal_config_service: TerminalConfiguration | None = (
            self.device_service(  # type: ignore[assignment]
                "TerminalConfiguration"
            )
        )

    @property
    def display_brightness(self) -> int | None:
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_brightness

    @display_brightness.setter
    def display_brightness(self, value: int) -> None:
        if self._display_config_service is not None:
            self._display_config_service.display_brightness = value

    async def async_set_display_brightness(self, value: int) -> None:
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayBrightness(value)

    @property
    def display_on_time(self) -> int | None:
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_on_time

    @display_on_time.setter
    def display_on_time(self, value: int) -> None:
        if self._display_config_service is not None:
            self._display_config_service.display_on_time = value

    async def async_set_display_on_time(self, value: int) -> None:
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayOnTime(value)

    @property
    def humidity_warning_enabled(self) -> bool | None:
        if self._display_config_service is None:
            return None
        return self._display_config_service.humidity_warning_enabled

    @humidity_warning_enabled.setter
    def humidity_warning_enabled(self, value: bool) -> None:
        if self._display_config_service is not None:
            self._display_config_service.humidity_warning_enabled = value

    async def async_set_humidity_warning_enabled(self, value: bool) -> None:
        if self._display_config_service is not None:
            await self._display_config_service.async_set_humidityWarningEnabled(value)

    @property
    def display_direction(self) -> DisplayDirection.Direction | None:
        if self._display_direction_service is None:
            return None
        return self._display_direction_service.direction

    @display_direction.setter
    def display_direction(self, value: DisplayDirection.Direction) -> None:
        if self._display_direction_service is not None:
            self._display_direction_service.direction = value

    async def async_set_display_direction(
        self, value: DisplayDirection.Direction
    ) -> None:
        if self._display_direction_service is not None:
            await self._display_direction_service.async_set_direction(value)

    @property
    def displayed_temperature(
        self,
    ) -> DisplayedTemperatureConfiguration.DisplayedTemperature | None:
        if self._displayed_temp_service is None:
            return None
        return self._displayed_temp_service.displayed_temperature

    @displayed_temperature.setter
    def displayed_temperature(
        self, value: DisplayedTemperatureConfiguration.DisplayedTemperature
    ) -> None:
        if self._displayed_temp_service is not None:
            self._displayed_temp_service.displayed_temperature = value

    async def async_set_displayed_temperature(
        self, value: DisplayedTemperatureConfiguration.DisplayedTemperature
    ) -> None:
        if self._displayed_temp_service is not None:
            await self._displayed_temp_service.async_set_displayedTemperature(value)

    @property
    def terminal_type(self) -> TerminalConfiguration.Type | None:
        if self._terminal_config_service is None:
            return None
        return self._terminal_config_service.type

    @terminal_type.setter
    def terminal_type(self, value: TerminalConfiguration.Type) -> None:
        if self._terminal_config_service is not None:
            self._terminal_config_service.type = value

    async def async_set_terminal_type(self, value: TerminalConfiguration.Type) -> None:
        if self._terminal_config_service is not None:
            await self._terminal_config_service.async_set_type(value)

    @property
    def terminal_temperature(self) -> float | None:
        if self._terminal_config_service is None:
            return None
        return self._terminal_config_service.temperature

    @property
    def supported_terminal_types(self) -> list[Any]:
        if self._terminal_config_service is None:
            return []
        return self._terminal_config_service.supported_types

    @property
    def supports_display_configuration(self) -> bool:
        return self._display_config_service is not None

    @property
    def supports_display_direction(self) -> bool:
        return self._display_direction_service is not None

    @property
    def supports_displayed_temperature(self) -> bool:
        return self._displayed_temp_service is not None

    @property
    def supports_terminal_configuration(self) -> bool:
        return self._terminal_config_service is not None


class SHCUniversalSwitch(SHCBatteryDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._keypad_service: KeypadService = self.device_service("Keypad")  # type: ignore[assignment]
        # KeypadTrigger is optional/unconfirmed in rawscans — guard on None.
        self._keypadtrigger_service: KeypadTriggerService | None = self.device_service(  # type: ignore[assignment]
            "KeypadTrigger"
        )

    @property
    def supports_keypadtrigger(self) -> bool:
        return self._keypadtrigger_service is not None

    @property
    def keypadtrigger(self) -> KeypadTriggerService | None:
        """The KeypadTrigger service (scenario mapping), or None."""
        return self._keypadtrigger_service

    @property
    def keystates(self) -> list[str]:
        return ["LOWER_BUTTON", "UPPER_BUTTON"]

    @property
    def eventtypes(self) -> type[KeypadService.KeyEvent]:
        return self._keypad_service.KeyEvent

    @property
    def keycode(self) -> int:
        return self._keypad_service.keyCode

    @property
    def keyname(self) -> KeypadService.KeyState | None:
        return self._keypad_service.keyName

    @property
    def eventtype(self) -> KeypadService.KeyEvent | None:
        return self._keypad_service.eventType

    @property
    def eventtimestamp(self) -> int:
        return self._keypad_service.eventTimestamp


class SHCUniversalSwitch2(SHCUniversalSwitch):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)

    @property
    def keystates(self) -> list[str]:
        return [
            "LOWER_LEFT_BUTTON",
            "LOWER_RIGHT_BUTTON",
            "UPPER_LEFT_BUTTON",
            "UPPER_RIGHT_BUTTON",
        ]


class SHCMotionDetector(SHCBatteryDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._service: LatestMotionService = self.device_service("LatestMotion")  # type: ignore[assignment]
        self._multi_level_sensor_service: MultiLevelSensorService = self.device_service(  # type: ignore[assignment]
            "MultiLevelSensor"
        )

    @property
    def latestmotion(self) -> str:
        return self._service.latestMotionDetected

    @property
    def illuminance(self) -> int:
        return self._multi_level_sensor_service.illuminance


class SHCMotionDetector2(SHCBatteryDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._multi_level_switch_service: MultiLevelSwitchService = self.device_service(  # type: ignore[assignment]
            "MultiLevelSwitch"
        )
        self._binaryswitch_service: BinarySwitchService = self.device_service(  # type: ignore[assignment]
            "BinarySwitch"
        )
        self._detectiontest_service: DetectionTestService | None = self.device_service(  # type: ignore[assignment]
            "DetectionTest"
        )
        self._latestmotion_service: LatestMotionService = self.device_service(  # type: ignore[assignment]
            "LatestMotion"
        )
        self._multi_level_sensor_service: MultiLevelSensorService = self.device_service(  # type: ignore[assignment]
            "MultiLevelSensor"
        )
        self._latesttamper_service: LatestTamperService = self.device_service(  # type: ignore[assignment]
            "LatestTamper"
        )
        self._temperaturelevel_service: TemperatureLevelService = self.device_service(  # type: ignore[assignment]
            "TemperatureLevel"
        )
        self._pollcontrol_service: PollControlService = self.device_service(  # type: ignore[assignment]
            "PollControl"
        )
        self._pirsensorconfiguration_service: PirSensorConfigurationService = (
            self.device_service(  # type: ignore[assignment]
                "PirSensorConfiguration"
            )
        )
        self._occupancydetection_service: OccupancyDetectionService = (
            self.device_service(  # type: ignore[assignment]
                "OccupancyDetection"
            )
        )
        self._communicationquality_service: CommunicationQualityService = (
            self.device_service(  # type: ignore[assignment]
                "CommunicationQuality"
            )
        )
        self._petimmunity_service: PetImmunityService = self.device_service(  # type: ignore[assignment]
            "PetImmunity"
        )
        self._walktest_service: WalkTestService | None = self.device_service(  # type: ignore[assignment]
            "WalkTest"
        )
        self._smart_sensitivity_control_service: (
            SmartSensitivityControlService | None
        ) = self.device_service(  # type: ignore[assignment]
            "SmartSensitivityControl"
        )

    @property
    def latestmotion(self) -> str:
        return self._latestmotion_service.latestMotionDetected

    @property
    def illuminance(self) -> int:
        return self._multi_level_sensor_service.illuminance

    @property
    def multi_level_switch(self) -> int:
        return self._multi_level_switch_service.value

    @multi_level_switch.setter
    def multi_level_switch(self, value: int) -> None:
        self._multi_level_switch_service.put_state_element("level", value)

    async def async_set_multi_level_switch(self, value: int) -> None:
        """Async write: set indicator light brightness level (0-100)."""
        await self._multi_level_switch_service.async_put_state_element("level", value)

    @property
    def binaryswitch(self) -> bool:
        return self._binaryswitch_service.value

    @binaryswitch.setter
    def binaryswitch(self, value: bool) -> None:
        self._binaryswitch_service.put_state_element("on", bool(value))

    async def async_set_binaryswitch(self, value: bool) -> None:
        """Async write: turn indicator light on/off via BinarySwitch service."""
        await self._binaryswitch_service.async_put_state_element("on", bool(value))

    @property
    def detection_state(self) -> DetectionTestService.DetectionState | None:
        if self._detectiontest_service is None:
            return None
        return self._detectiontest_service.detection_state

    def set_detection_state_request(
        self, value: DetectionTestService.DetectionStateRequest
    ) -> None:
        """Sync write: start or stop the detection (walk) test."""
        if self._detectiontest_service is not None:
            self._detectiontest_service.set_detection_state_request(value)

    async def async_set_detection_state_request(
        self, value: DetectionTestService.DetectionStateRequest
    ) -> None:
        """Async write: start or stop the detection (walk) test."""
        if self._detectiontest_service is not None:
            await self._detectiontest_service.async_set_detection_state_request(value)

    @property
    def temperature(self) -> float:
        return self._temperaturelevel_service.temperature

    @property
    def long_poll_interval(self) -> PollControlService.PollControlState:
        return self._pollcontrol_service.longPollInterval

    @long_poll_interval.setter
    def long_poll_interval(self, value: PollControlService.PollControlState) -> None:
        self._pollcontrol_service.longPollInterval = value

    async def async_set_long_poll_interval(
        self, value: PollControlService.PollControlState
    ) -> None:
        """Async write: set the orientation-light polling profile (LONG/SHORT)."""
        await self._pollcontrol_service.async_set_long_poll_interval(value)

    @property
    def motion_sensitivity(self) -> PirSensorConfigurationService.MotionSensitivity:
        return self._pirsensorconfiguration_service.motionSensitivity

    @motion_sensitivity.setter
    def motion_sensitivity(
        self, value: PirSensorConfigurationService.MotionSensitivity
    ) -> None:
        self._pirsensorconfiguration_service.put_state_element(
            "motionSensitivity", value.name
        )

    async def async_set_motion_sensitivity(
        self, value: PirSensorConfigurationService.MotionSensitivity
    ) -> None:
        """Async write: set motion sensitivity on PirSensorConfiguration service."""
        await self._pirsensorconfiguration_service.async_put_state_element(
            "motionSensitivity", value.name
        )

    @property
    def occupied(self) -> bool:
        return self._occupancydetection_service.isOccupied

    @property
    def last_occupancy_change_time(self) -> str:
        return self._occupancydetection_service.lastOccupancyChangeTime

    @property
    def communicationquality(self) -> CommunicationQualityService.State:
        return self._communicationquality_service.value

    @property
    def pet_immunity_enabled(self) -> bool:
        return self._petimmunity_service.enabled

    @pet_immunity_enabled.setter
    def pet_immunity_enabled(self, value: bool) -> None:
        self._petimmunity_service.enabled = value

    async def async_set_pet_immunity_enabled(self, value: bool) -> None:
        """Async write: enable/disable pet immunity."""
        await self._petimmunity_service.async_put_state_element("enabled", value)

    @property
    def last_tamper_time(self) -> str:
        return self._latesttamper_service.last_tamper_time

    @property
    def was_tampered(self) -> bool:
        return self._latesttamper_service.was_tampered

    @property
    def tamper_protection_enabled(self) -> bool:
        return self._latesttamper_service.tamper_protection_enabled

    @tamper_protection_enabled.setter
    def tamper_protection_enabled(self, value: bool) -> None:
        self._latesttamper_service.tamper_protection_enabled = value

    async def async_set_tamper_protection_enabled(self, value: bool) -> None:
        """Async write: enable/disable tamper protection."""
        await self._latesttamper_service.async_set_tamper_protection_enabled(value)

    def reset_tampered_state(self) -> None:
        """Sync: reset an active tamper condition (confirm device in place)."""
        self._latesttamper_service.reset_tampered_state()

    async def async_reset_tampered_state(self) -> None:
        """Async: reset an active tamper condition."""
        await self._latesttamper_service.async_reset_tampered_state()

    @property
    def walk_state(self) -> WalkTestService.WalkState | None:
        if self._walktest_service is None:
            return None
        return self._walktest_service.walk_state

    @property
    def walk_state_request(self) -> WalkTestService.WalkStateRequest | None:
        if self._walktest_service is None:
            return None
        return self._walktest_service.walk_state_request

    @walk_state_request.setter
    def walk_state_request(self, value: WalkTestService.WalkStateRequest) -> None:
        if self._walktest_service is not None:
            self._walktest_service.walk_state_request = value

    @property
    def pet_immunity_walk_state(self) -> WalkTestService.PetImmunityState | None:
        if self._walktest_service is None:
            return None
        return self._walktest_service.pet_immunity_state

    def set_walk_state_request(self, value: WalkTestService.WalkStateRequest) -> None:
        """Sync write: start or stop the walk test."""
        if self._walktest_service is not None:
            self._walktest_service.walk_state_request = value

    async def async_set_walk_state_request(
        self, value: WalkTestService.WalkStateRequest
    ) -> None:
        """Async write: start or stop the walk test."""
        if self._walktest_service is not None:
            await self._walktest_service.async_set_walk_state_request(value)

    @property
    def smart_sensitivity_enabled(self) -> bool:
        if self._smart_sensitivity_control_service is None:
            return False
        return self._smart_sensitivity_control_service.enabled

    @smart_sensitivity_enabled.setter
    def smart_sensitivity_enabled(self, value: bool) -> None:
        if self._smart_sensitivity_control_service is not None:
            self._smart_sensitivity_control_service.enabled = value

    async def async_set_smart_sensitivity_enabled(self, value: bool) -> None:
        """Async write: enable/disable smart sensitivity control."""
        if self._smart_sensitivity_control_service is not None:
            await self._smart_sensitivity_control_service.async_set_enabled(value)

    def get_smart_sensitivity(
        self, context: SmartSensitivityControlService.SmartSensitivityContext
    ) -> dict[str, Any] | None:
        """Return the sensitivity dict for the given context."""
        if self._smart_sensitivity_control_service is None:
            return None
        return self._smart_sensitivity_control_service.get_sensitivity(context)

    def set_smart_sensitivity_manual_level(
        self,
        context: SmartSensitivityControlService.SmartSensitivityContext,
        level: SmartSensitivityControlService.MotionSensitivity,
    ) -> None:
        """Sync write: set manual sensitivity level for a context."""
        if self._smart_sensitivity_control_service is not None:
            self._smart_sensitivity_control_service.set_manual_level(context, level)

    async def async_set_smart_sensitivity_manual_level(
        self,
        context: SmartSensitivityControlService.SmartSensitivityContext,
        level: SmartSensitivityControlService.MotionSensitivity,
    ) -> None:
        """Async write: set manual sensitivity level for a context."""
        if self._smart_sensitivity_control_service is not None:
            await self._smart_sensitivity_control_service.async_set_manual_level(
                context, level
            )

    @property
    def supports_walk_test(self) -> bool:
        return self._walktest_service is not None

    @property
    def supports_detection_test(self) -> bool:
        return self._detectiontest_service is not None

    @property
    def supports_smart_sensitivity(self) -> bool:
        return self._smart_sensitivity_control_service is not None


class SHCTwinguard(SHCBatteryDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._airqualitylevel_service: AirQualityLevelService = self.device_service(  # type: ignore[assignment]
            "AirQualityLevel"
        )
        self._smokedetectorcheck_service: SmokeDetectorCheckService = (
            self.device_service(  # type: ignore[assignment]
                "SmokeDetectorCheck"
            )
        )
        self._smoke_sensitivity_service: SmokeSensitivityService | None = (
            self.device_service(  # type: ignore[assignment]
                "SmokeSensitivity"
            )
        )
        self._twinguard_nightly_promise_service: (
            TwinguardNightlyPromiseService | None
        ) = self.device_service(  # type: ignore[assignment]
            "TwinguardNightlyPromise"
        )

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

    def smoketest_requested(self) -> None:
        self._smokedetectorcheck_service.put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    async def async_smoketest_requested(self) -> None:
        """Async write: request a smoke test (Twinguard)."""
        await self._smokedetectorcheck_service.async_put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    @property
    def smoke_sensitivity(self) -> SmokeSensitivityService.SmokeSensitivityLevel | None:
        if self._smoke_sensitivity_service is None:
            return None
        return self._smoke_sensitivity_service.smoke_sensitivity

    @smoke_sensitivity.setter
    def smoke_sensitivity(
        self, value: SmokeSensitivityService.SmokeSensitivityLevel
    ) -> None:
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.smoke_sensitivity = value

    async def async_set_smoke_sensitivity(
        self, value: SmokeSensitivityService.SmokeSensitivityLevel
    ) -> None:
        """Async write: set smoke sensitivity level."""
        if self._smoke_sensitivity_service is not None:
            await self._smoke_sensitivity_service.async_set_smoke_sensitivity(value)

    @property
    def pre_alarm_enabled(self) -> bool:
        if self._smoke_sensitivity_service is None:
            return False
        return self._smoke_sensitivity_service.pre_alarm_enabled

    @pre_alarm_enabled.setter
    def pre_alarm_enabled(self, value: bool) -> None:
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.pre_alarm_enabled = value

    async def async_set_pre_alarm_enabled(self, value: bool) -> None:
        """Async write: enable/disable pre-alarm."""
        if self._smoke_sensitivity_service is not None:
            await self._smoke_sensitivity_service.async_set_pre_alarm_enabled(value)

    @property
    def supports_smoke_sensitivity(self) -> bool:
        return self._smoke_sensitivity_service is not None

    @property
    def supports_nightly_promise(self) -> bool:
        return self._twinguard_nightly_promise_service is not None

    @property
    def nightly_promise_enabled(self) -> bool:
        if self._twinguard_nightly_promise_service is None:
            return False
        return self._twinguard_nightly_promise_service.nightly_promise_enabled

    @nightly_promise_enabled.setter
    def nightly_promise_enabled(self, value: bool) -> None:
        if self._twinguard_nightly_promise_service is not None:
            self._twinguard_nightly_promise_service.nightly_promise_enabled = value

    async def async_set_nightly_promise_enabled(self, value: bool) -> None:
        """Async write: enable/disable nightly promise self-check."""
        if self._twinguard_nightly_promise_service is not None:
            await self._twinguard_nightly_promise_service.async_set_nightly_promise_enabled(
                value
            )


class SHCSmokeDetectionSystem(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._surveillancealarm_service: SurveillanceAlarmService = self.device_service(  # type: ignore[assignment]
            "SurveillanceAlarm"
        )
        # self._smokedetectioncontrol_service = self.device_service("SmokeDetectionControl")

    @property
    def alarm(self) -> SurveillanceAlarmService.State:
        return self._surveillancealarm_service.value


class SHCPresenceSimulationSystem(SHCDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._presencesimulationconfiguration_service: PresenceSimulationConfigurationService = self.device_service(  # type: ignore[assignment]
            "PresenceSimulationConfiguration"
        )

    @property
    def enabled(self) -> bool:
        return self._presencesimulationconfiguration_service.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._presencesimulationconfiguration_service.enabled = value

    async def async_set_enabled(self, value: bool) -> None:
        """Async write: enable/disable presence simulation."""
        await self._presencesimulationconfiguration_service.async_put_state_element(
            "enabled", value
        )


class SHCLight(SHCDevice):
    class Capabilities(Flag):
        BRIGHTNESS = auto()
        COLOR_TEMP = auto()
        COLOR_HSB = auto()

    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)

        self._binaryswitch_service: BinarySwitchService = self.device_service(  # type: ignore[assignment]
            "BinarySwitch"
        )
        self._multilevelswitch_service: MultiLevelSwitchService | None = (
            self.device_service(  # type: ignore[assignment]
                "MultiLevelSwitch"
            )
        )
        self._huecolortemperature_service: HueColorTemperatureService | None = (
            self.device_service(  # type: ignore[assignment]
                "HueColorTemperature"
            )
        )
        self._hsbcoloractuator_service: HSBColorActuatorService | None = (
            self.device_service(  # type: ignore[assignment]
                "HSBColorActuator"
            )
        )

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
    def binarystate(self, state: bool) -> None:
        self._binaryswitch_service.put_state_element("on", True if state else False)

    async def async_set_binarystate(self, state: bool) -> None:
        """Async write: turn light on/off via BinarySwitch service."""
        await self._binaryswitch_service.async_put_state_element(
            "on", True if state else False
        )

    @property
    def brightness(self) -> int:
        if self._multilevelswitch_service is not None:
            return self._multilevelswitch_service.value
        return 0

    @brightness.setter
    def brightness(self, state: int) -> None:
        if self._multilevelswitch_service is not None:
            self._multilevelswitch_service.put_state_element("level", state)

    async def async_set_brightness(self, state: int) -> None:
        """Async write: set brightness level (0-100) via MultiLevelSwitch service."""
        if self._multilevelswitch_service is not None:
            await self._multilevelswitch_service.async_put_state_element("level", state)

    @property
    def color(self) -> int:
        if self._huecolortemperature_service is not None:
            return self._huecolortemperature_service.value
        return 0

    @color.setter
    def color(self, state: int) -> None:
        if self._huecolortemperature_service is not None:
            self._huecolortemperature_service.put_state_element(
                "colorTemperature", state
            )

    async def async_set_color(self, state: int) -> None:
        """Async write: set color temperature (mireds) via HueColorTemperature service."""
        if self._huecolortemperature_service is not None:
            await self._huecolortemperature_service.async_put_state_element(
                "colorTemperature", state
            )

    @property
    def rgb(self) -> int:
        if self._hsbcoloractuator_service is not None:
            return self._hsbcoloractuator_service.value
        return 0

    @rgb.setter
    def rgb(self, state: int) -> None:
        if self._hsbcoloractuator_service is not None:
            self._hsbcoloractuator_service.put_state_element("rgb", state)

    async def async_set_rgb(self, state: int) -> None:
        """Async write: set RGB color via HSBColorActuator service."""
        if self._hsbcoloractuator_service is not None:
            await self._hsbcoloractuator_service.async_put_state_element("rgb", state)

    @property
    def min_color_temperature(self) -> int:
        if self._huecolortemperature_service is not None:
            return self._huecolortemperature_service.min_value
        if self._hsbcoloractuator_service is not None:
            return self._hsbcoloractuator_service.min_value
        return 0

    @property
    def max_color_temperature(self) -> int:
        if self._huecolortemperature_service is not None:
            return self._huecolortemperature_service.max_value
        if self._hsbcoloractuator_service is not None:
            return self._hsbcoloractuator_service.max_value
        return 0

    @property
    def supports_brightness(self) -> bool:
        return bool(self._capabilities & self.Capabilities.BRIGHTNESS)

    @property
    def supports_color_temp(self) -> bool:
        return bool(self._capabilities & self.Capabilities.COLOR_TEMP)

    @property
    def supports_color_hsb(self) -> bool:
        return bool(self._capabilities & self.Capabilities.COLOR_HSB)


class SHCWaterLeakageSensor(SHCBatteryDevice):
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)

        self._leakage_service: WaterLeakageSensorService = self.device_service(  # type: ignore[assignment]
            "WaterLeakageSensor"
        )
        self._tilt_service: WaterLeakageSensorTiltService = self.device_service(  # type: ignore[assignment]
            "WaterLeakageSensorTilt"
        )
        self._sensor_check_service: WaterLeakageSensorCheckService = (
            self.device_service(  # type: ignore[assignment]
                "WaterLeakageSensorCheck"
            )
        )

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
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        # #123: optional dimmer calibration config; guard on None.
        self._dimmerconfig_service: DimmerConfigurationService | None = (
            self.device_service(  # type: ignore[assignment]
                "DimmerConfiguration"
            )
        )

    @property
    def supports_dimmer_configuration(self) -> bool:
        return self._dimmerconfig_service is not None

    @property
    def dimmer_configuration(self) -> DimmerConfigurationService | None:
        """The DimmerConfiguration service (calibration), or None."""
        return self._dimmerconfig_service

    @property
    def binarystate(self) -> bool:
        if self._powerswitch_service is not None:
            return self._powerswitch_service.value == PowerSwitchService.State.ON
        return False

    @binarystate.setter
    def binarystate(self, state: bool) -> None:
        if self._powerswitch_service is not None:
            self._powerswitch_service.put_state_element(
                "switchState", "ON" if state else "OFF"
            )

    async def async_set_binarystate(self, state: bool) -> None:
        """Async write: turn dimmer on/off via PowerSwitch service (overrides SHCLight)."""
        if self._powerswitch_service is not None:
            await self._powerswitch_service.async_put_state_element(
                "switchState", "ON" if state else "OFF"
            )


class SHCOutdoorSiren(SHCBatteryDevice):
    """Bosch Outdoor Siren (model OUTDOOR_SIREN, #120).

    Exposes the read-only siren/tamper state, the writable configuration block
    (duration/sound-level/delays) and a test-alarm operation, plus power-supply
    diagnostics. The siren cannot be switched on directly — it fires from the
    intrusion system; the only on-demand acoustic check is the test alarm.
    """

    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        super().__init__(api, raw_device, raw_device_services)
        self._siren_service: OutdoorSirenService = self.device_service("OutdoorSiren")  # type: ignore[assignment]
        self._powersupply_service: OutdoorSirenPowerSupplyService | None = (
            self.device_service(  # type: ignore[assignment]
                "OutdoorSirenPowerSupply"
            )
        )

    @property
    def siren(self) -> OutdoorSirenService:
        return self._siren_service

    @property
    def power_supply(self) -> OutdoorSirenPowerSupplyService | None:
        return self._powersupply_service

    @property
    def supports_power_supply(self) -> bool:
        return self._powersupply_service is not None

    async def async_trigger_test_alarm(
        self, sound_level: OutdoorSirenService.SoundLevel | None = None
    ) -> None:
        """Async: fire a short test alarm at the given (or configured) level."""
        await self._siren_service.async_trigger_test_alarm(sound_level)


MODEL_MAPPING = {
    "SWD": SHCShutterContact,
    "SWD2": SHCShutterContact2,
    "SWD2_DUAL": SHCShutterContact2,
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
    "PLUG_COMPACT_DUAL": SHCSmartPlugCompact,
    "SD": SHCSmokeDetector,
    "SMOKE_DETECTOR2": SHCSmokeDetector,
    "CAMERA_EYES": SHCCameraEyes,
    "CAMERA_360": SHCCamera360,
    "CAMERA_OUTDOOR_GEN2": SHCCameraOutdoorGen2,
    "ROOM_CLIMATE_CONTROL": SHCClimateControl,
    "TRV": SHCThermostat,
    "TRV_GEN2": SHCThermostatGen2,
    "TRV_GEN2_DUAL": SHCThermostatGen2,
    "THB": SHCWallThermostat,
    "BWTH": SHCWallThermostat,
    "BWTH24": SHCWallThermostat,
    "RTH2_BAT": SHCRoomThermostat2,
    "RTH2_230": SHCRoomThermostat2,
    "WRC2": SHCUniversalSwitch,
    "SWITCH2": SHCUniversalSwitch2,
    "MD": SHCMotionDetector,
    "MD2": SHCMotionDetector2,
    "PRESENCE_SIMULATION_SERVICE": SHCPresenceSimulationSystem,
    "TWINGUARD": SHCTwinguard,
    "SMOKE_DETECTION_SYSTEM": SHCSmokeDetectionSystem,
    "LEDVANCE_LIGHT": SHCLight,
    "HUE_LIGHT": SHCLight,
    "WLS": SHCWaterLeakageSensor,
    "HEATING_CIRCUIT": SHCHeatingCircuit,
    "MICROMODULE_DIMMER": SHCMicromoduleDimmer,
    "OUTDOOR_SIREN": SHCOutdoorSiren,
}

SUPPORTED_MODELS = MODEL_MAPPING.keys()


def build(
    api: SHCAPI,
    raw_device: dict[str, Any],
    raw_device_services: list[dict[str, Any]],
) -> SHCDevice:
    device_model: str = raw_device["deviceModel"]
    if device_model not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported device model: {device_model!r}")
    return MODEL_MAPPING[device_model](
        api=api, raw_device=raw_device, raw_device_services=raw_device_services
    )
