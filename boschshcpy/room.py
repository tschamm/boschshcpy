class SHCRoom:
    def __init__(self, raw_room):
        self._raw_room = raw_room

    @property
    def id(self):
        return self._raw_room["id"]

    @property
    def icon_id(self):
        return self._raw_room["iconId"]

    @property
    def name(self):
        return self._raw_room["name"]

    def summary(self):
        print(f"Room      : {self.id}")
        print(f"  Name    : {self.name}")
        print(f"  Icon Id : {self.icon_id}")
