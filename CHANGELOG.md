# Changelog

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
