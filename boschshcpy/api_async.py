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
import urllib.parse
from typing import Any, cast

from .exceptions import SHCCertificateError, SHCConnectionError, SHCSessionError

logger = logging.getLogger("boschshcpy")

# Re-export so callers can ``from boschshcpy.api_async import JSONRPCError``
# without importing the sync api module.
from .api import JSONRPCError as JSONRPCError  # noqa: E402  -- explicit re-export for mypy


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
        ssl_context: Any | None = None,
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
            ssl_context: Optional pre-built mTLS SSLContext. Building it reads
                the cert/key/CA PEM files from disk (blocking I/O); pass one
                built off the event loop (e.g. HA
                ``await hass.async_add_executor_job(build_ssl_context, cert,
                key)``) to avoid a blocking-call-in-event-loop warning. When
                None, it is built here from ``certificate``/``key``.
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

        if ssl_context is not None:
            self._ssl_ctx = ssl_context
        else:
            # Caller didn't pre-build the context off-loop (e.g. a direct
            # library user, or a caller on an older boschshcpy without the
            # ssl_context parameter) — build it here. A corrupted/missing
            # cert or key file raises a raw ssl.SSLError/OSError from
            # OpenSSL here; translate it into the same typed exception the
            # sync-side certificate.py uses for the same failure class, so
            # every caller gets a catchable, self-explanatory error instead
            # of a cryptic "[SSL] PEM lib" traceback.
            try:
                self._ssl_ctx = build_ssl_context(certificate, key)
            except (ssl.SSLError, OSError, ValueError) as exc:
                raise SHCCertificateError(
                    f"Could not load client certificate/key ({certificate}, "
                    f"{key}): {exc}"
                ) from exc
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

    async def _retry_once_on_connection_drop(self, api_url: str, attempt: Any) -> Any:
        """Run attempt() once, retrying a single time on a bare connection drop.

        #281 parity with the sync client (api.py:_session_request): the SHC
        silently closes idle keep-alive connections, and aiohttp raises
        ClientConnectionError on the next request reusing that dead pooled
        connection before it reaches the controller. Because no response was
        received, the command was not processed, so a single retry on a fresh
        connection is safe (no risk of double-execution). Without this, the
        async path (the one actually used by session_async.py / HA's
        production long-poll session) hits the exact intermittent failure
        #281 already fixed on the sync path.

        ClientSSLError is a ClientConnectionError subclass but is
        deliberately NOT retried — a cert/handshake failure won't be fixed by
        trying again.
        """
        import aiohttp

        try:
            return await attempt()
        except aiohttp.ClientSSLError as exc:
            raise SHCConnectionError(f"API call returned SSLError: {exc}.") from exc
        except TimeoutError as exc:
            # aiohttp raises a bare TimeoutError (not a ClientConnectionError
            # subclass) when ClientTimeout elapses — sync parity with
            # requests.exceptions.Timeout, which api.py's RequestException
            # catch already wraps into SHCConnectionError.
            raise SHCConnectionError(f"API call timed out: {exc}.") from exc
        except aiohttp.ClientConnectionError as exc:
            logger.debug(
                "%s dropped (%s); retrying once on a fresh connection", api_url, exc
            )
            try:
                return await attempt()
            except aiohttp.ClientSSLError as exc2:
                raise SHCConnectionError(
                    f"API call returned SSLError: {exc2}."
                ) from exc2
            except TimeoutError as exc2:
                raise SHCConnectionError(f"API call timed out: {exc2}.") from exc2
            except aiohttp.ClientConnectionError as exc2:
                raise SHCConnectionError(f"API connection error: {exc2}.") from exc2

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

        async def _attempt() -> Any:
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

        return await self._retry_once_on_connection_drop(api_url, _attempt)

    async def _put_api_or_fail(
        self,
        api_url: str,
        body: Any,
        timeout: int = 30,
    ) -> Any:
        """Async PUT — mirrors sync ``_put_api_or_fail``."""
        import aiohttp

        logger.debug("PUT %s body=%s", api_url, body)

        async def _attempt() -> Any:
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
                logger.debug(
                    "PUT %s -> status=%s body=%s", api_url, resp.status, content
                )
                return json.loads(content) if content else {}

        return await self._retry_once_on_connection_drop(api_url, _attempt)

    async def _post_api_or_fail(
        self,
        api_url: str,
        body: Any,
        timeout: int = 30,
    ) -> Any:
        """Async POST — mirrors sync ``_post_api_or_fail``."""
        import aiohttp

        logger.debug("POST %s body=%s", api_url, body)

        async def _attempt() -> Any:
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
                logger.debug(
                    "POST %s -> status=%s body=%s", api_url, resp.status, content
                )
                return json.loads(content) if content else {}

        return await self._retry_once_on_connection_drop(api_url, _attempt)

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
            logger.error(
                "Failed to get public information from SHC controller: %s", exc
            )
            return None

    async def get_rooms(self) -> Any:
        api_url = f"{self._api_root}/rooms"
        return await self._get_api_result_or_fail(api_url, expected_element_type="room")

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

    async def post_userdefinedstate(self, state_data: Any) -> Any:
        """Async mirror of the sync client's ``post_userdefinedstate``."""
        api_url = f"{self._api_root}/userdefinedstates"
        return await self._post_api_or_fail(api_url, state_data)

    async def delete_userdefinedstate(self, userdefinedstate_id: str) -> None:
        """Async mirror of the sync client's ``delete_userdefinedstate``."""
        import aiohttp

        api_url = f"{self._api_root}/userdefinedstates/{urllib.parse.quote(userdefinedstate_id, safe='')}"

        async def _attempt() -> None:
            async with self._session.delete(
                api_url,
                headers=self._headers,
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if not resp.ok:
                    await self._process_nok_result(resp)

        await self._retry_once_on_connection_drop(api_url, _attempt)

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

    async def put_device(self, device_id: str, device_data: Any) -> Any:
        """Update a Device resource (full-body PUT).

        Used to write device-level fields such as the installation ``profile``.
        The SHC expects the full Device body (GET the device, mutate, PUT back).
        Undocumented in the local OpenAPI (GET-only); APK ground-truth.
        """
        api_url = f"{self._api_root}/devices/{device_id}"
        return await self._put_api_or_fail(api_url, device_data)

    async def put_device_firmware_activation(self, device_id: str) -> None:
        """Trigger a firmware update install for one device (no request body).

        Not in the official OpenAPI spec; APK ground-truth
        (RestRequests.putDeviceFirmwareActivation -> PUT
        devicemanagement/firmware/{deviceId}/activate). NEVER_BLIND_FIX:
        confirm on real hardware before relying on this outside tests.
        """
        api_url = f"{self._api_root}/devicemanagement/firmware/{urllib.parse.quote(device_id, safe='')}/activate"
        await self._put_api_or_fail(api_url, body=None)

    async def get_device_firmware_state(self, device_id: str) -> str | None:
        """Probe this device's firmware lifecycle state (no OpenAPI spec).

        Async mirror of the sync client's ``get_device_firmware_state`` --
        see there for the APK ground-truth and the 404-means-unsupported
        contract.
        """
        import aiohttp

        api_url = f"{self._api_root}/devicemanagement/firmware/{urllib.parse.quote(device_id, safe='')}"

        async def _attempt() -> str | None:
            async with self._session.get(
                api_url,
                headers=self._headers,
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 404:
                    return None
                if not resp.ok:
                    await self._process_nok_result(resp)
                content = await resp.read()
                if len(content) == 0:
                    return None
                return cast(str, json.loads(content))

        return cast(
            "str | None", await self._retry_once_on_connection_drop(api_url, _attempt)
        )

    async def get_automation_rules(self) -> Any:
        """Async mirror of the sync client's ``get_automation_rules``."""
        api_url = f"{self._api_root}/automation/rules"
        return await self._get_api_result_or_fail(
            api_url, expected_element_type="automationRule"
        )

    async def post_automation_rule(self, rule_data: Any) -> Any:
        """Async mirror of the sync client's ``post_automation_rule``."""
        api_url = f"{self._api_root}/automation/rules"
        return await self._post_api_or_fail(api_url, rule_data)

    async def get_automation_rule(self, rule_id: str) -> Any:
        api_url = (
            f"{self._api_root}/automation/rules/{urllib.parse.quote(rule_id, safe='')}"
        )
        return await self._get_api_result_or_fail(
            api_url, expected_type="automationRule"
        )

    async def put_automation_rule(self, rule_id: str, rule_data: Any) -> Any:
        api_url = (
            f"{self._api_root}/automation/rules/{urllib.parse.quote(rule_id, safe='')}"
        )
        return await self._put_api_or_fail(api_url, rule_data)

    async def trigger_automation_rule(self, rule_id: str) -> None:
        api_url = (
            f"{self._api_root}/automation/rules/"
            f"{urllib.parse.quote(rule_id, safe='')}/trigger"
        )
        await self._put_api_or_fail(api_url, body=None)

    async def delete_automation_rule(self, rule_id: str) -> None:
        """Delete an automation rule permanently. Not exposed via HA entities."""
        import aiohttp

        api_url = (
            f"{self._api_root}/automation/rules/{urllib.parse.quote(rule_id, safe='')}"
        )

        async def _attempt() -> None:
            async with self._session.delete(
                api_url,
                headers=self._headers,
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if not resp.ok:
                    await self._process_nok_result(resp)

        await self._retry_once_on_connection_drop(api_url, _attempt)

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

    async def post_device_service_operation(
        self, device_id: str, service_id: str, operation: str, data: Any = None
    ) -> Any:
        api_url = (
            f"{self._api_root}/devices/{device_id}/services/{service_id}"
            f"/operation/{operation}"
        )
        return await self._post_api_or_fail(api_url, body=data)

    async def get_domain_intrusion_detection(self) -> Any:
        api_url = f"{self._api_root}/intrusion/states/system"
        return await self._get_api_result_or_fail(api_url, expected_type="systemState")

    async def get_zigbee_routing_info(self, device_id: str) -> Any:
        """Async counterpart to SHCAPI.get_zigbee_routing_info."""
        api_url = (
            f"{self._api_root}/zigbee/routinginfo/"
            f"{urllib.parse.quote(device_id, safe='')}"
        )
        return await self._get_api_result_or_fail(api_url)

    async def post_domain_action(self, path: str, data: Any = None) -> None:
        api_url = f"{self._api_root}/{path}"
        await self._post_api_or_fail(api_url, body=data)

    async def put_domain_action(self, path: str, data: Any = None) -> None:
        api_url = f"{self._api_root}/{path}"
        await self._put_api_or_fail(api_url, body=data)

    async def get_water_alarm_system_state(self) -> Any:
        """Whole-home water-leak alarm system state (no OpenAPI spec)."""
        api_url = f"{self._api_root}/wateralarm"
        return await self._get_api_result_or_fail(
            api_url, expected_type="waterAlarmSystemState"
        )

    async def get_water_alarm_system_configuration(self) -> Any:
        api_url = f"{self._api_root}/wateralarm/configuration"
        return await self._get_api_result_or_fail(
            api_url, expected_type="waterAlarmSystemConfiguration"
        )

    async def get_intrusion_profiles(self) -> Any:
        api_url = f"{self._api_root}/intrusion/profiles"
        return await self._get_api_result_or_fail(api_url)

    async def get_intrusion_profile(self, profile_id: str) -> Any:
        api_url = f"{self._api_root}/intrusion/profiles/{urllib.parse.quote(profile_id, safe='')}"
        return await self._get_api_result_or_fail(api_url)

    async def get_intrusion_profile_states(self) -> Any:
        api_url = f"{self._api_root}/intrusion/states/profiles"
        return await self._get_api_result_or_fail(api_url)

    async def get_intrusion_endpoint_alarm_actuators(self) -> Any:
        api_url = f"{self._api_root}/intrusion/endpoints/alarm/actuators"
        return await self._get_api_result_or_fail(api_url)

    async def get_intrusion_endpoint_alarm_triggers(self) -> Any:
        api_url = f"{self._api_root}/intrusion/endpoints/alarm/triggers"
        return await self._get_api_result_or_fail(api_url)

    async def get_intrusion_endpoint_reminder_actuators(self) -> Any:
        api_url = f"{self._api_root}/intrusion/endpoints/reminder/actuators"
        return await self._get_api_result_or_fail(api_url)

    async def get_open_windows(self) -> Any:
        """Whole-home open-door/open-window summary (official OpenAPI spec).

        Async mirror of the sync client's ``get_open_windows``.
        """
        api_url = f"{self._api_root}/doors-windows/openwindows"
        return await self._get_api_result_or_fail(api_url)

    async def get_thermostat_regulation_config(self, device_id: str) -> Any:
        """Fetch this device's regulation-algorithm config.

        Async mirror of the sync client's ``get_thermostat_regulation_config``
        -- returns None on HTTP 404 (device has no regulation-algorithm
        config), matching get_device_firmware_state's contract.
        """
        import aiohttp

        api_url = (
            f"{self._api_root}/thermostat/regulation/"
            f"{urllib.parse.quote(device_id, safe='')}/config"
        )

        async def _attempt() -> Any:
            async with self._session.get(
                api_url,
                headers=self._headers,
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 404:
                    return None
                if not resp.ok:
                    await self._process_nok_result(resp)
                content = await resp.read()
                if len(content) == 0:
                    return None
                return json.loads(content)

        return await self._retry_once_on_connection_drop(api_url, _attempt)

    async def put_thermostat_regulation_config(
        self, device_id: str, config: Any
    ) -> Any:
        api_url = (
            f"{self._api_root}/thermostat/regulation/"
            f"{urllib.parse.quote(device_id, safe='')}/config"
        )
        return await self._put_api_or_fail(api_url, config)

    async def get_temperature_drop_services(self) -> Any:
        api_url = f"{self._api_root}/climate/temperaturedropservice"
        return await self._get_api_result_or_fail(api_url)

    async def get_temperature_drop_service(self, room_id: str) -> Any:
        api_url = (
            f"{self._api_root}/climate/temperaturedropservice/"
            f"{urllib.parse.quote(room_id, safe='')}"
        )
        return await self._get_api_result_or_fail(api_url)

    async def put_temperature_drop_service(self, room_id: str, data: Any) -> Any:
        api_url = (
            f"{self._api_root}/climate/temperaturedropservice/"
            f"{urllib.parse.quote(room_id, safe='')}"
        )
        return await self._put_api_or_fail(api_url, data)

    async def get_hydraulic_balancing_configurations(self) -> Any:
        api_url = f"{self._api_root}/climate/hydraulicbalancing"
        return await self._get_api_result_or_fail(api_url)

    async def get_hydraulic_balancing_configuration(self, config_id: str) -> Any:
        api_url = (
            f"{self._api_root}/climate/hydraulicbalancing/"
            f"{urllib.parse.quote(config_id, safe='')}"
        )
        return await self._get_api_result_or_fail(api_url)

    async def put_hydraulic_balancing_configuration(
        self, config_id: str, config: Any
    ) -> Any:
        api_url = (
            f"{self._api_root}/climate/hydraulicbalancing/"
            f"{urllib.parse.quote(config_id, safe='')}"
        )
        return await self._put_api_or_fail(api_url, config)

    async def get_comfort_zone_templates(self, sensor_id: str) -> Any:
        api_url = (
            f"{self._api_root}/airquality/comfortzone/templates/"
            f"{urllib.parse.quote(sensor_id, safe='')}"
        )
        return await self._get_api_result_or_fail(api_url)

    async def put_comfort_zone_template(self, sensor_id: str, comfort_zone: Any) -> Any:
        api_url = (
            f"{self._api_root}/airquality/comfortzone/templates/"
            f"{urllib.parse.quote(sensor_id, safe='')}/custom"
        )
        return await self._put_api_or_fail(api_url, comfort_zone)

    # Multiroom Boiler Control room-linking (official OpenAPI spec,
    # MultiroomBoilerControl-local-openapi-v3.yml). NOT live-confirmed -- no
    # owned Boiler hardware; implemented directly from the spec.
    async def get_boiler_capable_rooms(self) -> Any:
        api_url = f"{self._api_root}/relay/boiler/rooms"
        return await self._get_api_result_or_fail(api_url)

    async def get_boiler_linked_rooms(self, boiler_id: str) -> Any:
        api_url = (
            f"{self._api_root}/relay/boiler/"
            f"{urllib.parse.quote(boiler_id, safe='')}/rooms"
        )
        return await self._get_api_result_or_fail(api_url)

    async def put_boiler_linked_rooms(
        self, boiler_id: str, room_ids: list[str]
    ) -> None:
        api_url = (
            f"{self._api_root}/relay/boiler/"
            f"{urllib.parse.quote(boiler_id, safe='')}/rooms"
        )
        await self._put_api_or_fail(api_url, room_ids)

    async def put_boiler_add_room(self, boiler_id: str, room_id: str) -> None:
        """Spec requires a bare text/plain body, not JSON."""
        import aiohttp

        api_url = (
            f"{self._api_root}/relay/boiler/"
            f"{urllib.parse.quote(boiler_id, safe='')}/room"
        )

        async def _attempt() -> None:
            async with self._session.put(
                api_url,
                data=room_id.encode("utf-8"),
                headers={**self._headers, "Content-Type": "text/plain"},
                ssl=self._ssl_ctx,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if not resp.ok:
                    await self._process_nok_result(resp)

        await self._retry_once_on_connection_drop(api_url, _attempt)

    # ------------------------------------------------------------------
    # Long-poll methods (Phase 1: async POST calls only — thread not replaced)
    # Phase 2 will wrap these in asyncio.Task + async retry loop.
    # ------------------------------------------------------------------

    @staticmethod
    def _check_jsonrpc_version(result: list[Any], method: str) -> None:
        # A transient non-JSON-RPC-shaped 2xx (proxy hiccup, SHC mid-reboot)
        # previously raised a bare IndexError/AttributeError here instead of
        # a handled SHCSessionError — this is the long-poll path HA actually
        # runs, so an unguarded crash here isn't caught by the poll loop's
        # JSONRPCError-specific resubscribe handling.
        if (
            not isinstance(result, list)
            or not result
            or not isinstance(result[0], dict)
        ):
            raise SHCSessionError(
                f"Malformed JSON-RPC response in {method}: expected a "
                f"non-empty list of objects, got {result!r}"
            )
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
        return str(result[0]["result"])

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
