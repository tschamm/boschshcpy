from .api import SHCAPI


class SHCDeviceService:
    def __init__(self, api: SHCAPI, raw_device_service):
        self._api = api
        self._raw_device_service = raw_device_service
        self._raw_state = (
            self._raw_device_service["state"]
            if "state" in self._raw_device_service
            else {}
        )

        self._callbacks = {}
        self._event_callbacks = {}

    @property
    def id(self):
        return self._raw_device_service["id"]

    @property
    def device_id(self):
        return self._raw_device_service["deviceId"]

    @property
    def state(self):
        return self._raw_state

    @property
    def path(self):
        return self._raw_device_service["path"]

    def subscribe_callback(self, entity, callback):
        self._callbacks[entity] = callback

    def unsubscribe_callback(self, entity):
        self._callbacks.pop(entity, None)

    def register_event(self, event, callback):
        self._event_callbacks[event] = callback

    def summary(self):
        print(f"  Device Service: {self.id}")
        print(f"    State: {self.state}")
        print(f"    Path:  {self.path}")

    def put_state(self, key_value_pairs):
        self._api.put_device_service_state(
            self.device_id.replace("#", "%23"),
            self.id,
            {"@type": self.state["@type"], **key_value_pairs},
        )

    def put_state_element(self, key, value):
        self.put_state({key: value})

    def short_poll(self):
        self._raw_device_service = self._api.get_device_service(self.device_id, self.id)
        self._raw_state = (
            self._raw_device_service["state"]
            if "state" in self._raw_device_service
            else {}
        )

    def process_long_polling_poll_result(self, raw_result):
        assert raw_result["@type"] == "DeviceServiceData"
        self._raw_device_service = raw_result  # Update device service data

        if "state" in self._raw_device_service:
            assert raw_result["state"]["@type"] == self.state["@type"]
            self._raw_state = raw_result["state"]  # Update state

            for callback in self._callbacks:
                self._callbacks[callback]()

            self._process_events(raw_result)

    def _process_events(self, raw_result):
        if raw_result["id"] == "Keypad":
            if raw_result["state"]["keyName"] in self._event_callbacks:
                self._event_callbacks[raw_result["state"]["keyName"]]()
        if raw_result["id"] == "LatestMotion":
            if raw_result["deviceId"] in self._event_callbacks:
                self._event_callbacks[raw_result["deviceId"]]()
