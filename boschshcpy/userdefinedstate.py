from __future__ import annotations

from typing import Any

from .api import SHCAPI
from .exceptions import SHCException
from .information import SHCInformation


class SHCUserDefinedState:
    def __init__(self, api: SHCAPI, info: SHCInformation, raw_state: dict[str, Any]) -> None:
        self._api = api
        self._info = info
        self._raw_state = raw_state

    @property
    def id(self) -> str:
        return str(self._raw_state["id"])

    @property
    def root_device_id(self) -> str | None:
        mac = self._info.macAddress
        return str(mac) if mac is not None else None

    @property
    def name(self) -> str:
        return str(self._raw_state["name"])

    @property
    def deleted(self) -> bool:
        return bool(self._raw_state.get("deleted", False))

    @property
    def state(self) -> bool:
        return bool(self._raw_state.get("state", False))

    @state.setter
    def state(self, state: bool) -> None:
        self._api._put_api_or_fail(
            f"{self._api._api_root}/userdefinedstates/{self.id}/state", state
        )

    async def async_set_state(self, state: bool) -> None:
        """Async write: set user-defined state on/off via the async API."""
        await self._api._put_api_or_fail(
            f"{self._api._api_root}/userdefinedstates/{self.id}/state", state
        )

    def update_raw_information(self, raw_state: dict[str, Any]) -> None:
        if self._raw_state["id"] != raw_state["id"]:
            raise SHCException("Error due to mismatching ids!")
        self._raw_state = raw_state

    def summary(self) -> None:
        print(f"userdefinedstate: {self.id}")
        print(f"  Name          : {self.name}")
        print(f"  State         : {self.state}")
