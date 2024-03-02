#import typing
import logging

logger = logging.getLogger("boschshcpy")

class SHCMessage:
    def __init__(self, api, raw_message):
        self.api = api
        self._raw_message = raw_message

    @property
    def id(self):
        return self._raw_message["id"]

    @property
    def message_code(self):
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
        _flags_string = "; ".join(self.flags)
        print(f"  Flags      : {_flags_string}")
        #_arguments_string = "; ".join(self.arguments)
        #print(f"  Arguments  : {_arguments_string}")
        print(f"  Arguments  : {self.arguments}")

    def process_long_polling_result(self, raw_result):
        assert raw_result["@type"] == "message"
        message_id = raw_result["id"]
        logger.debug(
            f"Got long polling result, not yet supported {message_id}"
        )