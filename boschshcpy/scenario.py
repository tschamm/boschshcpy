from .api import SHCAPI


class SHCScenario:
    def __init__(self, api: SHCAPI, raw_scenario):
        self._api = api
        self._raw_scenario = raw_scenario

    @property
    def id(self):
        return self._raw_scenario["id"]

    @property
    def icon_id(self):
        return self._raw_scenario["iconId"]

    @property
    def name(self):
        return self._raw_scenario["name"]

    def trigger(self):
        return self._api._post_api_or_fail(
            f"{self._api._api_root}/scenarios/{self.id}/triggers", ""
        )

    def summary(self):
        print(f"scenario: {self.id}")
        print(f"  Name   : {self.name}")
        print(f"  Icon Id: {self.icon_id}")
