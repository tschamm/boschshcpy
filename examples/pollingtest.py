#!/usr/bin/env python

import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import time

import BoschShcPy
from BoschShcPy.polling_service import PollingService

ACCESS_CERT = 'keystore/aps-cert.pem'
ACCESS_KEY = 'keystore/aps-key.pem'

# SHUTTER_CONTROL_ID = "hdm:HomeMaticIP:3014F711A00018D878598448"
IP_SHC = '192.168.1.6'
PORT_SHC = '8443'

def callback(device):
    print("Notification of device update")
    print(device)

try:
    # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
    client = BoschShcPy.Client(IP_SHC, PORT_SHC, ACCESS_CERT, ACCESS_KEY)
    
    shc_info = client.shc_information()
    print('  version        : %s' % shc_info.version)
    print('  updateState    : %s' % shc_info.updateState)
    
    #   device = client.device(shutter_control_ID)
    #   print(device)
    # 
    
    print("Accessing all devices...")
    
    hashed_devices = {}
#     client.register_device_list(client.device_list(), callback)
    
    hashed_plugs = {}
    smart_plugs = BoschShcPy.smart_plug.initialize_smart_plugs(client, client.device_list())
    for item in smart_plugs:
#         item.update()
#         hashed_plugs[item.id] = item
#         hashed_devices[item.id] = item
        client.register_device(item, callback)
        client.register_device(item.device, callback)

    hashed_controls = {}
    shutter_controls = BoschShcPy.shutter_control.initialize_shutter_controls(client, client.device_list())
    for item in shutter_controls:
#         item.update()
        client.register_device(item, callback)
        client.register_device(item.device, callback)
#         hashed_controls[item.id] = item
#         hashed_devices[item.id] = item

    print("Starting polling")
    client.start_subscription()
    time.sleep(20)
    client.stop_subscription()
#     polling_service = PollingService()
#     polling_service.id = "boschshc"
#     polling_service.result = "e68d0iag5-12"



#     i = 0
#     while(i < 5):
#         i = i+1
#         query = client.polling(polling_service, 10)
# #         print (query)
#         for elem in list(query):
#             if 'result' in elem.keys():
#                 for result in elem['result']:
# #                     print(result)
#                     if result['deviceId'] in hashed_devices:
#                         hashed_devices[result['deviceId']].update_from_query(result)
#                         print(hashed_plugs[result['deviceId']])
# 
    print("Stopping polling")
#     client.unsubscribe_polling(polling_service)


except BoschShcPy.client.ErrorException as e:
    print('\nAn error occured while requesting a SmartPlug object:\n')

    for error in e.errors:
        print('  code        : %d' % error.code)
        print('  description : %s' % error.description)
        print('  parameter   : %s\n' % error.parameter)
