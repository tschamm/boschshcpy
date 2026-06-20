"""Tests for models_impl.py — temperature/humidity None-guards.

Isolation: NO HA harness, NO real network.
Run with:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_models_none_guards.py -q \
    -o addopts= -p no:cacheprovider
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from boschshcpy.models_impl import _TemperatureLevel, _HumidityLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raw_device(device_id="dev-1", model="THERMOSTAT"):
    return {
        "id": device_id,
        "rootDeviceId": "root-1",
        "deviceModel": model,
        "name": "Test Device",
        "manufacturer": "Bosch",
        "status": "AVAILABLE",
        "deviceServiceIds": [],
    }


def _raw_temp_service(temp=21.5):
    return {
        "id": "TemperatureLevel",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/TemperatureLevel",
        "state": {
            "@type": "temperatureLevelState",
            "temperature": temp,
        },
    }


def _raw_humidity_service(humidity=55.0):
    return {
        "id": "HumidityLevel",
        "deviceId": "dev-1",
        "path": "/devices/dev-1/services/HumidityLevel",
        "state": {
            "@type": "humidityLevelState",
            "humidity": humidity,
        },
    }


def _make_api():
    return MagicMock(name="SHCAPI")


# ---------------------------------------------------------------------------
# _TemperatureLevel
# ---------------------------------------------------------------------------

class TestTemperatureLevelNoneGuard:
    def test_temperature_returns_value_when_service_present(self):
        """temperature property returns the service value when service exists."""
        api = _make_api()
        device = _TemperatureLevel(api, _raw_device(), [_raw_temp_service(21.5)])
        assert device.temperature == 21.5

    def test_temperature_returns_none_when_service_absent(self):
        """temperature property returns None when TemperatureLevel service is absent."""
        api = _make_api()
        device = _TemperatureLevel(api, _raw_device(), [])
        # No TemperatureLevel service registered → device_service() returns None
        assert device._temperaturelevel_service is None
        assert device.temperature is None


# ---------------------------------------------------------------------------
# _HumidityLevel
# ---------------------------------------------------------------------------

class TestHumidityLevelNoneGuard:
    def test_humidity_returns_value_when_service_present(self):
        """humidity property returns the service value when service exists."""
        api = _make_api()
        device = _HumidityLevel(api, _raw_device(), [_raw_humidity_service(55.0)])
        assert device.humidity == 55.0

    def test_humidity_returns_none_when_service_absent(self):
        """humidity property returns None when HumidityLevel service is absent."""
        api = _make_api()
        device = _HumidityLevel(api, _raw_device(), [])
        assert device._humiditylevel_service is None
        assert device.humidity is None

    def test_supports_humidity_true_when_service_present(self):
        """supports_humidity is True when HumidityLevel service is registered."""
        api = _make_api()
        device = _HumidityLevel(api, _raw_device(), [_raw_humidity_service()])
        assert device.supports_humidity is True

    def test_supports_humidity_false_when_service_absent(self):
        """supports_humidity is False when HumidityLevel service is absent."""
        api = _make_api()
        device = _HumidityLevel(api, _raw_device(), [])
        assert device.supports_humidity is False
