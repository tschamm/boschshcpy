import logging
from .device import SHCDevice
from .information import SHCInformation

logger = logging.getLogger("boschshcpy")


class SHCEmma(SHCDevice):

    def __init__(self, api, shc_info: SHCInformation = None, raw_result=None):
        _emma_raw_device = {
            "rootDeviceId": shc_info.macAddress if shc_info else "",
            "id": "com.bosch.tt.emma.applink",
            "manufacturer": "BOSCH",
            "roomId": "",
            "deviceModel": "EMMA",
            "serial": (
                shc_info.macAddress + "_" + "com.bosch.tt.emma.applink"
                if shc_info
                else ""
            ),
            "name": "EMMA",
            "status": (
                "AVAILABLE"
                if raw_result
                else "UNAVAILABLE" if shc_info else "UNDEFINED"
            ),
            "deviceServiceIds": [],
        }

        if not raw_result:
            raw_result = {
                "version": "",
                "localizedTitles": {"en": ""},
                "localizedInformation": {"en": "0 W"},
            }

        super().__init__(api=api, raw_device=_emma_raw_device, raw_device_services=None)
        self.api = api
        self._raw_result = raw_result

    @property
    def version(self) -> str:
        return self._raw_result["version"]

    @property
    def localizedTitles(self) -> str:
        return self._raw_result["localizedTitles"]["en"]

    @property
    def localizedInformation(self) -> str:
        return self._raw_result["localizedInformation"]["en"]

    @property
    def parsedInformation(self) -> str:
        return self.localizedInformation.split(" W")[0]

    def summary(self):
        super().summary()
        print(f"EMMA       : {self.id}")
        print(f"  Name     : {self.name}")
        print(f"  Version  : {self.version}")
        print(f"  Title    : {self.localizedTitles}")
        print(f"  Info     : {self.parsedInformation}")
