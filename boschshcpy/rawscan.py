import json
import logging
import os, sys

from boschshcpy import SHCSession, SHCDeviceHelper, SHCAuthenticationError

logger = logging.getLogger("boschshcpy")

#### Main Program ####


def main():
    import argparse, sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--certificate",
        "-cert",
        help="Certificate of a registered client.",
    )
    parser.add_argument(
        "--key",
        "-key",
        help="Key of a registered client.",
    )
    parser.add_argument("--ip_address", "-ip", help="IP of the smart home controller.")

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.required = True

    parser_device = subparsers.add_parser("devices")
    parser_device = subparsers.add_parser("services")
    parser_device = subparsers.add_parser("scenarios")
    parser_device = subparsers.add_parser("rooms")
    parser_device = subparsers.add_parser("info")
    parser_device = subparsers.add_parser("information")
    parser_device = subparsers.add_parser("public_information")
    parser_device = subparsers.add_parser("intrusion_detection")

    parser_service = subparsers.add_parser("device")
    parser_service.add_argument("device_id", help="Specify the device id.")

    parser_device = subparsers.add_parser("device_services")
    parser_device.add_argument("device_id", help="Specify the device id.")

    parser_service = subparsers.add_parser("device_service")
    parser_service.add_argument("device_id", help="Specify the device id.")
    parser_service.add_argument("service_id", help="Specify the service id.")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
    try:
        session = SHCSession(
            controller_ip=args.ip_address,
            certificate=args.certificate,
            key=args.key,
        )
    except SHCAuthenticationError as e:
        print(e)
        sys.exit()

    match (args.subcommand):
        case "devices":
            print(json.dumps(session.api.get_devices(), indent=4))

        case "services":
            print(json.dumps(session.api.get_services(), indent=4))

        case "rooms":
            print(json.dumps(session.api.get_rooms(), indent=4))

        case "scenarios":
            print(json.dumps(session.api.get_scenarios(), indent=4))

        case "device":
            print(json.dumps(session.api.get_device(args.device_id), indent=4))

        case "device_services":
            print(json.dumps(session.api.get_device_services(args.device_id), indent=4))

        case "device_service":
            print(
                json.dumps(
                    session.api.get_device_service(args.device_id, args.service_id),
                    indent=4,
                )
            )

        case "info" | "information":
            print(json.dumps(session.api.get_information(), indent=4))

        case "public_information":
            print(json.dumps(session.api.get_public_information(), indent=4))

        case "intrusion_detection":
            print(json.dumps(session.api.get_domain_intrusion_detection(), indent=4))

        case _:
            print("Please select a valid mode.")

    sys.exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
