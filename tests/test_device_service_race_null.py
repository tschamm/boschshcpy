"""Short-poll vs push race and null-state tests (no hardware)."""

import asyncio
from unittest.mock import MagicMock

from boschshcpy.device_service import SHCDeviceService


def _svc(state=None, **extra):
    raw = {"id": "S", "deviceId": "d", "state": state, **extra}
    return SHCDeviceService(api=MagicMock(), raw_device_service=raw)


def _push(temp):
    return {
        "@type": "DeviceServiceData",
        "id": "S",
        "state": {"@type": "t", "temperature": temp},
    }


def test_short_poll_does_not_overwrite_newer_push():
    svc = _svc({"@type": "t", "temperature": 0})

    def slow_get(*_a):
        svc.process_long_polling_poll_result(_push(2))  # push lands mid-GET
        return {"id": "S", "state": {"@type": "t", "temperature": 1}}

    svc._api.get_device_service.side_effect = slow_get
    svc.short_poll()
    assert svc.state["temperature"] == 2


def test_async_short_poll_does_not_overwrite_newer_push():
    svc = _svc({"@type": "t", "temperature": 0})

    async def slow_get(*_a):
        svc.process_long_polling_poll_result(_push(2))
        return {"id": "S", "state": {"@type": "t", "temperature": 1}}

    svc._api.get_device_service = slow_get
    asyncio.run(svc.async_short_poll())
    assert svc.state["temperature"] == 2


def test_short_poll_applies_when_no_push():
    svc = _svc({"@type": "t", "temperature": 0})
    svc._api.get_device_service.return_value = {
        "id": "S",
        "state": {"@type": "t", "temperature": 1},
    }
    svc.short_poll()
    assert svc.state["temperature"] == 1


def test_null_state_construction_and_refresh():
    svc = _svc(None)
    assert svc.state == {}
    svc2 = _svc({"@type": "t", "temperature": 3})
    svc2._api.get_device_service.return_value = {"id": "S", "state": None}
    svc2.short_poll()
    assert svc2.state == {"@type": "t", "temperature": 3}
