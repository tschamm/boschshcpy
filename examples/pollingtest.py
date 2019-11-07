#!/usr/bin/env python

import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import time
import logging

import BoschShcPy

ACCESS_CERT = 'keystore/aps-cert.pem'
ACCESS_KEY = 'keystore/aps-key.pem'

logging.basicConfig(level=logging.INFO)

IP_SHC = '192.168.1.6'
PORT_SHC = '8444'

def callback(device):
    print("Notification of device update:")
    print(device)

def setup_client():
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

        smart_plugs = BoschShcPy.smart_plug.initialize_smart_plugs(client, client.device_list())
        for item in smart_plugs:
            client.register_device(item, callback)
            client.register_device(item.device, callback)

        shutter_controls = BoschShcPy.shutter_control.initialize_shutter_controls(client, client.device_list())
        for item in shutter_controls:
            client.register_device(item, callback)
            client.register_device(item.device, callback)

        shutter_contacts = BoschShcPy.shutter_contact.initialize_shutter_contacts(client, client.device_list())
        for item in shutter_contacts:
            client.register_device(item, callback)
            client.register_device(item.device, callback)

        # intrusion_detection = BoschShcPy.IntrusionDetection(client)
        # intrusion_detection.register_polling(client, callback)

    except BoschShcPy.client.ErrorException as e:
        print('\nAn error occured while requesting a SmartPlug object:\n')

        for error in e.errors:
            print('  code        : %d' % error.code)
            print('  description : %s' % error.description)
            print('  parameter   : %s\n' % error.parameter)

    return client

def main():
    exit = False
    client = setup_client()
    duration = 0
    while not exit:
        userInput = input("Enter seconds for polling duration (or nothing to exit) ")

        if userInput.isdigit():
            duration = int(userInput)
            print("Starting polling for {} seconds".format(duration))
            client.start_subscription()
            time.sleep(duration)
            client.stop_subscription()
            print("Stopping polling")
        else:
            exit = True
            print("OK Bye, bye.")

if __name__ == "__main__":
    main()