#!/usr/bin/env python

import sys, os, time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import BoschShcPy

ACCESS_CERT = 'keystore/aps-cert.pem'
ACCESS_KEY = 'keystore/aps-key.pem'

HDM_ID = "hdm:Cameras:fa991a12-8c6b-3f3c-b9c5-727ff4c318b6"
IP_SHC = '192.168.1.6'
PORT_SHC = '8444'


try:
    # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
    client = BoschShcPy.Client(IP_SHC, PORT_SHC, ACCESS_CERT, ACCESS_KEY)
    
    shc_info = client.shc_information()
    print('  version        : %s' % shc_info.version)
    print('  updateState    : %s' % shc_info.updateState)
    
    #   device = client.device(SMART_PLUG_ID)
    #   print(device)
    # 
    
    # print("Accessing a dummy device...")
    # camera = BoschShcPy.CameraEyes(
    #     client, BoschShcPy.Device(), HDM_ID, "Dummy")
    # camera.update()
    # print(camera)
    
    # print("Toggle state of dummy device...")
    # state = camera.get_light_state
    # camera.set_light_state(not state)
    # print(camera)
    # time.sleep(2)
    # camera.set_light_state(state)
    # print(camera)

    print("Accessing all camera devices...")
    cameras = BoschShcPy.camera_eyes.initialize_camera_eyes(
        client, client.device_list())
    for item in cameras:
        print (item)

except BoschShcPy.client.ErrorException as e:
    print('\nAn error occured while requesting a SmartPlug object:\n')

    for error in e.errors:
        print('  code        : %d' % error.code)
        print('  description : %s' % error.description)
        print('  parameter   : %s\n' % error.parameter)
