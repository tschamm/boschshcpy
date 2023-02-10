import base64
import json
import logging
import os.path
import sys

import pkg_resources
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

from .exceptions import SHCRegistrationError, SHCSessionError
from .generate_cert import generate_certificate

logger = logging.getLogger("boschshcpy")


class HostNameIgnoringAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, assert_hostname=False
        )


class SHCRegisterClient:
    """Press and hold the button at the front of the SHC until the lights are flashing before you POST the command. When the SHC is not in pairing mode, there will be a connection error."""

    def __init__(self, controller_ip: str, password: str):
        """Initializes with IP address and access credentials."""
        self._controller_ip = controller_ip
        self._url = f"https://{self._controller_ip}:8443/smarthome/clients"

        # Settings for API call
        password_base64 = base64.b64encode(password.encode("utf-8"))
        self._requests_session = requests.Session()
        self._requests_session.mount("https://", HostNameIgnoringAdapter())
        self._requests_session.headers.update(
            {
                "Content-Type": "application/json",
                "Systempassword": password_base64.decode("utf-8"),
            }
        )
        self._requests_session.verify = pkg_resources.resource_filename(
            "boschshcpy", "tls_ca_chain.pem"
        )

        import urllib3

        urllib3.disable_warnings()

    def _post_api_or_fail(self, body, timeout=30):
        try:
            result = self._requests_session.post(
                self._url, data=json.dumps(body), timeout=timeout
            )
            if not result.ok:
                self._process_nok_result(result)
            if len(result.content) > 0:
                return json.loads(result.content)
            else:
                return {}
        except requests.exceptions.SSLError as e:
            raise SHCRegistrationError(
                f"SHC probably not in pairing mode! Please press the Bosch Smart Home Controller button until LED starts flashing.\n(SSL Error: {e})."
            )

    def _process_nok_result(self, result):
        raise SHCRegistrationError(
            f"API call returned non-OK result (code {result.status_code})!: {result.content}... Please check your password?"
        )

    def register(self, client_id, name):
        cert, key = generate_certificate(client_id, name)
        cert_str = (
            cert.decode("utf-8")
            .replace("\n", "")
            .replace("-----BEGIN CERTIFICATE-----", "-----BEGIN CERTIFICATE-----\r")
            .replace("-----END CERTIFICATE-----", "\r-----END CERTIFICATE-----")
        )

        data = {
            "@type": "client",
            "id": client_id,
            "name": f"oss_{name}_Binding",
            "primaryRole": "ROLE_RESTRICTED_CLIENT",
            "certificate": cert_str,
        }
        logger.debug(
            f"Registering new client with id {data['id']} and name {data['name']}."
        )

        result = self._post_api_or_fail(data)
        return (
            {"token": result["token"], "cert": cert, "key": key}
            if "token" in result
            else None
        )


def write_tls_asset(filename: str, asset: bytes) -> None:
    """Write the tls assets to disk."""
    with open(filename, "w", encoding="utf8") as file_handle:
        file_handle.write(asset.decode("utf-8"))


def main():
    import argparse, sys

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-pw",
        "--password",
        help="system password which was set-up initially in the SHC setup process.",
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Name of the new client user (default: BOSCHSHCPY_Client)",
        default="BOSCHSHCPY_Client",
    )
    parser.add_argument(
        "-id",
        "--id",
        help="ID of the new client user (default: boschshcpy_client)",
        default="boschshcpy_client",
    )
    parser.add_argument("-ip", "--ip_address", help="IP of the smart home controller.")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
    helper = SHCRegisterClient(args.ip_address, args.password)
    result = None
    try:
        result = helper.register(args.id, args.name)
    except SHCRegistrationError as e:
        print(e)

    if result != None:
        print("successful registered new device with token {}".format(result["token"]))
        print(f"Cert: {result['cert']}")
        print(f"Key: {result['key']}")

        hostname = result["token"].split(":", 1)[1]
        print(
            f"Create new certificate key pair: {'oss_' + args.id + '_' + hostname + '_cert.pem'} {'oss_' + args.id + '_' + hostname + '_key.pem'}"
        )
        write_tls_asset("oss_" + args.id + "_" + hostname + "_cert.pem", result["cert"])
        write_tls_asset("oss_" + args.id + "_" + hostname + "_key.pem", result["key"])

    else:
        print(
            "No valid token received. Did you press client registration button on smart home controller?"
        )
        sys.exit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
