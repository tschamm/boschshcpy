from __future__ import annotations

import importlib.resources
import json
import logging
import urllib.parse
from typing import Any, NoReturn, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from .exceptions import SHCConnectionError, SHCSessionError
from .exceptions import JSONRPCError as JSONRPCError  # noqa: F401 -- explicit re-export

logger = logging.getLogger("boschshcpy")


class HostNameIgnoringAdapter(HTTPAdapter):
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
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if not result.ok:
            self._process_nok_result(result)

        else:
            if len(result.content) > 0:
                result = json.loads(result.content)
                if expected_type is not None and result.get("@type") != expected_type:
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

    def _put_api_or_fail(self, api_url: str, body: Any, timeout: int = 30) -> Any:
        logger.debug("PUT %s body=%s", api_url, body)
        try:
            result = self._session_request(
                "PUT", api_url, data=json.dumps(body), timeout=timeout
            )
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if not result.ok:
            self._process_nok_result(result)
        logger.debug(
            "PUT %s -> status=%s body=%s", api_url, result.status_code, result.content
        )
        if len(result.content) > 0:
            return json.loads(result.content)
        else:
            return {}

    def _post_api_or_fail(self, api_url: str, body: Any, timeout: int = 30) -> Any:
        logger.debug("POST %s body=%s", api_url, body)
        try:
            result = self._session_request(
                "POST", api_url, data=json.dumps(body), timeout=timeout
            )
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if not result.ok:
            self._process_nok_result(result)
        logger.debug(
            "POST %s -> status=%s body=%s", api_url, result.status_code, result.content
        )
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
            f"API call returned non-OK result (code {result.status_code})!: {result.content.decode('utf-8', errors='replace')}"
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

    def post_userdefinedstate(self, state_data: Any) -> Any:
        """Create a new UserDefinedState (APK ground-truth, undocumented POST).

        Body's "id" should be blank -- the SHC assigns it server-side and
        echoes the created state, including the new id, in the response.
        Confirmed live (create+delete round-trip) against a real SHC.
        """
        api_url = f"{self._api_root}/userdefinedstates"
        return self._post_api_or_fail(api_url, state_data)

    def delete_userdefinedstate(self, userdefinedstate_id: str) -> None:
        """Delete a UserDefinedState permanently (APK ground-truth, undocumented DELETE)."""
        api_url = f"{self._api_root}/userdefinedstates/{urllib.parse.quote(userdefinedstate_id, safe='')}"
        try:
            result = self._session_request("DELETE", api_url, timeout=30)
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if not result.ok:
            self._process_nok_result(result)

    def get_messages(self) -> Any:
        api_url = f"{self._api_root}/messages"
        return self._get_api_result_or_fail(api_url, expected_element_type="message")

    def get_devices(self) -> Any:
        api_url = f"{self._api_root}/devices"
        return self._get_api_result_or_fail(api_url, expected_element_type="device")

    def get_device(self, device_id: str) -> Any:
        api_url = f"{self._api_root}/devices/{device_id}"
        return self._get_api_result_or_fail(api_url, expected_type="device")

    def put_device(self, device_id: str, device_data: Any) -> Any:
        """Update a Device resource (full-body PUT).

        Used to write device-level fields such as the installation ``profile``.
        The SHC expects the full Device body (GET the device, mutate, PUT back).
        Undocumented in the local OpenAPI (GET-only); APK ground-truth.
        """
        api_url = f"{self._api_root}/devices/{device_id}"
        return self._put_api_or_fail(api_url, device_data)

    def put_device_firmware_activation(self, device_id: str) -> None:
        """Trigger a firmware update install for one device (no request body).

        Not in the official OpenAPI spec; APK ground-truth
        (RestRequests.putDeviceFirmwareActivation -> PUT
        devicemanagement/firmware/{deviceId}/activate). NEVER_BLIND_FIX:
        confirm on real hardware before relying on this outside tests.
        """
        api_url = f"{self._api_root}/devicemanagement/firmware/{urllib.parse.quote(device_id, safe='')}/activate"
        self._put_api_or_fail(api_url, body=None)

    def get_device_firmware_state(self, device_id: str) -> str | None:
        """Probe this device's firmware lifecycle state (no OpenAPI spec).

        APK ground-truth (RestRequests.getDeviceFirmwareState -> GET
        devicemanagement/firmware/{deviceId}), device-agnostic and
        independent of deviceServiceIds -- confirmed against a real SHC to
        return a bare JSON string (e.g. "UpToDate", "AwaitingActivation") for
        any device with firmware, and HTTP 404 for devices/virtual entries
        without it (returned here as None, not an error).
        """
        api_url = f"{self._api_root}/devicemanagement/firmware/{urllib.parse.quote(device_id, safe='')}"
        try:
            result = self._session_request("GET", api_url, timeout=30)
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if result.status_code == 404:
            return None
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) == 0:
            return None
        return cast(str, json.loads(result.content))

    def get_automation_rules(self) -> Any:
        """List all local automation rules (APK ground-truth, no OpenAPI spec).

        Bosch's own native "if this then that" rule engine, entirely separate
        from Home Assistant's automations. Confirmed live: GET
        automation/rules returns a JSON array of "automationRule" objects.
        """
        api_url = f"{self._api_root}/automation/rules"
        return self._get_api_result_or_fail(
            api_url, expected_element_type="automationRule"
        )

    def post_automation_rule(self, rule_data: Any) -> Any:
        """Create a new automation rule (APK ground-truth, undocumented POST).

        Body's "id" should be blank -- the SHC assigns it server-side and
        echoes the created rule, including the new id, in the response.
        Confirmed live (create+delete round-trip) against a real SHC.
        """
        api_url = f"{self._api_root}/automation/rules"
        return self._post_api_or_fail(api_url, rule_data)

    def get_automation_rule(self, rule_id: str) -> Any:
        api_url = (
            f"{self._api_root}/automation/rules/{urllib.parse.quote(rule_id, safe='')}"
        )
        return self._get_api_result_or_fail(api_url, expected_type="automationRule")

    def put_automation_rule(self, rule_id: str, rule_data: Any) -> Any:
        """Update an automation rule (full-body PUT, e.g. to toggle enabled)."""
        api_url = (
            f"{self._api_root}/automation/rules/{urllib.parse.quote(rule_id, safe='')}"
        )
        return self._put_api_or_fail(api_url, rule_data)

    def trigger_automation_rule(self, rule_id: str) -> None:
        """Manually fire an automation rule now (PUT .../trigger, no body)."""
        api_url = (
            f"{self._api_root}/automation/rules/"
            f"{urllib.parse.quote(rule_id, safe='')}/trigger"
        )
        self._put_api_or_fail(api_url, body=None)

    def delete_automation_rule(self, rule_id: str) -> None:
        """Delete an automation rule permanently. Not exposed via HA entities."""
        api_url = (
            f"{self._api_root}/automation/rules/{urllib.parse.quote(rule_id, safe='')}"
        )
        try:
            result = self._session_request("DELETE", api_url, timeout=30)
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if not result.ok:
            self._process_nok_result(result)

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

    def get_zigbee_routing_info(self, device_id: str) -> Any:
        """Fetch Zigbee routing info for a device.

        Undocumented in the local OpenAPI (no /zigbee/* paths at all); APK
        ground-truth (com.bosch.sh.common.model.zigbee). Response has no
        "@type" tag (unlike device/service resources), so no
        expected_type check — mirrors the bare passthrough of
        get_device_services(). Errors propagate the same way as every
        other sibling GET helper here (SHCConnectionError on transport
        failure, SHCSessionError on a non-OK HTTP response) — callers that
        want a None-on-failure fallback should catch at the SHCSession
        layer instead, matching get_device_services()'s convention.
        """
        api_url = (
            f"{self._api_root}/zigbee/routinginfo/"
            f"{urllib.parse.quote(device_id, safe='')}"
        )
        return self._get_api_result_or_fail(api_url)

    def post_domain_action(self, path: str, data: Any = None) -> None:
        api_url = f"{self._api_root}/{path}"
        self._post_api_or_fail(api_url, body=data)

    def put_domain_action(self, path: str, data: Any = None) -> None:
        api_url = f"{self._api_root}/{path}"
        self._put_api_or_fail(api_url, body=data)

    def get_water_alarm_system_state(self) -> Any:
        """Whole-home water-leak alarm system state (no OpenAPI spec)."""
        api_url = f"{self._api_root}/wateralarm"
        return self._get_api_result_or_fail(
            api_url, expected_type="waterAlarmSystemState"
        )

    def get_water_alarm_system_configuration(self) -> Any:
        api_url = f"{self._api_root}/wateralarm/configuration"
        return self._get_api_result_or_fail(
            api_url, expected_type="waterAlarmSystemConfiguration"
        )

    # intrusion detection configuration discovery (no OpenAPI spec; APK
    # ground-truth RestRequests.getIntrusionDetectionConfigurationProfiles*/
    # getIntrusionConfigurationEndpoint*). Read-only, confirmed live.
    def get_intrusion_profiles(self) -> Any:
        api_url = f"{self._api_root}/intrusion/profiles"
        return self._get_api_result_or_fail(api_url)

    def get_intrusion_profile(self, profile_id: str) -> Any:
        api_url = f"{self._api_root}/intrusion/profiles/{urllib.parse.quote(profile_id, safe='')}"
        return self._get_api_result_or_fail(api_url)

    def get_intrusion_profile_states(self) -> Any:
        api_url = f"{self._api_root}/intrusion/states/profiles"
        return self._get_api_result_or_fail(api_url)

    def get_intrusion_endpoint_alarm_actuators(self) -> Any:
        api_url = f"{self._api_root}/intrusion/endpoints/alarm/actuators"
        return self._get_api_result_or_fail(api_url)

    def get_intrusion_endpoint_alarm_triggers(self) -> Any:
        api_url = f"{self._api_root}/intrusion/endpoints/alarm/triggers"
        return self._get_api_result_or_fail(api_url)

    def get_intrusion_endpoint_reminder_actuators(self) -> Any:
        api_url = f"{self._api_root}/intrusion/endpoints/reminder/actuators"
        return self._get_api_result_or_fail(api_url)

    def get_open_windows(self) -> Any:
        """Whole-home open-door/open-window summary (official OpenAPI spec,
        MainResources-local-openapi-v3.yml). Live-confirmed. The real
        response is a superset of the documented `Windows` schema -- it also
        includes bypassedDoors/bypassedWindows/openOthers/bypassedOthers/
        unknownOthers alongside the documented allDoors/openDoors/
        unknownDoors/allWindows/openWindows/unknownWindows/allOthers, each a
        list of {identifier, name, roomName}.
        """
        api_url = f"{self._api_root}/doors-windows/openwindows"
        return self._get_api_result_or_fail(api_url)

    # thermostat regulation algorithm (per-device, no OpenAPI spec; APK
    # ground-truth RestRequests.getThermostatRegulationAlgorithmConfiguration/
    # putThermostatRegulationAlgorithmConfiguration).
    def get_thermostat_regulation_config(self, device_id: str) -> Any:
        """Fetch this device's regulation-algorithm config.

        Returns None on HTTP 404 (device has no regulation-algorithm
        config), matching get_device_firmware_state's contract -- not
        every device advertising deviceServiceIds has this endpoint.
        """
        api_url = (
            f"{self._api_root}/thermostat/regulation/"
            f"{urllib.parse.quote(device_id, safe='')}/config"
        )
        try:
            result = self._session_request("GET", api_url, timeout=30)
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if result.status_code == 404:
            return None
        if not result.ok:
            self._process_nok_result(result)
        if len(result.content) == 0:
            return None
        return json.loads(result.content)

    def put_thermostat_regulation_config(self, device_id: str, config: Any) -> Any:
        api_url = (
            f"{self._api_root}/thermostat/regulation/"
            f"{urllib.parse.quote(device_id, safe='')}/config"
        )
        return self._put_api_or_fail(api_url, config)

    # temperature drop service (per-room anti-frost/window-open compensation;
    # no OpenAPI spec; APK ground-truth RestRequests.getTemperatureDropService(s)/
    # putTemperatureDropService). Confirmed live across 12 real rooms.
    def get_temperature_drop_services(self) -> Any:
        api_url = f"{self._api_root}/climate/temperaturedropservice"
        return self._get_api_result_or_fail(api_url)

    def get_temperature_drop_service(self, room_id: str) -> Any:
        api_url = (
            f"{self._api_root}/climate/temperaturedropservice/"
            f"{urllib.parse.quote(room_id, safe='')}"
        )
        return self._get_api_result_or_fail(api_url)

    def put_temperature_drop_service(self, room_id: str, data: Any) -> Any:
        api_url = (
            f"{self._api_root}/climate/temperaturedropservice/"
            f"{urllib.parse.quote(room_id, safe='')}"
        )
        return self._put_api_or_fail(api_url, data)

    # hydraulic balancing (no OpenAPI spec; APK ground-truth
    # RestRequests.get(All)HydraulicBalancingConfiguration(s)/
    # putHydraulicBalancingConfiguration). NOT live-confirmed -- this test
    # installation returns 503 (no hydraulic-balancing-capable devices) --
    # implemented from the decompiled Kotlin data class only.
    def get_hydraulic_balancing_configurations(self) -> Any:
        api_url = f"{self._api_root}/climate/hydraulicbalancing"
        return self._get_api_result_or_fail(api_url)

    def get_hydraulic_balancing_configuration(self, config_id: str) -> Any:
        api_url = (
            f"{self._api_root}/climate/hydraulicbalancing/"
            f"{urllib.parse.quote(config_id, safe='')}"
        )
        return self._get_api_result_or_fail(api_url)

    def put_hydraulic_balancing_configuration(self, config_id: str, config: Any) -> Any:
        api_url = (
            f"{self._api_root}/climate/hydraulicbalancing/"
            f"{urllib.parse.quote(config_id, safe='')}"
        )
        return self._put_api_or_fail(api_url, config)

    # comfort zone templates (Twinguard/air-quality sensors; no OpenAPI spec;
    # APK ground-truth RestRequests.getComfortZoneTemplatesRequest/
    # getSaveCustomComfortZoneTemplateRequest). NOT live-confirmed -- this
    # installation has no Twinguard device.
    def get_comfort_zone_templates(self, sensor_id: str) -> Any:
        api_url = (
            f"{self._api_root}/airquality/comfortzone/templates/"
            f"{urllib.parse.quote(sensor_id, safe='')}"
        )
        return self._get_api_result_or_fail(api_url)

    def put_comfort_zone_template(self, sensor_id: str, comfort_zone: Any) -> Any:
        api_url = (
            f"{self._api_root}/airquality/comfortzone/templates/"
            f"{urllib.parse.quote(sensor_id, safe='')}/custom"
        )
        return self._put_api_or_fail(api_url, comfort_zone)

    # Multiroom Boiler Control room-linking (official OpenAPI spec,
    # MultiroomBoilerControl-local-openapi-v3.yml). NOT live-confirmed -- no
    # owned Boiler hardware; implemented directly from the spec.
    def get_boiler_capable_rooms(self) -> Any:
        api_url = f"{self._api_root}/relay/boiler/rooms"
        return self._get_api_result_or_fail(api_url)

    def get_boiler_linked_rooms(self, boiler_id: str) -> Any:
        api_url = (
            f"{self._api_root}/relay/boiler/"
            f"{urllib.parse.quote(boiler_id, safe='')}/rooms"
        )
        return self._get_api_result_or_fail(api_url)

    def put_boiler_linked_rooms(self, boiler_id: str, room_ids: list[str]) -> None:
        api_url = (
            f"{self._api_root}/relay/boiler/"
            f"{urllib.parse.quote(boiler_id, safe='')}/rooms"
        )
        self._put_api_or_fail(api_url, room_ids)

    def put_boiler_add_room(self, boiler_id: str, room_id: str) -> None:
        """Spec requires a bare text/plain body, not JSON."""
        api_url = (
            f"{self._api_root}/relay/boiler/"
            f"{urllib.parse.quote(boiler_id, safe='')}/room"
        )
        try:
            result = self._session_request(
                "PUT",
                api_url,
                data=room_id.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            raise SHCConnectionError(f"API call failed: {e}.") from e
        if not result.ok:
            self._process_nok_result(result)

    @staticmethod
    def _check_jsonrpc_version(result: Any, method: str) -> None:
        # A transient non-JSON-RPC-shaped 2xx (e.g. a proxy hiccup or the SHC
        # mid-reboot) previously raised a bare IndexError/AttributeError here
        # instead of a handled SHCSessionError — callers only catch
        # JSONRPCError/SHCSessionError, so this could crash the polling
        # thread's exception handling in an unexpected way.
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
