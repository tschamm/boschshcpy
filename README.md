# Bosch Smart Home Controller API Python Library

This library implements the local communication REST API for the Bosch Smart Home Controller system. It supports both long and short polling. The API documentation is available [here](https://github.com/BoschSmartHome/bosch-shc-api-docs).

The following device services are implemented:

* ```TemperatureLevel```
* ```HumidityLevel```
* ```RoomClimateControl```
* ```ShutterContact```
* ```ValveTappet```
* ```PowerSwitch```
* ```PowerMeter```
* ```Routing```
* ```PowerSwitchProgram```
* ```PresenceSimulationConfiguration```
* ```BinarySwitch```
* ```SmokeDetectorCheck```
* ```Alarm```
* ```ShutterControl```
* ```CameraLight```
* ```PrivacyMode```
* ```CameraNotification```
* ```IntrusionDetectionControl```
* ```Keypad```
* ```LatestMotion```
* ```AirQualityLevel```
* ```SurveillanceAlarm```
* ```BatteryLevel```
* ```Thermostat```
* ```WaterLeakageSensor```
* ```WaterLeakageSensorTilt```
* and more

The following device models are implemented, using the above services:

* ```ShutterContact```, ```ShutterContact2```
* ```ShutterControl```, ```Micromodule Shutter```
* ```SmartPlug```
* ```SmartPlugCompact```
* ```LightControl```, ```Micromodule Light Control```, ```Micromodule Light Attached```, ```Micromodule Relay```
* ```SmokeDetector```
* ```CameraEyes```, ```Camera360```
* ```IntrusionDetectionSystem```
* ```RoomClimateControl```
* ```Thermostat```, ```Thermostat2```
* ```WallThermostat```
* ```UniversalSwitch```
* ```MotionDetector```
* ```PresenceSimulationSystem```
* ```Twinguard```
* ```WaterLeakageSensor```

## Command line access to SHC
1. Install a `python` (>=3.10) environment on your computer.
2. Install latest version of `boschshcpy`, you should have at least `version>=0.2.45`.
```bash
pip install boschshcpy
```

### Registering a new client

To register a new client, use the script `boschshc_registerclient`:
```bash
boschshc_registerclient -ip _your_shc_ip_ -pw _your_shc_password_
```

This will register your client and will write the associated certificate/key pair into your working directory. See also [Usage Guide](#usage-guide)

### Rawscans

To make a rawscan of your devices, use the script `boschshc_rawscan`

#### Make a rawscan of the public information
```bash
boschshc_rawscan -ip _your_shc_ip_ -cert _your_shc_cert_file_ -key _your_shc_key_file_ public_information
```

#### Make a rawscan of all devices
```bash
boschshc_rawscan -ip _your_shc_ip_ -cert _your_shc_cert_file_ -key _your_shc_key_file_ devices
```

#### Make a rawscan of a single device with a known `device_id`
```bash
boschshc_rawscan -ip _your_shc_ip_ -cert _your_shc_cert_file_ -key _your_shc_key_file_ device _your_device_id_
```

An exemplary output looks as follows:
```bash
    {
        "@type": "device",
        "rootDeviceId": "xx-xx-xx-xx-xx-xx",
        "id": "hdm:HomeMaticIP:30xxx",
        "deviceServiceIds": [
            "Thermostat",
            "BatteryLevel",
            "ValveTappet",
            "SilentMode",
            "TemperatureLevel",
            "Linking",
            "TemperatureOffset"
        ],
        "manufacturer": "BOSCH",
        "roomId": "hz_8",
        "deviceModel": "TRV",
        "serial": "30xxx",
        "profile": "GENERIC",
        "name": "Test Thermostat",
        "status": "AVAILABLE",
        "parentDeviceId": "roomClimateControl_hz_8",
        "childDeviceIds": []
    },
```

#### Make a rawscan of the associated services of a device
```bash
boschshc_rawscan -ip _your_shc_ip_ -cert _your_shc_cert_file_ -key _your_shc_key_file_ device_services _your_device_id_
```

The exemplary output will look as follows:
```bash
[
    {
        "@type": "DeviceServiceData",
        "id": "BatteryLevel",
        "deviceId": "hdm:HomeMaticIP:30xxx",
        "path": "/devices/hdm:HomeMaticIP:30xxx/services/BatteryLevel"
    },
    {
        "@type": "DeviceServiceData",
        "id": "Thermostat",
        "deviceId": "hdm:HomeMaticIP:30xxx",
        "state": {
            "@type": "childLockState",
            "childLock": "OFF"
        },
        "path": "/devices/hdm:HomeMaticIP:30xxx/services/Thermostat"
    },
...
]
```

#### Make a rawscan of the a service of a device, where the `device_id` as well as the `service_id` are known
```bash
boschshc_rawscan -ip _your_shc_ip_ -cert _your_shc_cert_file_ -key _your_shc_key_file_ device_service _your_device_id_ _your_service_id
```

#### Make a rawscan of the all scenarios
```bash
boschshc_rawscan -ip _your_shc_ip_ -cert _your_shc_cert_file_ -key _your_shc_key_file_ scenarios
```

#### Make a rawscan of the all rooms
```bash
boschshc_rawscan -ip _your_shc_ip_ -cert _your_shc_cert_file_ -key _your_shc_key_file_ rooms
```

## Example code to use the `boschshcpy` library

```python
import boschshcpy

# Create session
session = boschshcpy.SHCSession(controller_ip="192.168.25.51", certificate='cert.pem', key='key.pem')
session.information.summary()

device = session.device('roomClimateControl_hz_5')
service = device.device_service('TemperatureLevel')
print(service.temperature)

# Update this service's state
service.short_poll()

# Start long polling thread in background
session.start_polling()

# Do work here
...

# Stop polling
session.stop_polling()

# Trigger intrusion detection system
intrusion_control = session.intrusion_system
intrusion_control.arm()

# Get rawscan of devices
scan_result = session.rawscan(command="devices")
```

## Usage guide

Before accessing the Bosch Smart Home Controller, a client must be registered on the controller. For this a valid cert/key pair must be provided to the controller. To start the client registration, press and hold the button on the controller until the led starts flashing. More information [here](https://github.com/BoschSmartHome/bosch-shc-api-docs/tree/master/postman#register-a-new-client-to-the-bosch-smart-home-controller).
