from __future__ import annotations

import logging
import socket
import time
from enum import Enum
from typing import Any, Callable

from getmac import get_mac_address
from zeroconf import Error as ZeroconfError
from zeroconf import (
    IPVersion,
    ServiceBrowser,
    ServiceInfo,
    ServiceStateChange,
    current_time_millis,
)

from boschshcpy.exceptions import (
    SHCAuthenticationError,
    SHCConnectionError,
)

logger = logging.getLogger("boschshcpy")


class SHCListener:
    """SHC Listener for Zeroconf browser updates."""

    def __init__(
        self,
        zeroconf: Any,
        callback: Callable[[dict[str, ServiceInfo]], None],
    ) -> None:
        """Initialize SHC Listener."""
        self.shc_services: dict[str, ServiceInfo] = {}
        self.waiting = True

        browser = ServiceBrowser(
            zeroconf, "_http._tcp.local.", handlers=[self.service_update]
        )
        current_millis = current_time_millis()
        while (
            self.waiting and current_time_millis() - current_millis < 10000
        ):  # Give zeroconf some time to respond
            time.sleep(0.1)
        callback(self.shc_services)
        browser.cancel()

    def service_update(
        self,
        zeroconf: Any,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        """Service state changed."""

        if state_change != ServiceStateChange.Added:
            return

        try:
            service_info = zeroconf.get_service_info(service_type, name)
        except ZeroconfError:
            logger.exception("Failed to get info for device %s", name)
            return

        if service_info is not None:
            if service_info.name.startswith("Bosch SHC"):
                self.waiting = False
            self.shc_services[name] = service_info

        return


class SHCInformation:
    class UpdateState(Enum):
        NO_UPDATE_AVAILABLE = "NO_UPDATE_AVAILABLE"
        DOWNLOADING = "DOWNLOADING"
        UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
        UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
        # Spec (ShcInfo) values that were missing — without them updateState
        # returns None for these and .name access elsewhere would crash.
        INSTALLING = "INSTALLING"
        UPDATE_SUCCESS = "UPDATE_SUCCESS"
        UPDATE_FAILED = "UPDATE_FAILED"

    def __init__(
        self, api: Any, authenticate: bool = True, zeroconf: Any = None
    ) -> None:
        self._api = api
        self._unique_id: str | None = None
        self._name: str | None = None

        self._pub_info: dict[str, Any] = self._api.get_public_information()
        if self._pub_info is None:
            raise SHCConnectionError

        if authenticate:
            if self._api.get_information() is None:
                raise SHCAuthenticationError

        self.get_unique_id(zeroconf)

    @property
    def version(self) -> str | None:
        sw: dict[str, Any] = self._pub_info.get("softwareUpdateState", {})
        return sw.get("swInstalledVersion", None)

    @property
    def available_version(self) -> str | None:
        """Available SW version offered by the controller (if any).

        Read-only field from the public /information endpoint
        (softwareUpdateState.swUpdateAvailableVersion). May be None or equal
        to the installed version when no update is pending.
        """
        sw: dict[str, Any] = self._pub_info.get("softwareUpdateState", {})
        return sw.get("swUpdateAvailableVersion", None)

    @property
    def automatic_updates_enabled(self) -> bool | None:
        """Whether the controller installs updates automatically (read-only)."""
        sw: dict[str, Any] = self._pub_info.get("softwareUpdateState", {})
        return sw.get("automaticUpdatesEnabled", None)

    @property
    def updateState(self) -> UpdateState | None:
        sw: dict[str, Any] = self._pub_info.get("softwareUpdateState", {})
        raw = sw.get("swUpdateState", None)
        if raw is None:
            return None
        try:
            return self.UpdateState(raw)
        except ValueError:
            return None

    @property
    def shcIpAddress(self) -> str | None:
        """Get the ip address from public information."""
        return (
            str(self._pub_info["shcIpAddress"])
            if "shcIpAddress" in self._pub_info
            else None
        )

    @property
    def macAddress(self) -> str | None:
        """Get the mac address from public information."""
        return (
            str(self._pub_info["macAddress"])
            if "macAddress" in self._pub_info
            else None
        )

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def unique_id(self) -> str | None:
        return self._unique_id

    def filter(self, service_info: dict[str, ServiceInfo]) -> None:
        mac_address = None
        name = None

        try:
            host_ip = socket.gethostbyname(self.shcIpAddress)  # type: ignore[arg-type]
        except Exception:
            host_ip = None

        for info in service_info.values():
            if "Bosch SHC" in info.name:
                if (
                    host_ip in info.parsed_addresses(IPVersion.V4Only)
                    or host_ip is None
                ):
                    mac_address = info.name[
                        info.name.find("[") + 1 : info.name.find("]")
                    ]
                    server_pos = info.server.find(".local.")
                    if server_pos > -1:
                        name = info.server[:server_pos]
        if mac_address is None or name is None:
            return
        self._unique_id = format_mac(mac_address)
        self._name = name

    def get_unique_id(self, zeroconf: Any) -> None:
        if zeroconf is not None:
            self._listener = SHCListener(zeroconf, self.filter)
            if self._unique_id is not None:
                logger.debug(
                    "Obtain unique_id for '%s' via zeroconf: '%s'",
                    self._name,
                    self._unique_id,
                )
                return

        if self.macAddress is not None:
            self._unique_id = self.macAddress
            self._name = (
                self.shcIpAddress if self.shcIpAddress is not None else self.macAddress
            )
            logger.debug(
                "Obtain unique_id for '%s' via public information: '%s'",
                self._name,
                self._unique_id,
            )
        elif self.shcIpAddress is not None:
            host = self.shcIpAddress
            mac_address: str | None = None
            try:
                mac_address = get_mac_address(ip=host)
                if not mac_address:
                    mac_address = get_mac_address(hostname=host)
            except Exception as err:  # pylint: disable=broad-except
                logger.exception("Unable to get mac address: %s", err)

            if mac_address is not None:
                self._unique_id = format_mac(mac_address)
                logger.debug(
                    "Obtain unique_id for '%s' via host IP: '%s'",
                    self._name,
                    self._unique_id,
                )
            else:
                self._unique_id = host
                logger.warning(
                    "Cannot obtain unique id, using IP address '%s' instead. Please make sure the IP stays the same!",
                    host,
                )
            self._name = host
        else:
            raise SHCConnectionError

    def summary(self) -> None:
        print("Information:")
        print(f"  shcIpAddress       : {self.shcIpAddress}")
        print(f"  macAddress         : {self.macAddress}")
        print(f"  SW-Version         : {self.version}")
        print(
            f"  updateState        : {self.updateState.name if self.updateState else 'N/A'}"
        )
        print(f"  uniqueId           : {self.unique_id}")
        print(f"  name               : {self.name}")


def format_mac(mac: str) -> str:
    """
    Format the mac address string.
    Helper function from homeassistant.helpers.device_registry.py
    """
    to_test = mac

    if len(to_test) == 17 and to_test.count("-") == 5:
        return to_test.lower()

    if len(to_test) == 17 and to_test.count(":") == 5:
        to_test = to_test.replace(":", "")
    elif len(to_test) == 14 and to_test.count(".") == 2:
        to_test = to_test.replace(".", "")

    if len(to_test) == 12:
        # no - included
        return "-".join(to_test.lower()[i : i + 2] for i in range(0, 12, 2))

    # Not sure how formatted, return original
    return mac
