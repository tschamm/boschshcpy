from enum import Enum
import logging
from getmac import get_mac_address

logger = logging.getLogger("boschshcpy")


class SHCInformation:
    class UpdateState(Enum):
        NO_UPDATE_AVAILABLE = "NO_UPDATE_AVAILABLE"
        DOWNLOADING = "DOWNLOADING"
        UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
        UPDATE_AVAILABLE = "UPDATE_AVAILABLE"

    def __init__(self, api, raw_information):
        self._api = api
        self._raw_information = raw_information

    @property
    def version(self):
        return self._raw_information["version"]

    @property
    def updateState(self) -> UpdateState:
        return self.UpdateState(self._raw_information["updateState"])

    @property
    def connectivityVersion(self):
        return self._raw_information["connectivityVersion"]

    @property
    def macAddress(self):
        return get_mac(host=self._api._controller_ip)

    def summary(self):
        print(f"Information:")
        print(f"  SW Version         : {self.version}")
        print(f"  State              : {self.updateState}")
        print(f"  connectivityVersion: {self.connectivityVersion}")
        print(f"  mac address        : {self.macAddress}")

def get_mac(host):
    """Get the mac address of the given host."""
    try:
        mac_address = get_mac_address(ip=host)
        if not mac_address:
            mac_address=get_mac_address(hostname = host)
    except Exception as err:  # pylint: disable=broad-except
        logging.error("Unable to get mac address: %s", err)
        mac_address=None
    return mac_address
