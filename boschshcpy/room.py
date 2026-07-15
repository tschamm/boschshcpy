from __future__ import annotations

from typing import Any


class SHCRoom:
    def __init__(self, api: Any, raw_room: dict[str, Any]) -> None:
        self._api = api
        self._raw_room = raw_room

    @property
    def id(self) -> str:
        return str(self._raw_room.get("id", ""))

    @property
    def icon_id(self) -> str:
        # Not in the OpenAPI "required" list — a room using the default icon
        # can legitimately omit iconId.
        return str(self._raw_room.get("iconId", ""))

    @property
    def name(self) -> str:
        return str(self._raw_room.get("name", ""))

    def summary(self) -> None:
        print(f"Room: {self.id}")
        print(f"  Name   : {self.name}")
        print(f"  Icon Id: {self.icon_id}")

    def temperature_drop_service(self) -> Any:
        """This room's anti-frost/window-open temperature-drop service state.

        Not in the official OpenAPI spec; APK ground-truth
        (RestRequests.getTemperatureDropService). Raises SHCSessionError
        (404) for rooms without this capability.
        """
        return self._api.get_temperature_drop_service(self.id)

    async def async_temperature_drop_service(self) -> Any:
        """Async counterpart to temperature_drop_service()."""
        return await self._api.get_temperature_drop_service(self.id)

    def _temperature_drop_put_body(
        self, field: str, value: Any, current: dict[str, Any]
    ) -> dict[str, Any]:
        # The SHC expects the full roomTemperatureDropService body back
        # (read-modify-write), same pattern as device.py's profile PUT --
        # only "configuration" is meant to be edited; the sibling
        # supports*/requires* fields are server-derived capability flags.
        configuration = {**current.get("configuration", {}), field: value}
        return {**current, "configuration": configuration}

    def set_temperature_drop_enabled(self, enabled: bool) -> None:
        """Enable/disable the temperature-drop service for this room (sync)."""
        current = self._api.get_temperature_drop_service(self.id)
        body = self._temperature_drop_put_body("enabled", enabled, current)
        self._api.put_temperature_drop_service(self.id, body)

    async def async_set_temperature_drop_enabled(self, enabled: bool) -> None:
        """Enable/disable the temperature-drop service for this room (async)."""
        current = await self._api.get_temperature_drop_service(self.id)
        body = self._temperature_drop_put_body("enabled", enabled, current)
        await self._api.put_temperature_drop_service(self.id, body)

    def set_temperature_drop_value(self, drop_temperature: float) -> None:
        """Set how many degrees to drop the setpoint by (sync)."""
        current = self._api.get_temperature_drop_service(self.id)
        body = self._temperature_drop_put_body(
            "dropTemperature", drop_temperature, current
        )
        self._api.put_temperature_drop_service(self.id, body)

    async def async_set_temperature_drop_value(self, drop_temperature: float) -> None:
        """Set how many degrees to drop the setpoint by (async)."""
        current = await self._api.get_temperature_drop_service(self.id)
        body = self._temperature_drop_put_body(
            "dropTemperature", drop_temperature, current
        )
        await self._api.put_temperature_drop_service(self.id, body)
