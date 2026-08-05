"""Unit tests for boschshcpy.automation.SHCAutomationRule and the
automation-rule API methods on SHCAPI/SHCAPIAsync.

Bosch's own local automation-rule engine (system/automation, no OpenAPI
spec) -- traced via APK decompile and confirmed live against a real SHC.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from boschshcpy.automation import SHCAutomationRule
from boschshcpy.exceptions import SHCException


def _raw_rule(rule_id="rule-1", name="TV aus", enabled=True, **kw):
    base = {
        "@type": "automationRule",
        "id": rule_id,
        "name": name,
        "enabled": enabled,
        "automationTriggers": [{"type": "KeypadButtonPressTrigger", "configuration": "{}"}],
        "automationConditions": [],
        "automationActions": [
            {"type": "SmartPlugOnOffAction", "delayInSeconds": 0, "configuration": "{}"}
        ],
        "conditionLogicalOp": "AND",
    }
    base.update(kw)
    return base


def _make_rule(raw=None, api=None):
    rule = SHCAutomationRule.__new__(SHCAutomationRule)
    rule._api = api if api is not None else MagicMock()
    rule._raw_rule = raw if raw is not None else _raw_rule()
    return rule


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Basic properties
# ---------------------------------------------------------------------------


def test_id_name_enabled():
    rule = _make_rule()
    assert rule.id == "rule-1"
    assert rule.name == "TV aus"
    assert rule.enabled is True


def test_name_defaults_to_empty_string():
    rule = _make_rule(_raw_rule(name=None))
    # a raw dict with name=None should not crash -- but real payloads always
    # carry a name; guard against a missing key instead
    raw = _raw_rule()
    del raw["name"]
    rule = _make_rule(raw)
    assert rule.name == ""


def test_enabled_defaults_to_false_when_missing():
    raw = _raw_rule()
    del raw["enabled"]
    rule = _make_rule(raw)
    assert rule.enabled is False


def test_trigger_condition_action_counts():
    rule = _make_rule(
        _raw_rule(
            automationTriggers=[{"type": "A"}, {"type": "B"}],
            automationConditions=[{"type": "C"}],
            automationActions=[],
        )
    )
    assert rule.trigger_count == 2
    assert rule.condition_count == 1
    assert rule.action_count == 0


def test_counts_are_safe_when_lists_missing():
    raw = _raw_rule()
    del raw["automationTriggers"]
    del raw["automationConditions"]
    del raw["automationActions"]
    rule = _make_rule(raw)
    assert rule.trigger_count == 0
    assert rule.condition_count == 0
    assert rule.action_count == 0


# ---------------------------------------------------------------------------
# update_raw_rule
# ---------------------------------------------------------------------------


def test_update_raw_rule_applies_new_data():
    rule = _make_rule()
    rule.update_raw_rule(_raw_rule(enabled=False))
    assert rule.enabled is False


def test_update_raw_rule_raises_on_id_mismatch():
    rule = _make_rule()
    with pytest.raises(SHCException):
        rule.update_raw_rule(_raw_rule(rule_id="rule-2"))


# ---------------------------------------------------------------------------
# set_enabled (sync + async)
# ---------------------------------------------------------------------------


def test_set_enabled_sends_full_body_and_applies_response():
    api = MagicMock()
    api.put_automation_rule.return_value = _raw_rule(enabled=False)
    rule = _make_rule(api=api)

    rule.set_enabled(False)

    sent_body = api.put_automation_rule.call_args[0][1]
    assert sent_body["enabled"] is False
    assert sent_body["id"] == "rule-1"
    assert rule.enabled is False


def test_set_enabled_falls_back_to_request_body_on_empty_response():
    api = MagicMock()
    api.put_automation_rule.return_value = None
    rule = _make_rule(api=api)

    rule.set_enabled(False)

    assert rule.enabled is False


def test_async_set_enabled_awaits_api():
    from unittest.mock import AsyncMock

    api = MagicMock()
    api.put_automation_rule = AsyncMock(return_value=_raw_rule(enabled=False))
    rule = _make_rule(api=api)

    _run(rule.async_set_enabled(False))

    api.put_automation_rule.assert_awaited_once()
    assert rule.enabled is False


# ---------------------------------------------------------------------------
# refresh (sync + async)
# ---------------------------------------------------------------------------


def test_refresh_applies_latest_state():
    api = MagicMock()
    api.get_automation_rule.return_value = _raw_rule(enabled=False)
    rule = _make_rule(api=api)
    rule.refresh()
    api.get_automation_rule.assert_called_once_with("rule-1")
    assert rule.enabled is False


def test_async_refresh_awaits_api():
    from unittest.mock import AsyncMock

    api = MagicMock()
    api.get_automation_rule = AsyncMock(return_value=_raw_rule(enabled=False))
    rule = _make_rule(api=api)
    _run(rule.async_refresh())
    api.get_automation_rule.assert_awaited_once_with("rule-1")
    assert rule.enabled is False


# ---------------------------------------------------------------------------
# trigger (sync + async)
# ---------------------------------------------------------------------------


def test_trigger_calls_api_with_id():
    api = MagicMock()
    rule = _make_rule(api=api)
    rule.trigger()
    api.trigger_automation_rule.assert_called_once_with("rule-1")


def test_async_trigger_awaits_api():
    from unittest.mock import AsyncMock

    api = MagicMock()
    api.trigger_automation_rule = AsyncMock()
    rule = _make_rule(api=api)
    _run(rule.async_trigger())
    api.trigger_automation_rule.assert_awaited_once_with("rule-1")


# ---------------------------------------------------------------------------
# delete (sync + async)
# ---------------------------------------------------------------------------


def test_delete_calls_api_with_id():
    api = MagicMock()
    rule = _make_rule(api=api)
    rule.delete()
    api.delete_automation_rule.assert_called_once_with("rule-1")


def test_async_delete_awaits_api():
    from unittest.mock import AsyncMock

    api = MagicMock()
    api.delete_automation_rule = AsyncMock()
    rule = _make_rule(api=api)
    _run(rule.async_delete())
    api.delete_automation_rule.assert_awaited_once_with("rule-1")


def test_summary_prints_key_fields(capsys):
    _make_rule().summary()
    out = capsys.readouterr().out
    assert "rule-1" in out
    assert "TV aus" in out
