"""Contract tests: validate our service-state enums against the OFFICIAL Bosch SHC
OpenAPI specs (github.com/BoschSmartHome/bosch-shc-api-docs, checked out alongside
this repo as ../bosch-shc-api-docs).

This is the automated form of "run the official API against our code": if Bosch
documents an enum value our code does not handle, our `self.State(value)` parsing
raises and the consuming entity breaks (the #311 class of bug). This test fails
loudly when that happens.

Skips gracefully when the spec repo is not present (e.g. on CI that only checks
out boschshcpy), so it is a local/dev drift guard.
"""
import glob
import os

import pytest

yaml = pytest.importorskip("yaml")

from boschshcpy.services_impl import (
    AirQualityLevelService,
    BlindsControlService,
    DetectionTestService,
    KeypadService,
    PirSensorConfigurationService,
    PrivacyModeService,
    ShutterContactService,
    ShutterControlService,
    SilentModeService,
    SmokeDetectorCheckService,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
_SPEC_DIR = os.path.normpath(
    os.path.join(_HERE, "..", "..", "bosch-shc-api-docs", "openapi")
)


def _spec_files():
    files = sorted(glob.glob(os.path.join(_SPEC_DIR, "*.yml")))
    if not files:
        pytest.skip("bosch-shc-api-docs not checked out alongside boschshcpy")
    return files


def _collect_enums(node, parent_key, out):
    """Recursively map every `enum:` list to the property name it sits under."""
    if isinstance(node, dict):
        if "enum" in node and isinstance(node["enum"], list) and parent_key:
            out.setdefault(parent_key, set()).update(str(v) for v in node["enum"])
        for key, value in node.items():
            _collect_enums(value, key, out)
    elif isinstance(node, list):
        for item in node:
            _collect_enums(item, parent_key, out)


def _all_spec_enums():
    out: dict[str, set] = {}
    for path in _spec_files():
        try:
            doc = yaml.safe_load(open(path, encoding="utf-8"))
        except Exception:
            continue
        _collect_enums(doc, None, out)
    return out


# Official-spec enum field name -> our enum class. Curated + verified against the
# enum dump of our services_impl/domain_impl.
ENUM_MAP = {
    "operationState": ShutterControlService.State,
    "ShutterContactState": ShutterContactService.State,
    "PrivacyModeState": PrivacyModeService.State,
    "KeypadEventState": KeypadService.KeyEvent,
    "KeypadKeyState": KeypadService.KeyState,
    "RatingState": AirQualityLevelService.RatingState,
    "mode": SilentModeService.State,
    "motionSensitivity": PirSensorConfigurationService.MotionSensitivity,
    "blindsType": BlindsControlService.BlindsType,
    "detectionState": DetectionTestService.DetectionState,
    "SmokeDetectorCheckState": SmokeDetectorCheckService.State,
}

# Spec values our code does NOT model yet. These are real findings from the
# 2026-06-20 API audit; per the never-blind-fix rule they must be confirmed
# against live devices before we add them (a wrong enum value is harmless but a
# guessed semantic is not). Tracked here so the test stays green AND the gap is
# visible; a NEW gap (not in this list) fails the test loudly.
KNOWN_DISCREPANCIES = {
    "motionSensitivity": {"UNKNOWN"},
    "blindsType": {"DEGREE_360"},
    "detectionState": {
        "DETECTION_STATE_START",
        "DETECTION_STATE_STOP",
        "DETECTION_TEST_UNKNOWN",
    },
}


def _our_values(enum_cls):
    return {member.value for member in enum_cls}


@pytest.mark.parametrize("field,enum_cls", list(ENUM_MAP.items()))
def test_our_enum_covers_official_spec(field, enum_cls):
    """Every value the official spec lists for a state we model must be parseable
    by our enum (modulo the documented KNOWN_DISCREPANCIES)."""
    spec_enums = _all_spec_enums()
    spec_values = spec_enums.get(field, set())
    if not spec_values:
        pytest.skip(f"spec field '{field}' not present in the checked-out specs")
    allowed_gap = KNOWN_DISCREPANCIES.get(field, set())
    missing = spec_values - _our_values(enum_cls) - allowed_gap
    assert not missing, (
        f"{enum_cls.__qualname__} does not handle official spec values for "
        f"'{field}': {sorted(missing)} — Bosch added a value we would crash on. "
        f"Confirm against a device, then extend the enum."
    )


def test_known_discrepancies_are_still_missing():
    """Guard the allowlist: if we later add one of these, this reminds us to drop
    it from KNOWN_DISCREPANCIES so the allowlist stays honest."""
    for field, gap in KNOWN_DISCREPANCIES.items():
        enum_cls = ENUM_MAP[field]
        still_missing = gap - _our_values(enum_cls)
        assert still_missing == gap, (
            f"{enum_cls.__qualname__} now handles part of {field}'s allowlisted "
            f"gap {gap - still_missing}; remove it from KNOWN_DISCREPANCIES."
        )


def test_spec_repo_present_and_parsed():
    """Sanity: we actually loaded enums from the official specs."""
    spec_enums = _all_spec_enums()
    assert "operationState" in spec_enums
    assert {"OPENING", "CLOSING", "STOPPED"} <= spec_enums["operationState"]
