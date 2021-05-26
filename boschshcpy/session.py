import asyncio
import json
import logging
import threading
import time
import typing
from collections import defaultdict

from .api import SHCAPI, JSONRPCError
from .device import SHCDevice
from .device_helper import SHCDeviceHelper
from .domain_impl import SHCIntrusionSystem
from .exceptions import SHCAuthenticationError, SHCSessionError, SHCConnectionError
from .information import SHCInformation
from .room import SHCRoom
from .scenario import SHCScenario
from .services_impl import SUPPORTED_DEVICE_SERVICE_IDS

logger = logging.getLogger("boschshcpy")


class SHCSession:
    def __init__(self, controller_ip: str, certificate, key, zeroconf=None):
        # API
        self._api = SHCAPI(
            controller_ip=controller_ip, certificate=certificate, key=key
        )
        self._device_helper = SHCDeviceHelper(self._api)

        # Subscription status
        self._poll_id = None

        # SHC Information
        self._shc_information = None
        self._zeroconf = zeroconf

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

    async def auth_init(self, websession, lazy=False):
        await self._api.init(websession)

        pub_info = await self._api.async_get_public_information()
        if pub_info == None:
            raise SHCConnectionError

        auth_info = await self._api.async_get_information()
        if auth_info == None:
            raise SHCAuthenticationError

        self._shc_information = SHCInformation(pub_info=pub_info)

        if not lazy:
            await self._async_enumerate_all()

    async def _async_enumerate_all(self):
        await self._async_enumerate_services()
        await self._async_enumerate_devices()
        await self._async_enumerate_rooms()
        await self._async_enumerate_scenarios()
        await self._async_initialize_domains()
        print("Enumerate end")

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

    def _long_poll(self, wait_seconds=10):
        if self._poll_id is None:
            self._poll_id = self.api.long_polling_subscribe()
            logger.debug(f"Subscribed for long poll. Poll id: {self._poll_id}")
        try:
            raw_results = self.api.long_polling_poll(self._poll_id, wait_seconds)
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

    def _maybe_unsubscribe(self):
        if self._poll_id is not None:
            self.api.long_polling_unsubscribe(self._poll_id)
            logger.debug(f"Unsubscribed from long poll w/ poll id {self._poll_id}")
            self._poll_id = None

    def _process_long_polling_poll_result(self, raw_result):
        logger.debug(f"Long poll: {raw_result}")
        if raw_result["@type"] == "DeviceServiceData":
            device_id = raw_result["deviceId"]
            if device_id in self._devices_by_id.keys():
                device = self._devices_by_id[device_id]
                device.process_long_polling_poll_result(raw_result)
            else:
                logger.debug(
                    f"Skipping polling result with unknown device id {device_id}."
                )
            return
        if raw_result["@type"] == "message":
            assert "arguments" in raw_result
            if "deviceServiceDataModel" in raw_result["arguments"]:
                raw_data_model = json.loads(
                    raw_result["arguments"]["deviceServiceDataModel"]
                )
                self._process_long_polling_poll_result(raw_data_model)
            return
        if raw_result["@type"] == "scenarioTriggered":
            if self._callback is not None:
                self._callback(
                    raw_result["id"],
                    raw_result["name"],
                    raw_result["lastTimeTriggered"],
                )
            return
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
            return
        if raw_result["@type"] in SHCIntrusionSystem.DOMAIN_STATES:
            if self.intrusion_system is not None:
                self.intrusion_system.process_long_polling_poll_result(raw_result)
            return
        return

    def start_polling(self):
        if self._polling_thread is None:

            def polling_thread_main():
                while not self._stop_polling_thread:
                    try:
                        if not self._long_poll():
                            logger.warning(
                                "_long_poll returned False. Waiting 1 second."
                            )
                            time.sleep(1.0)
                    except RuntimeError as err:
                        self._stop_polling_thread = True
                        logger.info(
                            "Stopping polling thread after expected runtime error."
                        )
                        logger.info(f"Error description: {err}. {err.args}")
                        logger.info(f"Attempting unsubscribe...")
                        try:
                            self._maybe_unsubscribe()
                        except Exception as ex:
                            logger.info(f"Unsubscribe not successful: {ex}")

                    except Exception as ex:
                        logger.error(
                            f"Error in polling thread: {ex}. Waiting 15 seconds."
                        )
                        time.sleep(15.0)

            self._polling_thread = threading.Thread(
                target=polling_thread_main, name="SHCPollingThread"
            )
            self._polling_thread.start()

        else:
            raise SHCSessionError("Already polling!")

    def stop_polling(self):
        if self._polling_thread is not None:
            logger.debug(f"Unsubscribing from long poll")
            self._stop_polling_thread = True
            self._polling_thread.join()

            self._maybe_unsubscribe()
            self._polling_thread = None
            self._poll_id = None
        else:
            raise SHCSessionError("Not polling!")

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

        return SHCRoom(self.api, {"id": "n/a", "name": "n/a", "iconId": "0"})

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

    def authenticate(self):
        self._shc_information = SHCInformation(api=self._api, zeroconf=self._zeroconf)

    def mdns_info(self) -> SHCInformation:
        return SHCInformation(
            api=self._api, authenticate=False, zeroconf=self._zeroconf
        )

    @property
    def information(self) -> SHCInformation:
        return self._shc_information

    @property
    def intrusion_system(self) -> SHCIntrusionSystem:
        return self._domains_by_id["IDS"]

    @property
    def api(self):
        return self._api

    @property
    def device_helper(self) -> SHCDeviceHelper:
        return self._device_helper
