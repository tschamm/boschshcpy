from .api import SHCAPI


class SHCDeviceService:
    def __init__(self, api: SHCAPI, raw_device_service):
        self._api = api
        self._raw_device_service = raw_device_service
        self._raw_state = self._raw_device_service["state"]

        self.on_state_changed = None

    @property
    def id(self):
        return self._raw_device_service['id']

    @property
    def device_id(self):
        return self._raw_device_service['deviceId']

    @property
    def state(self):
        return self._raw_state

    @property
    def path(self):
        return self._raw_device_service['path']

    def summary(self):
        print(f"  Device Service: {self.id}")
        print(f"    State: {self.state}")
        print(f"    Path:  {self.path}")

    def set_callback(self, callback):
        self.on_state_changed = callback

    def put_state_element(self, key, value):
        self._api.put_device_service_state(self.device_id, self.id, {"@type": self.state["@type"], key: value})

        # TODO figure out nice logic to replace this with the "true" value. For now, long polling will solve this
        self.state[key] = value

    def short_poll(self):
        self._raw_device_service = self._api.get_device_service(self.device_id, self.id)

    def process_long_polling_poll_result(self, raw_result):
        assert raw_result["@type"] == "DeviceServiceData"
        assert raw_result["state"]["@type"] == self.state["@type"]

        # Update state
        self._raw_state = raw_result["state"]

        if self.on_state_changed is not None:
            self.on_state_changed()
