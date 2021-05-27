from enum import Enum


class SHCInformation:
    class UpdateState(Enum):
        NO_UPDATE_AVAILABLE = "NO_UPDATE_AVAILABLE"
        DOWNLOADING = "DOWNLOADING"
        UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
        UPDATE_AVAILABLE = "UPDATE_AVAILABLE"

    def __init__(self, pub_info):
        self._pub_info = pub_info

        self._unique_id = self.macAddress
        self._name = self.shcIpAddress

    @property
    def version(self):
        return self._pub_info["softwareUpdateState"]["swInstalledVersion"]

    @property
    def updateState(self) -> UpdateState:
        return self.UpdateState(self._pub_info["softwareUpdateState"]["swUpdateState"])

    @property
    def shcIpAddress(self):
        """Get the ip address from public information."""
        return self._pub_info["shcIpAddress"]

    @property
    def macAddress(self):
        """Get the mac address from public information."""
        return self._pub_info["macAddress"] if "macAddress" in self._pub_info else None

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    def summary(self):
        print("Information          :")
        print(f"  shcIpAddress       : {self.shcIpAddress}")
        print(f"  macAddress         : {self.macAddress}")
        print(f"  SW-Version         : {self.version}")
        print(f"  updateState        : {self.updateState.name}")
        print(f"  uniqueId           : {self.unique_id}")
        print(f"  name               : {self.name}")
