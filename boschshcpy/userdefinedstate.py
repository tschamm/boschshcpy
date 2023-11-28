from .api import SHCAPI


class SHCUserDefinedState:
    def __init__(self, api: SHCAPI, raw_state):
        self._api = api
        self._raw_state = raw_state

    @property
    def id(self):
        return self._raw_state["id"]

    @property
    def name(self):
        return self._raw_state["name"]

    @property
    def deleted(self):
        return self._raw_state["deleted"]

    @property
    def state(self):
        return self._raw_state["state"]

    @state.setter
    def state(self, state: bool):
        return self._api._put_api_or_fail(
            f"{self._api._api_root}/userdefinedstates/{self.id}/state", state
        )

    def summary(self):
        print(f"userdefinedstate: {self.id}")
        print(f"  Name          : {self.name}")
        print(f"  State         : {self.state}")
