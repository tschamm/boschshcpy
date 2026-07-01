from __future__ import annotations

import logging
import typing
from typing import Any, Callable

from .api import SHCAPI
from .device_service import SHCDeviceService
from .exceptions import SHCException
from .services_impl import SUPPORTED_DEVICE_SERVICE_IDS, build

logger = logging.getLogger("boschshcpy")


class SHCDevice:
    def __init__(
        self,
        api: SHCAPI,
        raw_device: dict[str, Any],
        raw_device_services: list[dict[str, Any]],
    ) -> None:
        self._api = api
        self._raw_device = raw_device

        self._callbacks: dict[Any, Callable[[], None]] = {}
        self._device_services_by_id: dict[str, SHCDeviceService] = {}
        if not raw_device_services:
            raw_device_services = self._enumerate_services()

        self._init_services(raw_device_services)

    def _enumerate_services(self) -> list[dict[str, Any]]:
        raw_device_services: list[dict[str, Any]] = []
        for device_service_id in self._raw_device["deviceServiceIds"]:
            if device_service_id not in SUPPORTED_DEVICE_SERVICE_IDS:
                continue

            raw_device_service_data = self._api.get_device_service(
                self.id, device_service_id
            )
            raw_device_services.append(raw_device_service_data)
        return raw_device_services

    def _init_services(self, raw_device_services: list[dict[str, Any]]) -> None:
        for raw_device_service_data in raw_device_services:
            device_service = build(self._api, raw_device_service_data)
            self._device_services_by_id[raw_device_service_data["id"]] = device_service

    @property
    def root_device_id(self) -> str:
        return str(self._raw_device.get("rootDeviceId", ""))

    @property
    def id(self) -> str:
        # Deliberately still a direct index: id is used as the dict key
        # throughout device_helper.py/session.py — if the SHC omits it the
        # device can't be indexed/used at all, so failing loudly here is
        # more useful than limping on with an empty id.
        return str(self._raw_device["id"])

    @property
    def manufacturer(self) -> str:
        return str(self._raw_device.get("manufacturer", ""))

    @property
    def room_id(self) -> str | None:
        return str(self._raw_device["roomId"]) if "roomId" in self._raw_device else None

    @property
    def device_model(self) -> str:
        return str(self._raw_device.get("deviceModel", ""))

    @property
    def serial(self) -> str | None:
        return str(self._raw_device["serial"]) if "serial" in self._raw_device else None

    @property
    def profile(self) -> str | None:
        return (
            str(self._raw_device["profile"]) if "profile" in self._raw_device else None
        )

    @property
    def supported_profiles(self) -> list[Any]:
        return list(self._raw_device.get("supportedProfiles", []))

    def _profile_put_body(self, profile: str) -> dict[str, Any]:
        """Validate ``profile`` and build the full Device body to PUT.

        The installation profile is a device-level field (not a service). The
        SHC requires the complete Device resource on PUT, so we fetch the
        current body and swap only ``profile``. Raises SHCException when the
        device advertises supportedProfiles and ``profile`` is not among them.
        """
        supported = self.supported_profiles
        if supported and profile not in supported:
            raise SHCException(
                f"Profile '{profile}' not in supportedProfiles {supported} "
                f"for device {self.id}"
            )
        return {**self._raw_device, "profile": profile}

    def set_profile(self, profile: str) -> None:
        """Set the installation profile (sync; e.g. GENERIC / OUTDOOR)."""
        body = self._profile_put_body(profile)
        response = self._api.put_device(self.id, body)
        # Prefer the server's canonical object (it may normalize fields); fall
        # back to our request body when the SHC answers with an empty 2xx.
        self.update_raw_information(response if response else body)

    async def async_set_profile(self, profile: str) -> None:
        """Set the installation profile (async; e.g. GENERIC / OUTDOOR)."""
        body = self._profile_put_body(profile)
        response = await self._api.put_device(self.id, body)
        # Prefer the server's canonical object (it may normalize fields); fall
        # back to our request body when the SHC answers with an empty 2xx.
        self.update_raw_information(response if response else body)

    @property
    def name(self) -> str:
        # Not in the OpenAPI "required" list for Device — .get() to match the
        # existing roomId/serial/profile pattern above rather than crash on a
        # display-only field.
        return str(self._raw_device.get("name", ""))

    @property
    def status(self) -> str:
        return str(self._raw_device.get("status", ""))

    @property
    def deleted(self) -> bool:
        return (
            True
            if "deleted" in self._raw_device and self._raw_device["deleted"] is True
            else False
        )

    @property
    def child_device_ids(self) -> list[str] | None:
        return (
            list(self._raw_device["childDeviceIds"])
            if "childDeviceIds" in self._raw_device
            else None
        )

    @property
    def parent_device_id(self) -> str | None:
        return (
            str(self._raw_device["parentDeviceId"])
            if "parentDeviceId" in self._raw_device
            else None
        )

    @property
    def software_update(self) -> SHCDeviceService | None:
        """The per-device SoftwareUpdate service, or None if not exposed.

        Spec-grounded (APK 10.33). Most devices do not carry this service, so
        callers must guard on the None return. Read-only firmware status — the
        local API has no per-device install action (hass#186 lesson).
        """
        return self.device_service("SoftwareUpdate")

    @property
    def supports_software_update(self) -> bool:
        return self.device_service("SoftwareUpdate") is not None

    @property
    def device_services(self) -> typing.Sequence[SHCDeviceService]:
        return list(self._device_services_by_id.values())

    @property
    def device_service_ids(self) -> typing.Set[str]:
        return set(self._device_services_by_id.keys())

    def subscribe_callback(self, entity: Any, callback: Callable[[], None]) -> None:
        self._callbacks[entity] = callback

    def unsubscribe_callback(self, entity: Any) -> None:
        self._callbacks.pop(entity, None)

    def update_raw_information(self, raw_device: dict[str, Any]) -> None:
        if self._raw_device["id"] != raw_device["id"]:
            raise SHCException("Error due to mismatching device ids!")
        self._raw_device = raw_device

        for fn in list(self._callbacks.values()):
            fn()

    def device_service(self, device_service_id: str) -> SHCDeviceService | None:
        return (
            self._device_services_by_id[device_service_id]
            if device_service_id in self._device_services_by_id
            else None
        )

    def update(self, fire_callbacks: bool = False) -> None:
        for service in self.device_services:
            service.short_poll(fire_callbacks=fire_callbacks)

    async def async_update(self, fire_callbacks: bool = False) -> None:
        """Async counterpart to update() for the SHCAPIAsync path.

        HA should_poll entities (e.g. camera switches) call this for an
        on-demand refresh; the sync update()/short_poll() path cannot run
        against the async api (it would leave a coroutine in _raw_device_service).
        """
        for service in self.device_services:
            await service.async_short_poll(fire_callbacks=fire_callbacks)

    def summary(self) -> None:
        print(f"Device: {self.id}")
        print(f"  Name          : {self.name}")
        print(f"  Manufacturer  : {self.manufacturer}")
        print(f"  Model         : {self.device_model}")
        print(f"  Room          : {self.room_id}")
        print(f"  Serial        : {self.serial}")
        print(f"  Profile       : {self.profile}")
        print(f"  Status        : {self.status}")
        print(f"  ParentDevice  : {self.parent_device_id}")
        print(f"  ChildDevices  : {self.child_device_ids}")
        print(f"  DeviceServices: {self._raw_device['deviceServiceIds']}")
        for device_service in self.device_services:
            device_service.summary()

    def process_long_polling_poll_result(self, raw_result: dict[str, Any]) -> None:
        if raw_result.get("@type") != "DeviceServiceData":
            return
        device_service_id = raw_result["id"]
        if device_service_id in self._device_services_by_id:
            device_service: SHCDeviceService = self._device_services_by_id[
                device_service_id
            ]
            device_service.process_long_polling_poll_result(raw_result)
        else:
            logger.debug(
                f"Skipping polling result with unknown device service id {device_service_id}."
            )
