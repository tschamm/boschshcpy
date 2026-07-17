from __future__ import annotations

import json
import logging
import threading
import time
import typing
from collections import defaultdict
from collections.abc import Callable
from typing import Any, cast

from .api import SHCAPI
from .api import JSONRPCError as JSONRPCError  # noqa: F401 -- explicit re-export
from .automation import SHCAutomationRule
from .device import SHCDevice
from .device_helper import SHCDeviceHelper
from .domain_impl import SHCIntrusionSystem, SHCWaterAlarmSystem
from .exceptions import SHCConnectionError, SHCException, SHCSessionError
from .information import SHCInformation
from .room import SHCRoom
from .scenario import SHCScenario
from .message import SHCMessage
from .emma import SHCEmma
from .userdefinedstate import SHCUserDefinedState
from .services_impl import SUPPORTED_DEVICE_SERVICE_IDS
from .zigbee_routing import SHCZigbeeRoutingInfo

logger = logging.getLogger("boschshcpy")


class SHCSession:
    def __init__(
        self,
        controller_ip: str,
        certificate: str,
        key: str,
        lazy: bool = False,
        zeroconf: Any = None,
        long_poll_timeout: int = 10,
        verify_hostname: bool = False,
        ssl_verify: bool = True,
    ) -> None:
        # API
        self._long_poll_timeout = long_poll_timeout
        self._api = SHCAPI(
            controller_ip=controller_ip,
            certificate=certificate,
            key=key,
            verify_hostname=verify_hostname,
            ssl_verify=ssl_verify,
        )
        self._device_helper = SHCDeviceHelper(self._api)

        # Subscription status
        self._poll_id: str | None = None

        # SHC Information
        self._shc_information: SHCInformation | None = None
        self._zeroconf: Any = zeroconf

        # All devices
        self._rooms_by_id: dict[str, SHCRoom] = {}
        self._scenarios_by_id: dict[str, SHCScenario] = {}
        self._automation_rules_by_id: dict[str, SHCAutomationRule] = {}
        self._devices_by_id: dict[str, SHCDevice] = {}
        self._services_by_device_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
        # Guards _devices_by_id / _services_by_device_id. The SHCPollingThread
        # is the sole mutator (device add/update/delete during long-poll
        # processing), but `devices`/`device()` are read from other threads
        # (e.g. HA's executor). Without this, a mutation racing a concurrent
        # `.values()` iteration can raise "dictionary changed size during
        # iteration" in the READING thread. RLock (not Lock) so a callback
        # invoked while the polling thread still holds the lock — or any
        # future nested acquire on the same thread — can't self-deadlock;
        # callers still release the lock before invoking subscriber/device
        # callbacks wherever practical to keep the critical section short.
        self._devices_lock = threading.RLock()
        self._domains_by_id: dict[str, Any] = {}
        self._messages_by_id: dict[str, SHCMessage] = {}
        self._userdefinedstates_by_id: dict[str, SHCUserDefinedState] = {}
        self._subscribers: list[Any] = []
        self._emma: SHCEmma = SHCEmma(self._api)

        if not lazy:
            self._enumerate_all()

        self._polling_thread: threading.Thread | None = None
        self._stop_polling_thread: bool = False

        # Stop polling function
        self.reset_connection_listener: Callable[[], None] | None = None

        self._scenario_callbacks: dict[str, Callable[..., Any]] = {}
        self._userdefinedstate_callbacks: dict[str, list[Callable[[], None]]] = (
            defaultdict(list)
        )

    def _enumerate_all(self) -> None:
        self.authenticate()
        self._enumerate_services()
        self._enumerate_devices()
        self._enumerate_rooms()
        self._enumerate_scenarios()
        self._enumerate_automation_rules()
        self._enumerate_messages()
        self._enumerate_userdefinedstates()
        self._initialize_domains()
        self._initialize_emma()

    def _add_device(
        self, raw_device: dict[str, Any], update_services: bool = False
    ) -> SHCDevice | None:
        device_id = raw_device["id"]

        if update_services:
            with self._devices_lock:
                self._services_by_device_id.pop(device_id, None)
            # I/O — deliberately outside the lock.
            raw_services = self._api.get_device_services(device_id)
            with self._devices_lock:
                for service in raw_services:
                    if service["id"] not in SUPPORTED_DEVICE_SERVICE_IDS:
                        continue
                    device_id = service["deviceId"]
                    self._services_by_device_id[device_id].append(service)

        with self._devices_lock:
            services = list(self._services_by_device_id[device_id])

        if not services:
            logger.debug(
                f"Skipping device id {device_id} which has no services that are supported by this library"
            )
            return None

        device = self._device_helper.device_init(raw_device, services)
        with self._devices_lock:
            self._devices_by_id[device_id] = device
        return device

    def _update_device(self, raw_device: dict[str, Any]) -> None:
        device_id = str(raw_device["id"])
        with self._devices_lock:
            device = self._devices_by_id[device_id]
        device.update_raw_information(raw_device)

    def _enumerate_services(self) -> None:
        raw_services = self._api.get_services()
        for service in raw_services:
            if service["id"] not in SUPPORTED_DEVICE_SERVICE_IDS:
                continue
            device_id = service["deviceId"]
            self._services_by_device_id[device_id].append(service)

    def _enumerate_devices(self) -> None:
        raw_devices = self._api.get_devices()

        for raw_device in raw_devices:
            self._add_device(raw_device)

    def _enumerate_rooms(self) -> None:
        raw_rooms = self._api.get_rooms()
        for raw_room in raw_rooms:
            room_id = raw_room["id"]
            room = SHCRoom(api=self._api, raw_room=raw_room)
            self._rooms_by_id[room_id] = room

    def _enumerate_scenarios(self) -> None:
        raw_scenarios = self._api.get_scenarios()
        for raw_scenario in raw_scenarios:
            scenario_id = raw_scenario["id"]
            scenario = SHCScenario(api=self._api, raw_scenario=raw_scenario)
            self._scenarios_by_id[scenario_id] = scenario

    def _enumerate_automation_rules(self) -> None:
        raw_rules = self._api.get_automation_rules()
        for raw_rule in raw_rules:
            self._automation_rules_by_id[raw_rule["id"]] = SHCAutomationRule(
                api=self._api, raw_rule=raw_rule
            )

    def refresh_automation_rules(self) -> None:
        """Re-fetch every automation rule's current state (enabled/etc.).

        Rules aren't part of the long-poll device-service push model, so
        callers (e.g. HA's should_poll entities) must call this explicitly.
        """
        raw_rules = self._api.get_automation_rules()
        for raw_rule in raw_rules:
            rule_id = raw_rule["id"]
            if rule_id in self._automation_rules_by_id:
                self._automation_rules_by_id[rule_id].update_raw_rule(raw_rule)
            else:
                self._automation_rules_by_id[rule_id] = SHCAutomationRule(
                    api=self._api, raw_rule=raw_rule
                )

    def _enumerate_messages(self) -> None:
        raw_messages = self._api.get_messages()
        for raw_message in raw_messages:
            message_id = raw_message["id"]
            message = SHCMessage(api=self._api, raw_message=raw_message)
            self._messages_by_id[message_id] = message

    def _enumerate_userdefinedstates(self) -> None:
        raw_states = self._api.get_userdefinedstates()
        for raw_state in raw_states:
            userdefinedstate_id = raw_state["id"]
            userdefinedstate = SHCUserDefinedState(
                api=self._api,
                info=self.information,
                raw_state=raw_state,
            )
            self._userdefinedstates_by_id[userdefinedstate_id] = userdefinedstate

    def _initialize_domains(self) -> None:
        self._domains_by_id["IDS"] = SHCIntrusionSystem(
            self._api,
            self._api.get_domain_intrusion_detection(),
            self.information.macAddress,
        )
        try:
            raw_water_alarm_state = self._api.get_water_alarm_system_state()
        except SHCException as ex:
            # installations without any water-leak sensors may not expose
            # this domain at all; degrade rather than failing session setup.
            logger.debug("Water alarm system domain unavailable: %s", ex)
        else:
            self._domains_by_id["WATERALARM"] = SHCWaterAlarmSystem(
                self._api, raw_water_alarm_state, self.information.macAddress
            )

    def _initialize_emma(self) -> None:
        self._emma = SHCEmma(self._api, self._shc_information, None)

    def _long_poll(self, wait_seconds: int | None = None) -> bool:
        if wait_seconds is None:
            wait_seconds = self._long_poll_timeout
        resubscribed = False
        if self._poll_id is None:
            self._poll_id = self.api.long_polling_subscribe()
            logger.debug(f"Subscribed for long poll. Poll id: {self._poll_id}")
            resubscribed = True
        try:
            raw_results = self.api.long_polling_poll(self._poll_id, wait_seconds)
            for raw_result in raw_results:
                self._process_long_polling_poll_result(raw_result)

            if resubscribed:
                # hass#370: bulk-refresh every device's own top-level info (in
                # particular `status`) before the service-level short-poll
                # below — see session_async.py's mirror of this block for the
                # full root-cause writeup. Without this, a device that went
                # UNDEFINED during the gap and later reconnected would keep
                # reporting stale availability indefinitely.
                try:
                    raw_devices = self.api.get_devices()
                except Exception as ex:  # noqa: BLE001
                    logger.warning(
                        "Failed to fetch device list after resubscribe: %s",
                        ex,
                    )
                    raw_devices = []
                for raw_device in raw_devices:
                    device = self._devices_by_id.get(raw_device.get("id"))
                    if device is None:
                        continue
                    try:
                        device.update_raw_information(raw_device)
                    except Exception as ex:  # noqa: BLE001
                        logger.warning(
                            "Failed to refresh device status for %s after "
                            "resubscribe: %s",
                            raw_device.get("id"),
                            ex,
                        )

                # Refresh all device-service states after a poll-id resubscribe
                # (#183): the SHC invalidates poll IDs roughly every 24 h; any
                # device state that changed during the gap is not delivered in the
                # next long-poll response.  Calling device.update() issues a
                # short-poll (GET /devices/<id>/services/<svc>) for every
                # registered service so listeners receive current state.  This
                # runs on the SHCPollingThread — no event-loop involvement.
                logger.debug(
                    "Poll-id resubscribed — refreshing %d device(s) via short-poll (#183)",
                    len(self._devices_by_id),
                )
                for device in list(self._devices_by_id.values()):
                    try:
                        # fire_callbacks=True so listeners (HA entity closures)
                        # are notified of any state that changed during the
                        # poll-id gap (#183).  The ordinary HA poll path calls
                        # device.update() without this flag and stays quiet.
                        device.update(fire_callbacks=True)
                    except Exception as ex:  # noqa: BLE001
                        logger.warning(
                            "Short-poll refresh failed for device %s after resubscribe: %s",
                            device.id,
                            ex,
                        )

            return True
        except JSONRPCError as json_rpc_error:
            # Any JSON-RPC-level error on the poll call means this poll_id is
            # no longer usable -- reusing it would just repeat the same error
            # every iteration. Previously only code -32001 invalidated
            # poll_id; any other code (e.g. an event-buffer-limit error) hit
            # the generic Exception handler in polling_thread_main, which
            # logs+sleeps but keeps the same dead poll_id, looping on the
            # same error forever instead of recovering via resubscribe.
            self._poll_id = None
            if json_rpc_error.code == -32001:
                logger.debug(
                    "SHC claims unknown poll id. Invalidating poll id and trying resubscribe next time..."
                )
            else:
                logger.warning(
                    "Long-poll request failed (code: %s, message: %s). "
                    "Invalidating poll id and resubscribing next time...",
                    json_rpc_error.code,
                    json_rpc_error.message,
                )
            return False

    def _maybe_unsubscribe(self) -> None:
        if self._poll_id is not None:
            self.api.long_polling_unsubscribe(self._poll_id)
            logger.debug(f"Unsubscribed from long poll w/ poll id {self._poll_id}")
            self._poll_id = None

    def _process_long_polling_poll_result(self, raw_result: dict[str, Any]) -> None:
        logger.debug(f"Long poll: {raw_result}")
        # .get() rather than direct indexing: a poll result (top-level or an
        # embedded deviceServiceDataModel recursed into below) missing "@type"
        # entirely used to raise KeyError and stall the poll thread for 15s
        # (chaos-testing finding, no live incident) -- treat it like any other
        # unrecognized type instead, since every branch below already no-ops
        # on a value it doesn't recognize.
        result_type = raw_result.get("@type")
        if result_type == "DeviceServiceData":
            device_id = raw_result["deviceId"]
            if device_id in self._devices_by_id:  # [S1]
                device = self._devices_by_id[device_id]
                device.process_long_polling_poll_result(raw_result)
            else:
                logger.debug(
                    f"Skipping polling result with unknown device id {device_id}."
                )
            return
        if result_type == "message":
            # The SHC can emit messages without "arguments" (e.g. during boot /
            # firmware update), with "arguments" present but not a dict, or
            # with "deviceServiceDataModel" present but not valid embedded
            # JSON (json.loads raising TypeError/JSONDecodeError); guard all
            # three instead of asserting so the poll thread survives.
            arguments = raw_result.get("arguments")
            device_service_data_model = (
                arguments.get("deviceServiceDataModel")
                if isinstance(arguments, dict)
                else None
            )
            if device_service_data_model is not None:
                try:
                    raw_data_model = json.loads(device_service_data_model)
                except (TypeError, ValueError) as ex:
                    logger.debug(
                        "Ignoring malformed embedded deviceServiceDataModel: %s", ex
                    )
                else:
                    self._process_long_polling_poll_result(raw_data_model)
            else:
                # callback is missing when receiving new message
                message_id = raw_result["id"]
                message = SHCMessage(api=self._api, raw_message=raw_result)
                self._messages_by_id[message_id] = message
            return
        if result_type == "scenarioTriggered":
            if raw_result["id"] in self._scenario_callbacks:
                self._scenario_callbacks[raw_result["id"]](raw_result)
            if (
                "shc" in self._scenario_callbacks
            ):  # deprecated for providing bosch_shc.event trigger callbacks
                self._scenario_callbacks["shc"](raw_result)
            return
        if result_type == "device":
            device_id = raw_result["id"]
            if device_id in self._devices_by_id:  # [S1]
                self._update_device(raw_result)
                if (
                    "deleted" in raw_result and raw_result["deleted"] is True
                ):  # Device deleted
                    logger.debug("Deleting device with id %s", device_id)
                    with self._devices_lock:
                        self._services_by_device_id.pop(device_id, None)
                        self._devices_by_id.pop(device_id, None)
            else:  # New device registered
                logger.debug("Found new device with id %s", device_id)
                new_device = self._add_device(raw_result, update_services=True)
                if new_device is not None:
                    for instance, callback in list(self._subscribers):
                        if isinstance(new_device, instance):
                            callback(new_device)
            return
        if result_type in SHCIntrusionSystem.DOMAIN_STATES:
            if self.intrusion_system is not None:
                self.intrusion_system.process_long_polling_poll_result(raw_result)
            return
        if result_type == "waterAlarmSystemState":
            if self.water_alarm_system is not None:
                self.water_alarm_system.process_long_polling_poll_result(raw_result)
            return
        if result_type == "userDefinedState":
            state_id = raw_result["id"]
            if state_id in self._userdefinedstates_by_id:
                self._userdefinedstates_by_id[state_id].update_raw_information(
                    raw_result
                )
            elif (info := self._shc_information) is not None:
                # Read the attribute, not the raising property: the poll
                # processor must never crash, whatever the session state.
                userdefinedstate = SHCUserDefinedState(
                    api=self._api,
                    info=info,
                    raw_state=raw_result,
                )
                self._userdefinedstates_by_id[state_id] = userdefinedstate
                for instance, callback in list(self._subscribers):
                    if isinstance(userdefinedstate, instance):
                        callback(userdefinedstate)
            if state_id in self._userdefinedstate_callbacks:
                for callback in list(self._userdefinedstate_callbacks[state_id]):
                    callback()
            return
        if result_type == "link":
            link_id = raw_result["id"]
            if link_id == "com.bosch.tt.emma.applink":
                self._emma.update_emma_data(raw_result)
        return

    def start_polling(self) -> None:
        if self._polling_thread is None:

            def polling_thread_main() -> None:
                try:
                    while not self._stop_polling_thread:
                        try:
                            if not self._long_poll():
                                logger.debug(
                                    "_long_poll returned False. Waiting 1 second."
                                )
                                time.sleep(1.0)
                        except RuntimeError as err:
                            self._stop_polling_thread = True
                            logger.debug(
                                "Stopping polling thread after expected runtime error."
                            )
                            logger.debug(f"Error description: {err}. {err.args}")
                            logger.debug("Attempting unsubscribe...")
                            try:
                                self._maybe_unsubscribe()
                            except Exception as ex:
                                logger.debug(f"Unsubscribe not successful: {ex}")

                        except Exception as ex:
                            logger.error(
                                f"Error in polling thread: {ex}. Waiting 15 seconds."
                            )
                            time.sleep(15.0)
                finally:
                    # Ensure the handle is cleared however the thread exits, so a
                    # dead thread (e.g. after the RuntimeError path above) doesn't
                    # permanently block start_polling() with "Already polling!".
                    # Deliberately NOT touching self._poll_id here: on a normal
                    # stop_polling() exit this `finally` runs (inside this thread)
                    # before join() returns, so clearing _poll_id here would make
                    # stop_polling()'s own _maybe_unsubscribe() a no-op (it's
                    # guarded on _poll_id is not None) — leaking the SHC-side
                    # long-poll subscription on every clean stop. _poll_id is
                    # already reset by the RuntimeError branch's own
                    # _maybe_unsubscribe() above when that path is taken, and by
                    # stop_polling() itself on the normal path.
                    self._polling_thread = None

            self._polling_thread = threading.Thread(
                target=polling_thread_main, name="SHCPollingThread", daemon=True
            )
            self._polling_thread.start()

        else:
            raise SHCSessionError("Already polling!")

    def stop_polling(self) -> None:
        # Capture a local reference: the thread's own finally-block can clear
        # self._polling_thread concurrently (e.g. after a RuntimeError), which
        # would otherwise turn the .join()/.is_alive() calls below into an
        # AttributeError on None.
        polling_thread = self._polling_thread
        if polling_thread is not None:
            logger.debug("Unsubscribing from long poll")
            self._stop_polling_thread = True
            # The polling thread may be blocked inside a long-poll HTTP call
            # (timeout = long_poll_timeout + 5). Bound the join so an in-flight
            # poll can't wedge HA shutdown for the full timeout; the daemon
            # thread is reaped by the interpreter if it outlives the join.
            polling_thread.join(timeout=self._long_poll_timeout + 10)
            if polling_thread.is_alive():
                logger.warning(
                    "Long-poll thread did not stop within %ss; it will be "
                    "reaped on interpreter exit",
                    self._long_poll_timeout + 10,
                )

            self._maybe_unsubscribe()
            self._polling_thread = None
            self._poll_id = None
        else:
            raise SHCSessionError("Not polling!")

    def subscribe(self, callback_tuple: Any) -> None:
        self._subscribers.append(callback_tuple)

    def subscribe_scenario_callback(
        self, scenario_id: str, callback: Callable[..., Any]
    ) -> None:
        self._scenario_callbacks[scenario_id] = callback

    def unsubscribe_scenario_callback(self, scenario_id: str) -> None:
        self._scenario_callbacks.pop(scenario_id, None)

    def subscribe_userdefinedstate_callback(
        self, userdefinedstate_id: str, callback: Callable[[], None]
    ) -> None:
        self._userdefinedstate_callbacks[userdefinedstate_id].append(callback)

    def unsubscribe_userdefinedstate_callbacks(self, userdefinedstate_id: str) -> None:
        self._userdefinedstate_callbacks.pop(userdefinedstate_id, None)

    @property
    def devices(self) -> typing.Sequence[SHCDevice]:
        # Called from other threads (e.g. HA's executor) while the
        # SHCPollingThread may be concurrently adding/removing devices —
        # snapshot under the lock, then release before returning.
        with self._devices_lock:
            return list(self._devices_by_id.values())

    def device(self, device_id: str) -> SHCDevice:
        with self._devices_lock:
            return self._devices_by_id[device_id]

    @property
    def rooms(self) -> typing.Sequence[SHCRoom]:
        return list(self._rooms_by_id.values())

    def room(self, room_id: str | None) -> SHCRoom:
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

    def scenario(self, scenario_id: str) -> SHCScenario:
        return self._scenarios_by_id[scenario_id]

    @property
    def automation_rules(self) -> typing.Sequence[SHCAutomationRule]:
        return list(self._automation_rules_by_id.values())

    def automation_rule(self, rule_id: str) -> SHCAutomationRule:
        return self._automation_rules_by_id[rule_id]

    @property
    def messages(self) -> typing.Sequence[SHCMessage]:
        return list(self._messages_by_id.values())

    @property
    def emma(self) -> SHCEmma:
        return self._emma

    @property
    def userdefinedstates(self) -> typing.Sequence[SHCUserDefinedState]:
        return list(self._userdefinedstates_by_id.values())

    def userdefinedstate(self, userdefinedstate_id: str) -> SHCUserDefinedState:
        return self._userdefinedstates_by_id[userdefinedstate_id]

    def get_zigbee_routing_info(self, device_id: str) -> SHCZigbeeRoutingInfo:
        """Fetch+parse Zigbee routing info for a device (on-demand, not cached)."""
        raw_routing_info = self._api.get_zigbee_routing_info(device_id)
        return SHCZigbeeRoutingInfo(raw_routing_info)

    def authenticate(self) -> None:
        self._shc_information = SHCInformation(api=self._api, zeroconf=self._zeroconf)
        if self._shc_information.unique_id is None:
            # The resolution chain (mDNS -> public macAddress -> ARP -> host)
            # exhausted every source; a controller without an identity cannot
            # be paired or addressed reliably.
            raise SHCConnectionError("Unable to resolve a unique id for the controller")

    def mdns_info(self) -> SHCInformation:
        return SHCInformation(
            api=self._api, authenticate=False, zeroconf=self._zeroconf
        )

    @property
    def information(self) -> SHCInformation:
        """The authenticated controller's information.

        Populated by authenticate(); a session constructed with ``lazy=True``
        must enumerate first.
        """
        if self._shc_information is None:
            raise SHCSessionError("Session is not authenticated")
        return self._shc_information

    @property
    def unique_id(self) -> str:
        """Stable controller identifier, validated during authenticate()."""
        unique_id = self.information.unique_id
        if unique_id is None:
            raise SHCSessionError("Session is not authenticated")
        return unique_id

    @property
    def intrusion_system(self) -> SHCIntrusionSystem:
        return cast(SHCIntrusionSystem, self._domains_by_id["IDS"])

    @property
    def water_alarm_system(self) -> SHCWaterAlarmSystem | None:
        """None on installations where the domain didn't initialize (no water sensors)."""
        return cast("SHCWaterAlarmSystem | None", self._domains_by_id.get("WATERALARM"))

    @property
    def api(self) -> SHCAPI:
        return self._api

    @property
    def device_helper(self) -> SHCDeviceHelper:
        return self._device_helper

    @property
    def rawscan_commands(self) -> list[str]:
        return [
            "devices",
            "device",
            "services",
            "device_services",
            "device_service",
            "rooms",
            "scenarios",
            "messages",
            "info",
            "information",
            "public_information",
            "intrusion_detection",
            "zigbee_routing_info",
        ]

    def rawscan(self, **kwargs: Any) -> Any:
        match kwargs["command"].lower():
            case "devices":
                return self._api.get_devices()

            case "device":
                return self._api.get_device(device_id=kwargs["device_id"])

            case "services":
                return self._api.get_services()

            case "device_services":
                return self._api.get_device_services(device_id=kwargs["device_id"])

            case "device_service":
                return self._api.get_device_service(
                    device_id=kwargs["device_id"], service_id=kwargs["service_id"]
                )

            case "rooms":
                return self._api.get_rooms()

            case "scenarios":
                return self._api.get_scenarios()

            case "messages":
                return self._api.get_messages()

            case "info" | "information":
                return self._api.get_information()

            case "public_information":
                return self._api.get_public_information()

            case "intrusion_detection":
                return self._api.get_domain_intrusion_detection()

            case "zigbee_routing_info":
                return self._api.get_zigbee_routing_info(device_id=kwargs["device_id"])

            case _:
                return None
