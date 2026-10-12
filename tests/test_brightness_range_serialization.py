"""Sequential brightness-range writes must not undo each other (no hardware)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from boschshcpy.services_impl import DimmerConfigurationService


def _svc():
    raw = {
        "id": "DimmerConfiguration",
        "deviceId": "d",
        "state": {
            "@type": "dimmerConfigurationState",
            "brightnessRange": {"minBrightness": 10, "maxBrightness": 90},
        },
    }
    svc = DimmerConfigurationService(api=MagicMock(), raw_device_service=raw)
    svc.async_put_state = AsyncMock()
    return svc


def test_sequential_min_then_max_keeps_both():
    svc = _svc()

    async def go():
        await svc.async_set_brightness_range(min_brightness=20)
        await svc.async_set_brightness_range(max_brightness=80)

    asyncio.run(go())
    sent = [c.args[0]["brightnessRange"] for c in svc.async_put_state.await_args_list]
    assert sent == [
        {"minBrightness": 20, "maxBrightness": 90},
        {"minBrightness": 20, "maxBrightness": 80},
    ]


def test_concurrent_min_and_max_keep_both():
    svc = _svc()

    async def go():
        await asyncio.gather(
            svc.async_set_brightness_range(min_brightness=20),
            svc.async_set_brightness_range(max_brightness=80),
        )

    asyncio.run(go())
    last = svc.async_put_state.await_args_list[-1].args[0]["brightnessRange"]
    assert last == {"minBrightness": 20, "maxBrightness": 80}


def test_push_state_supersedes_written_bounds():
    svc = _svc()

    async def go():
        await svc.async_set_brightness_range(min_brightness=20)
        svc.process_long_polling_poll_result(
            {
                "@type": "DeviceServiceData",
                "id": "DimmerConfiguration",
                "state": {
                    "@type": "dimmerConfigurationState",
                    "brightnessRange": {"minBrightness": 5, "maxBrightness": 95},
                },
            }
        )
        await svc.async_set_brightness_range(max_brightness=80)

    asyncio.run(go())
    last = svc.async_put_state.await_args_list[-1].args[0]["brightnessRange"]
    assert last == {"minBrightness": 5, "maxBrightness": 80}


def test_push_during_write_await_supersedes_written_bounds():
    svc = _svc()

    async def put(*_a, **_k):
        # push arrives while the PUT is in flight
        svc.process_long_polling_poll_result(
            {
                "@type": "DeviceServiceData",
                "id": "DimmerConfiguration",
                "state": {
                    "@type": "dimmerConfigurationState",
                    "brightnessRange": {"minBrightness": 5, "maxBrightness": 95},
                },
            }
        )

    svc.async_put_state = AsyncMock(side_effect=put)

    async def go():
        await svc.async_set_brightness_range(min_brightness=20)
        await svc.async_set_brightness_range(max_brightness=80)

    asyncio.run(go())
    last = svc.async_put_state.await_args_list[-1].args[0]["brightnessRange"]
    assert last == {"minBrightness": 5, "maxBrightness": 80}
