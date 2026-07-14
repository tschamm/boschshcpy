# Changelog

## Unreleased

## 0.4.14 — device status refresh on long-poll resubscribe (hass#370)

**No breaking changes.**

- **`session.py`/`session_async.py`:** after a long-poll poll-id resubscribe
  (happens roughly every 24h, or any time the connection was interrupted
  long enough for the old poll id to be invalidated — e.g. during an SHC
  firmware update/reboot), the existing per-device refresh only short-polled
  each device's *services*. It never re-fetched the device's own top-level
  info, so `status` (`AVAILABLE`/`UNDEFINED`/...) stayed stuck at whatever it
  was before the gap. A device that went `UNDEFINED` during the gap and
  later reconnected kept reporting stale availability indefinitely, while
  its service short-poll happily refreshed with the SHC's own last-cached
  (possibly stale) value — the combination made a genuinely uncertain
  reading look like a fresh, confident one (hass#370: a window/door contact
  showed "closed" instead of "unavailable" right after an SHC firmware
  update, misleading automations that assumed it was really closed). Fixed
  by bulk-refreshing every device's own info (one `get_devices()` call) at
  the start of the resubscribe-refresh block, before the existing
  service-level short-poll runs.
- **`api.py`/`register_client.py`:** removed a now-unused `# type: ignore[misc]`
  on `HostNameIgnoringAdapter` in both files — `requests`' type stubs no
  longer need the suppression, mypy was flagging both as unused.

## 0.4.13

**No breaking changes.**

Found via a chaos-engineering test round targeting the long-poll processing
path (fault injection, not a live incident) — 4 instances of one pattern in
`session.py`'s `_process_long_polling_poll_result` and `device_service.py`'s
`process_long_polling_poll_result`: trusting the SHC's message shape without
verifying it before indexing/`.get()`-ing into it, which raised an uncaught
`KeyError`/`TypeError`/`AttributeError` and stalled the poll thread for 15s
on a malformed message.

- **`session.py`:** `raw_result["@type"]` → `.get("@type")` (top-level and
  via recursion into an embedded `deviceServiceDataModel`); guarded the
  `"message"` branch's `"arguments"` field against being present-but-not-a-dict;
  caught `TypeError`/`JSONDecodeError` from `json.loads()` on a non-string or
  invalid `deviceServiceDataModel` value.
- **`device_service.py`:** guarded `process_long_polling_poll_result`'s
  `"state"` field against being present-but-not-a-dict before comparing
  `@type`.

All four are behavior-preserving for well-formed traffic (dedicated
regression tests confirm), verified with 2 independent adversarial bug-hunt
passes.

## 0.4.12

**No breaking changes.**

- **`session.py`:** fixed a thread-safety race between `SHCPollingThread`
  (sole mutator of `_devices_by_id`/`_services_by_device_id`) and cross-thread
  readers (`devices` property, `device()`) — a device add/remove racing a
  concurrent read could raise an unhandled `RuntimeError: dictionary changed
  size during iteration` in the reading thread. Added `self._devices_lock`
  (`threading.RLock`), held only for the actual dict mutation/snapshot —
  never across I/O (`get_device_services`) or subscriber-callback invocation,
  to avoid stalling readers/writers or risking deadlock. Found via a targeted
  bug-hunt round; not tied to a user report.

## 0.4.11

**No breaking changes.**

Findings from a broad bug-hunt round across the sync/async session/api/services/models layers:

