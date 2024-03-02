#!/usr/bin/env python

# Use this script to register a new client connection to Bosch Smart Home products
# See https://github.com/BoschSmartHome/bosch-shc-api-docs
# Before executing the script to register a new client, the button on the controller has to be pressed until the LED begins flashing.

import os, sys
import time
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from boschshcpy.register_client import SHCRegisterClient
import boschshcpy

def registering():
    # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
    helper = SHCRegisterClient(args.ip_address, args.password)
    #result = helper.register(args.id, args.name, args.access_cert)
    result = helper.register(args.id, args.name)

    if result != None:
        print('successful registered new device with token {}'.format(result["token"]))
        print(f"Cert: {result['cert']}")
        print(f"Key: {result['key']}")
    else:
        print('No valid token received. Did you press client registration button on smart home controller?')
        sys.exit()

if __name__ == "__main__":
    import argparse, sys
    
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-pw", "--password",
                        help="systempassword was set-up initially in the SHC setup process.")
    parser.add_argument("-ac", "--access_cert",
                        help="Path to access certificat.",
                        default=None)
    parser.add_argument("-n", "--name",
                        help="Name of the new client user.",
                        default="SHC Api Test")
    parser.add_argument("-id", "--id",
                        help="ID of the new client user.",
                        default="shc_api_test")
    parser.add_argument("-ip", "--ip_address",
                        help="IP of the smart home controller.")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    registering()
