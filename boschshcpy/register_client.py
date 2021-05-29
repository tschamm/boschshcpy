import asyncio
import base64
import json
import logging
import os.path
import ssl

import aiohttp
import pkg_resources

from .exceptions import SHCRegistrationError, SHCSessionError
from .generate_cert import generate_certificate

logger = logging.getLogger("boschshcpy")


class SHCRegisterClient:
    """ Press and hold the button at the front of the SHC until the lights are blinking before you POST the command. When the SHC is not in pairing mode, there will be a connection error."""

    def __init__(self, controller_ip: str, password: str):
        """Initializes with IP address and access credentials."""
        self._controller_ip = controller_ip
        self._url = f"https://{self._controller_ip}:8443/smarthome/clients"
        self._cafile = pkg_resources.resource_filename("boschshcpy", "tls_ca_chain.pem")
        self._password_base64 = base64.b64encode(password.encode("utf-8"))

        self._requests_session = None
        self._sslcontext = None

    async def _post_api_or_fail(self, body, timeout=30):
        try:
            async with self._requests_session.post(
                self._url, data=json.dumps(body), timeout=timeout, ssl=self._sslcontext
            ) as result:
                if not result.ok:
                    self._process_nok_result(result)
                return await result.json()
        except aiohttp.ClientSSLError as err:
            raise SHCRegistrationError(
                f"SHC probably not in pairing mode! Please press the Bosch Smart Home Controller button until LED starts blinking.\n(SSL Error: {err})."
            )

    def _process_nok_result(self, result):
        raise SHCRegistrationError(
            f"API call returned non-OK result (code {result.status})!: {result.content}... Please check your password?"
        )

    async def register(self, session, client_id, name, certificate=None):
        self._requests_session = session

        self._sslcontext = ssl.create_default_context(cafile=self._cafile)
        self._sslcontext.verify_mode = ssl.CERT_REQUIRED
        self._sslcontext.check_hostname = False

        self._requests_session.headers.update(
            {
                "api-version": "2.1",
                "Content-Type": "application/json",
                "Systempassword": self._password_base64.decode("utf-8"),
            }
        )

        cert = key = None
        if not certificate:
            cert, key = generate_certificate(client_id, name)
            certstr = (
                cert.decode("utf-8")
                .replace("\n", "")
                .replace("-----BEGIN CERTIFICATE-----", "-----BEGIN CERTIFICATE-----\r")
                .replace("-----END CERTIFICATE-----", "\r-----END CERTIFICATE-----")
            )

        else:
            if not os.path.exists(certificate):
                logger.error("No valid cert file, aborting!")
                # only continue if path to certificate is valid
                return None

            with open(certificate, "r") as file:
                certstr = (
                    file.read()
                    .replace("\n", "")
                    .replace(
                        "-----BEGIN CERTIFICATE-----", "-----BEGIN CERTIFICATE-----\r"
                    )
                    .replace("-----END CERTIFICATE-----", "\r-----END CERTIFICATE-----")
                )

        data = {
            "@type": "client",
            "id": client_id,
            "name": f"oss_{name}_Binding",
            "primaryRole": "ROLE_RESTRICTED_CLIENT",
            "certificate": certstr,
        }

        result = await self._post_api_or_fail(data)
        return (
            {"token": result["token"], "cert": cert, "key": key}
            if "token" in result
            else None
        )
