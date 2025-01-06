import typing
import logging

logger = logging.getLogger("boschshcpy")


class SHCMessage:
    def __init__(self, api, raw_message):
        self.api = api
        self._raw_message = raw_message

    class MessageCode:
        def __init__(self, message_code):
            self._message_code = message_code

        @property
        def name(self):
            return self._message_code["name"]

        @property
        def category(self):
            return self._message_code["category"]

    @property
    def id(self):
        return self._raw_message["id"]

    @property
    def message_code(self) -> MessageCode:
        return self._raw_message["messageCode"]

    @property
    def source_type(self):
        return self._raw_message["sourceType"]

    @property
    def timestamp(self):
        return self._raw_message["timestamp"]

    @property
    def flags(self):
        return self._raw_message["flags"]

    @property
    def arguments(self):
        return self._raw_message["arguments"]

    def summary(self):
        print(f"Message      : {self.id}")
        print(f"  Source     : {self.source_type}")
        print(f"  Timestamp  : {self.timestamp}")
        print(f"  MessageCode: {self.message_code}")
        if self.flags:
            _flags_string = "; ".join(self.flags)
            print(f"  Flags      : {_flags_string}")
        print(f"  Arguments  : {self.arguments}")
