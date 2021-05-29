import asyncio
import json
import logging
import ssl

import aiohttp
import pkg_resources

from .exceptions import SHCSessionError

logger = logging.getLogger("boschshcpy")


class JSONRPCError(Exception):
    def __init__(self, code, message):
        super().__init__()
        self._code = code
        self._message = message

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    def __str__(self):
        return f"JSONRPCError (code: {self.code}, message: {self.message})"


class SHCAPI:
    def __init__(self, controller_ip: str, certificate, key):
        self._certificate = certificate
        self._key = key
        self._controller_ip = controller_ip
        self._api_root = f"https://{self._controller_ip}:8444/smarthome"
        self._public_root = f"https://{self._controller_ip}:8446/smarthome/public"
        self._rpc_root = f"https://{self._controller_ip}:8444/remote/json-rpc"
        self._cafile = pkg_resources.resource_filename("boschshcpy", "tls_ca_chain.pem")

        self._requests_session = None
        self._sslcontext = None

    async def init(self, session):
        self._requests_session = session

        self._sslcontext = ssl.create_default_context(cafile=self._cafile)
        self._sslcontext.load_cert_chain(self._certificate, self._key)
        self._sslcontext.verify_mode = ssl.CERT_REQUIRED
        self._sslcontext.check_hostname = False
        self._requests_session.headers.update(
            {"api-version": "2.1", "Content-Type": "application/json"}
        )

    @property
    def controller_ip(self):
        return self._controller_ip

    async def _get_api_result_or_fail(
        self,
        api_url,
        expected_type=None,
        expected_element_type=None,
        headers=None,
        timeout=30,
    ):
        try:
            async with self._requests_session.get(
                api_url, headers=headers, timeout=timeout, ssl=self._sslcontext
            ) as result:
                if not result.ok:
                    self._process_nok_result(result)

                else:
                    json_result = await result.json()
                    if expected_type is not None:
                        assert json_result["@type"] == expected_type
                    if expected_element_type is not None:
                        for result_ in json_result:
                            assert result_["@type"] == expected_element_type
                    return json_result
        except aiohttp.ClientSSLError as err:
            raise Exception(f"API call returned SSLError: {err}.")

    async def _put_api_or_fail(self, api_url, body, timeout=30):
        async with self._requests_session.put(
            api_url, data=json.dumps(body), timeout=timeout, ssl=self._sslcontext
        ) as result:
            if not result.ok:
                self._process_nok_result(result)
            return await result.json()

    async def _post_api_or_fail(self, api_url, body, timeout=30):
        async with self._requests_session.post(
            api_url, data=json.dumps(body), timeout=timeout, ssl=self._sslcontext
        ) as result:
            if not result.ok:
                self._process_nok_result(result)
            return await result.json()

    def _process_nok_result(self, result):
        logging.error(f"Body: {result.request.body}")
        logging.error(f"Headers: {result.request.headers}")
        logging.error(f"URL: {result.request.url}")
        raise SHCSessionError(
            f"API call returned non-OK result (code {result.status})!: {result.content}"
        )

    # API calls here
    async def get_information(self):
        api_url = f"{self._api_root}/information"
        try:
            result = await self._get_api_result_or_fail(api_url)
        except Exception as err:
            logging.error(f"Failed to get information from SHC controller: {err}")
            return None
        return result

    async def get_public_information(self):
        api_url = f"{self._public_root}/information"
        try:
            result = await self._get_api_result_or_fail(api_url, headers={})
        except Exception as err:
            logging.error(
                f"Failed to get public information from SHC controller: {err}"
            )
            return None
        return result

    async def get_rooms(self):
        api_url = f"{self._api_root}/rooms"
        return await self._get_api_result_or_fail(api_url, expected_element_type="room")

    async def get_scenarios(self):
        api_url = f"{self._api_root}/scenarios"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="scenario"
        )

    async def get_devices(self):
        api_url = f"{self._api_root}/devices"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="device"
        )

    async def get_services(self):
        api_url = f"{self._api_root}/services"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="DeviceServiceData"
        )

    async def get_device_service(self, device_id, service_id):
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}"
        return await self._get_api_result_or_fail(
            api_url, expected_type="DeviceServiceData"
        )

    async def put_device_service_state(self, device_id, service_id, state_update):
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}/state"
        return await self._put_api_or_fail(api_url, state_update)

    async def get_domain_intrusion_detection(self):
        api_url = f"{self._api_root}/intrusion/states/system"
        return await self._get_api_result_or_fail(api_url, expected_type="systemState")

    async def post_domain_action(self, path, data=None):
        api_url = f"{self._api_root}/{path}"
        return await self._post_api_or_fail(api_url, data)

    async def post_scenario_trigger(self, scenario_id, data=None):
        api_url = f"{self._api_root}/scenarios/{scenario_id}/triggers"
        return await self._post_api_or_fail(api_url, data)

    async def long_polling_subscribe(self):
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/subscribe",
                "params": ["com/bosch/sh/remote/*", None],
            }
        ]
        result = await self._post_api_or_fail(self._rpc_root, data)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        return result[0]["result"]

    async def long_polling_poll(self, poll_id, wait_seconds=30):
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/longPoll",
                "params": [poll_id, wait_seconds],
            }
        ]
        result = await self._post_api_or_fail(self._rpc_root, data, wait_seconds + 5)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        return result[0]["result"]

    async def long_polling_unsubscribe(self, poll_id):
        data = [{"jsonrpc": "2.0", "method": "RE/unsubscribe", "params": [poll_id]}]
        result = await self._post_api_or_fail(self._rpc_root, data)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        return result[0]["result"]
