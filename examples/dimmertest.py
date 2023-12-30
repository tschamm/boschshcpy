#!/usr/bin/env python

# Use this script to register a new client connection to Bosch Smart Home products
# See https://github.com/BoschSmartHome/bosch-shc-api-docs
# Before executing the script to register a new client, the button on the controller has to be pressed until the LED begins flashing.

import os, sys
from random import randint
import time
import logging

#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import boschshcpy

def dimmer_test():
    session = boschshcpy.SHCSession(args.ip_address, args.access_cert, args.access_key, False)
    #session.information.summary()


    #dimmers = session.device_helper.micromodule_dimmers
    #devices = session._devices_by_id
    devices = session.devices
    for device in devices:
        if(device.id == "hdm:ZigBee:0cae5ffffe3a99c3"):
            dimmer = device
            #dimmer.state = False
    
    

    for dimmer in session.device_helper.micromodule_dimmers:
        dimmer.summary()
    
    new_brightness = randint(1, 50)
    #dimmer.brightness = new_brightness
    print(new_brightness)
    dimmer.state = True
    print(dimmer.state)

    exit()  
    
    plugs = session.device_helper.smart_plugs_compact
    for plug in plugs:        
        if(plug.name == "Tannenbaum"):
            if(plug.state == plug.PowerSwitchService.State.ON):
                plug.state = False
            else:
                plug.state = True
    

if __name__ == "__main__":
    import argparse, sys
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-ac", "--access_cert",
                        help="Path to access certificate.",
                        default="keystore/boschshc-cert.pem")
    parser.add_argument("-ak", "--access_key",
                        help="Path to access key.",
                        default="keystore/boschshc-key.pem")
    parser.add_argument("-ip", "--ip_address",
                        help="IP of the smart home controller.")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    dimmer_test()