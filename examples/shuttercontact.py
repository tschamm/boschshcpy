#!/usr/bin/env python

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import time
import logging

import BoschShcPy

ACCESS_CERT = 'keystore/boschshc-cert.pem'
ACCESS_KEY = 'keystore/boschshc-key.pem'

logging.basicConfig(level=logging.DEBUG)

# SHUTTER_CONTACT_ID = "hdm:HomeMaticIP:3014F711A00018D878598448"
IP_SHC = '192.168.1.6'
PORT_SHC = '8444'

def callback(device):
    print("Notification of device update")
    print(device)

if __name__ == '__main__':
    try:
        # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
        client = BoschShcPy.Client(IP_SHC, PORT_SHC, ACCESS_CERT, ACCESS_KEY)

        shc_info = client.shc_information()
        print('  version        : %s' % shc_info.version)
        print('  updateState    : %s' % shc_info.updateState)

        #   device = client.device(shutter_contact_ID)
        #   print(device)
        #

        print("Accessing all shutter contact devices...")
        shutter_contacts = BoschShcPy.shutter_contact.initialize_shutter_contacts(client, client.device_list())
        for item in shutter_contacts:
            item.async_update(callback)
            # item.update()
            # print(item)

#         client.request("smarthome/devices/"+item.id+"/services/BatteryLevel")

    except BoschShcPy.client.ErrorException as e:
        print('\nAn error occured while requesting a SmartPlug object:\n')

        for error in e.errors:
            print('  code        : %d' % error.code)
            print('  description : %s' % error.description)
            print('  parameter   : %s\n' % error.parameter)
