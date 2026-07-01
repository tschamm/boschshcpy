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
