from boschshcpy import device
from enum import Enum
import time
import logging

from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo, IPVersion

logger = logging.getLogger("boschshcpy")

class SHCListener:
    def __init__(self) -> None:
        self.shc_services = {}

    def update_service(self, arg0, arg1, arg2):
        return

    def remove_service(self, zeroconf, type, name):
        self.shc_services[name] = None

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        self.shc_services[name] = info

def discover_shc_devices():
    zeroconf = Zeroconf()
    listener = SHCListener()
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
    time.sleep(3) # We have to give zeroconf services time to respond
    zeroconf.close()

    return listener.shc_services


class SHCInformation:
    class UpdateState(Enum):
        NO_UPDATE_AVAILABLE = "NO_UPDATE_AVAILABLE"
        DOWNLOADING = "DOWNLOADING"
        UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
        UPDATE_AVAILABLE = "UPDATE_AVAILABLE"

    def __init__(self, api, raw_information):
        self._api = api
        self._raw_information = raw_information

        self._name = None
        self._mac_address = None        
        self.filter(discover_shc_devices())

        if self._mac_address is None or self._name is None:
            logger.error("Unable to discover SHC device!")

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
        return self._mac_address

    def filter(self, devices):
        info: ServiceInfo
        for info in devices.values():
            if "Bosch SHC" in info.name: 
                if self._api._controller_ip in info.parsed_addresses(IPVersion.V4Only):
                    self._mac_address = info.name[info.name.find('[')+1:info.name.find(']')]
                    server_pos = info.server.find('.local.')
                    if server_pos > -1:
                        self._name = info.server[:server_pos]

    def summary(self):
        print(f"Information:")
        print(f"  SW-Version         : {self.version}")
        print(f"  updateState        : {self.updateState}")
        print(f"  connectivityVersion: {self.connectivityVersion}")
        print(f"  macAddress         : {self.macAddress}")
        print(f"  name               : {self._name}")
