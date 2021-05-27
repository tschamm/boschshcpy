import asyncio
import json
import logging
import threading
import time
import typing
from collections import defaultdict

from aiohttp import client_exceptions

from .api import SHCAPI, JSONRPCError
from .device import SHCDevice
from .device_helper import SHCDeviceHelper
from .domain_impl import SHCIntrusionSystem
from .exceptions import SHCAuthenticationError, SHCConnectionError, SHCSessionError
from .information import SHCInformation
from .room import SHCRoom
from .scenario import SHCScenario
from .services_impl import SUPPORTED_DEVICE_SERVICE_IDS

logger = logging.getLogger("boschshcpy")


class SHCSession:
    def __init__(self, controller_ip: str, certificate, key):
        # API
        self._api = SHCAPI(
            controller_ip=controller_ip, certificate=certificate, key=key
        )
        self._device_helper = SHCDeviceHelper(self._api)

        # Subscription status
        self._poll_id = None

        # SHC Information
        self._shc_information = None

        # All devices
        self._rooms_by_id = {}
        self._scenarios_by_id = {}
        self._devices_by_id = {}
        self._services_by_device_id = defaultdict(list)
        self._domains_by_id = {}

        self._polling_thread = None
        self._stop_polling_thread = False

        # Stop polling function
        self.reset_connection_listener = None

        self._callback = None

    async def init(self, websession, authenticate=True):
        await self._api.init(websession)

        pub_info = await self._api.async_get_public_information()
        if pub_info == None:
            raise SHCConnectionError

        self._shc_information = SHCInformation(pub_info=pub_info)

        if authenticate:
            await self._async_enumerate_all()

    async def _async_enumerate_all(self):
        await self.authenticate()
        self.cleanup()

        await self._async_enumerate_services()
        await self._async_enumerate_devices()
        await self._async_enumerate_rooms()
        await self._async_enumerate_scenarios()
        await self._async_initialize_domains()

    async def authenticate(self):
        auth_info = await self._api.async_get_information()
        if auth_info == None:
            raise SHCAuthenticationError

    def cleanup(self):
        self._rooms_by_id = {}
        self._scenarios_by_id = {}
        self._devices_by_id = {}
        self._services_by_device_id = defaultdict(list)
        self._domains_by_id = {}

    @property
    def information(self) -> SHCInformation:
        return self._shc_information

    @property
    def api(self):
        return self._api

    def _add_device(self, raw_device):
        device_id = raw_device["id"]

        if not self._services_by_device_id[device_id]:
            logger.debug(
                f"Skipping device id {device_id} which has no services that are supported by this library"
            )
            return

        self._devices_by_id[device_id] = self._device_helper.device_init(
            raw_device, self._services_by_device_id[device_id]
        )

    def _update_device(self, raw_device):
        device_id = raw_device["id"]
        self._devices_by_id[device_id].update_raw_information(raw_device)

    async def _async_enumerate_services(self):
        raw_services = await self._api.async_get_services()
        for service in raw_services:
            if service["id"] not in SUPPORTED_DEVICE_SERVICE_IDS:
                continue
            device_id = service["deviceId"]
            self._services_by_device_id[device_id].append(service)

    async def _async_enumerate_devices(self):
        raw_devices = await self._api.async_get_devices()

        for raw_device in raw_devices:
            self._add_device(raw_device)

    async def _async_enumerate_rooms(self):
        raw_rooms = await self._api.async_get_rooms()
        for raw_room in raw_rooms:
            room_id = raw_room["id"]
            room = SHCRoom(raw_room=raw_room)
            self._rooms_by_id[room_id] = room

    async def _async_enumerate_scenarios(self):
        raw_scenarios = await self._api.async_get_scenarios()
        for raw_scenario in raw_scenarios:
            scenario_id = raw_scenario["id"]
            scenario = SHCScenario(api=self._api, raw_scenario=raw_scenario)
            self._scenarios_by_id[scenario_id] = scenario

    async def _async_initialize_domains(self):
        raw_ids_domain = await self._api.async_get_domain_intrusion_detection()
        self._domains_by_id["IDS"] = SHCIntrusionSystem(self._api, raw_ids_domain)

    async def _async_long_poll(self, wait_seconds=10):
        if self._poll_id is None:
            self._poll_id = await self.api.async_long_polling_subscribe()
            logger.debug(f"Subscribed for long poll. Poll id: {self._poll_id}")
        try:
            raw_results = await self.api.async_long_polling_poll(
                self._poll_id, wait_seconds
            )
            for raw_result in raw_results:
                self._process_long_polling_poll_result(raw_result)

            return True
        except JSONRPCError as json_rpc_error:
            if json_rpc_error.code == -32001:
                self._poll_id = None
                logger.warning(
                    f"SHC claims unknown poll id. Invalidating poll id and trying resubscribe next time..."
                )
                return False
            else:
                raise json_rpc_error

    def _process_long_polling_poll_result(self, raw_result):
        logger.debug(f"Received event: {raw_result}")
        if raw_result["@type"] == "DeviceServiceData":
            device_id = raw_result["deviceId"]
            if device_id in self._devices_by_id.keys():
                device = self._devices_by_id[device_id]
                device.process_long_polling_poll_result(raw_result)
            else:
                logger.debug(
                    f"Skipping polling result with unknown device id {device_id}."
                )
            return raw_result
        if raw_result["@type"] == "message":
            assert "arguments" in raw_result
            if "deviceServiceDataModel" in raw_result["arguments"]:
                raw_data_model = json.loads(
                    raw_result["arguments"]["deviceServiceDataModel"]
                )
                self._process_long_polling_poll_result(raw_data_model)
            return raw_result
        if raw_result["@type"] == "scenarioTriggered":
            if self._callback is not None:
                self._callback(
                    raw_result["id"],
                    raw_result["name"],
                    raw_result["lastTimeTriggered"],
                )
            return raw_result
        if raw_result["@type"] == "device":
            device_id = raw_result["id"]
            if device_id in self._devices_by_id.keys():
                self._update_device(raw_result)
                if (
                    "deleted" in raw_result and raw_result["deleted"] == True
                ):  # Device deleted
                    # inform on deleted device
                    logger.debug("Deleting device with id %s", device_id)
                    self._devices_by_id.pop(device_id, None)
            else:  # New device registered
                logger.debug("Found new device with id %s", device_id)
                self._add_device(raw_result)
                # inform on new device
            return raw_result
        if raw_result["@type"] in SHCIntrusionSystem.DOMAIN_STATES:
            if self.intrusion_system is not None:
                self.intrusion_system.process_long_polling_poll_result(raw_result)
            return raw_result
        return raw_result

    async def _async_maybe_unsubscribe(self):
        if self._poll_id is not None:
            await self.api.async_long_polling_unsubscribe(self._poll_id)
            logger.debug(f"Unsubscribed from long poll w/ poll id {self._poll_id}")
            self._poll_id = None

    async def start_polling(self):
        pending_events = asyncio.Queue()

        async def receive_events():
            while True:
                if self._poll_id is None:
                    self._poll_id = await self.api.async_long_polling_subscribe()
                    logger.debug(f"Subscribed for long poll. Poll id: {self._poll_id}")
                try:
                    for raw_result in await self.api.async_long_polling_poll(
                        self._poll_id, 360
                    ):
                        pending_events.put_nowait(raw_result)

                except JSONRPCError as json_rpc_error:
                    if json_rpc_error.code == -32001:
                        self._poll_id = None
                        logger.warning(
                            f"SHC claims unknown poll id. Invalidating poll id and trying re-subscribe next time..."
                        )
                    else:
                        raise json_rpc_error
                except client_exceptions.ServerDisconnectedError:
                    logger.debug("Polling endpoint disconnected")
                except client_exceptions.ClientError as err:
                    if isinstance(err, client_exceptions.ClientResponseError):
                        # We get 503 when it's too busy, but any other error
                        # is probably also because too busy.
                        logger.debug(
                            "Got status %s from endpoint. Sleeping while waiting to resolve",
                            err.status,
                        )
                    else:
                        logger.debug("Unable to reach event endpoint: %s", err)

                    await asyncio.sleep(5)
                except asyncio.TimeoutError:
                    pass
                except asyncio.CancelledError:
                    logger.debug(f"Unsubscribing from long poll")
                    await self._async_maybe_unsubscribe()
                except Exception:
                    logger.exception("Unexpected error")
                    pending_events.put(None)
                    break

        event_task = asyncio.create_task(receive_events())

        while True:
            try:
                event = await pending_events.get()
            except asyncio.CancelledError:
                logger.debug("Cancel processing events")
                event_task.cancel()
                await event_task
                raise

            # If unexpected error occurred
            if event is None:
                return

            yield self._process_long_polling_poll_result(event)

    def subscribe_scenario_callback(self, callback):
        self._callback = callback

    def unsubscribe_scenario_callback(self):
        self._callback = None

    @property
    def devices(self) -> typing.Sequence[SHCDevice]:
        return list(self._devices_by_id.values())

    def device(self, device_id) -> SHCDevice:
        return self._devices_by_id[device_id]

    @property
    def rooms(self) -> typing.Sequence[SHCRoom]:
        return list(self._rooms_by_id.values())

    def room(self, room_id) -> SHCRoom:
        if room_id is not None:
            return self._rooms_by_id[room_id]

        return SHCRoom({"id": "n/a", "name": "n/a", "iconId": "0"})

    @property
    def scenarios(self) -> typing.Sequence[SHCScenario]:
        return list(self._scenarios_by_id.values())

    @property
    def scenario_names(self) -> typing.Sequence[str]:
        scenario_names = []
        for scenario in self.scenarios:
            scenario_names.append(scenario.name)
        return scenario_names

    def scenario(self, scenario_id) -> SHCScenario:
        return self._scenarios_by_id[scenario_id]

    @property
    def intrusion_system(self) -> SHCIntrusionSystem:
        return self._domains_by_id["IDS"]

    @property
    def device_helper(self) -> SHCDeviceHelper:
        return self._device_helper
