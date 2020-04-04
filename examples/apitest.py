#!/usr/bin/env python

# Use this script to register a new client connection to Bosch Smart Home products
# See https://github.com/BoschSmartHome/bosch-shc-api-docs
# Before executing the script to register a new client, the button on the controller has to be pressed until the LED begins flashing.

import os, sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import boschshcpy

def api_test():
    session = boschshcpy.SHCSession(args.ip_address, args.access_cert, args.access_key, False)
    session.information.summary()
    
    if session.information.version != "n/a":
        session.reinitialize()

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

    api_test()
