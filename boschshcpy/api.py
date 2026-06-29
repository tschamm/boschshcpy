from __future__ import annotations

import importlib.resources
import json
import logging
from typing import Any, NoReturn, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from .exceptions import SHCConnectionError, SHCSessionError
from .exceptions import JSONRPCError as JSONRPCError  # noqa: F401 -- explicit re-export

logger = logging.getLogger("boschshcpy")


class HostNameIgnoringAdapter(HTTPAdapter):  # type: ignore[misc]
    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = False,
        **connection_pool_kw: Any,
    ) -> None:
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, assert_hostname=False
        )


class SHCAPI:
    def __init__(
        self,
        controller_ip: str,
        certificate: str,
        key: str,
        verify_hostname: bool = False,
        ssl_verify: bool = True,
    ) -> None:
        self._certificate = certificate
        self._key = key
        self._controller_ip = controller_ip
        self._api_root = f"https://{self._controller_ip}:8444/smarthome"
        self._public_root = f"https://{self._controller_ip}:8446/smarthome/public"
        self._rpc_root = f"https://{self._controller_ip}:8444/remote/json-rpc"

        # Settings for all API calls
        self._requests_session = requests.Session()
        if verify_hostname:
            adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
        else:
            adapter = HostNameIgnoringAdapter(pool_connections=20, pool_maxsize=20)
        self._requests_session.mount("https://", adapter)
        self._requests_session.cert = (self._certificate, self._key)
        self._requests_session.headers.update(
            {"api-version": "3.2", "Content-Type": "application/json"}
        )
        if ssl_verify:
            # Verify the SHC server certificate against the bundled Bosch CA.
            self._requests_session.verify = str(
                importlib.resources.files("boschshcpy") / "tls_ca_chain.pem"
            )
        else:
            # #264: opt-in for local-only LAN setups whose SHC server
            # certificate has expired (controller offline → no FW/cert
            # updates). Skips server-cert verification only; mTLS client-cert
            # authentication is unaffected.
            self._requests_session.verify = False
            logger.warning(
                "SSL certificate verification is DISABLED for the SHC at %s "
                "(ssl_verify=False). Only use this on a trusted local network.",
                controller_ip,
            )
            import urllib3
            from urllib3.exceptions import InsecureRequestWarning

            # Suppress InsecureRequestWarning only when the user opts out of
            # verification — and scope it to that one warning so legitimate SSL
            # warnings from other HA integrations are not silenced.
            urllib3.disable_warnings(InsecureRequestWarning)

    @property
    def controller_ip(self) -> str:
        return self._controller_ip

    def _session_request(
        self, method: str, api_url: str, **kwargs: Any
    ) -> requests.Response:
        """Issue a request, retrying once on a bare connection drop.

        #281: the SHC silently closes idle keep-alive connections. The next
        request reusing that dead pooled connection then raises
        ConnectionError(RemoteDisconnected('Remote end closed connection
        without response')) before the request reaches the controller. Because
        no response was received, the command was not processed, so a single
        retry on a fresh connection is safe (no risk of double-execution) and
        turns the intermittent automation failure into a transparent recovery.
        """
        # Dispatch on the named verb (session.get/put/post) so callers and tests
        # observe the same call surface as before this retry wrapper existed.
        verb = getattr(self._requests_session, method.lower())
        try:
            return cast(requests.Response, verb(api_url, **kwargs))
        except requests.exceptions.ConnectionError as err:
            logger.debug(
                "%s %s dropped (%s); retrying once on a fresh connection",
                method,
                api_url,
                err,
            )
            return cast(requests.Response, verb(api_url, **kwargs))

    def _get_api_result_or_fail(
        self,
        api_url: str,
        expected_type: str | None = None,
        expected_element_type: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> Any:
        try:
            result = self._session_request(
                "GET", api_url, headers=headers, timeout=timeout
            )
            if not result.ok:
                self._process_nok_result(result)

            else:
                if len(result.content) > 0:
                    result = json.loads(result.content)
                    if (
                        expected_type is not None
                        and result.get("@type") != expected_type
                    ):
                        raise SHCSessionError(
                            f"Unexpected @type in API response: expected "
                            f"{expected_type!r}, got {result.get('@type')!r}"
                        )
                    if expected_element_type is not None:
                        for result_ in result:
                            if result_.get("@type") != expected_element_type:
                                raise SHCSessionError(
                                    f"Unexpected @type in API response element: "
                                    f"expected {expected_element_type!r}, got "
                                    f"{result_.get('@type')!r}"
                                )

                    return result
                else:
                    return {}
        except requests.exceptions.SSLError as e:
            raise SHCConnectionError(f"API call returned SSLError: {e}.") from e

    def _put_api_or_fail(self, api_url: str, body: Any, timeout: int = 30) -> Any:
        result = self._session_request(
            "PUT", api_url, data=json.dumps(body), timeout=timeout
        )
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) > 0:
            return json.loads(result.content)
        else:
            return {}

    def _post_api_or_fail(self, api_url: str, body: Any, timeout: int = 30) -> Any:
        result = self._session_request(
            "POST", api_url, data=json.dumps(body), timeout=timeout
        )
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) > 0:
            return json.loads(result.content)
        else:
            return {}

    def _process_nok_result(self, result: requests.Response) -> NoReturn:
        safe_headers = {
            k: v
            for k, v in result.request.headers.items()
            if k.lower() not in ("systempassword", "authorization", "cookie")
        }
        logger.debug("Body: %s", result.request.body)
        logger.error("Headers: %s", safe_headers)
        logger.error("URL: %s", result.request.url)
        raise SHCSessionError(
            f"API call returned non-OK result (code {result.status_code})!: {result.content}"
        )

    # API calls here
    def get_information(self) -> Any:
        api_url = f"{self._api_root}/information"
        try:
            result = self._get_api_result_or_fail(api_url)
        except Exception as e:
            logger.error("Failed to get information from SHC controller: %s", e)
            return None
        return result

    def get_public_information(self) -> Any:
        api_url = f"{self._public_root}/information"
        try:
            result = self._get_api_result_or_fail(api_url, headers={})
        except Exception as e:
            logger.error("Failed to get public information from SHC controller: %s", e)
            return None
        return result

    def get_rooms(self) -> Any:
        api_url = f"{self._api_root}/rooms"
        return self._get_api_result_or_fail(api_url, expected_element_type="room")

    def get_scenarios(self) -> Any:
        api_url = f"{self._api_root}/scenarios"
        return self._get_api_result_or_fail(api_url, expected_element_type="scenario")

    def get_userdefinedstates(self) -> Any:
        api_url = f"{self._api_root}/userdefinedstates"
        return self._get_api_result_or_fail(
            api_url, expected_element_type="userDefinedState"
        )

    def get_messages(self) -> Any:
        api_url = f"{self._api_root}/messages"
        return self._get_api_result_or_fail(api_url, expected_element_type="message")

    def get_devices(self) -> Any:
        api_url = f"{self._api_root}/devices"
        return self._get_api_result_or_fail(api_url, expected_element_type="device")

    def get_device(self, device_id: str) -> Any:
        api_url = f"{self._api_root}/devices/{device_id}"
        return self._get_api_result_or_fail(api_url, expected_type="device")

    def get_services(self) -> Any:
        api_url = f"{self._api_root}/services"
        return self._get_api_result_or_fail(
            api_url, expected_element_type="DeviceServiceData"
        )

    def get_device_services(self, device_id: str) -> Any:
        api_url = f"{self._api_root}/devices/{device_id}/services"
        return self._get_api_result_or_fail(api_url)

    def get_device_service(self, device_id: str, service_id: str) -> Any:
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}"
        return self._get_api_result_or_fail(api_url, expected_type="DeviceServiceData")

    def put_device_service_state(
        self, device_id: str, service_id: str, state_update: Any
    ) -> None:
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}/state"
        self._put_api_or_fail(api_url, state_update)

    def post_device_service_operation(
        self, device_id: str, service_id: str, operation: str, data: Any = None
    ) -> Any:
        api_url = (
            f"{self._api_root}/devices/{device_id}/services/{service_id}"
            f"/operation/{operation}"
        )
        return self._post_api_or_fail(api_url, body=data)

    def get_domain_intrusion_detection(self) -> Any:
        api_url = f"{self._api_root}/intrusion/states/system"
        return self._get_api_result_or_fail(api_url, expected_type="systemState")

    def post_domain_action(self, path: str, data: Any = None) -> None:
        api_url = f"{self._api_root}/{path}"
        self._post_api_or_fail(api_url, body=data)

    @staticmethod
    def _check_jsonrpc_version(result: Any, method: str) -> None:
        if result[0].get("jsonrpc") != "2.0":
            raise SHCSessionError(
                f"Unexpected JSON-RPC version in {method} response: "
                f"{result[0].get('jsonrpc')!r}"
            )

    def long_polling_subscribe(self) -> Any:
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/subscribe",
                "params": ["com/bosch/sh/remote/*", None],
            }
        ]
        result = self._post_api_or_fail(self._rpc_root, data)
        self._check_jsonrpc_version(result, "RE/subscribe")
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        else:
            return result[0]["result"]

    def long_polling_poll(self, poll_id: str, wait_seconds: int = 30) -> Any:
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/longPoll",
                "params": [poll_id, wait_seconds],
            }
        ]
        result = self._post_api_or_fail(self._rpc_root, data, wait_seconds + 5)
        self._check_jsonrpc_version(result, "RE/longPoll")
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        else:
            return result[0]["result"]

    def long_polling_unsubscribe(self, poll_id: str) -> Any:
        data = [{"jsonrpc": "2.0", "method": "RE/unsubscribe", "params": [poll_id]}]
        result = self._post_api_or_fail(self._rpc_root, data)
        self._check_jsonrpc_version(result, "RE/unsubscribe")
        if "error" in result[0].keys():
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        else:
            return result[0]["result"]
