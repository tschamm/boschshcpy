"""An empty Twinguard battery can leave AirQualityLevel values absent (core#186016)."""

from boschshcpy.services_impl import AirQualityLevelService

from tests.test_services_impl import _make_svc


def test_air_quality_values_present():
    svc = _make_svc(AirQualityLevelService, {"temperature": 21.7, "purity": 812.7})
    assert svc.temperature == 21.7
    assert svc.purity == 812


def test_air_quality_temperature_and_purity_absent_return_none():
    svc = _make_svc(AirQualityLevelService, {"humidity": 55.5})
    assert svc.temperature is None
    assert svc.purity is None


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
