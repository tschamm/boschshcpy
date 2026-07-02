# Changelog

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
