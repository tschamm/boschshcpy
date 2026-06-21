"""async HTTP layer for boschshcpy — Phase 1 foundation.

NON-BREAKING: importing this module is optional. The sync SHCAPI in api.py is
untouched. aiohttp is imported lazily inside this module so that
``import boschshcpy`` remains light when aiohttp is not installed.

mTLS strategy
-------------
The Bosch SHC serves its HTTPS endpoints on an IP address whose TLS
certificate carries neither a matching CN nor a SAN that equals the IP.
The sync SHCAPI works around this with a custom requests adapter that passes
``assert_hostname=False`` to urllib3's PoolManager.

The async equivalent is:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False          # no CN/SAN validation against IP
    ctx.verify_mode = ssl.CERT_REQUIRED  # but still verify the Bosch CA
    ctx.load_verify_locations(cafile=<bundled tls_ca_chain.pem>)
    ctx.load_cert_chain(certfile=certificate, keyfile=key)  # mTLS client cert

This is the aiohttp equivalent of the HostNameIgnoringAdapter pattern and must
be validated against live SHC hardware before Phase 1 ships (see
01_analysis/async-phase1-verify.md).

External session
----------------
Pass an existing ``aiohttp.ClientSession`` via ``external_session`` to let HA's
``async_create_clientsession`` manage the lifecycle. When no external session is
provided, SHCAPIAsync creates and owns its own session; call ``await api.close()``
when done.
"""

from __future__ import annotations

import importlib.resources
import json
import logging
import ssl
from typing import Any

from .exceptions import SHCConnectionError, SHCSessionError

logger = logging.getLogger("boschshcpy")

# Re-export so callers can ``from boschshcpy.api_async import JSONRPCError``
# without importing the sync api module.
from .api import JSONRPCError  # noqa: E402  (after stdlib imports is fine)


def build_ssl_context(certificate: str, key: str) -> ssl.SSLContext:
    """Build an mTLS SSLContext that mirrors the sync HostNameIgnoringAdapter.

    Args:
        certificate: Path to the PEM client certificate file.
        key: Path to the PEM private key file.

    Returns:
        ssl.SSLContext configured for Bosch SHC mTLS:
        - check_hostname=False  (SHC cert CN/SAN doesn't match its IP)
        - verify_mode=CERT_REQUIRED  (still pins to the bundled Bosch CA)
        - client cert + key loaded for mutual TLS
    """
    ca_chain = str(importlib.resources.files("boschshcpy") / "tls_ca_chain.pem")

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # Must be set BEFORE verify_mode so the combination is valid
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_verify_locations(cafile=ca_chain)
    ctx.load_cert_chain(certfile=certificate, keyfile=key)
    return ctx


