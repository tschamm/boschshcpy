#!/usr/bin/env python

# Use this script to see messages from api

import os, sys
import time
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import boschshcpy

logger = logging.getLogger("boschshcpy")

def api_test():
    session = boschshcpy.SHCSession(args.ip_address, args.access_cert, args.access_key, False)
    #session.information.summary()
    logger.debug("getting messages")
    for _message in session.messages:
        print(_message.summary())

if __name__ == "__main__":
    import argparse, sys

    logging.basicConfig(level=logging.DEBUG)
    
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
