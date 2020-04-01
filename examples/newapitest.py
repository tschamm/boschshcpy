import os
import sys
import time
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import boschshcpy

# logging.basicConfig(level=logging.DEBUG)

# Create session
session = boschshcpy.SHCSession(
    controller_ip="192.168.1.6", certificate='examples/keystore/boschshcpy-cert.pem', key='examples/keystore/boschshcpy-key.pem')

for device in session.devices:
    device.summary()

for room in session.rooms:
    room.summary()

for scenario in session.scenarios:
    scenario.summary()

# scenario = session.scenario("7be2874f-6ef6-4a27-b68b-23c755835bed")
# scenario.summary()
# scenario.trigger()

shuttercontact = session.device("hdm:HomeMaticIP:3014F711A000009A18587DB1")
shuttercontact.summary()
print(shuttercontact.device_class)

shuttercontrols = session.device_helper.shutter_controls
for control in shuttercontrols:
    print(f"Name: {control.name}, level: {control.level}")

cameras = session.device_helper.camera_eyes
for cam in cameras:
    print(f"Name: {cam.name}, light: {cam.get_light_state}")


# shuttercontrol = session.device('hdm:HomeMaticIP:3014F711A00018D878598325')
# shuttercontrol.summary()
# print(shuttercontrol.level)
# shuttercontrol.set_level(0.)
# time.sleep(0.8)
# shuttercontrol.set_stopped()
# time.sleep(6)
# print(shuttercontrol.level)

# # Update this service's state


# def callback():
#     print("callback ...")
#     print(service.state)

# service.set_callback(callback)

# # Start long polling thread in background
# session.start_polling()

# # Do work here
# service.put_state_element('level', '0.0')
# time.sleep(2)

# # Stop polling
# session.stop_polling()

# # service.put_state_element('level', '0.0')
# # print(service.value)
