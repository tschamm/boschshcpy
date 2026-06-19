"""Tests for SHCEmma.value / localizedSubtitles bugs.

REGRESSION: commit 42dec84 introduced two bugs in emma.py:
  1. `localizedSubTitles` (capital T) key lookup crashes with KeyError on
     every real reading because the Bosch API sends `localizedSubtitles`
     (lowercase t).  The KeyError propagates through `value` because the
     except clause only catches ValueError.
  2. A dead `else: return None` after the except clause (unreachable, since
     `return` inside `try` exits before `else` runs), but reflects the
     original mis-belief that the property always returns None.
"""

from unittest.mock import MagicMock
from boschshcpy.emma import SHCEmma


def _make_emma(localized_information="500 W", localized_subtitles="Local Consumption"):
    """Build a minimal SHCEmma with the keys the Bosch API actually sends."""
    shc_info = MagicMock()
    shc_info.macAddress = "AA:BB:CC:DD:EE:FF"
    raw_result = {
        "version": "1.0",
        "localizedTitles": {"en": "Current Power"},
        "localizedSubtitles": {"en": localized_subtitles},  # lowercase t
        "localizedInformation": {"en": localized_information},
    }
    return SHCEmma(api=None, shc_info=shc_info, raw_result=raw_result)


# ---------- regression tests (were failing before the fix) ----------

def test_value_returns_positive_watts_for_local_consumption():
    """REGRESSION: value must return 500 (not None, not KeyError) for normal local reading."""
    emma = _make_emma("500 W", "Local Consumption")
    assert emma.value == 500.0


def test_value_returns_negative_watts_for_grid_supply():
    """REGRESSION: Grid Supply direction must flip the sign."""
    emma = _make_emma("200 W", "Grid Supply")
    assert emma.value == -200.0


def test_value_returns_none_for_unparseable_info():
    """Malformed localizedInformation (no integer) must yield None without raising."""
    emma = _make_emma("N/A W", "Local Consumption")
    assert emma.value is None


def test_localized_subtitles_property():
    """REGRESSION: localizedSubtitles must not raise KeyError (typo was SubTitles)."""
    emma = _make_emma("100 W", "Grid Feed-In")
    assert emma.localizedSubtitles == "Grid Feed-In"


# ---------- non-regression sanity checks ----------

def test_zero_watts():
    emma = _make_emma("0 W", "Local Consumption")
    assert emma.value == 0.0


def test_large_value():
    emma = _make_emma("11000 W", "Local Consumption")
    assert emma.value == 11000.0
