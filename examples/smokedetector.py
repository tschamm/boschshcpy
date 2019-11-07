#!/usr/bin/env python

import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import time

import BoschShcPy

ACCESS_CERT = 'keystore/aps-cert.pem'
ACCESS_KEY = 'keystore/aps-key.pem'

IP_SHC = '192.168.1.6'
PORT_SHC = '8444'


try:
    # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
    client = BoschShcPy.Client(IP_SHC, PORT_SHC, ACCESS_CERT, ACCESS_KEY)
    
    shc_info = client.shc_information()
    print('  version        : %s' % shc_info.version)
    print('  updateState    : %s' % shc_info.updateState)
    
    #   device = client.device(shutter_control_ID)
    #   print(device)
    # 
    
    print("Accessing all smoke detector devices...")
    smoke_detectors = BoschShcPy.smoke_detector.initialize_smoke_detectors(client, client.device_list())
    for item in smoke_detectors:
        item.update()
        print(item)

except BoschShcPy.client.ErrorException as e:
    print('\nAn error occured while requesting a SmartPlug object:\n')

    for error in e.errors:
        print('  code        : %d' % error.code)
        print('  description : %s' % error.description)
        print('  parameter   : %s\n' % error.parameter)
