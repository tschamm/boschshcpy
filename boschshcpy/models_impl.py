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

    async def async_set_child_lock(self, state: bool):
        """Async write: set childLockActive on ChildProtection service."""
        await self._childprotection_service.async_put_state_element("childLockActive", state)


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

    async def async_set_child_lock(self, state: bool):
        """Async write: set childLock on Thermostat service."""
        await self._thermostat_service.async_put_state_element(
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

    async def async_set_switchstate(self, state: bool):
        """Async write: set switchState on PowerSwitch service."""
        await self._powerswitch_service.async_put_state_element(
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
    def temperature(self) -> float | None:
        if self._temperaturelevel_service is None:
            return None
        return self._temperaturelevel_service.temperature


class _HumidityLevel(SHCDevice):
    from .services_impl import HumidityLevelService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._humiditylevel_service = self.device_service("HumidityLevel")

    @property
    def supports_humidity(self) -> bool:
        return self._humiditylevel_service is not None

    @property
    def humidity(self) -> float | None:
        if self._humiditylevel_service is None:
            return None
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

    async def async_set_offset(self, value: float):
        """Async write: set temperature offset."""
        await self._temperatureoffset_service.async_put_state_element("offset", value)

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

    async def async_set_silentmode(self, state: bool):
        """Async write: set silent mode."""
        if self.supports_silentmode:
            await self._silentmode_service.async_put_state_element(
                "mode", "MODE_SILENT" if state else "MODE_NORMAL"
            )


class SHCSmokeDetector(SHCBatteryDevice):
    from .services_impl import AlarmService, SmokeSensitivityService, SmokeDetectorCheckService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._alarm_service = self.device_service("Alarm")
        self._smokedetectorcheck_service = self.device_service("SmokeDetectorCheck")
        self._smoke_sensitivity_service = self.device_service("SmokeSensitivity")

    @property
    def alarmstate(self) -> AlarmService.State:
        return self._alarm_service.value

    @alarmstate.setter
    def alarmstate(self, state: str):
        self._alarm_service.put_state_element("value", state)

    async def async_set_alarmstate(self, state: str):
        """Async write: set alarm state on Alarm service."""
        await self._alarm_service.async_put_state_element("value", state)

    @property
    def smokedetectorcheck_state(self) -> SmokeDetectorCheckService.State:
        return self._smokedetectorcheck_service.value

    def smoketest_requested(self):
        self._smokedetectorcheck_service.put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    async def async_smoketest_requested(self):
        """Async write: request a smoke test."""
        await self._smokedetectorcheck_service.async_put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    @property
    def has_smoke_sensitivity_service(self) -> bool:
        return self._smoke_sensitivity_service is not None

    @property
    def smoke_sensitivity(self):
        if self._smoke_sensitivity_service is None:
            return None
        return self._smoke_sensitivity_service.smoke_sensitivity

    @smoke_sensitivity.setter
    def smoke_sensitivity(self, value: "SmokeSensitivityService.SmokeSensitivityLevel"):
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.smoke_sensitivity = value

    async def async_set_smoke_sensitivity(
        self, value: "SmokeSensitivityService.SmokeSensitivityLevel"
    ):
        """Async write: set smoke sensitivity level (if service present)."""
        if self._smoke_sensitivity_service is not None:
            await self._smoke_sensitivity_service.async_set_smoke_sensitivity(value)

    @property
    def pre_alarm_enabled(self) -> bool:
        if self._smoke_sensitivity_service is None:
            return False
        return self._smoke_sensitivity_service.pre_alarm_enabled

    @pre_alarm_enabled.setter
    def pre_alarm_enabled(self, value: bool):
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.pre_alarm_enabled = value

    async def async_set_pre_alarm_enabled(self, value: bool):
        """Async write: enable/disable pre-alarm (if service present)."""
        if self._smoke_sensitivity_service is not None:
            await self._smoke_sensitivity_service.async_set_pre_alarm_enabled(value)

    @property
    def supports_smoke_sensitivity(self) -> bool:
        return self._smoke_sensitivity_service is not None


class SHCSmartPlug(_PowerMeter, _PowerSwitch, _PowerSwitchProgram):
    from .services_impl import (
        EnergySavingModeService,
        LedBrightnessConfigurationService,
        PowerSwitchConfigurationService,
        PowerSwitchWarningService,
        RoutingService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._routing_service = self.device_service("Routing")
        self._energy_saving_mode_service = self.device_service("EnergySavingMode")
        self._led_brightness_configuration_service = self.device_service(
            "LedBrightnessConfiguration"
        )
        self._power_switch_configuration_service = self.device_service(
            "PowerSwitchConfiguration"
        )
        self._power_switch_warning_service = self.device_service("PowerSwitchWarning")

    @property
    def routing(self) -> RoutingService.State:
        return self._routing_service.value

    @routing.setter
    def routing(self, state: bool):
        self._routing_service.put_state_element(
            "value", "ENABLED" if state else "DISABLED"
        )

    async def async_set_routing(self, state: bool):
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
    def energy_saving_mode_enabled(self, value: bool):
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.energy_saving_mode_enabled = value

    async def async_set_energy_saving_mode_enabled(self, value: bool):
        """Async write: enable/disable energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_energy_saving_mode_enabled(value)

    @property
    def power_threshold(self):
        if self._energy_saving_mode_service is None:
            return None
        return self._energy_saving_mode_service.power_threshold

    @power_threshold.setter
    def power_threshold(self, value):
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.power_threshold = value

    async def async_set_power_threshold(self, value):
        """Async write: set power threshold for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_power_threshold(value)

    @property
    def enter_duration_seconds(self) -> int:
        if self._energy_saving_mode_service is None:
            return 0
        return self._energy_saving_mode_service.enter_duration_seconds

    @enter_duration_seconds.setter
    def enter_duration_seconds(self, value: int):
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.enter_duration_seconds = value

    async def async_set_enter_duration_seconds(self, value: int):
        """Async write: set enter duration for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_enter_duration_seconds(value)

    @property
    def led_brightness(self):
        if self._led_brightness_configuration_service is None:
            return None
        return self._led_brightness_configuration_service.brightness

    @led_brightness.setter
    def led_brightness(self, value):
        if self._led_brightness_configuration_service is not None:
            self._led_brightness_configuration_service.brightness = value

    async def async_set_led_brightness(self, value):
        """Async write: set LED brightness."""
        if self._led_brightness_configuration_service is not None:
            await self._led_brightness_configuration_service.async_set_brightness(value)

    @property
    def state_after_power_outage(self):
        if self._power_switch_configuration_service is None:
            return None
        return self._power_switch_configuration_service.state_after_power_outage

    @state_after_power_outage.setter
    def state_after_power_outage(
        self, value: "PowerSwitchConfigurationService.StateAfterPowerOutage"
    ):
        if self._power_switch_configuration_service is not None:
            self._power_switch_configuration_service.state_after_power_outage = value

    async def async_set_state_after_power_outage(
        self, value: "PowerSwitchConfigurationService.StateAfterPowerOutage"
    ):
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
    def warning_suppressed(self, value: bool):
        if self._power_switch_warning_service is not None:
            self._power_switch_warning_service.warning_suppressed = value

    async def async_set_warning_suppressed(self, value: bool):
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
    from .services_impl import (
        EnergySavingModeService,
        LedBrightnessConfigurationService,
        PowerSwitchConfigurationService,
        PowerSwitchWarningService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._energy_saving_mode_service = self.device_service("EnergySavingMode")
        self._led_brightness_configuration_service = self.device_service(
            "LedBrightnessConfiguration"
        )
        self._power_switch_configuration_service = self.device_service(
            "PowerSwitchConfiguration"
        )
        self._power_switch_warning_service = self.device_service("PowerSwitchWarning")

    @property
    def energy_saving_mode_enabled(self) -> bool:
        if self._energy_saving_mode_service is None:
            return False
        return self._energy_saving_mode_service.energy_saving_mode_enabled

    @energy_saving_mode_enabled.setter
    def energy_saving_mode_enabled(self, value: bool):
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.energy_saving_mode_enabled = value

    async def async_set_energy_saving_mode_enabled(self, value: bool):
        """Async write: enable/disable energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_energy_saving_mode_enabled(value)

    @property
    def power_threshold(self):
        if self._energy_saving_mode_service is None:
            return None
        return self._energy_saving_mode_service.power_threshold

    @power_threshold.setter
    def power_threshold(self, value):
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.power_threshold = value

    async def async_set_power_threshold(self, value):
        """Async write: set power threshold for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_power_threshold(value)

    @property
    def enter_duration_seconds(self) -> int:
        if self._energy_saving_mode_service is None:
            return 0
        return self._energy_saving_mode_service.enter_duration_seconds

    @enter_duration_seconds.setter
    def enter_duration_seconds(self, value: int):
        if self._energy_saving_mode_service is not None:
            self._energy_saving_mode_service.enter_duration_seconds = value

    async def async_set_enter_duration_seconds(self, value: int):
        """Async write: set enter duration for energy saving mode."""
        if self._energy_saving_mode_service is not None:
            await self._energy_saving_mode_service.async_set_enter_duration_seconds(value)

    @property
    def led_brightness(self):
        if self._led_brightness_configuration_service is None:
            return None
        return self._led_brightness_configuration_service.brightness

    @led_brightness.setter
    def led_brightness(self, value):
        if self._led_brightness_configuration_service is not None:
            self._led_brightness_configuration_service.brightness = value

    async def async_set_led_brightness(self, value):
        """Async write: set LED brightness."""
        if self._led_brightness_configuration_service is not None:
            await self._led_brightness_configuration_service.async_set_brightness(value)

    @property
    def state_after_power_outage(self):
        if self._power_switch_configuration_service is None:
            return None
        return self._power_switch_configuration_service.state_after_power_outage

    @state_after_power_outage.setter
    def state_after_power_outage(
        self, value: "PowerSwitchConfigurationService.StateAfterPowerOutage"
    ):
        if self._power_switch_configuration_service is not None:
            self._power_switch_configuration_service.state_after_power_outage = value

    async def async_set_state_after_power_outage(
        self, value: "PowerSwitchConfigurationService.StateAfterPowerOutage"
    ):
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
    def warning_suppressed(self, value: bool):
        if self._power_switch_warning_service is not None:
            self._power_switch_warning_service.warning_suppressed = value

    async def async_set_warning_suppressed(self, value: bool):
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
    from .services_impl import SwitchConfiguration

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._switch_config_service = self.device_service("SwitchConfiguration")

    @property
    def switch_type(self):
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.switch_type

    @switch_type.setter
    def switch_type(self, value: "SwitchConfiguration.SwitchType"):
        if self._switch_config_service is not None:
            self._switch_config_service.switch_type = value

    async def async_set_switch_type(self, value: "SwitchConfiguration.SwitchType"):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_switchType(value)

    @property
    def swap_inputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_inputs

    @swap_inputs.setter
    def swap_inputs(self, value: bool):
        if self._switch_config_service is not None:
            self._switch_config_service.swap_inputs = value

    async def async_set_swap_inputs(self, value: bool):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapInputs(value)

    @property
    def swap_outputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_outputs

    @swap_outputs.setter
    def swap_outputs(self, value: bool):
        if self._switch_config_service is not None:
            self._switch_config_service.swap_outputs = value

    async def async_set_swap_outputs(self, value: bool):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapOutputs(value)

    @property
    def actuator_type(self):
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.actuator_type

    @actuator_type.setter
    def actuator_type(self, value: "SwitchConfiguration.ActuatorType"):
        if self._switch_config_service is not None:
            self._switch_config_service.actuator_type = value

    async def async_set_actuator_type(self, value: "SwitchConfiguration.ActuatorType"):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_actuatorType(value)

    @property
    def output_mode(self):
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.output_mode

    @output_mode.setter
    def output_mode(self, value: "SwitchConfiguration.OutputMode"):
        if self._switch_config_service is not None:
            self._switch_config_service.output_mode = value

    async def async_set_output_mode(self, value: "SwitchConfiguration.OutputMode"):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_outputMode(value)


class SHCMicromoduleRelay(
    _CommunicationQuality, _ChildProtection, _PowerSwitch, _PowerSwitchProgram
):
    from .services_impl import (
        ImpulseSwitchService,
        SwitchConfiguration,
    )

    class RelayType(Enum):
        BUTTON = "BUTTON"
        SWITCH = "SWITCH"

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)

        self._impulseswitch_service = self.device_service("ImpulseSwitch")
        self._switch_config_service = self.device_service("SwitchConfiguration")

    @property
    def relay_type(self) -> RelayType:
        return (
            self.RelayType.BUTTON
            if self._impulseswitch_service is not None
            else self.RelayType.SWITCH
        )

    def trigger_impulse_state(self):
        if self._impulseswitch_service:
            self._impulseswitch_service.put_state_element("impulseState", True)

    async def async_trigger_impulse_state(self):
        """Async write: trigger impulse relay."""
        if self._impulseswitch_service:
            await self._impulseswitch_service.async_put_state_element("impulseState", True)

    @property
    def impulse_length(self) -> int:
        if self._impulseswitch_service is None:
            return None
        return self._impulseswitch_service.impulse_length

    @impulse_length.setter
    def impulse_length(self, impulse_length: int):
        if self._impulseswitch_service is None:
            return
        self._impulseswitch_service.put_state_element("impulseLength", impulse_length)

    async def async_set_impulse_length(self, impulse_length: int):
        """Async write: set impulse length (tenths of seconds)."""
        if self._impulseswitch_service is not None:
            await self._impulseswitch_service.async_put_state_element(
                "impulseLength", impulse_length
            )

    @property
    def instant_of_last_impulse(self) -> str:
        if self._impulseswitch_service:
            return self._impulseswitch_service.instant_of_last_impulse

    @property
    def switch_type(self):
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.switch_type

    @switch_type.setter
    def switch_type(self, value: "SwitchConfiguration.SwitchType"):
        if self._switch_config_service is not None:
            self._switch_config_service.switch_type = value

    async def async_set_switch_type(self, value: "SwitchConfiguration.SwitchType"):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_switchType(value)

    @property
    def swap_inputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_inputs

    @swap_inputs.setter
    def swap_inputs(self, value: bool):
        if self._switch_config_service is not None:
            self._switch_config_service.swap_inputs = value

    async def async_set_swap_inputs(self, value: bool):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapInputs(value)

    @property
    def swap_outputs(self) -> bool:
        if self._switch_config_service is None:
            return False
        return self._switch_config_service.swap_outputs

    @swap_outputs.setter
    def swap_outputs(self, value: bool):
        if self._switch_config_service is not None:
            self._switch_config_service.swap_outputs = value

    async def async_set_swap_outputs(self, value: bool):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_swapOutputs(value)

    @property
    def actuator_type(self):
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.actuator_type

    @actuator_type.setter
    def actuator_type(self, value: "SwitchConfiguration.ActuatorType"):
        if self._switch_config_service is not None:
            self._switch_config_service.actuator_type = value

    async def async_set_actuator_type(self, value: "SwitchConfiguration.ActuatorType"):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_actuatorType(value)

    @property
    def output_mode(self):
        if self._switch_config_service is None:
            return None
        return self._switch_config_service.output_mode

    @output_mode.setter
    def output_mode(self, value: "SwitchConfiguration.OutputMode"):
        if self._switch_config_service is not None:
            self._switch_config_service.output_mode = value

    async def async_set_output_mode(self, value: "SwitchConfiguration.OutputMode"):
        if self._switch_config_service is not None:
            await self._switch_config_service.async_set_outputMode(value)

    @property
    def supports_switch_configuration(self) -> bool:
        return self._switch_config_service is not None


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

    async def async_set_level(self, level):
        """Async write: set cover position level (0.0 closed .. 1.0 open)."""
        await self._service.async_put_state_element("level", level)

    def stop(self):
        self._service.put_state_element("operationState", "STOPPED")

    async def async_stop(self):
        """Async write: stop the shutter/cover."""
        await self._service.async_put_state_element("operationState", "STOPPED")

    @property
    def operation_state(self) -> ShutterControlService.State:
        return self._service.operation_state


class SHCMicromoduleShutterControl(
    SHCShutterControl, _CommunicationQuality, _ChildProtection, _PowerMeter
):
    from .services_impl import KeypadService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._keypad_service = self.device_service("Keypad")

    @property
    def keystates(self) -> dict[str]:
        return ["UNDEFINED_BUTTON"]

    @property
    def eventtypes(self) -> dict[str]:
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
    def keyname(self) -> KeypadService.KeyState:
        return self._keypad_service.keyName if self._keypad_service is not None else None

    @property
    def eventtype(self) -> KeypadService.KeyEvent:
        return (
            self._keypad_service.eventType
            if self._keypad_service is not None
            else None
        )

    @eventtype.setter
    def eventtype(self, value: KeypadService.KeyEvent):
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

    async def async_set_target_angle(self, value: float):
        """Async write: set blind slat angle (0.0..1.0)."""
        await self._blindscontrol_service.async_put_state_element("targetAngle", value)

    @property
    def blinds_level(self) -> float:
        return self._blindsscenecontrol_service.level

    @blinds_level.setter
    def blinds_level(self, level: float):
        self._blindsscenecontrol_service.level = level

    async def async_set_blinds_level(self, level: float):
        """Async write: set blinds position (0.0 closed .. 1.0 open).

        BlindsSceneControl requires both level + angle in the PUT body.
        """
        await self._blindsscenecontrol_service.async_put_state(
            {"level": level, "angle": self._blindsscenecontrol_service.angle}
        )

    @property
    def blinds_type(self) -> BlindsControlService.BlindsType:
        return self._blindscontrol_service.blinds_type

    def stop_blinds(self):
        # Spec-correct STOP: PUT ShutterControl/state operationState=STOPPED
        # (the old /shading/shutters/{id}/stop endpoint is not in the API).
        self._service.put_state_element("operationState", "STOPPED")

    async def async_stop_blinds(self):
        """Async write: stop the blinds (same endpoint as async_stop on parent)."""
        await self._service.async_put_state_element("operationState", "STOPPED")


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

    async def async_set_bypass(self, state: bool):
        """Async write: set bypass on Bypass service."""
        await self._bypass_service.async_put_state_element(
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

    async def async_set_vibration_enabled(self, state: bool):
        """Async write: enable/disable vibration sensor."""
        await self._vibrationsensor_service.async_put_state_element("enabled", state)

    @property
    def sensitivity(self) -> VibrationSensorService.SensitivityState:
        return self._vibrationsensor_service.sensitivity

    @sensitivity.setter
    def sensitivity(self, state: VibrationSensorService.SensitivityState):
        self._vibrationsensor_service.put_state_element("sensitivity", state.name)

    async def async_set_sensitivity(self, state: VibrationSensorService.SensitivityState):
        """Async write: set vibration sensitivity."""
        await self._vibrationsensor_service.async_put_state_element(
            "sensitivity", state.name
        )


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

    async def async_set_privacymode(self, state: bool):
        """Async write: set privacy mode (True = camera on/DISABLED, False = ENABLED)."""
        await self._privacymode_service.async_put_state_element(
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

    async def async_set_cameranotification(self, state: bool):
        """Async write: enable/disable camera notification."""
        if self._cameranotification_service:
            await self._cameranotification_service.async_put_state_element(
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

    async def async_set_cameralight(self, state: bool):
        """Async write: turn camera light on/off."""
        if self._cameralight_service:
            await self._cameralight_service.async_put_state_element(
                "value", "ON" if state else "OFF"
            )


class SHCCameraOutdoorGen2(SHCCamera360):
    from .services_impl import CameraAmbientLightService, CameraFrontLightService

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._cameraambientlight_service = self.device_service("CameraAmbientLight")
        self._camerafrontlight_service = self.device_service("CameraFrontLight")

    @property
    def cameraambientlight(self) -> CameraAmbientLightService.State:
        if self._cameraambientlight_service:
            return self._cameraambientlight_service.value

    @cameraambientlight.setter
    def cameraambientlight(self, state: bool):
        if self._cameraambientlight_service:
            self._cameraambientlight_service.put_state_element(
                "value", "ON" if state else "OFF"
            )

    async def async_set_cameraambientlight(self, state: bool):
        """Async write: turn camera ambient light on/off."""
        if self._cameraambientlight_service:
            await self._cameraambientlight_service.async_put_state_element(
                "value", "ON" if state else "OFF"
            )

    @property
    def camerafrontlight(self) -> CameraFrontLightService.State:
        if self._camerafrontlight_service:
            return self._camerafrontlight_service.value

    @camerafrontlight.setter
    def camerafrontlight(self, state: bool):
        if self._camerafrontlight_service:
            self._camerafrontlight_service.put_state_element(
                "value", "ON" if state else "OFF"
            )

    async def async_set_camerafrontlight(self, state: bool):
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

    async def async_set_setpoint_temperature(self, temperature: float):
        """Async write: set target temperature."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "setpointTemperature", temperature
        )

    @property
    def operation_mode(self) -> RoomClimateControlService.OperationMode:
        return self._roomclimatecontrol_service.operation_mode

    @operation_mode.setter
    def operation_mode(self, mode: RoomClimateControlService.OperationMode):
        self._roomclimatecontrol_service.operation_mode = mode

    async def async_set_operation_mode(self, mode: RoomClimateControlService.OperationMode):
        """Async write: set operation mode (AUTOMATIC/MANUAL)."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "operationMode", mode.value
        )

    @property
    def boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.boost_mode

    @boost_mode.setter
    def boost_mode(self, value: bool):
        self._roomclimatecontrol_service.boost_mode = value

    async def async_set_boost_mode(self, value: bool):
        """Async write: set boost mode."""
        await self._roomclimatecontrol_service.async_put_state_element("boostMode", value)

    @property
    def supports_boost_mode(self) -> bool:
        return self._roomclimatecontrol_service.supports_boost_mode

    @property
    def low(self) -> bool:
        return self._roomclimatecontrol_service.low

    @low.setter
    def low(self, value: bool):
        self._roomclimatecontrol_service.low = value

    async def async_set_low(self, value: bool):
        """Async write: set ECO (low) mode."""
        await self._roomclimatecontrol_service.async_put_state_element("low", value)

    @property
    def summer_mode(self) -> bool:
        return self._roomclimatecontrol_service.summer_mode

    @summer_mode.setter
    def summer_mode(self, value: bool):
        self._roomclimatecontrol_service.summer_mode = value

    async def async_set_summer_mode(self, value: bool):
        """Async write: set summer mode (off-season / HVAC off)."""
        await self._roomclimatecontrol_service.async_put_state_element("summerMode", value)

    @property
    def room_control_mode(self) -> str:
        return self._roomclimatecontrol_service.room_control_mode

    @room_control_mode.setter
    def room_control_mode(self, value: str):
        self._roomclimatecontrol_service.room_control_mode = value

    async def async_set_room_control_mode(self, value: str):
        """Async write: set room control mode (HEATING/COOLING)."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "roomControlMode", value
        )

    @property
    def cooling_mode(self) -> bool:
        return self._roomclimatecontrol_service.cooling_mode

    @cooling_mode.setter
    def cooling_mode(self, value: bool):
        self._roomclimatecontrol_service.cooling_mode = value

    async def async_set_cooling_mode(self, value: bool):
        """Async write: set cooling mode (True=COOLING, False=HEATING)."""
        await self._roomclimatecontrol_service.async_put_state_element(
            "roomControlMode", "COOLING" if value else "HEATING"
        )

    @property
    def supports_cooling(self) -> bool:
        return self._roomclimatecontrol_service.supports_cooling

    @property
    def has_demand(self) -> bool:
        return self._roomclimatecontrol_service.has_demand


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

    async def async_set_setpoint_temperature(self, temperature: float):
        """Async write: set HeatingCircuit setpoint temperature."""
        await self._heating_circuit_service.async_put_state_element(
            "setpointTemperature", temperature
        )

    @property
    def operation_mode(self) -> HeatingCircuitService.OperationMode:
        return self._heating_circuit_service.operation_mode

    @operation_mode.setter
    def operation_mode(self, mode: HeatingCircuitService.OperationMode):
        self._heating_circuit_service.operation_mode = mode

    async def async_set_operation_mode(self, mode: HeatingCircuitService.OperationMode):
        """Async write: set HeatingCircuit operation mode (AUTOMATIC/MANUAL)."""
        await self._heating_circuit_service.async_put_state_element(
            "operationMode", mode.value
        )

    async def async_set_setpoint_temperature_eco(self, temperature: float):
        """Async write: set HeatingCircuit ECO setpoint temperature."""
        await self._heating_circuit_service.async_put_state_element(
            "setpointTemperatureForLevelEco", temperature
        )

    async def async_set_setpoint_temperature_comfort(self, temperature: float):
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
    def heating_type(self):
        return self._heating_circuit_service.heating_type


class SHCWallThermostat(SHCBatteryDevice, _TemperatureLevel, _HumidityLevel, _Thermostat):
    pass


class SHCThermostatGen2(SHCThermostat):
    from .services_impl import (
        DisplayConfiguration,
        DisplayDirection,
        DisplayedTemperatureConfiguration,
        WallThermostatConfiguration,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._display_config_service = self.device_service("DisplayConfiguration")
        self._display_direction_service = self.device_service("DisplayDirection")
        self._displayed_temp_service = self.device_service(
            "DisplayedTemperatureConfiguration"
        )
        self._wall_thermostat_config_service = self.device_service(
            "WallThermostatConfiguration"
        )

    @property
    def display_brightness(self):
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_brightness

    @display_brightness.setter
    def display_brightness(self, value):
        if self._display_config_service is not None:
            self._display_config_service.display_brightness = value

    async def async_set_display_brightness(self, value):
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayBrightness(value)

    @property
    def display_on_time(self):
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_on_time

    @display_on_time.setter
    def display_on_time(self, value):
        if self._display_config_service is not None:
            self._display_config_service.display_on_time = value

    async def async_set_display_on_time(self, value):
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayOnTime(value)

    @property
    def humidity_warning_enabled(self):
        if self._display_config_service is None:
            return None
        return self._display_config_service.humidity_warning_enabled

    @humidity_warning_enabled.setter
    def humidity_warning_enabled(self, value: bool):
        if self._display_config_service is not None:
            self._display_config_service.humidity_warning_enabled = value

    async def async_set_humidity_warning_enabled(self, value: bool):
        if self._display_config_service is not None:
            await self._display_config_service.async_set_humidityWarningEnabled(value)

    @property
    def display_direction(self):
        if self._display_direction_service is None:
            return None
        return self._display_direction_service.direction

    @display_direction.setter
    def display_direction(self, value: "DisplayDirection.Direction"):
        if self._display_direction_service is not None:
            self._display_direction_service.direction = value

    async def async_set_display_direction(self, value: "DisplayDirection.Direction"):
        if self._display_direction_service is not None:
            await self._display_direction_service.async_set_direction(value)

    @property
    def displayed_temperature(self):
        if self._displayed_temp_service is None:
            return None
        return self._displayed_temp_service.displayed_temperature

    @displayed_temperature.setter
    def displayed_temperature(
        self, value: "DisplayedTemperatureConfiguration.DisplayedTemperature"
    ):
        if self._displayed_temp_service is not None:
            self._displayed_temp_service.displayed_temperature = value

    async def async_set_displayed_temperature(
        self, value: "DisplayedTemperatureConfiguration.DisplayedTemperature"
    ):
        if self._displayed_temp_service is not None:
            await self._displayed_temp_service.async_set_displayedTemperature(value)

    @property
    def valve_type(self):
        if self._wall_thermostat_config_service is None:
            return None
        return self._wall_thermostat_config_service.valve_type

    @valve_type.setter
    def valve_type(self, value: "WallThermostatConfiguration.ValveType"):
        if self._wall_thermostat_config_service is not None:
            self._wall_thermostat_config_service.valve_type = value

    async def async_set_valve_type(
        self, value: "WallThermostatConfiguration.ValveType"
    ):
        if self._wall_thermostat_config_service is not None:
            await self._wall_thermostat_config_service.async_set_valveType(value)

    @property
    def heater_type(self):
        if self._wall_thermostat_config_service is None:
            return None
        return self._wall_thermostat_config_service.heater_type

    @heater_type.setter
    def heater_type(self, value: "WallThermostatConfiguration.HeaterType"):
        if self._wall_thermostat_config_service is not None:
            self._wall_thermostat_config_service.heater_type = value

    async def async_set_heater_type(
        self, value: "WallThermostatConfiguration.HeaterType"
    ):
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
    from .services_impl import (
        DisplayConfiguration,
        DisplayDirection,
        DisplayedTemperatureConfiguration,
        TerminalConfiguration,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._display_config_service = self.device_service("DisplayConfiguration")
        self._display_direction_service = self.device_service("DisplayDirection")
        self._displayed_temp_service = self.device_service(
            "DisplayedTemperatureConfiguration"
        )
        self._terminal_config_service = self.device_service("TerminalConfiguration")

    @property
    def display_brightness(self):
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_brightness

    @display_brightness.setter
    def display_brightness(self, value):
        if self._display_config_service is not None:
            self._display_config_service.display_brightness = value

    async def async_set_display_brightness(self, value):
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayBrightness(value)

    @property
    def display_on_time(self):
        if self._display_config_service is None:
            return None
        return self._display_config_service.display_on_time

    @display_on_time.setter
    def display_on_time(self, value):
        if self._display_config_service is not None:
            self._display_config_service.display_on_time = value

    async def async_set_display_on_time(self, value):
        if self._display_config_service is not None:
            await self._display_config_service.async_set_displayOnTime(value)

    @property
    def humidity_warning_enabled(self):
        if self._display_config_service is None:
            return None
        return self._display_config_service.humidity_warning_enabled

    @humidity_warning_enabled.setter
    def humidity_warning_enabled(self, value: bool):
        if self._display_config_service is not None:
            self._display_config_service.humidity_warning_enabled = value

    async def async_set_humidity_warning_enabled(self, value: bool):
        if self._display_config_service is not None:
            await self._display_config_service.async_set_humidityWarningEnabled(value)

    @property
    def display_direction(self):
        if self._display_direction_service is None:
            return None
        return self._display_direction_service.direction

    @display_direction.setter
    def display_direction(self, value: "DisplayDirection.Direction"):
        if self._display_direction_service is not None:
            self._display_direction_service.direction = value

    async def async_set_display_direction(self, value: "DisplayDirection.Direction"):
        if self._display_direction_service is not None:
            await self._display_direction_service.async_set_direction(value)

    @property
    def displayed_temperature(self):
        if self._displayed_temp_service is None:
            return None
        return self._displayed_temp_service.displayed_temperature

    @displayed_temperature.setter
    def displayed_temperature(
        self, value: "DisplayedTemperatureConfiguration.DisplayedTemperature"
    ):
        if self._displayed_temp_service is not None:
            self._displayed_temp_service.displayed_temperature = value

    async def async_set_displayed_temperature(
        self, value: "DisplayedTemperatureConfiguration.DisplayedTemperature"
    ):
        if self._displayed_temp_service is not None:
            await self._displayed_temp_service.async_set_displayedTemperature(value)

    @property
    def terminal_type(self):
        if self._terminal_config_service is None:
            return None
        return self._terminal_config_service.type

    @terminal_type.setter
    def terminal_type(self, value: "TerminalConfiguration.Type"):
        if self._terminal_config_service is not None:
            self._terminal_config_service.type = value

    async def async_set_terminal_type(self, value: "TerminalConfiguration.Type"):
        if self._terminal_config_service is not None:
            await self._terminal_config_service.async_set_type(value)

    @property
    def terminal_temperature(self):
        if self._terminal_config_service is None:
            return None
        return self._terminal_config_service.temperature

    @property
    def supported_terminal_types(self) -> list:
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


class SHCMotionDetector2(SHCBatteryDevice):
    from .services_impl import (
        LatestMotionService,
        MultiLevelSensorService,
        MultiLevelSwitchService,
        BinarySwitchService,
        DetectionTestService,
        LatestTamperService,
        TemperatureLevelService,
        PollControlService,
        PirSensorConfigurationService,
        OccupancyDetectionService,
        CommunicationQualityService,
        PetImmunityService,
        WalkTestService,
        SmartSensitivityControlService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._multi_level_switch_service = self.device_service("MultiLevelSwitch")
        self._binaryswitch_service = self.device_service("BinarySwitch")
        self._detectiontest_service = self.device_service("DetectionTest")
        self._latestmotion_service = self.device_service("LatestMotion")
        self._multi_level_sensor_service = self.device_service("MultiLevelSensor")
        self._latesttamper_service = self.device_service("LatestTamper")
        self._temperaturelevel_service = self.device_service("TemperatureLevel")
        self._pollcontrol_service = self.device_service("PollControl")
        self._pirsensorconfiguration_service = self.device_service("PirSensorConfiguration")
        self._occupancydetection_service = self.device_service("OccupancyDetection")
        self._communicationquality_service = self.device_service("CommunicationQuality")
        self._petimmunity_service = self.device_service("PetImmunity")
        self._walktest_service = self.device_service("WalkTest")
        self._smart_sensitivity_control_service = self.device_service("SmartSensitivityControl")

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
    def multi_level_switch(self, value: int):
        self._multi_level_switch_service.put_state_element("level", value)

    async def async_set_multi_level_switch(self, value: int):
        """Async write: set indicator light brightness level (0-100)."""
        await self._multi_level_switch_service.async_put_state_element("level", value)

    @property
    def binaryswitch(self) -> bool:
        return self._binaryswitch_service.value

    @binaryswitch.setter
    def binaryswitch(self, value: bool):
        self._binaryswitch_service.put_state_element("on", bool(value))

    async def async_set_binaryswitch(self, value: bool):
        """Async write: turn indicator light on/off via BinarySwitch service."""
        await self._binaryswitch_service.async_put_state_element("on", bool(value))

    @property
    def detection_state(self) -> DetectionTestService.DetectionState:
        return self._detectiontest_service.detection_state

    @property
    def temperature(self) -> float:
        return self._temperaturelevel_service.temperature

    @property
    def long_poll_interval(self) -> PollControlService.PollControlState:
        return self._pollcontrol_service.longPollInterval

    @property
    def motion_sensitivity(self) -> PirSensorConfigurationService.MotionSensitivity:
        return self._pirsensorconfiguration_service.motionSensitivity

    @motion_sensitivity.setter
    def motion_sensitivity(
        self, value: PirSensorConfigurationService.MotionSensitivity
    ):
        self._pirsensorconfiguration_service.put_state_element(
            "motionSensitivity", value.name
        )

    async def async_set_motion_sensitivity(
        self, value: PirSensorConfigurationService.MotionSensitivity
    ):
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
    def pet_immunity_enabled(self, value: bool):
        self._petimmunity_service.enabled = value

    async def async_set_pet_immunity_enabled(self, value: bool):
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

    @property
    def walk_state(self):
        if self._walktest_service is None:
            return None
        return self._walktest_service.walk_state

    @property
    def walk_state_request(self):
        if self._walktest_service is None:
            return None
        return self._walktest_service.walk_state_request

    @walk_state_request.setter
    def walk_state_request(self, value: "WalkTestService.WalkStateRequest"):
        if self._walktest_service is not None:
            self._walktest_service.walk_state_request = value

    @property
    def pet_immunity_walk_state(self):
        if self._walktest_service is None:
            return None
        return self._walktest_service.pet_immunity_state

    def set_walk_state_request(self, value: "WalkTestService.WalkStateRequest"):
        """Sync write: start or stop the walk test."""
        if self._walktest_service is not None:
            self._walktest_service.set_walk_state_request(value)

    async def async_set_walk_state_request(
        self, value: "WalkTestService.WalkStateRequest"
    ):
        """Async write: start or stop the walk test."""
        if self._walktest_service is not None:
            await self._walktest_service.async_set_walk_state_request(value)

    @property
    def smart_sensitivity_enabled(self) -> bool:
        if self._smart_sensitivity_control_service is None:
            return False
        return self._smart_sensitivity_control_service.enabled

    @smart_sensitivity_enabled.setter
    def smart_sensitivity_enabled(self, value: bool):
        if self._smart_sensitivity_control_service is not None:
            self._smart_sensitivity_control_service.enabled = value

    async def async_set_smart_sensitivity_enabled(self, value: bool):
        """Async write: enable/disable smart sensitivity control."""
        if self._smart_sensitivity_control_service is not None:
            await self._smart_sensitivity_control_service.async_set_enabled(value)

    def get_smart_sensitivity(self, context):
        """Return the sensitivity dict for the given context."""
        if self._smart_sensitivity_control_service is None:
            return None
        return self._smart_sensitivity_control_service.get_sensitivity(context)

    def set_smart_sensitivity_manual_level(
        self,
        context: "SmartSensitivityControlService.SmartSensitivityContext",
        level: "SmartSensitivityControlService.MotionSensitivity",
    ):
        """Sync write: set manual sensitivity level for a context."""
        if self._smart_sensitivity_control_service is not None:
            self._smart_sensitivity_control_service.set_manual_level(context, level)

    async def async_set_smart_sensitivity_manual_level(
        self,
        context: "SmartSensitivityControlService.SmartSensitivityContext",
        level: "SmartSensitivityControlService.MotionSensitivity",
    ):
        """Async write: set manual sensitivity level for a context."""
        if self._smart_sensitivity_control_service is not None:
            await self._smart_sensitivity_control_service.async_set_manual_level(
                context, level
            )

    @property
    def supports_walk_test(self) -> bool:
        return self._walktest_service is not None

    @property
    def supports_smart_sensitivity(self) -> bool:
        return self._smart_sensitivity_control_service is not None


class SHCTwinguard(SHCBatteryDevice):
    from .services_impl import (
        AirQualityLevelService,
        SmokeSensitivityService,
        SmokeDetectorCheckService,
        TwinguardNightlyPromiseService,
    )

    def __init__(self, api, raw_device, raw_device_services):
        super().__init__(api, raw_device, raw_device_services)
        self._airqualitylevel_service = self.device_service("AirQualityLevel")
        self._smokedetectorcheck_service = self.device_service("SmokeDetectorCheck")
        self._smoke_sensitivity_service = self.device_service("SmokeSensitivity")
        self._twinguard_nightly_promise_service = self.device_service(
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

    def smoketest_requested(self):
        self._smokedetectorcheck_service.put_state_element(
            "value", "SMOKE_TEST_REQUESTED"
        )

    @property
    def smoke_sensitivity(self):
        if self._smoke_sensitivity_service is None:
            return None
        return self._smoke_sensitivity_service.smoke_sensitivity

    @smoke_sensitivity.setter
    def smoke_sensitivity(self, value: "SmokeSensitivityService.SmokeSensitivityLevel"):
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.smoke_sensitivity = value

    async def async_set_smoke_sensitivity(
        self, value: "SmokeSensitivityService.SmokeSensitivityLevel"
    ):
        """Async write: set smoke sensitivity level."""
        if self._smoke_sensitivity_service is not None:
            await self._smoke_sensitivity_service.async_set_smoke_sensitivity(value)

    @property
    def pre_alarm_enabled(self) -> bool:
        if self._smoke_sensitivity_service is None:
            return False
        return self._smoke_sensitivity_service.pre_alarm_enabled

    @pre_alarm_enabled.setter
    def pre_alarm_enabled(self, value: bool):
        if self._smoke_sensitivity_service is not None:
            self._smoke_sensitivity_service.pre_alarm_enabled = value

    async def async_set_pre_alarm_enabled(self, value: bool):
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
    def nightly_promise_enabled(self, value: bool):
        if self._twinguard_nightly_promise_service is not None:
            self._twinguard_nightly_promise_service.nightly_promise_enabled = value

    async def async_set_nightly_promise_enabled(self, value: bool):
        """Async write: enable/disable nightly promise self-check."""
        if self._twinguard_nightly_promise_service is not None:
            await self._twinguard_nightly_promise_service.async_set_nightly_promise_enabled(
                value
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

    async def async_set_enabled(self, value: bool):
        """Async write: enable/disable presence simulation."""
        await self._presencesimulationconfiguration_service.async_put_state_element(
            "enabled", value
        )


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

    async def async_set_binarystate(self, state: bool):
        """Async write: turn light on/off via BinarySwitch service."""
        await self._binaryswitch_service.async_put_state_element(
            "on", True if state else False
        )

    @property
    def brightness(self) -> int:
        if self.supports_brightness:
            return self._multilevelswitch_service.value
        return 0

    @brightness.setter
    def brightness(self, state: int):
        if self.supports_brightness:
            self._multilevelswitch_service.put_state_element("level", state)

    async def async_set_brightness(self, state: int):
        """Async write: set brightness level (0-100) via MultiLevelSwitch service."""
        if self.supports_brightness:
            await self._multilevelswitch_service.async_put_state_element("level", state)

    @property
    def color(self) -> int:
        if self.supports_color_temp:
            return self._huecolortemperature_service.value
        return 0

    @color.setter
    def color(self, state: int):
        if self.supports_color_temp:
            self._huecolortemperature_service.put_state_element(
                "colorTemperature", state
            )

    async def async_set_color(self, state: int):
        """Async write: set color temperature (mireds) via HueColorTemperature service."""
        if self.supports_color_temp:
            await self._huecolortemperature_service.async_put_state_element(
                "colorTemperature", state
            )

    @property
    def rgb(self) -> int:
        if self.supports_color_hsb:
            return self._hsbcoloractuator_service.value
        return 0

    @rgb.setter
    def rgb(self, state: int):
        if self.supports_color_hsb:
            self._hsbcoloractuator_service.put_state_element("rgb", state)

    async def async_set_rgb(self, state: int):
        """Async write: set RGB color via HSBColorActuator service."""
        if self.supports_color_hsb:
            await self._hsbcoloractuator_service.async_put_state_element("rgb", state)

    @property
    def min_color_temperature(self) -> int:
        if self.supports_color_temp:
            return self._huecolortemperature_service.min_value
        if self.supports_color_hsb:
            return self._hsbcoloractuator_service.min_value
        return 0

    @property
    def max_color_temperature(self) -> int:
        if self.supports_color_temp:
            return self._huecolortemperature_service.max_value
        if self.supports_color_hsb:
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

    async def async_set_binarystate(self, state: bool):
        """Async write: turn dimmer on/off via PowerSwitch service (overrides SHCLight)."""
        if self._powerswitch_service:
            await self._powerswitch_service.async_put_state_element(
                "switchState", "ON" if state else "OFF"
            )


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
}

SUPPORTED_MODELS = MODEL_MAPPING.keys()


def build(api, raw_device, raw_device_services) -> SHCDevice:
    device_model = raw_device["deviceModel"]
    assert device_model in SUPPORTED_MODELS, "Device model is supported"
    return MODEL_MAPPING[device_model](
        api=api, raw_device=raw_device, raw_device_services=raw_device_services
    )
