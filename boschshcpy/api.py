import json
import logging

import pkg_resources
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager

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


class HostNameIgnoringAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, assert_hostname=False
        )


class SHCAPI:
    def __init__(self, controller_ip: str, certificate, key):
        self._certificate = certificate
        self._key = key
        self._controller_ip = controller_ip
        self._api_root = f"https://{self._controller_ip}:8444/smarthome"
        self._public_root = f"https://{self._controller_ip}:8446/smarthome/public"
        self._rpc_root = f"https://{self._controller_ip}:8444/remote/json-rpc"

        # Settings for all API calls
        self._requests_session = requests.Session()
        self._requests_session.mount("https://", HostNameIgnoringAdapter())
        self._requests_session.cert = (self._certificate, self._key)
        self._requests_session.headers.update(
            {"api-version": "2.1", "Content-Type": "application/json"}
        )
        self._requests_session.verify = pkg_resources.resource_filename(
            "boschshcpy", "tls_ca_chain.pem"
        )

        import urllib3

        urllib3.disable_warnings()

    @property
    def controller_ip(self):
        return self._controller_ip

    def _get_api_result_or_fail(
        self,
        api_url,
        expected_type=None,
        expected_element_type=None,
        headers=None,
        timeout=30,
    ):
        try:
            result = self._requests_session.get(
                api_url, headers=headers, timeout=timeout
            )
            if not result.ok:
                self._process_nok_result(result)

            else:
                if len(result.content) > 0:
                    result = json.loads(result.content)
                    if expected_type is not None:
                        assert result["@type"] == expected_type
                    if expected_element_type is not None:
                        for result_ in result:
                            assert result_["@type"] == expected_element_type

                    return result
                else:
                    return {}
        except requests.exceptions.SSLError as e:
            raise Exception(f"API call returned SSLError: {e}.")

    def _put_api_or_fail(self, api_url, body, timeout=30):
        result = self._requests_session.put(
            api_url, data=json.dumps(body), timeout=timeout
        )
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) > 0:
            return json.loads(result.content)
        else:
            return {}

    def _post_api_or_fail(self, api_url, body, timeout=30):
        result = self._requests_session.post(
            api_url, data=json.dumps(body), timeout=timeout
        )
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) > 0:
            return json.loads(result.content)
        else:
            return {}

    def _process_nok_result(self, result):
        logging.error(f"Body: {result.request.body}")
        logging.error(f"Headers: {result.request.headers}")
        logging.error(f"URL: {result.request.url}")
        raise SHCSessionError(
            f"API call returned non-OK result (code {result.status_code})!: {result.content}"
        )

    # API calls here
    def get_information(self):
        api_url = f"{self._api_root}/information"
        try:
            result = self._get_api_result_or_fail(api_url)
        except Exception as e:
            logging.error(f"Failed to get information from SHC controller: {e}")
            return None
        return result

    def get_public_information(self):
        api_url = f"{self._public_root}/information"
        try:
            result = self._get_api_result_or_fail(api_url, headers={})
        except Exception as e:
            logging.error(f"Failed to get public information from SHC controller: {e}")
            return None
        return result

    def get_rooms(self):
        api_url = f"{self._api_root}/rooms"
        return self._get_api_result_or_fail(api_url, expected_element_type="room")

    def get_scenarios(self):
        api_url = f"{self._api_root}/scenarios"
        return self._get_api_result_or_fail(api_url, expected_element_type="scenario")

    def get_devices(self):
        api_url = f"{self._api_root}/devices"
        return self._get_api_result_or_fail(api_url, expected_element_type="device")

    def get_device_service(self, device_id, service_id):
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}"
        return self._get_api_result_or_fail(api_url, expected_type="DeviceServiceData")

    def put_device_service_state(self, device_id, service_id, state_update):
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}/state"
        self._put_api_or_fail(api_url, state_update)

    def get_domain_intrusion_detection(self):
        api_url = f"{self._api_root}/intrusion/states/system"
        return self._get_api_result_or_fail(api_url, expected_type="systemState")

    def post_domain_action(self, path, data=None):
        api_url = f"{self._api_root}/{path}"
        self._post_api_or_fail(api_url, data)

    def long_polling_subscribe(self):
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/subscribe",
                "params": ["com/bosch/sh/remote/*", None],
            }
        ]
        result = self._post_api_or_fail(self._rpc_root, data)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        else:
            return result[0]["result"]

    def long_polling_poll(self, poll_id, wait_seconds=30):
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/longPoll",
                "params": [poll_id, wait_seconds],
            }
        ]
        result = self._post_api_or_fail(self._rpc_root, data, wait_seconds + 5)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        else:
            return result[0]["result"]

    def long_polling_unsubscribe(self, poll_id):
        data = [{"jsonrpc": "2.0", "method": "RE/unsubscribe", "params": [poll_id]}]
        result = self._post_api_or_fail(self._rpc_root, data)
        assert result[0]["jsonrpc"] == "2.0"
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        else:
            return result[0]["result"]
