"""Zigbee routing-info model for boschshcpy.

Endpoint: ``GET /smarthome/zigbee/routinginfo/{deviceId}``. Not documented in
the official OpenAPI spec — discovered via decompiling the official Bosch
Android app and confirmed working (HTTP 200) against real hardware.

Example response::

    {
        "device": "hdm:ZigBee:0123456789abcdef",
        "aggregatedQuality": "GOOD",
        "route": [
            {"deviceId": "hdm:ZigBee:0123456789abcdef", "quality": "GOOD"}
        ]
    }

A device with no connection returns an empty ``route`` and
``aggregatedQuality: "NO_CONNECTION"``. Multi-hop routes list one entry per
hop, ordered from the target device back to the controller.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, NamedTuple


class ZigbeeRoutingQuality(Enum):
    """Link quality of a Zigbee routing hop.

    Values from the decompiled APK class
    ``com.bosch.sh.common.model.zigbee.ZigbeeRoutingInformationData$Quality``.
    """

    GOOD = "GOOD"
    MEDIUM = "MEDIUM"
    BAD = "BAD"
    NO_CONNECTION = "NO_CONNECTION"
    DEVICE_NOT_INITIALIZED = "DEVICE_NOT_INITIALIZED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object) -> ZigbeeRoutingQuality:
        # Robust parsing, same pattern as CommunicationQualityService.value /
        # SHCInformation.updateState: an unexpected/new enum string from the
        # controller must not crash the caller, it should fall back to
        # UNKNOWN.
        return cls.UNKNOWN


class ZigbeeRoutingHop(NamedTuple):
    """A single hop in a Zigbee routing path."""

    device_id: str
    quality: ZigbeeRoutingQuality


class SHCZigbeeRoutingInfo:
    """Parsed response of ``GET /smarthome/zigbee/routinginfo/{deviceId}``."""

    def __init__(self, raw_routing_info: dict[str, Any]) -> None:
        self._raw_routing_info = raw_routing_info

    @property
    def device_id(self) -> str:
        return str(self._raw_routing_info.get("device", ""))

    @property
    def aggregated_quality(self) -> ZigbeeRoutingQuality:
        return ZigbeeRoutingQuality(
            self._raw_routing_info.get("aggregatedQuality", "UNKNOWN")
        )

    @property
    def route(self) -> list[ZigbeeRoutingHop]:
        return [
            ZigbeeRoutingHop(
                device_id=str(hop.get("deviceId", "")),
                quality=ZigbeeRoutingQuality(hop.get("quality", "UNKNOWN")),
            )
            for hop in self._raw_routing_info.get("route", [])
        ]

    def summary(self) -> None:
        print(f"Zigbee routing info: {self.device_id}")
        print(f"  Aggregated quality: {self.aggregated_quality.name}")
        for hop in self.route:
            print(f"    - {hop.device_id}: {hop.quality.name}")
