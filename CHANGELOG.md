# Changelog

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
