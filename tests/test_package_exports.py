"""Regression coverage for boschshcpy/__init__.py's top-level exports.

Catches the class-of-bug hit twice this round (SHCWaterAlarmSystem in 0.5.0,
SHCBoiler in 0.6.0): a new device/domain class added to models_impl.py or
domain_impl.py but never added to __init__.py's imports/__all__ — the class
still works fine via normal session enumeration, so nothing else catches it.
"""

import boschshcpy


def test_shc_boiler_exported():
    assert hasattr(boschshcpy, "SHCBoiler")
    assert "SHCBoiler" in boschshcpy.__all__


def test_shc_water_alarm_system_exported():
    assert hasattr(boschshcpy, "SHCWaterAlarmSystem")
    assert "SHCWaterAlarmSystem" in boschshcpy.__all__


def test_shc_automation_rule_exported():
    assert hasattr(boschshcpy, "SHCAutomationRule")
    assert "SHCAutomationRule" in boschshcpy.__all__


def test_all_names_are_actually_importable():
    """Every name in __all__ must resolve to a real attribute (catches typos)."""
    for name in boschshcpy.__all__:
        assert hasattr(boschshcpy, name), f"{name} listed in __all__ but not importable"
