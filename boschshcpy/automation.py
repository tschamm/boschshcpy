from __future__ import annotations

from typing import Any

from .api import SHCAPI
from .exceptions import SHCException


class SHCAutomationRule:
    """A Bosch Smart Home automation rule.

    Bosch's own native "if this then that" rule engine (arm/disarm state,
    keypad presses, astro time, shutter contacts, user-defined states, ...
    triggering plug/light/climate/camera/notification actions) -- entirely
    separate from Home Assistant's own automations. Not in the official
    OpenAPI spec; traced via APK decompile
    (RestRequests.getAutomationRulesRequest/getAutomationTriggerRequest/
    getAutomationUpdateRequest) and confirmed live against a real SHC with
    23 real user-configured rules.
    """

    def __init__(self, api: SHCAPI, raw_rule: dict[str, Any]) -> None:
        self._api = api
        self._raw_rule = raw_rule

    @property
    def id(self) -> str:
        return str(self._raw_rule["id"])

    @property
    def name(self) -> str:
        return str(self._raw_rule.get("name", ""))

    @property
    def enabled(self) -> bool:
        return bool(self._raw_rule.get("enabled", False))

    @property
    def trigger_count(self) -> int:
        return len(self._raw_rule.get("automationTriggers", []) or [])

    @property
    def condition_count(self) -> int:
        return len(self._raw_rule.get("automationConditions", []) or [])

    @property
    def action_count(self) -> int:
        return len(self._raw_rule.get("automationActions", []) or [])

    def update_raw_rule(self, raw_rule: dict[str, Any]) -> None:
        if self._raw_rule["id"] != raw_rule["id"]:
            raise SHCException("Error due to mismatching automation rule ids!")
        self._raw_rule = raw_rule

    def _enabled_put_body(self, enabled: bool) -> dict[str, Any]:
        return {**self._raw_rule, "enabled": enabled}

    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable this rule (sync; full-body PUT)."""
        body = self._enabled_put_body(enabled)
        response = self._api.put_automation_rule(self.id, body)
        self.update_raw_rule(response if response else body)

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable/disable this rule (async; full-body PUT)."""
        body = self._enabled_put_body(enabled)
        response = await self._api.put_automation_rule(self.id, body)
        self.update_raw_rule(response if response else body)

    def refresh(self) -> None:
        """Re-fetch just this rule's current state (sync; single-rule GET)."""
        self.update_raw_rule(self._api.get_automation_rule(self.id))

    async def async_refresh(self) -> None:
        """Re-fetch just this rule's current state (async; single-rule GET)."""
        self.update_raw_rule(await self._api.get_automation_rule(self.id))

    def trigger(self) -> None:
        """Manually fire this rule now (sync)."""
        self._api.trigger_automation_rule(self.id)

    async def async_trigger(self) -> None:
        """Manually fire this rule now (async)."""
        await self._api.trigger_automation_rule(self.id)  # type: ignore[misc,func-returns-value]

    def summary(self) -> None:
        print(f"automation rule: {self.id}")
        print(f"  Name      : {self.name}")
        print(f"  Enabled   : {self.enabled}")
        print(f"  Triggers  : {self.trigger_count}")
        print(f"  Conditions: {self.condition_count}")
        print(f"  Actions   : {self.action_count}")
