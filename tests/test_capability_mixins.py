"""The public capability mixins.

Typed cross-device access for consumers (e.g. HA sensor descriptions typed
against a capability instead of a union of concrete device classes): every
device exposing a reading must be a subclass of that reading's mixin.
"""

from boschshcpy import (
    CommunicationQualityMixin,
    HumidityLevelMixin,
    PowerMeterMixin,
    SHCLightSwitchBSM,
    SHCSmartPlug,
    SHCSmartPlugCompact,
    SHCThermostat,
    SHCTwinguard,
    SHCWallThermostat,
    TemperatureLevelMixin,
)


def _raw_device(model="TWINGUARD"):
    return {
        "id": "dev-1",
        "rootDeviceId": "root-1",
        "deviceModel": model,
        "name": "Test Device",
        "manufacturer": "Bosch",
        "status": "AVAILABLE",
        "deviceServiceIds": [],
    }


def _raw_airquality_service(temp=21.5, humidity=55.0):
    return {
        "id": "AirQualityLevel",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/AirQualityLevel",
        "state": {
            "@type": "airQualityLevelState",
            "temperature": temp,
            "humidity": humidity,
            "purity": 550,
        },
    }


def test_temperature_capability_covers_every_temperature_device():
    for cls in (SHCThermostat, SHCWallThermostat, SHCTwinguard):
        assert issubclass(cls, TemperatureLevelMixin)


def test_humidity_capability_covers_every_humidity_device():
    for cls in (SHCWallThermostat, SHCTwinguard):
        assert issubclass(cls, HumidityLevelMixin)


def test_power_meter_capability_covers_every_metering_device():
    for cls in (SHCSmartPlug, SHCSmartPlugCompact, SHCLightSwitchBSM):
        assert issubclass(cls, PowerMeterMixin)


def test_communication_quality_capability():
    assert issubclass(SHCSmartPlugCompact, CommunicationQualityMixin)


def test_twinguard_readings_come_from_airquality_service():
    """Twinguard overrides the mixin properties with AirQualityLevel data.

    It carries no TemperatureLevel/HumidityLevel device services, so the
    inherited mixin lookups resolve to None and must never shadow the
    overrides.
    """
    device = SHCTwinguard(
        api=None,
        raw_device=_raw_device(),
        raw_device_services=[_raw_airquality_service(temp=21.5, humidity=55.0)],
    )
    assert device.temperature == 21.5
    assert device.humidity == 55.0
    assert device.supports_humidity is True


def test_private_mixin_aliases_kept():
    from boschshcpy.models_impl import (
        _CommunicationQuality,
        _HumidityLevel,
        _PowerMeter,
        _TemperatureLevel,
    )

    assert _TemperatureLevel is TemperatureLevelMixin
    assert _HumidityLevel is HumidityLevelMixin
    assert _PowerMeter is PowerMeterMixin
    assert _CommunicationQuality is CommunicationQualityMixin
