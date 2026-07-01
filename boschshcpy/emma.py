from __future__ import annotations

import logging
from typing import Any

from .device import SHCDevice
from .exceptions import SHCException
from .information import SHCInformation

logger = logging.getLogger("boschshcpy")


class SHCEmma(SHCDevice):
    def __init__(
        self,
        api: Any,
        shc_info: SHCInformation | None = None,
        raw_result: dict[str, Any] | None = None,
    ) -> None:
        _emma_raw_device: dict[str, Any] = {
            "rootDeviceId": shc_info.macAddress if shc_info else "",
            "id": "com.bosch.tt.emma.applink",
            "manufacturer": "BOSCH",
            "roomId": "",
            "deviceModel": "EMMA",
            "serial": (
                (shc_info.macAddress or "") + "_" + "com.bosch.tt.emma.applink"
                if shc_info
                else ""
            ),
            "name": "EMMA",
            "status": (
                "AVAILABLE"
                if raw_result
                else "UNAVAILABLE"
                if shc_info
                else "UNDEFINED"
            ),
            "deviceServiceIds": [],
        }

        if not raw_result:
            raw_result = {
                "version": "",
                "localizedTitles": {"en": ""},
                "localizedInformation": {"en": "0 W"},
            }

        super().__init__(api=api, raw_device=_emma_raw_device, raw_device_services=None)  # type: ignore[arg-type]
        self.api = api
        self._shc_info = shc_info
        self._raw_result: dict[str, Any] = raw_result

    @property
    def version(self) -> str:
        return str(self._raw_result.get("version", ""))

    @property
    def localizedTitles(self) -> str:
        return str((self._raw_result.get("localizedTitles") or {}).get("en", ""))

    @property
    def localizedSubtitles(self) -> str:
        # Bosch has used both "localizedSubtitles" and "localizedSubTitles" —
        # accept either spelling and never raise KeyError on an odd payload.
        subs = (
            self._raw_result.get("localizedSubtitles")
            or self._raw_result.get("localizedSubTitles")
            or {}
        )
        return str(subs.get("en", ""))

    @property
    def localizedInformation(self) -> str:
        return str((self._raw_result.get("localizedInformation") or {}).get("en", ""))

    @property
    def value(self) -> float | None:
        try:
            value = int(self.localizedInformation.split(" W")[0])
            sign = -1.0 if self.localizedSubtitles == "Grid Supply" else 1.0
            return sign * value
        except (ValueError, KeyError, TypeError):
            return None

    def update_emma_data(self, raw_result: dict[str, Any]) -> None:
        if self._shc_info is None:
            raise SHCException("Error due to missing initialization!")

        self._raw_result = raw_result
        self._raw_device["status"] = "AVAILABLE"

        for fn in list(self._callbacks.values()):
            fn()

    def summary(self) -> None:
        super().summary()
        print(f"EMMA       : {self.id}")
        print(f"  Name     : {self.name}")
        print(f"  Version  : {self.version}")
        print(f"  Title    : {self.localizedTitles}")
        print(f"  Subtitle : {self.localizedSubtitles}")
        print(f"  Info     : {self.value}")
