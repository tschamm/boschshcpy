# Bosch Smart Home Controller API Python Library

[![PyPI version](https://img.shields.io/pypi/v/boschshcpy.svg)](https://pypi.org/project/boschshcpy/)
[![BuyMeCoffee][buymecoffeebadge-tschamm]][buymecoffee-tschamm]
[![BuyMeCoffee][buymecoffeebadge-mosandlts]][buymecoffee-mosandlts]

Python client library for the Bosch Smart Home Controller (SHC) local REST API.
Communicates directly with the controller over mutual-TLS on the local network — no cloud, no Bosch account required.
The official API documentation is available at [github.com/BoschSmartHome/bosch-shc-api-docs](https://github.com/BoschSmartHome/bosch-shc-api-docs).

## Install

Requires Python ≥ 3.10.

```bash
pip install boschshcpy
```

Current PyPI version: **0.3.5**

## Supported device services

```
TemperatureLevel, HumidityLevel, RoomClimateControl, ShutterContact,
ValveTappet, PowerSwitch, PowerMeter, Routing, PowerSwitchProgram,
PresenceSimulationConfiguration, BinarySwitch, SmokeDetectorCheck, Alarm,
ShutterControl, CameraLight, PrivacyMode, CameraNotification,
IntrusionDetectionControl, Keypad, LatestMotion, AirQualityLevel,
SurveillanceAlarm, BatteryLevel, Thermostat, WaterLeakageSensor,
WaterLeakageSensorTilt, HeatingCircuit, PirSensorConfiguration,
SmartSensitivityControl, DetectionTest, WalkTest, LatestTamper, PollControl,
PetImmunity, OccupancyDetection, MultiLevelSwitch, and more
```

## Supported device models

| Model key | Description |
|---|---|
| `SWD` / `SWD2` / `SWD2_PLUS` / `SWD2_DUAL` | Shutter Contact Gen 1 + Gen 2 (incl. 2 Plus, Dual) |
| `BBL` | Shutter Control |
| `MICROMODULE_SHUTTER` / `MICROMODULE_AWNING` | Micromodule Shutter / Awning |
| `MICROMODULE_BLINDS` | Micromodule Blinds (with tilt) |
| `PSM` | Smart Plug |
| `PLUG_COMPACT` / `PLUG_COMPACT_DUAL` | Smart Plug Compact |
| `BSM` | Light Switch BSM |
| `MICROMODULE_LIGHT_CONTROL` / `MICROMODULE_LIGHT_ATTACHED` | Micromodule Light Control / Attached |
| `MICROMODULE_RELAY` | Micromodule Relay (switch and impulse types) |
| `MICROMODULE_DIMMER` | Micromodule Dimmer |
| `SD` / `SMOKE_DETECTOR2` | Smoke Detector Gen 1 + Gen 2 |
| `SMOKE_DETECTION_SYSTEM` | Smoke Detection System |
| `CAMERA_EYES` | Camera Eyes |
| `CAMERA_360` | Camera 360 |
| `CAMERA_OUTDOOR_GEN2` | Camera Outdoor Gen 2 |
| `ROOM_CLIMATE_CONTROL` | Room Climate Control (thermostat group) |
| `HEATING_CIRCUIT` | Heating Circuit |
| `TRV` / `TRV_GEN2` / `TRV_GEN2_DUAL` | Thermostat (Radiator Valve) Gen 1 + Gen 2 |
| `THB` / `BWTH` / `BWTH24` | Wall Thermostat |
| `RTH2_BAT` / `RTH2_230` | Room Thermostat 2 |
| `WRC2` / `SWITCH2` | Universal Switch |
| `MD` / `MD2` | Motion Detector Gen 1 + Gen 2 [+M] |
| `PRESENCE_SIMULATION_SERVICE` | Presence Simulation System |
| `TWINGUARD` | Twinguard (smoke + air quality) |
| `WLS` | Water Leakage Sensor |
| `LEDVANCE_LIGHT` / `HUE_LIGHT` | LEDVANCE / Hue lights (via SHC) |

## Usage

### Register a new client

Press and hold the button on the SHC controller until the LED starts flashing (registration mode).
Then run:

```bash
boschshc_registerclient -ip YOUR_SHC_IP -pw YOUR_SHC_PASSWORD
```

This writes a certificate/key pair (`cert.pem` / `key.pem`) to the working directory.

More details: [Bosch API docs — register a client](https://github.com/BoschSmartHome/bosch-shc-api-docs/tree/master/postman#register-a-new-client-to-the-bosch-smart-home-controller)

### Python API

```python
import boschshcpy

# Create session (lazy=False enumerates all devices on connect)
session = boschshcpy.SHCSession(
    controller_ip="192.168.25.51",
    certificate="cert.pem",
    key="key.pem",
)
session.information.summary()

# Access a device and service
device = session.device("roomClimateControl_hz_5")
service = device.device_service("TemperatureLevel")
print(service.temperature)

# Short-poll a single service
service.short_poll()

# Writing to a service — every writable service field has a setter.
# Sync property setter, or an async_set_* coroutine for the event loop:
device.multi_level_switch = 50              # sync write (PUT to the service)
await device.async_set_multi_level_switch(50)

# Motion Detector II examples (services the SHC exposes for the MD2 [+M]):
from boschshcpy.services_impl import DetectionTestService, PollControlService
md2 = session.device_helper.motion_detectors2[0]
md2.set_detection_state_request(                 # start a walk/detection test
    DetectionTestService.DetectionStateRequest.DETECTION_STATE_START)
md2.tamper_protection_enabled = True             # toggle tamper protection
md2.reset_tampered_state()                       # POST resetTamperedState
md2.long_poll_interval = PollControlService.PollControlState.SHORT  # orientation-light response
print(md2.profile, md2.supported_profiles)       # installation profile (read-only)

# Start long-poll thread (non-blocking)
session.start_polling()

# ... do work, handle callbacks ...

# Stop polling
session.stop_polling()

# Arm the intrusion detection system
session.intrusion_system.arm()

# Raw API dump
scan_result = session.rawscan(command="devices")
```

### Device helper accessors (`SHCSession.device_helper`)

`SHCDeviceHelper` exposes typed properties for each device category:

```
shutter_contacts, shutter_contacts2, shutter_controls,
micromodule_shutter_controls, micromodule_blinds, micromodule_relays,
micromodule_impulse_relays, micromodule_light_controls,
micromodule_light_attached, micromodule_dimmers, light_switches_bsm,
smart_plugs, smart_plugs_compact, smoke_detectors, smoke_detection_system,
climate_controls, heating_circuits, thermostats, wallthermostats,
roomthermostats, motion_detectors, motion_detectors2, twinguards,
universal_switches, camera_eyes, camera_360, camera_outdoor_gen2,
ledvance_lights, hue_lights, water_leakage_detectors,
presence_simulation_system
```

Other session attributes: `session.scenarios`, `session.rooms`, `session.intrusion_system`,
`session.emma` (EMMA grid power).

## Rawscans (command-line)

### Public information
```bash
boschshc_rawscan -ip YOUR_SHC_IP -cert cert.pem -key key.pem public_information
```

### All devices
```bash
boschshc_rawscan -ip YOUR_SHC_IP -cert cert.pem -key key.pem devices
```

### Single device
```bash
boschshc_rawscan -ip YOUR_SHC_IP -cert cert.pem -key key.pem device YOUR_DEVICE_ID
```

### Services of a device
```bash
boschshc_rawscan -ip YOUR_SHC_IP -cert cert.pem -key key.pem device_services YOUR_DEVICE_ID
```

### Single service of a device
```bash
boschshc_rawscan -ip YOUR_SHC_IP -cert cert.pem -key key.pem device_service YOUR_DEVICE_ID YOUR_SERVICE_ID
```

### All scenarios
```bash
boschshc_rawscan -ip YOUR_SHC_IP -cert cert.pem -key key.pem scenarios
```

### All rooms
```bash
boschshc_rawscan -ip YOUR_SHC_IP -cert cert.pem -key key.pem rooms
```

Example device output:
```json
{
    "@type": "device",
    "rootDeviceId": "xx-xx-xx-xx-xx-xx",
    "id": "hdm:HomeMaticIP:30xxx",
    "deviceServiceIds": [
        "Thermostat", "BatteryLevel", "ValveTappet",
        "SilentMode", "TemperatureLevel", "Linking", "TemperatureOffset"
    ],
    "manufacturer": "BOSCH",
    "roomId": "hz_8",
    "deviceModel": "TRV",
    "serial": "30xxx",
    "name": "Test Thermostat",
    "status": "AVAILABLE"
}
```

## Maintainers / support

| Role | |
|---|---|
| Original authors | Clemens-Alexander Brust ([@cabrust](https://github.com/cabrust)), Thomas Schamm ([@tschamm](https://github.com/tschamm)) |
| Co-maintainer | Thomas Mosandl ([@mosandlt](https://github.com/mosandlt)) |

[![Buy tschamm a coffee][buymecoffeebadge-tschamm]][buymecoffee-tschamm]
[![Buy mosandlts a coffee][buymecoffeebadge-mosandlts]][buymecoffee-mosandlts]

Bug reports and feature requests: [github.com/tschamm/boschshcpy/issues](https://github.com/tschamm/boschshcpy/issues)

[buymecoffee-tschamm]: https://www.buymeacoffee.com/tschamm
[buymecoffeebadge-tschamm]: https://img.shields.io/badge/buy%20tschamm%20a%20double%20espresso-donate-yellow.svg
[buymecoffee-mosandlts]: https://buymeacoffee.com/mosandlts
[buymecoffeebadge-mosandlts]: https://img.shields.io/badge/buy%20mosandlts%20a%20coffee-donate-yellow.svg
