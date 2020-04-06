# Bosch Smart Home Controller API Python Library

This library implements the local communication REST API for the Bosch Smart Home Controller system.
The API documentation is available [here](https://github.com/BoschSmartHome/bosch-shc-api-docs).
It supports both long and short polling. The following device services are implemented:

* ```TemperatureLevel```
* ```RoomClimateControl```
* ```ShutterContact```
* ```ValveTappet```
* ```PowerSwitch```
* ```PowerMeter```
* ```Routing```
* ```PowerSwitchProgram```
* ```BinarySwitch```
* ```SmokeDetectorCheck```
* ```Alarm```
* ```ShutterControl```
* ```CameraLight```
* ```PrivacyMode```
* ```CameraNotification```
* ```IntrusionDetectionControl```

The following device models are implemented, using the above services:

* ```ShutterContact```
* ```ShutterControl```
* ```SmartPlug```
* ```SmokeDetector```
* ```CameraEyes```
* ```-IntrusionDetectionSystem-```

## Example

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
intrusion_control = session.device_helper.intrusion_detection_system
intrusion_control.arm_instant()
```

## Usage guide

Before accessing the Bosch Smart Home Controller, a client must be registered on the controller. For this a valid cert/key pair must be provided to the controller. To start the client registration, press and hold the button on the controller until the led starts flashing. More information [here](https://github.com/BoschSmartHome/bosch-shc-api-docs/tree/master/postman#register-a-new-client-to-the-bosch-smart-home-controller)
