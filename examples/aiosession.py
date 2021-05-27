import asyncio
import aiohttp

from datetime import datetime
import os
import sys
import logging
import logging.config

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from boschshcpy import SHCSession, SHCDeviceHelper

logger = logging.getLogger("boschshcpy")
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,  # this fixes the problem
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "boschshcpy": {"handlers": ["default"], "level": "DEBUG", "propagate": True}
        },
    }
)


async def main():
    async with aiohttp.ClientSession() as session:
        await run(session)


async def run(websession):
    session = SHCSession(
        controller_ip="192.168.1.6",
        certificate="../keystore/dev-cert.pem",
        key="../keystore/dev-key.pem",
    )
    await session.init(websession)

    for device in session.devices:
        device.summary()

    session.information.summary()

    try:
        # await session.start_polling()
        async for updated_object in session.start_polling():
            print(datetime.now().strftime("%H:%M:%S"), end=" ")
            print("{}: {}".format(type(updated_object).__name__, updated_object))
    except GeneratorExit:
        pass


try:
    asyncio.get_event_loop().run_until_complete(main())
except KeyboardInterrupt:
    pass