- **`services_impl.py`:** `ChildProtectionService.childLockActive` indexed
  `self.state["childLockActive"]` directly. Shutter-II's OpenAPI spec (unlike
  Light-II's, which shares the same service class) does not mark this field
  required, so the SHC can legitimately omit it — the same missing-key crash
  class already fixed for `OccupancyDetectionService.isOccupied` and
  `UserDefinedState` (#351). Now defaults to `False` via `.get()`.
- **`api_async.py`:** `_retry_once_on_connection_drop` only caught
  `aiohttp.ClientSSLError`/`ClientConnectionError`. A request timeout
  (`ClientTimeout` elapsing) raises a bare `TimeoutError`, which fell through
  unwrapped — breaking parity with the sync client, where
  `requests.exceptions.Timeout` is always wrapped into `SHCConnectionError`.
  Now wrapped consistently on both the first attempt and the retry attempt.

Investigated, not fixed this round — flagged for a dedicated session rather
than a same-day fix, given the risk of a rushed change to shared threading
state: `session.py`'s `_devices_by_id`/`_services_by_device_id` dicts are
mutated only by `SHCPollingThread` but read (`devices`, `device()`) from
other threads with no lock; a device add/remove racing a concurrent read can
raise `RuntimeError: dictionary changed size during iteration` in the
*reading* thread, and — separately — the polling thread's own top-level
`RuntimeError` catch around `_long_poll()` currently treats any
`RuntimeError` there as fatal and permanently stops polling. Needs a
considered fix (locking or a copy-on-read pattern), not a quick patch.

## 0.4.10

**No breaking changes.**

**Added:**
- Zigbee routing-info support: `GET /smarthome/zigbee/routinginfo/{deviceId}`
  — an APK-discovered endpoint (not in the official OpenAPI docs), confirmed
  working (HTTP 200) against real hardware. New `ZigbeeRoutingQuality` enum
  (`GOOD`/`MEDIUM`/`BAD`/`NO_CONNECTION`/`DEVICE_NOT_INITIALIZED`/
  `NOT_SUPPORTED`/`UNKNOWN`, unknown strings fall back to `UNKNOWN`), new
  `SHCZigbeeRoutingInfo` model (`device_id`, `aggregated_quality`, `route` —
  an ordered list of `ZigbeeRoutingHop(device_id, quality)`), and
  `SHCAPI.get_zigbee_routing_info()` / `SHCAPIAsync.get_zigbee_routing_info()`
  / `SHCSession.get_zigbee_routing_info()` /
  `SHCSessionAsync.get_zigbee_routing_info()`. All new classes exported
  top-level from `boschshcpy`.

## 0.4.9

**No breaking changes.**

**Fixes:**
- `SHCAPI._put_api_or_fail`/`_post_api_or_fail` (used by e.g. scenario
  triggers and device writes) previously let a `requests.exceptions.*`
  transport error propagate completely unwrapped — only `_get_...` wrapped
  `SSLError`, and only that one type. All three now wrap any
  `requests.exceptions.RequestException` into `SHCConnectionError`, so
  callers only ever need to catch boschshcpy's own exception hierarchy,
  never `requests`' internals (flagged during home-assistant/core#174613's
  review).
- `SHCConnectionError` now subclasses `SHCException` instead of bare
  `Exception`, so `except SHCException` alone catches connection failures
  too. Existing `except SHCConnectionError:` call sites are unaffected;
  `raise SHCConnectionError` with no arguments still works (default
  message added).

## 0.4.8

**No breaking changes.** APK-decompile-verified fixes and additions across
several device services (hass audit), bundled with the Outdoor Siren fix.

