from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .api import SHCAPI


class SHCDeviceService:
    def __init__(self, api: SHCAPI, raw_device_service: dict[str, Any]) -> None:
        self._api = api
        self._raw_device_service = raw_device_service
        self._raw_state: dict[str, Any] = (
            self._raw_device_service["state"]
            if "state" in self._raw_device_service
            else {}
        )
        self._last_update: datetime | None = None

        self._callbacks: dict[Any, Callable[[], None]] = {}
        self._event_callbacks: dict[str, Callable[[], None]] = {}
        # Baseline event timestamp (Keypad eventTimestamp / LatestMotion
        # latestMotionDetected), seeded from the construction snapshot so the
        # first post-subscribe poll of that same last event is suppressed
        # (prevents replaying the last button press on every HA restart). A
        # genuine new event (newer timestamp) still fires — see _process_events.
        self._last_event_timestamp: Any = self._raw_state.get(
            "eventTimestamp"
        ) or self._raw_state.get("latestMotionDetected")
        # Alarm/SurveillanceAlarm carry no timestamp, only a current "value"
        # enum (e.g. IDLE_OFF/ALARM_ON) — seed from the construction snapshot
        # and fire register_event callbacks only on an actual value change,
        # so a (re)subscribe/restart re-delivery of the unchanged current
        # value isn't dispatched as a fresh event.
        self._last_event_value: Any = self._raw_state.get("value")

    @property
    def id(self) -> str:
        return str(self._raw_device_service["id"])

    @property
    def device_id(self) -> str:
        return str(self._raw_device_service["deviceId"])

    @property
    def state(self) -> dict[str, Any]:
        return self._raw_state

    @property
    def path(self) -> str:
        return str(self._raw_device_service["path"])

    def subscribe_callback(self, entity: Any, callback: Callable[[], None]) -> None:
        self._callbacks[entity] = callback

    def unsubscribe_callback(self, entity: Any) -> None:
        self._callbacks.pop(entity, None)

    def register_event(self, event: str, callback: Callable[[], None]) -> None:
        self._event_callbacks[event] = callback

    def summary(self) -> None:
        print(f"  Device Service: {self.id}")
        print(f"    State: {self.state}")
        print(f"    Path:  {self.path}")

    def put_state(self, key_value_pairs: dict[str, Any]) -> None:
        self._api.put_device_service_state(
            self.device_id.replace("#", "%23"),
            self.id,
            {"@type": self.state.get("@type", ""), **key_value_pairs},
        )

    def put_state_element(self, key: str, value: Any) -> None:
        self.put_state({key: value})

    async def async_put_state(self, key_value_pairs: dict[str, Any]) -> None:
        """Async counterpart to put_state — awaits the async API."""
        await self._api.put_device_service_state(  # type: ignore[misc, func-returns-value]
            self.device_id.replace("#", "%23"),
            self.id,
            {"@type": self.state.get("@type", ""), **key_value_pairs},
        )

    async def async_put_state_element(self, key: str, value: Any) -> None:
        """Async counterpart to put_state_element — awaits the async API."""
        await self.async_put_state({key: value})

    def post_operation(self, operation: str, data: dict[str, Any] | None = None) -> Any:
        """POST a service operation (e.g. triggerTestAlarm) — sync."""
        return self._api.post_device_service_operation(
            self.device_id.replace("#", "%23"), self.id, operation, data
        )

    async def async_post_operation(
        self, operation: str, data: dict[str, Any] | None = None
    ) -> Any:
        """Async counterpart to post_operation — awaits the async API."""
        return await self._api.post_device_service_operation(
            self.device_id.replace("#", "%23"), self.id, operation, data
        )

    def short_poll(self, fire_callbacks: bool = False) -> None:
        now = datetime.now(timezone.utc)  # [S2] single clock read
        if self._last_update is None or (now - self._last_update) > timedelta(
            seconds=1
        ):
            self._raw_device_service = self._api.get_device_service(
                self.device_id.replace("#", "%23"), self.id
            )
            self._last_update = now
            self._raw_state = (
                self._raw_device_service["state"]
                if "state" in self._raw_device_service
                else {}
            )
            # #183: after a poll-id resubscribe (the SHC rotates poll IDs ~every
            # 24 h) the session refresh loop calls device.update(fire_callbacks=
            # True) → short_poll(fire_callbacks=True) for every service so that
            # listeners (e.g. HA entity on_state_changed closures) receive any
            # state that changed during the gap.  Without firing callbacks the
            # entities stay visually stale ("wired to a dead pipe").
            #
            # fire_callbacks defaults to False so the ordinary HA poll path
            # (SHCSwitch.update() → device.update() on should_poll=True camera
            # switches, every ~30 s) keeps its quiet pre-fix behaviour: HA reads
            # the refreshed _raw_state via the entity property and writes its own
            # state itself.  Firing here on every poll would fan out redundant
            # schedule_update_ha_state() calls to every co-registered entity.
            # At initial setup _callbacks is empty, so firing is a no-op anyway.
            if fire_callbacks:
                for fn in list(self._callbacks.values()):  # [S4]
                    fn()

    async def async_short_poll(self, fire_callbacks: bool = False) -> None:
        """Async counterpart to short_poll for the aiohttp (SHCAPIAsync) path.

        The sync short_poll calls a blocking GET; under the async session the
        device's api is SHCAPIAsync whose get_device_service is a coroutine —
        so an on-demand refresh (HA should_poll entities) must await here.
        Mirrors short_poll line-for-line otherwise.
        """
        now = datetime.now(timezone.utc)  # [S2] single clock read
        if self._last_update is None or (now - self._last_update) > timedelta(
            seconds=1
        ):
            self._raw_device_service = await self._api.get_device_service(
                self.device_id.replace("#", "%23"), self.id
            )
            self._last_update = now
            self._raw_state = (
                self._raw_device_service["state"]
                if "state" in self._raw_device_service
                else {}
            )
            if fire_callbacks:
                for fn in list(self._callbacks.values()):  # [S4]
                    fn()

    def process_long_polling_poll_result(self, raw_result: dict[str, Any]) -> None:
        # Defensive: skip malformed/mismatched results rather than assert
        # (asserts vanish under -O and an AssertionError would kill the poll
        # thread for this service permanently on a firmware schema change).
        if raw_result.get("@type") != "DeviceServiceData":
            return
        self._raw_device_service = raw_result  # Update device service data

        if "state" in self._raw_device_service:
            if self.state and raw_result["state"].get("@type") != self.state.get(
                "@type"
            ):
                return
            self._raw_state = raw_result["state"]  # Update state

            for fn in list(self._callbacks.values()):  # [S4]
                fn()

            self._process_events(raw_result)

    def _is_replayed_event(self, timestamp: Any) -> bool:
        """True if this event must be suppressed (replay on (re)subscribe).

        The SHC's first long-poll snapshot after a subscribe carries the
        service's *current* state — i.e. the last button press / last motion —
        which must not be dispatched as a fresh event (it would re-fire
        automations on every HA restart). The first snapshot only establishes
        a baseline; an event fires only once its timestamp advances past it.
        """
        if timestamp is None:
            return False  # no timestamp to compare → preserve old behavior
        if self._last_event_timestamp is None:
            self._last_event_timestamp = timestamp
            return True
        if timestamp <= self._last_event_timestamp:
            return True
        self._last_event_timestamp = timestamp
        return False

    def _is_replayed_value(self, value: Any) -> bool:
        """True if this Alarm/SurveillanceAlarm value must be suppressed.

        These services carry no event timestamp, only a current "value" enum
        (e.g. IDLE_OFF/ALARM_ON), so a genuine event is an edge (value change)
        rather than a fresh timestamp. Fires only when the value differs from
        the last seen one, mirroring the entity-level _last_fired_* guards.
        """
        if value == self._last_event_value:
            return True
        self._last_event_value = value
        return False

    def _process_events(self, raw_result: dict[str, Any]) -> None:
        if raw_result["id"] == "Keypad":
            state = raw_result.get("state", {})
            if self._is_replayed_event(state.get("eventTimestamp")):
                return
            key_name = state.get("keyName")
            if key_name in self._event_callbacks:
                self._event_callbacks[key_name]()
        if raw_result["id"] == "LatestMotion":
            state = raw_result.get("state", {})
            if self._is_replayed_event(state.get("latestMotionDetected")):
                return
            if raw_result["deviceId"] in self._event_callbacks:
                self._event_callbacks[raw_result["deviceId"]]()
        if raw_result["id"] in ("Alarm", "SurveillanceAlarm"):
            state = raw_result.get("state", {})
            if self._is_replayed_value(state.get("value")):
                return
            if raw_result["deviceId"] in self._event_callbacks:
                self._event_callbacks[raw_result["deviceId"]]()
