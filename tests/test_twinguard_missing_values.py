"""An empty Twinguard battery can leave AirQualityLevel values absent (core#186016)."""

from unittest.mock import MagicMock

from boschshcpy.services_impl import AirQualityLevelService


def _make_svc(cls, state_dict):
    svc = cls.__new__(cls)
    raw = {
        "id": cls.__name__,
        "deviceId": "test-device",
        "path": "/test",
        "state": {"@type": "testType", **state_dict},
    }
    svc._api = MagicMock()
    svc._raw_device_service = raw
    svc._raw_state = raw["state"]
    svc._last_update = None
    svc._callbacks = {}
    svc._event_callbacks = {}
    return svc


def test_air_quality_values_present():
    svc = _make_svc(AirQualityLevelService, {"temperature": 21.7, "purity": 812.7})
    assert svc.temperature == 21.7
    assert svc.purity == 812


def test_air_quality_temperature_and_purity_absent_return_none():
    svc = _make_svc(AirQualityLevelService, {"humidity": 55.5})
    assert svc.temperature is None
    assert svc.purity is None
    assert svc.humidity == 55.5


def test_air_quality_humidity_absent_or_null_returns_none():
    assert _make_svc(AirQualityLevelService, {}).humidity is None
    assert _make_svc(AirQualityLevelService, {"humidity": None}).humidity is None


def test_air_quality_ratings_absent_stay_unknown():
    svc = _make_svc(AirQualityLevelService, {})
    unknown = AirQualityLevelService.RatingState.UNKNOWN
    assert svc.combinedRating == unknown
    assert svc.purityRating == unknown
    assert svc.temperatureRating == unknown


def test_air_quality_temperature_and_purity_null_return_none():
    svc = _make_svc(AirQualityLevelService, {"temperature": None, "purity": None})
    assert svc.temperature is None
    assert svc.purity is None
