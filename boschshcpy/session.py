import typing
import logging
import threading
import time
import sys

from .api import SHCAPI, JSONRPCError
from .device import SHCDevice
from .room import SHCRoom
from .scenario import SHCScenario
from .information import SHCInformation
from .services_impl import SUPPORTED_DEVICE_SERVICE_IDS
from .device_helper import SHCDeviceHelper

logger = logging.getLogger("boschshcpy")


class SHCSession:
    def __init__(self, controller_ip: str, certificate, key, enumerate = True):
        # API
        self._api = SHCAPI(controller_ip=controller_ip, certificate=certificate, key=key)
        self._device_helper = SHCDeviceHelper(self._api)

        # Subscription status
        self._poll_id = None

        # SHC Information
        self._shc_information = None

        # All devices
        self._rooms_by_id = {}
        self._scenarios_by_id = {}
        self._devices_by_id = {}

        self._get_information()

        if enumerate: self._enumerate_all()

        self._polling_thread = None
        self._stop_polling_thread = False

    def _enumerate_all(self):
        self._enumerate_devices()
        self._enumerate_rooms()
        self._enumerate_scenarios()
        self._get_information()

    def _enumerate_devices(self):
        raw_devices = self._api.get_devices()

        for raw_device in raw_devices:
            device_id = raw_device['id']

            if set(raw_device['deviceServiceIds']).isdisjoint(SUPPORTED_DEVICE_SERVICE_IDS):
                logger.debug(f"Skipping device id {device_id} which has no services that are supported by this library")
                continue
            
            self._devices_by_id[device_id] = self._device_helper.device_init(raw_device)

    def _enumerate_rooms(self):
        raw_rooms = self._api.get_rooms()
        for raw_room in raw_rooms:
            room_id = raw_room["id"]
            room = SHCRoom(api=self._api, raw_room=raw_room)
            self._rooms_by_id[room_id] = room

    def _enumerate_scenarios(self):
        raw_scenarios = self._api.get_scenarios()
        for raw_scenario in raw_scenarios:
            scenario_id = raw_scenario["id"]
            scenario = SHCScenario(api=self._api, raw_scenario=raw_scenario)
            self._scenarios_by_id[scenario_id] = scenario

    def _get_information(self):
        raw_information = self._api.get_shcinformation()
        self._shc_information = SHCInformation(api=self._api, raw_information=raw_information)

    def _long_poll(self, wait_seconds=30):
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
                logger.warning(f"SHC claims unknown poll id. Invalidating poll id and trying resubscribe next time...")
                return False
            else:
                raise json_rpc_error

    def _maybe_unsubscribe(self):
        if self._poll_id is not None:
            self.api.long_polling_unsubscribe(self._poll_id)

    def _process_long_polling_poll_result(self, raw_result):
        if raw_result["@type"] != "DeviceServiceData":
            # Skipping polling results of type message, device or unknown type
            return
        device_id = raw_result["deviceId"]
        if device_id in self._devices_by_id.keys():
            device = self._devices_by_id[device_id]
            device.process_long_polling_poll_result(raw_result)
        else:
            logger.debug(f"Skipping polling result with unknown device id {device_id}.")
    
    def start_polling(self):
        if self._polling_thread is None:
            def polling_thread_main():
                while not self._stop_polling_thread:
                    try:
                        if not self._long_poll():
                            logging.warning("_long_poll returned False. Waiting 1 second.")
                            time.sleep(1.0)
                    except RuntimeError as err:
                        self._stop_polling_thread = True
                        logging.info("Stopping polling thread after expected runtime error.")
                        logging.info(f"Error description: {err}. {err.args}")
                        logging.info(f"Attempting unsubscribe...")
                        try:
                            self._maybe_unsubscribe()
                        except Exception as ex:
                            logging.info(f"Unsubscribe unsuccessful: {ex}")

                    except Exception as ex:
                        logging.error(f"Error in polling thread: {ex}. Waiting 15 seconds.")
                        time.sleep(15.0)

            self._polling_thread = threading.Thread(target=polling_thread_main, name="SHCPollingThread")
            self._polling_thread.start()

        else:
            raise ValueError("Already polling!")

    def stop_polling(self):
        if self._polling_thread is not None:
            self._stop_polling_thread = True
            self._polling_thread.join()

            self._maybe_unsubscribe()
            self._polling_thread = None
            self._poll_id = None
        else:
            raise ValueError("Not polling!")

    def reinitialize(self):
        reinit_polling = False
        if self._polling_thread is not None:
            self.stop_polling()
            reinit_polling = True

        self._shc_information = None

        self._rooms_by_id = {}
        self._scenarios_by_id = {}
        self._devices_by_id = {}

        self._get_information()
        self._enumerate_all()

        if reinit_polling:
            self.start_polling()

    @property
    def devices(self) -> typing.Sequence[SHCDevice]:
        return list(self._devices_by_id.values())

    def device(self, device_id) -> SHCDevice:
        return self._devices_by_id[device_id]

    @property
    def rooms(self) -> typing.Sequence[SHCRoom]:
        return list(self._rooms_by_id.values())

    def room(self, room_id) -> SHCRoom:
        return self._rooms_by_id[room_id]

    @property
    def scenarios(self) -> typing.Sequence[SHCScenario]:
        return list(self._scenarios_by_id.values())

    def scenario(self, scenario_id) -> SHCScenario:
        return self._scenarios_by_id[scenario_id]

    @property
    def information(self) -> SHCInformation:
        return self._shc_information
    
    @property
    def api(self):
        return self._api

    @property
    def device_helper(self):
        return self._device_helper
