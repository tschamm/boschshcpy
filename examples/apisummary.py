import os
import sys
import logging
import zeroconf
from zeroconf import Zeroconf

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from boschshcpy import (
    SHCSession,
    SHCDeviceHelper,
    SHCThermostat,
    SHCBatteryDevice,
    SHCShutterContact,
    SHCShutterContact2,
)

# Create session with additional zeroconf info
zeroconf = Zeroconf()
session = SHCSession(
    controller_ip="192.168.1.6",
    certificate="../keystore/dev-cert.pem",
    key="../keystore/dev-key.pem",
    zeroconf=zeroconf,
)
zeroconf.close()

for device in session.devices:
    device.summary()

for room in session.rooms:
    room.summary()

for scenario in session.scenarios:
    scenario.summary()

for state in session.userdefinedstates:
    state.summary()

session.intrusion_system.summary()

session.information.summary()

res = session.rawscan(
    command="device_service",
    device_id="hdm:ZigBee:000d6f000b856cb6",
    service_id="MultiLevelSensor",
)

device = next(iter(session.device_helper.shutter_contacts))
print(f"isinstance SHCShutterContact2: {isinstance(device, SHCShutterContact2)}")
print(f"isinstance SHCShutterContact: {isinstance(device, SHCShutterContact)}")
print(f"isinstance SHCBatteryDevice: {isinstance(device, SHCBatteryDevice)}")

print(res)
res = session.rawscan(command="intrusion_detection")
print(res)
