"""Async session for boschshcpy — Phase 2 of the async migration.

Replaces the blocking SHCPollingThread in session.py with an asyncio.Task
whose callbacks fire on the event loop.  The sync SHCSession is UNCHANGED.

Design notes
------------
* Shares the same device-model constructors (SHCDevice, SHCDeviceHelper, etc.)
  — these are pure sync dict-parsers, safe to call on the event loop.
* process_long_polling_poll_result on device services is sync dict-processing
  + callback firing — also safe on the event loop (no I/O, no blocking).
* The write path (put_state / put_state_element on device services) stays sync
  this round; Phase 3 will inject an async API reference into each service so
  that ``await device_service.async_put_state(...)`` works.  For now callers
  must use ``hass.async_add_executor_job(service.put_state, ...)`` from HA.
* ``external_session`` plumbs straight through to SHCAPIAsync so HA can pass
  ``async_create_clientsession(hass)`` for Phase 3.

Cancellation contract
---------------------
CancelledError is a BaseException (Python 3.8+) and is NOT caught by bare
``except Exception:``.  The _poll_loop uses try/finally so cleanup (setting
the stop flag, recording the poll_id) always runs, and re-raises
CancelledError after cleanup so the calling await-task sees it.

stop_polling() cancels the task, awaits it (suppressing CancelledError from
the await, because that's the expected outcome), then best-effort
unsubscribes and closes the API session.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Sequence, cast

from .api_async import JSONRPCError as JSONRPCError, SHCAPIAsync  # noqa: F401
from .device import SHCDevice
from .device_helper import SHCDeviceHelper
from .domain_impl import SHCIntrusionSystem
from .emma import SHCEmma
from .exceptions import SHCAuthenticationError, SHCConnectionError, SHCSessionError
from .information import SHCInformation
from .message import SHCMessage
from .room import SHCRoom
from .scenario import SHCScenario
from .services_impl import SUPPORTED_DEVICE_SERVICE_IDS
from .userdefinedstate import SHCUserDefinedState

logger = logging.getLogger("boschshcpy")

# Backoff constants (mirroring sync session.py polling_thread_main)
_BACKOFF_STALE_POLL_ID = 1.0  # seconds to wait after -32001 before next iteration
_BACKOFF_OTHER_ERROR = 15.0  # seconds to wait after unexpected error


class SHCSessionAsync:
    """Async counterpart to SHCSession.

    Uses SHCAPIAsync (aiohttp) for all I/O and an asyncio.Task for the
    long-poll loop instead of a blocking thread.  Callbacks fire on the event
    loop so the HA integration no longer needs call_soon_threadsafe marshalling.

    Lifecycle::

        session = SHCSessionAsync(ip, cert, key)
        await session.async_init()        # enumerate devices/rooms/scenarios
        await session.start_polling()     # subscribe + start long-poll Task

        # ... HA runs ...

        await session.stop_polling()      # cancel Task + unsubscribe + close
    """

    def __init__(
        self,
        controller_ip: str,
        certificate: str,
        key: str,
        *,
        external_session: Any | None = None,
        long_poll_timeout: int = 30,
        ssl_context: Any | None = None,
    ) -> None:
        """Initialise without doing any I/O.

        Args:
            controller_ip: IP address of the SHC controller.
            certificate: Path to the PEM client certificate.
            key: Path to the PEM private key.
            external_session: Optional existing ``aiohttp.ClientSession``.
                When provided it is passed to SHCAPIAsync which will NOT close
                it in ``close()``.  Intended for HA ``async_create_clientsession``.
            long_poll_timeout: Seconds passed as wait_seconds to RE/longPoll
                (default 30).  The HTTP timeout is set to this + 5 s inside
                SHCAPIAsync.long_polling_poll().
            ssl_context: Optional pre-built mTLS SSLContext (see SHCAPIAsync).
                Pass one built off the event loop to avoid blocking file I/O
                when constructing on the loop.
        """
        self._long_poll_timeout = long_poll_timeout

        # Build the async API layer (aiohttp lazy-imported inside SHCAPIAsync)
        self._api = SHCAPIAsync(
            controller_ip=controller_ip,
            certificate=certificate,
            key=key,
            external_session=external_session,
            ssl_context=ssl_context,
        )

        # SHCDeviceHelper mirrors the sync path — it takes a sync SHCAPI but
        # only stores it (never calls it at init).  The async session passes
        # itself as a compatible "api" because device_helper only uses it to
        # categorise models; it does NOT call any network methods at build time.
        # For now we pass None and set it after async_init builds real devices.
        self._device_helper: SHCDeviceHelper | None = None

        # Device model dictionaries (same shape as SHCSession)
        self._rooms_by_id: dict[str, SHCRoom] = {}
        self._scenarios_by_id: dict[str, SHCScenario] = {}
        self._devices_by_id: dict[str, SHCDevice] = {}
        self._services_by_device_id: dict[str, list[Any]] = defaultdict(list)
        self._domains_by_id: dict[str, Any] = {}
        self._messages_by_id: dict[str, SHCMessage] = {}
        self._userdefinedstates_by_id: dict[str, SHCUserDefinedState] = {}
        self._subscribers: list[Any] = []
        self._emma: SHCEmma | None = None

        # SHC information (populated by async_init)
        self._shc_information: Any = None

        # Long-poll state
        self._poll_id: str | None = None
        self._poll_task: asyncio.Task[None] | None = None
        self._stop_polling: bool = False

        # Callback registries (same API as SHCSession)
        self._scenario_callbacks: dict[str, Callable[..., Any]] = {}
        self._userdefinedstate_callbacks: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Initialisation (async)
    # ------------------------------------------------------------------

    async def async_init(self) -> None:
        """Enumerate all devices/rooms/scenarios/etc. from the SHC.

        Must be awaited once before calling start_polling().

        Mirrors SHCSession._enumerate_all() + SHCSession.authenticate().
        """
        await self._async_authenticate()
        await self._async_enumerate_services()
        await self._async_enumerate_devices()
        await self._async_enumerate_rooms()
        await self._async_enumerate_scenarios()
        await self._async_enumerate_messages()
        await self._async_enumerate_userdefinedstates()
        await self._async_initialize_domains()
        await self._async_initialize_emma()

    async def _async_authenticate(self) -> None:
        """Mirrors SHCSession.authenticate() — builds SHCInformation."""
        # SHCInformation.__init__ calls sync API methods (get_public_information,
        # get_information).  We call the async equivalents here and hand the
        # raw results to an object that mirrors what SHCInformation exposes but
        # does NOT do its own I/O.  Rather than duplicate SHCInformation's logic
        # we use a thin wrapper that provides the same .macAddress/.version etc.
        # properties that the rest of the session code depends on.
        pub_info = await self._api.get_public_information()
        if pub_info is None:
            raise SHCConnectionError(
                "Failed to get public information from SHC controller"
            )

        info_raw = await self._api.get_information()
        if info_raw is None:
            raise SHCAuthenticationError(
                "Authentication failed: could not get SHC information"
            )

        self._shc_information = _AsyncSHCInformation(pub_info, info_raw, self._api)

    async def _async_enumerate_services(self) -> None:
        """Mirrors SHCSession._enumerate_services()."""
        raw_services = await self._api.get_services()
        for service in raw_services:
            if service["id"] not in SUPPORTED_DEVICE_SERVICE_IDS:
                continue
            device_id = service["deviceId"]
            self._services_by_device_id[device_id].append(service)

    async def _async_enumerate_devices(self) -> None:
        """Mirrors SHCSession._enumerate_devices()."""
        # Device helper must be built with a "sync-api-like" object.
        # SHCDeviceHelper.__init__ only stores the api ref and builds empty
        # model dicts; it does not call the api at construction.  We pass our
        # async api object — device_helper.device_init() calls build() from
        # models_impl which also only does dict-parsing, safe here.
        device_helper = SHCDeviceHelper(self._api)  # type: ignore[arg-type]
        self._device_helper = device_helper

        raw_devices = await self._api.get_devices()
        for raw_device in raw_devices:
            self._add_device(raw_device)

    def _add_device(
        self, raw_device: dict[str, Any], update_services: bool = False
    ) -> SHCDevice | None:
        """Sync helper — mirrors SHCSession._add_device().

        update_services=True is only used for new-device events that arrive
        during long-polling; it would need an async path (await get_device_services).
        For new-device events we call _async_add_device() instead.
        """
        device_id = raw_device["id"]

        if not self._services_by_device_id[device_id]:
            logger.debug(
                "Skipping device id %s which has no services that are "
                "supported by this library",
                device_id,
            )
            return None

        assert self._device_helper is not None
        device = self._device_helper.device_init(
            raw_device, self._services_by_device_id[device_id]
        )
        self._devices_by_id[device_id] = device
        return device

    async def _async_add_new_device(self, raw_device: dict[str, Any]) -> SHCDevice | None:
        """Async version of _add_device(update_services=True) for new-device events."""
        device_id = raw_device["id"]
        self._services_by_device_id.pop(device_id, None)
        raw_services = await self._api.get_device_services(device_id)
        for service in raw_services:
            if service["id"] not in SUPPORTED_DEVICE_SERVICE_IDS:
                continue
            self._services_by_device_id[device_id].append(service)

        return self._add_device(raw_device)

    async def _async_enumerate_rooms(self) -> None:
        """Mirrors SHCSession._enumerate_rooms()."""
        raw_rooms = await self._api.get_rooms()
        for raw_room in raw_rooms:
            room_id = raw_room["id"]
            room = SHCRoom(api=self._api, raw_room=raw_room)
            self._rooms_by_id[room_id] = room

    async def _async_enumerate_scenarios(self) -> None:
        """Mirrors SHCSession._enumerate_scenarios()."""
        raw_scenarios = await self._api.get_scenarios()
        for raw_scenario in raw_scenarios:
            scenario_id = raw_scenario["id"]
            scenario = SHCScenario(api=self._api, raw_scenario=raw_scenario)  # type: ignore[arg-type]
            self._scenarios_by_id[scenario_id] = scenario

    async def _async_enumerate_messages(self) -> None:
        """Mirrors SHCSession._enumerate_messages()."""
        raw_messages = await self._api.get_messages()
        for raw_message in raw_messages:
            message_id = raw_message["id"]
            message = SHCMessage(api=self._api, raw_message=raw_message)
            self._messages_by_id[message_id] = message

    async def _async_enumerate_userdefinedstates(self) -> None:
        """Mirrors SHCSession._enumerate_userdefinedstates()."""
        raw_states = await self._api.get_userdefinedstates()
        for raw_state in raw_states:
            userdefinedstate_id = raw_state["id"]
            userdefinedstate = SHCUserDefinedState(
                api=self._api,  # type: ignore[arg-type]
                info=self.information, raw_state=raw_state
            )
            self._userdefinedstates_by_id[userdefinedstate_id] = userdefinedstate

    async def _async_initialize_domains(self) -> None:
        """Mirrors SHCSession._initialize_domains()."""
        raw_ids = await self._api.get_domain_intrusion_detection()
        self._domains_by_id["IDS"] = SHCIntrusionSystem(
            self._api,
            raw_ids,
            self.information.macAddress,
        )

    async def _async_initialize_emma(self) -> None:
        """Mirrors SHCSession._initialize_emma()."""
        self._emma = SHCEmma(self._api, self._shc_information, None)

    # ------------------------------------------------------------------
    # Long-poll lifecycle
    # ------------------------------------------------------------------

    async def start_polling(self) -> None:
        """Subscribe + start the long-poll asyncio.Task.

        Mirrors SHCSession.start_polling() semantics.
        HA integration usage::

            await session.start_polling()
            # HA can store the session and later call await session.stop_polling()

        The created task is a background task (fire-and-forget from the
        caller's perspective).  It runs until stop_polling() cancels it.
        """
        if self._poll_task is not None:
            raise SHCSessionError("Already polling!")

        self._stop_polling = False
        self._poll_id = await self._api.long_polling_subscribe()
        logger.debug(
            "Async session subscribed for long poll. Poll id: %s", self._poll_id
        )

        self._poll_task = asyncio.get_running_loop().create_task(
            self._poll_loop(), name="SHCAsyncPollingTask"
        )

    async def stop_polling(self) -> None:
        """Cancel the poll task, unsubscribe, and close the API session.

        Mirrors SHCSession.stop_polling() semantics.
        Safe to call even if the task finished on its own.
        """
        if self._poll_task is None:
            raise SHCSessionError("Not polling!")

        self._stop_polling = True
        self._poll_task.cancel()

        try:
            await self._poll_task
        except asyncio.CancelledError:
            pass  # expected — the task was cancelled by us
        except Exception as ex:
            logger.debug("Poll task raised on stop: %s", ex)
        finally:
            self._poll_task = None

        # Best-effort unsubscribe (SHC session already cleaned up)
        if self._poll_id is not None:
            try:
                await self._api.long_polling_unsubscribe(self._poll_id)
                logger.debug(
                    "Async unsubscribed from long poll, poll id: %s", self._poll_id
                )
            except Exception as ex:
                logger.debug("Async unsubscribe failed (best-effort): %s", ex)
            finally:
                self._poll_id = None

        await self._api.close()

    # ------------------------------------------------------------------
    # Poll loop (asyncio.Task body)
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Main long-poll loop — runs as an asyncio.Task.

        Mirrors polling_thread_main() in session.py but:
        - uses ``await asyncio.sleep()`` instead of ``time.sleep()``
        - handles asyncio.CancelledError with try/finally + re-raise
        - dispatches to _process_long_polling_poll_result on the event loop
          (no call_soon_threadsafe needed)

        Error handling mirrors the sync session:
        - JSONRPCError -32001: re-subscribe (new poll_id) + asyncio.sleep(1)
        - Other exceptions: log + asyncio.sleep(15) + continue
        - asyncio.CancelledError: cleanup + re-raise (structured concurrency)
        """
        while not self._stop_polling:
            try:
                resubscribed = False

                # Re-subscribe if poll_id was invalidated (-32001 path)
                if self._poll_id is None:
                    self._poll_id = await self._api.long_polling_subscribe()
                    logger.debug(
                        "Async session re-subscribed for long poll. New poll id: %s",
                        self._poll_id,
                    )
                    resubscribed = True

                raw_results = await self._api.long_polling_poll(
                    self._poll_id, self._long_poll_timeout
                )

                for raw_result in raw_results:
                    await self._process_long_polling_poll_result(raw_result)

                if resubscribed:
                    # Mirrors session.py:183-206: after a poll-id resubscribe
                    # the SHC doesn't deliver state changes that happened during
                    # the gap.  Short-poll every device so listeners get current
                    # state (#183).  Use async_update() (not the sync update() +
                    # executor) — calling sync short_poll() against SHCAPIAsync
                    # stores an unawaited coroutine in _raw_device_service, which
                    # causes 'coroutine object is not subscriptable' on the next
                    # state write (issue #345).
                    logger.debug(
                        "Poll-id resubscribed — refreshing %d device(s) via "
                        "async short-poll (#183, async)",
                        len(self._devices_by_id),
                    )
                    for device in list(self._devices_by_id.values()):
                        try:
                            await device.async_update(fire_callbacks=True)
                        except Exception as ex:  # noqa: BLE001
                            logger.warning(
                                "Short-poll refresh failed for device %s "
                                "after async resubscribe: %s",
                                device.id,
                                ex,
                            )

            except asyncio.CancelledError:
                # Task was cancelled by stop_polling() — clean up and propagate.
                # CancelledError is BaseException; try/finally ensures this runs
                # even when raised deep in an await.
                logger.debug("Async poll task cancelled (stop_polling called).")
                raise  # MUST re-raise — swallowing breaks structured concurrency

            except JSONRPCError as json_rpc_error:
                if json_rpc_error.code == -32001:
                    # Stale poll id — SHC rotates these ~every 24h.
                    # Invalidate; next iteration will re-subscribe.
                    # Mirrors session.py:209-217.
                    self._poll_id = None
                    logger.debug(
                        "Async session: SHC claims unknown poll id. "
                        "Invalidating and resubscribing next iteration..."
                    )
                    await asyncio.sleep(_BACKOFF_STALE_POLL_ID)
                else:
                    logger.error(
                        "Async poll got unexpected JSONRPCError (code %s): %s. "
                        "Waiting %ss.",
                        json_rpc_error.code,
                        json_rpc_error,
                        _BACKOFF_OTHER_ERROR,
                    )
                    await asyncio.sleep(_BACKOFF_OTHER_ERROR)

            except Exception as ex:
                # Mirrors session.py:330-334: generic error → log + backoff.
                logger.error(
                    "Error in async polling task: %s. Waiting %ss.",
                    ex,
                    _BACKOFF_OTHER_ERROR,
                )
                await asyncio.sleep(_BACKOFF_OTHER_ERROR)

    # ------------------------------------------------------------------
    # Long-poll result dispatch
    # ------------------------------------------------------------------

    async def _process_long_polling_poll_result(self, raw_result: dict[str, Any]) -> None:
        """Dispatch a single long-poll event to the correct handler.

        Mirrors SHCSession._process_long_polling_poll_result() line-for-line
        (session.py:225-305).  The only difference is:
        - new-device events call ``await _async_add_new_device()`` instead of
          the sync ``_add_device(update_services=True)`` that issues a blocking
          GET.
        - The method is async so it can be awaited by _poll_loop; all the
          actual dispatch sub-calls remain sync (dict-parsing + callbacks).
        """
        logger.debug("Async long poll: %s", raw_result)

        # --- DeviceServiceData (session.py:227-236) ---
        if raw_result["@type"] == "DeviceServiceData":
            device_id = raw_result["deviceId"]
            if device_id in self._devices_by_id:
                device = self._devices_by_id[device_id]
                device.process_long_polling_poll_result(raw_result)
            else:
                logger.debug(
                    "Skipping async polling result with unknown device id %s.",
                    device_id,
                )
            return

        # --- message (session.py:237-253) ---
        if raw_result["@type"] == "message":
            if "arguments" in raw_result and (
                "deviceServiceDataModel" in raw_result["arguments"]
            ):
                raw_data_model = json.loads(
                    raw_result["arguments"]["deviceServiceDataModel"]
                )
                await self._process_long_polling_poll_result(raw_data_model)
            else:
                message_id = raw_result["id"]
                message = SHCMessage(api=self._api, raw_message=raw_result)
                self._messages_by_id[message_id] = message
            return

        # --- scenarioTriggered (session.py:254-261) ---
        if raw_result["@type"] == "scenarioTriggered":
            if raw_result["id"] in self._scenario_callbacks:
                self._scenario_callbacks[raw_result["id"]](raw_result)
            if "shc" in self._scenario_callbacks:
                self._scenario_callbacks["shc"](raw_result)
            return

        # --- device: update/delete/new (session.py:262-278) ---
        if raw_result["@type"] == "device":
            device_id = raw_result["id"]
            if device_id in self._devices_by_id:
                self._devices_by_id[device_id].update_raw_information(raw_result)
                if raw_result.get("deleted") is True:
                    logger.debug("Async session: deleting device with id %s", device_id)
                    self._services_by_device_id.pop(device_id, None)
                    self._devices_by_id.pop(device_id, None)
            else:
                logger.debug("Async session: found new device with id %s", device_id)
                new_device = await self._async_add_new_device(raw_result)
                if new_device is not None:
                    for instance, callback in self._subscribers:
                        if isinstance(new_device, instance):
                            callback(new_device)
            return

        # --- intrusion-system domain states (session.py:279-281) ---
        if raw_result["@type"] in SHCIntrusionSystem.DOMAIN_STATES:
            if self.intrusion_system is not None:
                self.intrusion_system.process_long_polling_poll_result(raw_result)
            return

        # --- userDefinedState (session.py:283-299) ---
        if raw_result["@type"] == "userDefinedState":
            state_id = raw_result["id"]
            if state_id in self._userdefinedstates_by_id:
                self._userdefinedstates_by_id[state_id].update_raw_information(
                    raw_result
                )
            else:
                userdefinedstate = SHCUserDefinedState(
                    api=self._api,  # type: ignore[arg-type]
                    info=self.information, raw_state=raw_result
                )
                self._userdefinedstates_by_id[state_id] = userdefinedstate
                for instance, callback in self._subscribers:
                    if isinstance(userdefinedstate, instance):
                        callback(userdefinedstate)
            if state_id in self._userdefinedstate_callbacks:
                for callback in self._userdefinedstate_callbacks[state_id]:
                    callback()
            return

        # --- link / emma (session.py:301-305) ---
        if raw_result["@type"] == "link":
            link_id = raw_result["id"]
            if link_id == "com.bosch.tt.emma.applink":
                if self._emma is not None:
                    self._emma.update_emma_data(raw_result)

    # ------------------------------------------------------------------
    # Subscription API (same as SHCSession)
    # ------------------------------------------------------------------

    def subscribe(self, callback_tuple: Any) -> None:
        self._subscribers.append(callback_tuple)

    def subscribe_scenario_callback(self, scenario_id: str, callback: Callable[..., Any]) -> None:
        self._scenario_callbacks[scenario_id] = callback

    def unsubscribe_scenario_callback(self, scenario_id: str) -> None:
        self._scenario_callbacks.pop(scenario_id, None)

    def subscribe_userdefinedstate_callback(
        self, userdefinedstate_id: str, callback: Callable[..., Any]
    ) -> None:
        self._userdefinedstate_callbacks[userdefinedstate_id].append(callback)

    def unsubscribe_userdefinedstate_callbacks(self, userdefinedstate_id: str) -> None:
        self._userdefinedstate_callbacks.pop(userdefinedstate_id, None)

    # ------------------------------------------------------------------
    # Public accessors (same surface as SHCSession)
    # ------------------------------------------------------------------

    @property
    def api(self) -> SHCAPIAsync:
        return self._api

    @property
    def device_helper(self) -> SHCDeviceHelper | None:
        return self._device_helper

    @property
    def devices(self) -> Sequence[SHCDevice]:
        return list(self._devices_by_id.values())

    def device(self, device_id: str) -> SHCDevice:
        return self._devices_by_id[device_id]

    @property
    def rooms(self) -> Sequence[SHCRoom]:
        return list(self._rooms_by_id.values())

    def room(self, room_id: str | None) -> SHCRoom:
        if room_id is not None:
            return self._rooms_by_id[room_id]
        return SHCRoom(self._api, {"id": "n/a", "name": "n/a", "iconId": "0"})

    @property
    def scenarios(self) -> Sequence[SHCScenario]:
        return list(self._scenarios_by_id.values())

    @property
    def scenario_names(self) -> Sequence[str]:
        return [sc.name for sc in self.scenarios]

    def scenario(self, scenario_id: str) -> SHCScenario:
        return self._scenarios_by_id[scenario_id]

    @property
    def messages(self) -> Sequence[SHCMessage]:
        return list(self._messages_by_id.values())

    @property
    def emma(self) -> SHCEmma | None:
        return self._emma

    @property
    def userdefinedstates(self) -> Sequence[SHCUserDefinedState]:
        return list(self._userdefinedstates_by_id.values())

    def userdefinedstate(self, userdefinedstate_id: str) -> SHCUserDefinedState:
        return self._userdefinedstates_by_id[userdefinedstate_id]

    @property
    def information(self) -> Any:
        return self._shc_information

    @property
    def intrusion_system(self) -> SHCIntrusionSystem | None:
        return self._domains_by_id.get("IDS")


# ---------------------------------------------------------------------------
# Lightweight async information wrapper
# ---------------------------------------------------------------------------


class _AsyncSHCInformation:
    """Minimal wrapper around raw SHC information dicts.

    Provides the same properties that SHCSession code accesses from
    SHCInformation without using zeroconf or blocking HTTP calls.

    Only the properties actually used by SHCSessionAsync internals or
    exposed to integrations are implemented here.
    """

    def __init__(self, pub_info: dict[str, Any], info: dict[str, Any], api: Any = None) -> None:
        self._pub_info = pub_info
        self._info = info
        self._api = api

    async def async_refresh(self) -> None:
        """Re-fetch the public /information block (software-update state etc.).

        Lets a polling entity see a firmware update that appears after startup
        (#186). No-op if no api was wired (e.g. unit-test construction).
        """
        if self._api is None:
            return
        pub_info = await self._api.get_public_information()
        if pub_info is not None:
            self._pub_info = pub_info

    @property
    def macAddress(self) -> str | None:
        return cast(str | None, self._pub_info.get("macAddress"))

    @property
    def shcIpAddress(self) -> str | None:
        return cast(str | None, self._pub_info.get("shcIpAddress"))

    @property
    def version(self) -> str | None:
        sw = self._pub_info.get("softwareUpdateState", {})
        return cast(str | None, sw.get("swInstalledVersion"))

    @property
    def available_version(self) -> str | None:
        """Available controller SW version (softwareUpdateState, read-only)."""
        sw = self._pub_info.get("softwareUpdateState", {})
        return cast(str | None, sw.get("swUpdateAvailableVersion"))

    @property
    def update_state(self) -> str | None:
        """Raw swUpdateState string (e.g. UPDATE_AVAILABLE, NO_UPDATE_AVAILABLE)."""
        sw = self._pub_info.get("softwareUpdateState", {})
        return cast(str | None, sw.get("swUpdateState"))

    @property
    def automatic_updates_enabled(self) -> bool | None:
        sw = self._pub_info.get("softwareUpdateState", {})
        return cast(bool | None, sw.get("automaticUpdatesEnabled"))

    @property
    def unique_id(self) -> str | None:
        # Prefer macAddress (same logic as SHCInformation.get_unique_id)
        mac = self.macAddress
        return mac if mac else self.shcIpAddress

    @property
    def name(self) -> str | None:
        return self.shcIpAddress

    def summary(self) -> None:
        print("AsyncSHCInformation:")
        print(f"  shcIpAddress : {self.shcIpAddress}")
        print(f"  macAddress   : {self.macAddress}")
        print(f"  SW-Version   : {self.version}")
        print(f"  unique_id    : {self.unique_id}")
