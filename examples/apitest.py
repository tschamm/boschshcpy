#!/usr/bin/env python

# Use this script to register a new client connection to Bosch Smart Home products
# See https://github.com/BoschSmartHome/bosch-shc-api-docs
# Before executing the script to register a new client, the button on the controller has to be pressed until the LED begins flashing.

import os, sys
import time
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import BoschShcPy

def api_test():
    try:
        ACCESS_CERT = args.access_cert
        ACCESS_KEY = args.access_key
        if not os.path.isfile(ACCESS_CERT) or not os.path.isfile(ACCESS_KEY):
            print ("No valid cert or key file, aborting!")
            sys.exit()

        # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
        client = BoschShcPy.Client(args.ip_address, args.port, ACCESS_CERT, ACCESS_KEY)
        api = BoschShcPy.Api(client)

        token = api.register_client(args.id, args.name, args.password)
        if token != None:
            print('successful registered new device with token {}'.format(token))
        else:
            print('No valid token received, did you press client registration button on smart home controller?')
            sys.exit()
        
        shc_info = client.shc_information()
        print('  version        : %s' % shc_info.version)
        print('  updateState    : %s' % shc_info.updateState)
        

    except BoschShcPy.client.ErrorException as e:
        print('\nAn error occured during new client registration:\n')
    
if __name__ == "__main__":
    import argparse, sys
    
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-pw", "--password",
                        help="systempassword - encoded in base64 - which you have set-up initially in the SHC-Setup process.")
    parser.add_argument("-ac", "--access_cert",
                        help="Path to access certificat.",
                        default="keystore/boschshc-cert.pem")
    parser.add_argument("-ak", "--access_key",
                        help="Path to access key.",
                        default="keystore/boschshc-key.pem")
    parser.add_argument("-n", "--name",
                        help="Name of the new client user.",
                        default="SHC Api Test")
    parser.add_argument("-id", "--id",
                        help="ID of the new client user.",
                        default="shc_api_test")
    parser.add_argument("-ip", "--ip_address",
                        help="IP of the smart home controller.")
    parser.add_argument("-p", "--port",
                        help="Port of the smart home controller.",
                        default="8443")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    api_test()
