from __future__ import annotations

from typing import Any

from .api import SHCAPI


class SHCScenario:
    def __init__(self, api: SHCAPI, raw_scenario: dict[str, Any]) -> None:
        self._api = api
        self._raw_scenario = raw_scenario

    @property
    def id(self) -> str:
        return str(self._raw_scenario["id"])

    @property
    def icon_id(self) -> str:
        # Not in the OpenAPI "required" list — same pattern as room.py's
        # icon_id fix.
        return str(self._raw_scenario.get("iconId", ""))

    @property
    def name(self) -> str:
        return str(self._raw_scenario.get("name", ""))

    def trigger(self) -> Any:
        return self._api._post_api_or_fail(
            f"{self._api._api_root}/scenarios/{self.id}/triggers", ""
        )

    async def async_trigger(self) -> None:
        """Async write: trigger this scenario."""
        await self._api._post_api_or_fail(
            f"{self._api._api_root}/scenarios/{self.id}/triggers", ""
        )

    def summary(self) -> None:
        print(f"scenario: {self.id}")
        print(f"  Name   : {self.name}")
        print(f"  Icon Id: {self.icon_id}")