**Fixes:**
- `OutdoorSirenService.async_trigger_test_alarm` (hass#120): the SHC's
  `operation/{name}` endpoints take a bare positional-args JSON array, not the
  named object the official OpenAPI spec describes — confirmed by decompiling
  the official Bosch Android app's request-building code
  (`DeviceService.executeOperation` passes its `Object[]` params straight into
  Jackson's serializer with no wrapping). The previous `{"soundLevel": "LOW"}`
  body (matching the spec) is rejected by the real SHC with 422
  `JSON_MAPPING_FAILED`; now sends `["LOW"]`/`["MEDIUM"]`/`["HIGH"]` instead.
  Not yet confirmed against real Outdoor Siren hardware — no maintainer owns
  one. If you have this device, please help verify and report back on
  https://github.com/tschamm/boschshc-hass/issues/120.
- `KeypadTriggerService.scenario_id_associations` returned `list(dict)` (just
  the dict's keys) instead of the actual `dict[str, str]` mapping the app
  reads — fixed to return the real mapping.
- `BypassService`: corrected docstring/comments for `timeout` — the field is
  in **minutes**, not seconds as previously assumed (confirmed via decompiled
  layout XML; no OpenAPI spec exists for Bypass at all).

**New read-only properties (additive, no breaking changes):**
- `HeatingCircuitService`: `setpoint_temperature_range`,
  `comfort_temperature_range`, `eco_temperature_range` — the app derives its
  setpoint slider bounds from these instead of a hardcoded 5–30 °C range.
- `RoomClimateControlService`: `active_schedule_id`,
  `setpoint_temperature_offset` (+`_active`/`_active_value`),
  `custom_duration_active` (+`_since`), `next_operation_mode`,
  `next_setpoint_temperature` (+`_change`).
- `PresenceSimulationConfigurationService`: `running_start_time`,
  `running_end_time` (JSON keys `runningStart`/`runningEnd`; the app's `"-"`
  sentinel for "not running" is normalized to `None`).
- `ShutterControlService` / `SHCShutterControl`: `end_position_supported`,
  `end_position_auto_detect`, `delay_compensation_supported`,
  `delay_compensation_time`, `automatic_delay_compensation`,
  `reference_moving_time_top_to_bottom_ms`,
  `reference_moving_time_bottom_to_top_ms`; `calibrated` is now also exposed
  at the model level (was service-only before).

**New write operations (additive):**
- `PowerMeterService.async_reset_energy_summation()` — resets a smart plug's
  accumulated energy counter (`resetEnergySummation`, empty-array
  `operation/{name}` call).
- `ShutterControlService.async_reset_calibration_and_open()` /
  `SHCShutterControl.async_reset_calibration_and_open()` — triggers a Shutter
  Control II end-position (re)calibration run (`resetCalibrationAndOpen`,
  empty-array `operation/{name}` call, confirmed genuinely reachable in the
  app's UI, unlike some other declared-but-unused shutter operations).

## 0.4.7

**No breaking changes.** Bugfixes plus one additive property.

Found while auditing `boschshc-hass`'s platform files against this
library's actual class hierarchy (5-round bug hunt) and while addressing
review feedback on the open home-assistant/core `bosch_shc` PRs.

### Fixed

- **`SHCShutterContact2Plus`**: added `async_set_enabled` as an alias for
  `async_set_vibration_enabled`. `boschshc-hass`'s generic switch platform
  derives the async writer method name from the read property name
  (`enabled` -> `async_set_enabled`), but only the vibration-specific name
  existed — toggling the vibration-sensor switch silently no-op'd
  (`AttributeError`, swallowed by the platform's guard).
- **`SHCLightControl.supports_switch_configuration`** was missing
  entirely, unlike sibling `SHCMicromoduleRelay` which already has it.
  `boschshc-hass`'s switch platform gates `swap_inputs`/`swap_outputs`
  entity creation on `getattr(device, "supports_switch_configuration",
  False)`, so Light/Shutter Control II devices never got those switches
  even with a real `SwitchConfiguration` service present. (The same gap
  independently surfaced via Copilot's automated review on the open
  home-assistant/core `select.py` PR.)
- **`OccupancyDetectionService.isOccupied`** hardened from a direct
  `self.state["isOccupied"]` index to `.get(..., False)`, matching every
  sibling boolean state property — the OpenAPI spec marks the field
  required, but this codebase has hit "required" fields missing in
  practice before (hass#351).
- **`SHCMotionDetector2.supports_tamper_reset`** added.
  `reset_tampered_state`/`async_reset_tampered_state` are defined
  unconditionally on this class, so `boschshc-hass`'s
  `hasattr(device, "reset_tampered_state")` gate for the tamper-reset
  button was always `True` and never actually detected a device missing
  the `LatestTamper` service.

### Added

- **`SHCLight.hs_color`** (get/set, sync + async): returns/accepts color
  as a `(hue 0-360, saturation 0-100)` tuple, packing/unpacking the
  existing `rgb` int property internally via `colorsys` (no new
  dependency; matches Home Assistant's own `color_RGB_to_hs`/
  `color_hs_to_RGB` algorithm numerically). Added so the
  home-assistant/core `bosch_shc` light platform can do RGB<->HS
  conversion via the library instead of hand-rolled bit-shifting, per
  reviewer feedback on that PR.

## 0.4.6

**No breaking config changes.** One behavior-relevant note: two numeric
fields revert from `float` back to `int` (see Fixed) — this corrects a
prior release, not a new change.

hass#356 turned out not to be an installation-profile issue as originally
guessed; finding the real cause led to a full audit of `boschshcpy`
against a decompiled copy of the official Bosch Android app (ground truth
for fields/enums/write-paths the public OpenAPI spec doesn't cover or gets
wrong), run as independent parallel finders per device domain, each
finding adversarially re-verified against primary sources before a fix was
applied — 3 findings were rejected at verification (a misread internal
app-UI-diff field, a decompiler-artifact-based naming guess, and an
unverified TLS assumption) and never touched the code.

### Fixed

- **`SHCMotionDetector2.supports_light` was never actually implemented**
  (hass#356). The 0.9.2 `boschshc-hass` CHANGELOG claimed this shipped
  paired with this lib's 0.4.5 — it didn't; confirmed absent from this
  repo's full history and from GitHub code search. Since `boschshc-hass`
  reads it via `getattr(light, "supports_light", False)`, the missing
  attribute silently defaulted to "unsupported" for every Motion Detector
  II `[+M]` since 0.9.2, regardless of installation profile (the profile
  was never actually the gating factor — every rawscan of the reporter's
  device, in `GENERIC` profile, shows both `BinarySwitch` and
  `MultiLevelSwitch` present). Added `supports_light` plus None-safe
  getters/setters (sync + async) so a genuine base Motion Detector II
  (no `[+M]` light hardware) degrades gracefully instead of raising.
- **`CommunicationQualityService.State` had an invented `MEDIUM` member
  that does not exist in the real API**, and was missing the real
  `NOT_SUPPORTED` value the Bosch app's own `Quality` enum defines.
  Replaced `MEDIUM` with `NOT_SUPPORTED`.
- **`ValveTappetService.position` / `SHCThermostat.position`** reverted
  from `float` back to `int` — the Bosch app's own `ValveTappetState`
  model declares this field `Integer`, unlike sibling
  `TemperatureLevelState`/`TemperatureOffsetState`, which really are
  `Float`. The OpenAPI spec's generic `number` typing over-generalized
  this in a prior release.
- **`AirQualityLevelService.purity` / `SHCTwinguard.purity`** reverted
  from `float` back to `int` for the same reason — the app's
  `AirQualityLevelState` declares `purity` as `Integer` while
  `temperature`/`humidity` on the same service really are `Float`.
- **`SmokeDetectorCheckService.State`** was missing 3 real firmware
  states (`COMMUNICATION_TEST_SENT`/`COMMUNICATION_TEST_OK`/
  `COMMUNICATION_TEST_REQUESTED`) that SD/SD2 devices can report; added,
  with the same graceful-fallback-to-`NONE` guard already used elsewhere.

### Added

- **`WallThermostatConfiguration.supported_heater_types` /
  `.decalcification_protection_enabled`** — previously unmapped fields
  confirmed on real RTH2_230/BWTH hardware (rawscan database).
- **`WallThermostatConfiguration.HeaterType.VOLT_FREE_HEATING`** — a real
  heater type seen on hardware (rawscan-confirmed) that was missing from
  the enum, silently collapsing to `UNKNOWN`.
- **Bypass configuration (timed/infinite auto-expiry)** for
  `BypassService`/`SHCShutterContact2` — new `configuration_enabled`/
  `timeout`/`infinite` read properties plus `set_bypass_configuration`/
  `async_set_bypass_configuration()` writers, mirroring
  `OutdoorSirenService`'s merge-then-PUT pattern so unrelated config
  fields aren't clobbered.
- **`SHCLightControl`/`SHCMicromoduleRelay.supports_swap_outputs`** —
  forwards the underlying switch-configuration capability flag, needed
  before a "Swap Outputs" control can be safely offered.
- **`CommunicationQualityService`/`._CommunicationQuality.request_communication_quality_test()`
  (sync + async)** — new write path to trigger a fresh communication
  quality test on demand, available to every device composing the shared
  `_CommunicationQuality` mixin.
- **`DetectionTestService.motion_sensitivity`** — the Motion Detector
  II's `DetectionTest` service also reports its own `motionSensitivity`
  reading (shares the `PirSensorConfiguration` enum vocabulary); now
  exposed instead of silently dropped.

## 0.4.5

**No breaking API changes.** Hotfix for 0.4.4.

### Fixed

- **mypy CI failure**: `SHCImpulseSwitch.impulse_length` (models_impl.py)
  still declared `-> int | None` after 0.4.4 changed the underlying
  `ImpulseSwitchService.impulse_length` to return `float` — now `float |
  None` for consistency. 0.4.4's remote Tests workflow failed on this
  (mypy strict), though the PyPI package itself was unaffected (mypy is a
  type-check gate, not a runtime error) — this release fixes CI green.
  Also added a local `mypy` gate to `scripts/local-ci.sh` so this class of
  gap is caught before tagging in the future.

## 0.4.4

**No breaking API changes.** Fully backward-compatible with 0.4.x. Two rounds
of proactive fleet bug-hunting (parallel independent agents), each fix
adversarially re-verified by an independent post-fix pass.

### Fixed

- **Permanent "Already polling!" lockout after a `RuntimeError`** in the
  sync `SHCSession` polling thread — the thread handle is now cleared in a
  `finally` block regardless of exit path, restoring the ability to restart
  polling. Deliberately does not also clear `_poll_id` there, since that
  would make a normal `stop_polling()` skip its own unsubscribe (caught by
  a post-fix pass).
- **`SmokeDetectionSystemEvent`/`SmokeDetectorEvent` never fired** —
  `device_service._process_events()` had no dispatch branch for
  `Alarm`/`SurveillanceAlarm`, so `register_event()` callbacks on those
  services were dead code. Added dispatch with an edge-triggered replay
  guard (these services carry no event timestamp, only a current value).
- **`SHCIntrusionSystem.active_configuration_profile` silently mis-reported
  an unrecognized IDS profile as `FULL_PROTECTION`** instead of surfacing it
  as unknown — new `Profile.UNKNOWN` member.
- **`SHCIntrusionSystem` crashed on missing optional fields** —
  `systemAvailability`/`armingState`/`alarmState`/`activeConfigurationProfile`/
  `securityGapState` are not in the OpenAPI "required" list; `__init__`,
  `short_poll` (hot poll path), and `process_long_polling_poll_result` now
  tolerate any of them being omitted. `arming_state` now also catches
  `KeyError` (previously only `ValueError`).
- **Outdoor siren duration/delay fields, solar charging current, and
  impulse-switch length were truncated to whole units** by `int()` instead
  of `float()` (OpenAPI types them `number`) — the siren fields also
  round-trip through every config PUT, so this could silently corrupt a
  user's app-configured value on any unrelated field change.
- **Malformed JSON-RPC responses crashed with a bare
  `IndexError`/`AttributeError`** instead of a handled `SHCSessionError` —
  `_check_jsonrpc_version` (sync and async) now validates the response
  shape first.
- **Async client (`SHCAPIAsync`) lacked the connection-drop retry the sync
  client has had since #281** — GET/PUT/POST now retry once on
  `aiohttp.ClientConnectionError`, closing an intermittent-failure gap on
  the async path, which is what `session_async.py` (HA's actual long-poll
  session) uses.
- **`DimmerConfigurationService.async_set_brightness_range()` could send an
  inverted min/max range** to the SHC — now raises `ValueError` instead.
- **Several more missing-optional-field crashes** (same class as #351):
  `message.py`, `room.py`, `device.py`, `scenario.py`, `emma.py` now
  `.get()`-guard fields not in the OpenAPI "required" list.
- **`information.py`'s zeroconf name parsing** could produce a garbage
  `mac_address` slice from a same-network announcement containing
  "Bosch SHC" but no `[mac]` suffix — now guarded and skipped.
- **`session_async.py` iterated the live subscriber list**, unguarded
  against mutation during iteration (unlike the sync `session.py`, which
  already snapshots via `list(...)`) — fixed for parity.

### Security

- **`register_client.py` wrote the client private key world-readable**
  under the default umask — now uses `os.open(..., 0o600)`. The CLI no
  longer prints cert/key material to stdout (ends up in shell
  history/CI logs), and prompts for the system password via `getpass`
  when `-pw` is omitted instead of requiring it as a plain CLI argument.

### Changed

- `JSONRPCError`/`SHCException` now pass their arguments through to
  `super().__init__()`, so `.args`/`repr()` carry the message (previously
  only available via the custom `__str__`).

## 0.4.3

**No breaking API changes.** Fully backward-compatible with 0.4.x.

### Added

- **Write support for the device installation profile** (groundwork for
  boschshc-hass #353). New `SHCDevice.set_profile()` / `async_set_profile()`
  change the device-level installation `profile` (e.g. `GENERIC` ↔ `OUTDOOR`
  on the Motion Detector II [+M]). The value is validated against the device's
  advertised `supportedProfiles` before writing. Backed by a new
  `SHCAPI.put_device()` / `SHCAPIAsync.put_device()` (full-body
  `PUT /devices/{deviceId}`). The profile is a device-level field, not a
  service; the write path is undocumented in the local OpenAPI (GET-only) and
  is APK-derived ground-truth.

## 0.4.2

**No breaking API changes.** Fully backward-compatible with 0.4.x.

### Fixed

- **More `number` readings were truncated to whole units** (follow-up to #352).
  The same `int()` truncation as the Twinguard temperature also affected three
  fields the local API types as `number`:
  - `AirQualityLevelService.humidity` (Twinguard) — was inconsistent with
    `HumidityLevelService.humidity`, which already returns `float`.
  - `AirQualityLevelService.purity` (Twinguard).
  - `ValveTappetService.position` (Thermostat II valve tappet).

  All three now return the full `float`; the matching model properties
  (`SHCTwinguard.humidity`/`purity`, valve `position`) changed `int` → `float`.
  This restores decimal resolution in the recorder/long-term statistics
  (the HA sensors display these rounded, so the visible value is unchanged).

## 0.4.1

**No breaking API changes.** Fully backward-compatible with 0.4.0.

### Fixed

- **Twinguard temperature truncated to whole degrees** (#352): `AirQualityLevelService.temperature`
  cast the reading with `int()`, discarding the decimal Bosch sends
  (OpenAPI `AirQualityLevelServiceStates.temperature` = `number`). The sensor
  reported stepwise integer jumps and appeared to flat-line. It now returns the
  full `float`; `SHCTwinguard.temperature` return type changed `int` → `float`.

## 0.4.0

**No breaking API changes.** Fully backward-compatible with 0.3.x.

### Type safety — `mypy --strict` fully clean

- `py.typed` PEP 561 marker — downstream consumers can type-check against `boschshcpy`
- `api.py`, `register_client.py`: bytes decoded safely in f-strings
- `register_client.py`: `cast(str, …)` for `Traversable` path in `requests.Session.verify`
- `information.py`: `None` guard on `info.server` before `.find()` / slice
- All public classes exported from top-level `__init__` (`SHCSessionAsync`, all service/model types)

### `SHCSessionAsync` — full async interface

- New `SHCSessionAsync` class: async/await drop-in API for Home Assistant and asyncio consumers
- Long-poll dispatch, device management, scenario callbacks, UDS callbacks — all async

### Defensive guards for partial long-poll updates

- 20 `.get()` / `try-except (KeyError, ValueError)` guards in `services_impl.py`
- `BatteryLevelService.warningLevel`: `try/except` → `State.NOT_AVAILABLE` (no more spurious `unknown`)
- Affected services: `ShutterContact`, `VibrationSensor`, `ValveTappet`, `PowerMeter`, `Routing`, `MultiLevelSensor`, `Alarm`, `ShutterControl`, `CameraNotification`, `Keypad`, `PetImmunity`, `AirQualityLevel`, `SurveillanceAlarm`, `WaterLeakageSensor`, `PresenceSimulationConfiguration`

### CI / release automation

- OIDC Trusted Publisher — pushing `vX.Y.Z` auto-publishes to PyPI and creates a GitHub Release
- `ruff` CI gate: format + lint enforced on every push
- `certificate.py`: use `not_valid_after_utc` (avoids Python 3.12+ deprecation warning)

---

## 0.3.21 — UserDefinedState KeyError fix

- `userdefinedstate.py`: `.get()` fallback for `'deleted'` and `'state'` keys — Bosch API omits them when `False`, causing `KeyError` in `SHCUserDefinedStateSwitch.available`
- 9 regression tests added

---

## 0.3.20 — Thread-safety list() copies + ruff CI gate

- `session.py`: `list()` copies on device/scenario/UDS iteration (prevents `RuntimeError` on concurrent long-poll callbacks)
- `ruff` check + format CI gate added

---

## 0.3.19 — dict-copy safety in callback iteration

- Defensive `dict.copy()` before iterating callback maps in `long_polling.py`
