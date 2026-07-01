from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("boschshcpy")


class SHCMessage:
    def __init__(self, api: Any, raw_message: dict[str, Any]) -> None:
        self.api = api
        self._raw_message = raw_message

    class MessageCode:
        def __init__(self, message_code: dict[str, Any]) -> None:
            self._message_code = message_code

        @property
        def name(self) -> str:
            return str(self._message_code.get("name", ""))

        @property
        def category(self) -> str:
            return str(self._message_code.get("category", ""))

    @property
    def id(self) -> str:
        return str(self._raw_message.get("id", ""))

    @property
    def message_code(self) -> MessageCode:
        # None of Message's fields are in the OpenAPI "required" list — the
        # SHC is free to omit any of them (same class of bug as #351's
        # UserDefinedState KeyError on an omitted "deleted" key).
        return self.MessageCode(self._raw_message.get("messageCode", {}))

    @property
    def source_type(self) -> str:
        return str(self._raw_message.get("sourceType", ""))

    @property
    def timestamp(self) -> Any:
        return self._raw_message.get("timestamp")

    @property
    def flags(self) -> Any:
        return self._raw_message.get("flags", [])

    @property
    def arguments(self) -> Any:
        return self._raw_message.get("arguments", {})

    def summary(self) -> None:
        print(f"Message      : {self.id}")
        print(f"  Source     : {self.source_type}")
        print(f"  Timestamp  : {self.timestamp}")
        print(f"  MessageCode: {self.message_code}")
        if self.flags:
            _flags_string = "; ".join(self.flags)
            print(f"  Flags      : {_flags_string}")
        print(f"  Arguments  : {self.arguments}")
