# Bosch Smart Home Local API Python Library

This library implements the local communication REST API for the Bosch Smart Home system.
The API documentation is available [here](https://github.com/BoschSmartHome/bosch-shc-api-docs).
It supports both long and short polling. The following device services are implemented:
 * ```TemperatureLevel```
 * ```ValveTappet```
 * ```ShutterContact```
 * ```RoomClimateControl```

Example:
```python
import bshlocal

# Create session
session = bshlocal.BSHLocalSession(controller_ip="192.168.25.51", certificate='cert.pem', key='key.pem')
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
```

# boschshcpy
Python3 package to access Bosch Smart Home Components (see https://github.com/BoschSmartHome/bosch-shc-api-docs)

Using the provided example code, the ip address of the Smart Home Controller has to be changed and a valid 
certificate keypair has to be provided.

Usage example:
```bash
cd examples && mkdir keystore
python3 apitest.py -pw "Your base64 encoded controller password" -ac keystore/test-cert.pem -ak keystore/test-key.pem -n "Your Application" -ip "IP of the controller"
```

More documentation to follow.
