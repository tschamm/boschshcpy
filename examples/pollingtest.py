import os
import sys, time
import zeroconf
import logging
from zeroconf import Zeroconf

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from boschshcpy import SHCSession, SHCDevice

logging.basicConfig(level=logging.DEBUG)


def callback():
    print("Notification of device update")


def setup_session():
    # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
    zeroconf = Zeroconf()
    session = SHCSession(
        controller_ip="192.168.1.6",
        certificate="../keystore/dev-cert.pem",
        key="../keystore/dev-key.pem",
        zeroconf=zeroconf,
    )
    zeroconf.close()

    shc_info = session.information
    print("  version        : %s" % shc_info.version)
    print("  updateState    : %s" % shc_info.updateState)

    print("Accessing all devices...")

    smart_plugs = session.device_helper.smart_plugs
    for item in smart_plugs:
        for service in item.device_services:
            service.subscribe_callback(item.id, callback)

    shutter_controls: SHCDevice = session.device_helper.shutter_controls
    for item in shutter_controls:
        for service in item.device_services:
            service.subscribe_callback(item.id, callback)

    return session


def main():
    exit = False
    session = setup_session()
    duration = 0
    while not exit:
        userInput = input("Enter seconds for polling duration (or nothing to exit) ")

        if userInput.isdigit():
            duration = int(userInput)
            print("Starting polling for {} seconds".format(duration))
            session.start_polling()
            time.sleep(duration)
            if session.emma:
                session.emma.summary()
            session.stop_polling()
            print("Stopping polling")
        else:
            exit = True
            print("OK Bye, bye.")


if __name__ == "__main__":
    main()