class SHCAPIAsync:
    """Async counterpart to the sync SHCAPI.

    Uses ``aiohttp.ClientSession`` + ``aiohttp.TCPConnector`` with the mTLS
    SSLContext produced by ``build_ssl_context()``.

    Phase 1 scope: all request/response methods are async.
    The long-poll *thread* is not replaced here — that is Phase 2.
    The async long_polling_* methods below provide the async POST calls that
    Phase 2 will use inside an asyncio.Task.
    """

    def __init__(
        self,
        controller_ip: str,
        certificate: str,
        key: str,
        *,
        external_session: Any | None = None,
    ) -> None:
        """Initialise the async API layer.

        Args:
            controller_ip: IP address of the SHC controller.
            certificate: Path to the PEM client certificate.
            key: Path to the PEM private key.
            external_session: Optional existing ``aiohttp.ClientSession``.  When
                provided, SHCAPIAsync does NOT create its own session and will
                NOT close it in ``close()``.  Intended for HA's
                ``async_create_clientsession(hass)`` pattern (Phase 3).
        """
        # Lazy import: boschshcpy stays importable without aiohttp
        try:
            import aiohttp
        except ImportError as exc:
            raise ImportError(
                "aiohttp is required for SHCAPIAsync. "
                "Install it with: pip install aiohttp"
            ) from exc

        self._controller_ip = controller_ip
        self._api_root = f"https://{controller_ip}:8444/smarthome"
        self._public_root = f"https://{controller_ip}:8446/smarthome/public"
        self._rpc_root = f"https://{controller_ip}:8444/remote/json-rpc"

        self._ssl_ctx = build_ssl_context(certificate, key)
        self._owns_session = external_session is None

        if self._owns_session:
            connector = aiohttp.TCPConnector(ssl=self._ssl_ctx)
            self._session: Any = aiohttp.ClientSession(
                connector=connector,
                headers={"api-version": "3.2", "Content-Type": "application/json"},
            )
        else:
            self._session = external_session

        self._headers = {"api-version": "3.2", "Content-Type": "application/json"}

    @property
    def controller_ip(self) -> str:
        return self._controller_ip

    async def close(self) -> None:
        """Close the managed ClientSession (no-op when an external session was provided)."""
        if self._owns_session and not self._session.closed:
            await self._session.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_api_result_or_fail(
        self,
        api_url: str,
        expected_type: str | None = None,
        expected_element_type: str | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> Any:
        """Async GET — mirrors sync ``_get_api_result_or_fail``."""
        import aiohttp

        headers = dict(self._headers)
        if extra_headers:
            headers.update(extra_headers)

        try:
            async with self._session.get(
                api_url,
                headers=headers,
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if not resp.ok:
                    await self._process_nok_result(resp)

                content = await resp.read()
                if len(content) == 0:
                    return {}

                result = json.loads(content)

                if expected_type is not None and result.get("@type") != expected_type:
                    raise SHCSessionError(
                        f"Unexpected @type in API response: expected "
                        f"{expected_type!r}, got {result.get('@type')!r}"
                    )
                if expected_element_type is not None:
                    for item in result:
                        if item.get("@type") != expected_element_type:
                            raise SHCSessionError(
                                f"Unexpected @type in API response element: "
                                f"expected {expected_element_type!r}, got "
                                f"{item.get('@type')!r}"
                            )
                return result

        except aiohttp.ClientSSLError as exc:
            raise SHCConnectionError(f"API call returned SSLError: {exc}.") from exc
        except aiohttp.ClientConnectionError as exc:
            raise SHCConnectionError(f"API connection error: {exc}.") from exc

    async def _put_api_or_fail(
        self,
        api_url: str,
        body: Any,
        timeout: int = 30,
    ) -> Any:
        """Async PUT — mirrors sync ``_put_api_or_fail``."""
        import aiohttp

        try:
            async with self._session.put(
                api_url,
                data=json.dumps(body),
                headers=self._headers,
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if not resp.ok:
                    await self._process_nok_result(resp)
                content = await resp.read()
                return json.loads(content) if content else {}

        except aiohttp.ClientSSLError as exc:
            raise SHCConnectionError(f"API call returned SSLError: {exc}.") from exc
        except aiohttp.ClientConnectionError as exc:
            raise SHCConnectionError(f"API connection error: {exc}.") from exc

    async def _post_api_or_fail(
        self,
        api_url: str,
        body: Any,
        timeout: int = 30,
    ) -> Any:
        """Async POST — mirrors sync ``_post_api_or_fail``."""
        import aiohttp

        try:
            async with self._session.post(
                api_url,
                data=json.dumps(body),
                headers=self._headers,
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if not resp.ok:
                    await self._process_nok_result(resp)
                content = await resp.read()
                return json.loads(content) if content else {}

        except aiohttp.ClientSSLError as exc:
            raise SHCConnectionError(f"API call returned SSLError: {exc}.") from exc
        except aiohttp.ClientConnectionError as exc:
            raise SHCConnectionError(f"API connection error: {exc}.") from exc

    async def _process_nok_result(self, resp: Any) -> None:
        """Raise SHCSessionError for non-OK HTTP responses."""
        try:
            body = await resp.read()
        except Exception:
            body = b""
        raise SHCSessionError(
            f"API call returned non-OK result (code {resp.status})!: {body!r}"
        )

    # ------------------------------------------------------------------
    # Public API methods (mirror the sync SHCAPI)
    # ------------------------------------------------------------------

    async def get_information(self) -> Any:
        api_url = f"{self._api_root}/information"
        try:
            return await self._get_api_result_or_fail(api_url)
        except Exception as exc:
            logger.error("Failed to get information from SHC controller: %s", exc)
            return None

    async def get_public_information(self) -> Any:
        api_url = f"{self._public_root}/information"
        try:
            return await self._get_api_result_or_fail(api_url, extra_headers={})
        except Exception as exc:
            logger.error("Failed to get public information from SHC controller: %s", exc)
            return None

    async def get_rooms(self) -> Any:
        api_url = f"{self._api_root}/rooms"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="room"
        )

    async def get_scenarios(self) -> Any:
        api_url = f"{self._api_root}/scenarios"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="scenario"
        )

    async def get_userdefinedstates(self) -> Any:
        api_url = f"{self._api_root}/userdefinedstates"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="userDefinedState"
        )

    async def get_messages(self) -> Any:
        api_url = f"{self._api_root}/messages"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="message"
        )

    async def get_devices(self) -> Any:
        api_url = f"{self._api_root}/devices"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="device"
        )

    async def get_device(self, device_id: str) -> Any:
        api_url = f"{self._api_root}/devices/{device_id}"
        return await self._get_api_result_or_fail(api_url, expected_type="device")

    async def get_services(self) -> Any:
        api_url = f"{self._api_root}/services"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="DeviceServiceData"
        )

    async def get_device_services(self, device_id: str) -> Any:
        api_url = f"{self._api_root}/devices/{device_id}/services"
        return await self._get_api_result_or_fail(api_url)

    async def get_device_service(self, device_id: str, service_id: str) -> Any:
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}"
        return await self._get_api_result_or_fail(
            api_url, expected_type="DeviceServiceData"
        )

    async def put_device_service_state(
        self, device_id: str, service_id: str, state_update: Any
    ) -> None:
        api_url = f"{self._api_root}/devices/{device_id}/services/{service_id}/state"
        await self._put_api_or_fail(api_url, state_update)

    async def get_domain_intrusion_detection(self) -> Any:
        api_url = f"{self._api_root}/intrusion/states/system"
        return await self._get_api_result_or_fail(api_url, expected_type="systemState")

    async def post_domain_action(self, path: str, data: Any = None) -> None:
        api_url = f"{self._api_root}/{path}"
        await self._post_api_or_fail(api_url, body=data)

    # ------------------------------------------------------------------
    # Long-poll methods (Phase 1: async POST calls only — thread not replaced)
    # Phase 2 will wrap these in asyncio.Task + async retry loop.
    # ------------------------------------------------------------------

    @staticmethod
    def _check_jsonrpc_version(result: list[Any], method: str) -> None:
        if result[0].get("jsonrpc") != "2.0":
            raise SHCSessionError(
                f"Unexpected JSON-RPC version in {method} response: "
                f"{result[0].get('jsonrpc')!r}"
            )

    async def long_polling_subscribe(self) -> str:
        """POST RE/subscribe → returns poll_id string."""
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/subscribe",
                "params": ["com/bosch/sh/remote/*", None],
            }
        ]
        result = await self._post_api_or_fail(self._rpc_root, data)
        self._check_jsonrpc_version(result, "RE/subscribe")
        if "error" in result[0]:
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        return result[0]["result"]

    async def long_polling_poll(self, poll_id: str, wait_seconds: int = 30) -> Any:
        """POST RE/longPoll → returns list of event dicts.

        NOTE (Phase 1): This method is provided for Phase 2 async task usage.
        The sync long-poll thread in session.py still calls the sync
        ``SHCAPI.long_polling_poll`` — that thread is NOT replaced until Phase 2.
        """
        data = [
            {
                "jsonrpc": "2.0",
                "method": "RE/longPoll",
                "params": [poll_id, wait_seconds],
            }
        ]
        result = await self._post_api_or_fail(
            self._rpc_root, data, timeout=wait_seconds + 5
        )
        self._check_jsonrpc_version(result, "RE/longPoll")
        if "error" in result[0]:
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        return result[0]["result"]

    async def long_polling_unsubscribe(self, poll_id: str) -> Any:
        """POST RE/unsubscribe."""
        data = [{"jsonrpc": "2.0", "method": "RE/unsubscribe", "params": [poll_id]}]
        result = await self._post_api_or_fail(self._rpc_root, data)
        self._check_jsonrpc_version(result, "RE/unsubscribe")
        if "error" in result[0]:
            raise JSONRPCError(
                result[0]["error"]["code"], result[0]["error"]["message"]
            )
        return result[0]["result"]
