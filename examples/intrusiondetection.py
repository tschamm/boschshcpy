#!/usr/bin/env python

import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import logging

import BoschShcPy

ACCESS_CERT = 'keystore/aps-cert.pem'
ACCESS_KEY = 'keystore/aps-key.pem'

logging.basicConfig(level=logging.DEBUG)

# SHUTTER_CONTACT_ID = "hdm:HomeMaticIP:3014F711A00018D878598448"
IP_SHC = '192.168.1.6'
PORT_SHC = '8444'

if __name__ == '__main__':
    try:
        # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
        client = BoschShcPy.Client(IP_SHC, PORT_SHC, ACCESS_CERT, ACCESS_KEY)
        
        shc_info = client.shc_information()
        print('  version        : %s' % shc_info.version)
        print('  updateState    : %s' % 'True' if shc_info.get_state() == BoschShcPy.shc_information.state.UPDATE_AVAILABLE else 'False')
        
        #   device = client.device(shutter_contact_ID)
        #   print(device)
        # 
        
        print("Accessing intrusion detection control...")
        intrusion_detection = BoschShcPy.IntrusionDetection(client)
        intrusion_detection.update()

        intrusion_detection.arm_instant()

        intrusion_detection.update()
        print(intrusion_detection)
        
        # print("Arming the IDC")
        # intrusion_detection.arm()
        # time.sleep(intrusion_detection.armActivationDelayTime)
        # intrusion_detection.update()
        # print(intrusion_detection)
        
#         print("Disarming the IDC")
#         intrusion_detection.disarm()
#         time.sleep(5)
#         intrusion_detection.update()
#         print(intrusion_detection)

        
#         client.request("smarthome/devices/"+item.id+"/services/BatteryLevel")
    
    except BoschShcPy.client.ErrorException as e:
        print('\nAn error occured while requesting a SmartPlug object:\n')
    
        for error in e.errors:
            print('  code        : %d' % error.code)
            print('  description : %s' % error.description)
            print('  parameter   : %s\n' % error.parameter)
