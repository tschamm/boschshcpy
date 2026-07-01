"""Additional tests for boschshcpy.api_async — coverage extension.

Targets lines NOT covered by test_api_async.py:
  - SHCAPIAsync.__init__ constructor paths (own session + external session)
  - _get_api_result_or_fail: extra_headers, empty-body, expected_element_type mismatch
  - _put_api_or_fail: SSL error, connection error paths
  - _post_api_or_fail: SSL error, connection error paths
  - _check_jsonrpc_version: bad version raises
  - All public API methods not yet exercised
  - long_polling_unsubscribe (success + error + bad jsonrpc version)
  - close() when session is already closed

All offline — no live SHC. aiohttp mocked via unittest.mock.

Run:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_api_async_more.py -q -o addopts= -p no:cacheprovider
"""

from __future__ import annotations

import asyncio
import json
import ssl
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from boschshcpy.api_async import SHCAPIAsync, build_ssl_context
from boschshcpy.exceptions import SHCConnectionError, SHCSessionError


# ---------------------------------------------------------------------------
# Shared cert fixture (mirrors test_api_async.py pattern; session-scoped)
# ---------------------------------------------------------------------------

def _build_selfsigned_cert_and_key() -> tuple[bytes, bytes]:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "SHCTestMore")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem, key_pem


@pytest.fixture(scope="session")
def cert_and_key_paths(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    tmp = tmp_path_factory.mktemp("certs_more")
    cert_pem, key_pem = _build_selfsigned_cert_and_key()
    cert_path = tmp / "client.crt"
    key_path = tmp / "client.key"
    cert_path.write_bytes(cert_pem)
    key_path.write_bytes(key_pem)
    return str(cert_path), str(key_path)


# ---------------------------------------------------------------------------
# Helpers (same _make_api + _make_mock_response pattern)
# ---------------------------------------------------------------------------

def _make_mock_response(
    status: int = 200,
    body: Any = None,
    ok: bool = True,
) -> MagicMock:
    body_bytes = json.dumps(body).encode() if body is not None else b""
    resp = MagicMock()
    resp.ok = ok
    resp.status = status
    resp.read = AsyncMock(return_value=body_bytes)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_api(cert_and_key_paths: tuple[str, str]) -> SHCAPIAsync:
    cert, key = cert_and_key_paths
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.close = AsyncMock()

    api = SHCAPIAsync.__new__(SHCAPIAsync)
    api._controller_ip = "192.0.2.1"
    api._api_root = "https://192.0.2.1:8444/smarthome"
    api._public_root = "https://192.0.2.1:8446/smarthome/public"
    api._rpc_root = "https://192.0.2.1:8444/remote/json-rpc"
    api._ssl_ctx = build_ssl_context(cert, key)
    api._owns_session = True
    api._session = mock_session
    api._headers = {"api-version": "3.2", "Content-Type": "application/json"}
    return api


# ---------------------------------------------------------------------------
# Constructor paths
# ---------------------------------------------------------------------------

class TestConstructor:
    """Cover __init__ lines (lines ~114-131): own-session + external-session."""

    def test_init_creates_own_session(self, cert_and_key_paths: tuple[str, str]) -> None:
        """When no external_session is given, owns_session=True and session is created."""
        cert, key = cert_and_key_paths

        mock_connector = MagicMock()
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()

        with (
            patch("aiohttp.TCPConnector", return_value=mock_connector) as mock_tcp,
            patch("aiohttp.ClientSession", return_value=mock_session) as mock_cls,
        ):
            api = SHCAPIAsync("192.0.2.99", cert, key)

        # TCPConnector must be created with the ssl context
        assert mock_tcp.called
        kwargs = mock_tcp.call_args[1]
        assert isinstance(kwargs.get("ssl"), ssl.SSLContext)

        # ClientSession must be created with the connector
        assert mock_cls.called
        assert api._owns_session is True
        assert api._controller_ip == "192.0.2.99"

    def test_init_with_external_session(self, cert_and_key_paths: tuple[str, str]) -> None:
        """When external_session is provided, owns_session=False and no new session."""
        cert, key = cert_and_key_paths

        external = MagicMock()
        external.closed = False
        external.close = AsyncMock()

        with (
            patch("aiohttp.TCPConnector") as mock_tcp,
            patch("aiohttp.ClientSession") as mock_cls,
        ):
            api = SHCAPIAsync("192.0.2.88", cert, key, external_session=external)

        # No internal session must be created
        mock_tcp.assert_not_called()
        mock_cls.assert_not_called()

        assert api._owns_session is False
        assert api._session is external
        assert api._controller_ip == "192.0.2.88"

    def test_init_roots_set_correctly(self, cert_and_key_paths: tuple[str, str]) -> None:
        """All URL roots are derived from controller_ip."""
        cert, key = cert_and_key_paths

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()

        with (
            patch("aiohttp.TCPConnector"),
            patch("aiohttp.ClientSession", return_value=mock_session),
        ):
            api = SHCAPIAsync("10.0.0.5", cert, key)

        assert api._api_root == "https://10.0.0.5:8444/smarthome"
        assert api._public_root == "https://10.0.0.5:8446/smarthome/public"
        assert api._rpc_root == "https://10.0.0.5:8444/remote/json-rpc"


# ---------------------------------------------------------------------------
# _get_api_result_or_fail: edge cases
# ---------------------------------------------------------------------------

class TestGetApiResultEdgeCases:
    """Cover extra_headers branch, empty-body path, expected_element_type mismatch."""

    def test_extra_headers_merged(self, cert_and_key_paths: tuple[str, str]) -> None:
        """extra_headers must be forwarded in the actual GET call (line ~159)."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"key": "value"})
        api._session.get = MagicMock(return_value=resp)

        asyncio.run(
            api._get_api_result_or_fail(
                "https://192.0.2.1:8444/smarthome/test",
                extra_headers={"X-Custom": "header-value"},
            )
        )

        kwargs = api._session.get.call_args[1]
        headers = kwargs.get("headers", {})
        assert headers.get("X-Custom") == "header-value"
        # Base headers must still be present
        assert headers.get("api-version") == "3.2"

    def test_empty_body_returns_empty_dict(self, cert_and_key_paths: tuple[str, str]) -> None:
        """200 with empty body must return {} without JSON-decode error (line ~173)."""
        api = _make_api(cert_and_key_paths)
        resp = MagicMock()
        resp.ok = True
        resp.status = 200
        resp.read = AsyncMock(return_value=b"")
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(
            api._get_api_result_or_fail("https://192.0.2.1:8444/smarthome/test")
        )
        assert result == {}

    def test_expected_element_type_mismatch_raises(self, cert_and_key_paths: tuple[str, str]) -> None:
        """Element with wrong @type must raise SHCSessionError (lines 184-185)."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"@type": "device"}, {"@type": "room"}]  # second item is wrong
        )
        api._session.get = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected @type in API response element"):
            asyncio.run(
                api._get_api_result_or_fail(
                    "https://192.0.2.1:8444/smarthome/devices",
                    expected_element_type="device",
                )
            )

    def test_expected_element_type_all_match_returns_list(self, cert_and_key_paths: tuple[str, str]) -> None:
        """All elements matching expected_element_type must return the full list."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"@type": "room", "id": "r1"}, {"@type": "room", "id": "r2"}]
        )
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(
            api._get_api_result_or_fail(
                "https://192.0.2.1:8444/smarthome/rooms",
                expected_element_type="room",
            )
        )
        assert result == [{"@type": "room", "id": "r1"}, {"@type": "room", "id": "r2"}]

    def test_no_extra_headers_does_not_crash(self, cert_and_key_paths: tuple[str, str]) -> None:
        """extra_headers=None (default) should not crash or pollute headers."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"result": "ok"})
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(
            api._get_api_result_or_fail("https://192.0.2.1:8444/smarthome/test")
        )
        kwargs = api._session.get.call_args[1]
        # No extra key should appear beyond the two base headers
        assert set(kwargs["headers"].keys()) == {"api-version", "Content-Type"}
        assert result == {"result": "ok"}


# ---------------------------------------------------------------------------
# _process_nok_result: read() failure branch
# ---------------------------------------------------------------------------

class TestProcessNokResult:
    """Cover except branch in _process_nok_result (lines 255-256)."""

    def test_process_nok_result_read_raises_still_raises_shcsessionerror(
        self, cert_and_key_paths: tuple[str, str]
    ) -> None:
        """If resp.read() throws inside _process_nok_result, body falls back to b''."""
        api = _make_api(cert_and_key_paths)

        # Build a non-OK response whose read() raises
        bad_resp = MagicMock()
        bad_resp.ok = False
        bad_resp.status = 503
        bad_resp.read = AsyncMock(side_effect=RuntimeError("read failed"))
        bad_resp.__aenter__ = AsyncMock(return_value=bad_resp)
        bad_resp.__aexit__ = AsyncMock(return_value=False)
        api._session.get = MagicMock(return_value=bad_resp)

        with pytest.raises(SHCSessionError) as exc_info:
            asyncio.run(
                api._get_api_result_or_fail("https://192.0.2.1:8444/smarthome/test")
            )

        # Must still mention status code (body was replaced by b"")
        assert "503" in str(exc_info.value)


# ---------------------------------------------------------------------------
# _put_api_or_fail: SSL + connection error paths
# ---------------------------------------------------------------------------

class TestPutApiErrors:
    """Cover SSL error (line 220) and connection error (line 222) in _put_api_or_fail."""

    def test_ssl_error_in_put_raises_shcconnectionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        import aiohttp

        api = _make_api(cert_and_key_paths)
        conn_key = MagicMock()
        conn_key.ssl = True
        ssl_err = aiohttp.ClientSSLError(conn_key, OSError("cert verify failed"))
        api._session.put = MagicMock(side_effect=ssl_err)

        with pytest.raises(SHCConnectionError, match="SSLError"):
            asyncio.run(api._put_api_or_fail("https://192.0.2.1:8444/smarthome/x", {"key": "v"}))

    def test_connection_error_in_put_raises_shcconnectionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        import aiohttp

        api = _make_api(cert_and_key_paths)
        conn_err = aiohttp.ClientConnectionError("connection refused")
        api._session.put = MagicMock(side_effect=conn_err)

        with pytest.raises(SHCConnectionError, match="connection error"):
            asyncio.run(api._put_api_or_fail("https://192.0.2.1:8444/smarthome/x", {}))

    def test_connection_drop_then_success_retries_once_and_returns_result(
        self, cert_and_key_paths: tuple[str, str]
    ) -> None:
        """Regression (#281 parity): a single dropped connection on the FIRST
        attempt must be retried once on a fresh connection, not surfaced as
        SHCConnectionError — matching the sync client's existing retry."""
        import aiohttp

        api = _make_api(cert_and_key_paths)
        conn_err = aiohttp.ClientConnectionError("connection refused")
        ok_resp = _make_mock_response(body={"ok": True})
        api._session.put = MagicMock(side_effect=[conn_err, ok_resp])

        result = asyncio.run(
            api._put_api_or_fail("https://192.0.2.1:8444/smarthome/x", {"key": "v"})
        )

        assert result == {"ok": True}
        assert api._session.put.call_count == 2

    def test_connection_drop_twice_raises_shcconnectionerror(
        self, cert_and_key_paths: tuple[str, str]
    ) -> None:
        """Two consecutive drops (retry also fails) must still raise —
        the retry is exactly once, not unbounded."""
        import aiohttp

        api = _make_api(cert_and_key_paths)
        conn_err = aiohttp.ClientConnectionError("connection refused")
        api._session.put = MagicMock(side_effect=[conn_err, conn_err])

        with pytest.raises(SHCConnectionError, match="connection error"):
            asyncio.run(api._put_api_or_fail("https://192.0.2.1:8444/smarthome/x", {}))

        assert api._session.put.call_count == 2

    def test_put_ok_empty_body_returns_empty_dict(self, cert_and_key_paths: tuple[str, str]) -> None:
        """PUT 200 with empty body returns {} (line ~217)."""
        api = _make_api(cert_and_key_paths)
        resp = MagicMock()
        resp.ok = True
        resp.status = 200
        resp.read = AsyncMock(return_value=b"")
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        api._session.put = MagicMock(return_value=resp)

        result = asyncio.run(api._put_api_or_fail("https://192.0.2.1:8444/smarthome/x", {"a": 1}))
        assert result == {}

    def test_put_sends_json_body(self, cert_and_key_paths: tuple[str, str]) -> None:
        """PUT body must be JSON-encoded."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={})
        api._session.put = MagicMock(return_value=resp)

        asyncio.run(api._put_api_or_fail("https://192.0.2.1:8444/smarthome/x", {"@type": "lightState", "on": True}))

        kwargs = api._session.put.call_args[1]
        sent = json.loads(kwargs["data"])
        assert sent == {"@type": "lightState", "on": True}


# ---------------------------------------------------------------------------
# _post_api_or_fail: SSL + connection error paths
# ---------------------------------------------------------------------------

class TestPostApiErrors:
    """Cover SSL error and connection error in _post_api_or_fail (lines 246-249)."""

    def test_ssl_error_in_post_raises_shcconnectionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        import aiohttp

        api = _make_api(cert_and_key_paths)
        conn_key = MagicMock()
        conn_key.ssl = True
        ssl_err = aiohttp.ClientSSLError(conn_key, OSError("cert verify failed"))
        api._session.post = MagicMock(side_effect=ssl_err)

        with pytest.raises(SHCConnectionError, match="SSLError"):
            asyncio.run(api._post_api_or_fail("https://192.0.2.1:8444/remote/json-rpc", []))

    def test_connection_error_in_post_raises_shcconnectionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        import aiohttp

        api = _make_api(cert_and_key_paths)
        conn_err = aiohttp.ClientConnectionError("timed out")
        api._session.post = MagicMock(side_effect=conn_err)

        with pytest.raises(SHCConnectionError, match="connection error"):
            asyncio.run(api._post_api_or_fail("https://192.0.2.1:8444/remote/json-rpc", []))

    def test_post_ok_empty_body_returns_empty_dict(self, cert_and_key_paths: tuple[str, str]) -> None:
        """POST 200 with empty body returns {}."""
        api = _make_api(cert_and_key_paths)
        resp = MagicMock()
        resp.ok = True
        resp.status = 200
        resp.read = AsyncMock(return_value=b"")
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        api._session.post = MagicMock(return_value=resp)

        result = asyncio.run(api._post_api_or_fail("https://192.0.2.1:8444/remote/json-rpc", [{"x": 1}]))
        assert result == {}


# ---------------------------------------------------------------------------
# _check_jsonrpc_version: bad version
# ---------------------------------------------------------------------------

class TestCheckJsonrpcVersion:
    """Cover the SHCSessionError raise when jsonrpc != '2.0' (line ~341)."""

    def test_bad_jsonrpc_version_in_subscribe_raises_shcsessionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "1.0", "result": "some-poll-id"}]
        )
        api._session.post = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected JSON-RPC version"):
            asyncio.run(api.long_polling_subscribe())

    def test_bad_jsonrpc_version_in_poll_raises_shcsessionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "1.0", "result": []}]
        )
        api._session.post = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected JSON-RPC version"):
            asyncio.run(api.long_polling_poll("some-id"))

    def test_bad_jsonrpc_version_in_unsubscribe_raises_shcsessionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "99.0", "result": True}]
        )
        api._session.post = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected JSON-RPC version"):
            asyncio.run(api.long_polling_unsubscribe("some-id"))

    def test_check_jsonrpc_version_static_called_directly(self) -> None:
        """_check_jsonrpc_version can be called as a static method."""
        # OK version → no raise
        SHCAPIAsync._check_jsonrpc_version([{"jsonrpc": "2.0", "result": "x"}], "RE/test")

        # Bad version → raise
        with pytest.raises(SHCSessionError, match="Unexpected JSON-RPC version"):
            SHCAPIAsync._check_jsonrpc_version([{"jsonrpc": "1.0"}], "RE/test")

    def test_empty_list_response_raises_shcsessionerror_not_indexerror(self) -> None:
        """Regression: a malformed/empty JSON-RPC response (e.g. a proxy
        hiccup during an SHC reboot returning `[]`) must raise a handled
        SHCSessionError, not a bare IndexError."""
        with pytest.raises(SHCSessionError, match="Malformed JSON-RPC response"):
            SHCAPIAsync._check_jsonrpc_version([], "RE/test")

    def test_non_list_response_raises_shcsessionerror_not_attributeerror(self) -> None:
        """Regression: a JSON object instead of a list must raise a handled
        SHCSessionError, not a bare AttributeError from result[0].get(...)."""
        with pytest.raises(SHCSessionError, match="Malformed JSON-RPC response"):
            SHCAPIAsync._check_jsonrpc_version({"jsonrpc": "2.0"}, "RE/test")

    def test_list_of_non_dict_response_raises_shcsessionerror(self) -> None:
        with pytest.raises(SHCSessionError, match="Malformed JSON-RPC response"):
            SHCAPIAsync._check_jsonrpc_version(["not-a-dict"], "RE/test")


# ---------------------------------------------------------------------------
# long_polling_unsubscribe
# ---------------------------------------------------------------------------

class TestLongPollingUnsubscribe:
    """Cover long_polling_unsubscribe (lines 389-396)."""

    def test_unsubscribe_success_returns_result(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "2.0", "result": True}]
        )
        api._session.post = MagicMock(return_value=resp)

        result = asyncio.run(api.long_polling_unsubscribe("poll-id-abc"))

        assert result is True
        # Verify the correct JSON-RPC method was sent
        kwargs = api._session.post.call_args[1]
        body = json.loads(kwargs["data"])
        assert body[0]["method"] == "RE/unsubscribe"
        assert body[0]["params"] == ["poll-id-abc"]
        assert body[0]["jsonrpc"] == "2.0"

    def test_unsubscribe_error_raises_jsonrpcerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        from boschshcpy.api import JSONRPCError

        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid request"}}]
        )
        api._session.post = MagicMock(return_value=resp)

        with pytest.raises(JSONRPCError) as exc_info:
            asyncio.run(api.long_polling_unsubscribe("bad-id"))

        assert exc_info.value.code == -32600

    def test_unsubscribe_posts_to_rpc_root(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[{"jsonrpc": "2.0", "result": True}])
        api._session.post = MagicMock(return_value=resp)

        asyncio.run(api.long_polling_unsubscribe("my-poll"))

        called_url = api._session.post.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/remote/json-rpc"


# ---------------------------------------------------------------------------
# Public API methods not covered in test_api_async.py
# ---------------------------------------------------------------------------

class TestPublicApiMethods:
    """Cover all public methods not yet exercised (lines ~273-331)."""

    def test_get_public_information_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        """get_public_information → _public_root/information (port 8446)."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "publicInformation"})
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_public_information())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8446/smarthome/public/information"
        assert result == {"@type": "publicInformation"}

    def test_get_public_information_returns_none_on_error(self, cert_and_key_paths: tuple[str, str]) -> None:
        """get_public_information swallows exceptions and returns None."""
        import aiohttp

        api = _make_api(cert_and_key_paths)
        api._session.get = MagicMock(
            side_effect=aiohttp.ClientConnectionError("refused")
        )

        result = asyncio.run(api.get_public_information())
        assert result is None

    def test_get_rooms_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[{"@type": "room", "id": "r1"}])
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_rooms())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/rooms"
        assert result == [{"@type": "room", "id": "r1"}]

    def test_get_scenarios_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[{"@type": "scenario", "id": "s1"}])
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_scenarios())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/scenarios"
        assert result == [{"@type": "scenario", "id": "s1"}]

    def test_get_device_url_and_type(self, cert_and_key_paths: tuple[str, str]) -> None:
        """get_device(device_id) → /devices/<id> with expected_type=device."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "device", "id": "hdm:ZigBee:abc"})
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_device("hdm:ZigBee:abc"))

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/devices/hdm:ZigBee:abc"
        assert result["id"] == "hdm:ZigBee:abc"

    def test_get_device_wrong_type_raises(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "room"})
        api._session.get = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected @type"):
            asyncio.run(api.get_device("hdm:ZigBee:abc"))

    def test_get_device_services_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[{"@type": "DeviceServiceData", "id": "TemperatureLevel"}])
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_device_services("hdm:ZigBee:abc"))

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/devices/hdm:ZigBee:abc/services"
        assert result[0]["id"] == "TemperatureLevel"

    def test_get_device_service_url_and_type(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "DeviceServiceData", "id": "TemperatureLevel"})
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_device_service("hdm:ZigBee:abc", "TemperatureLevel"))

        called_url = api._session.get.call_args[0][0]
        assert called_url == (
            "https://192.0.2.1:8444/smarthome/devices/hdm:ZigBee:abc/services/TemperatureLevel"
        )
        assert result["@type"] == "DeviceServiceData"

    def test_get_device_service_wrong_type_raises(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "wrong"})
        api._session.get = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected @type"):
            asyncio.run(api.get_device_service("hdm:ZigBee:abc", "TemperatureLevel"))

    def test_get_domain_intrusion_detection_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "systemState", "systemAvailability": "AVAILABLE"})
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_domain_intrusion_detection())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/intrusion/states/system"
        assert result["@type"] == "systemState"

    def test_post_domain_action_url_and_body(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={})
        api._session.post = MagicMock(return_value=resp)

        asyncio.run(api.post_domain_action("intrusion/actions", {"@type": "triggerManualAlarm"}))

        called_url = api._session.post.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/intrusion/actions"
        body = json.loads(api._session.post.call_args[1]["data"])
        assert body == {"@type": "triggerManualAlarm"}

    def test_post_domain_action_no_data(self, cert_and_key_paths: tuple[str, str]) -> None:
        """post_domain_action with data=None must still POST (body=None serialised)."""
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={})
        api._session.post = MagicMock(return_value=resp)

        asyncio.run(api.post_domain_action("intrusion/actions"))

        called_url = api._session.post.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/intrusion/actions"


# ---------------------------------------------------------------------------
# close() edge case: session already closed
# ---------------------------------------------------------------------------

class TestCloseEdgeCases:
    """close() must be a no-op when the session is already closed (line ~139)."""

    def test_close_already_closed_session_is_noop(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        api._owns_session = True
        api._session.closed = True  # already closed

        asyncio.run(api.close())

        api._session.close.assert_not_awaited()

    def test_close_open_session_calls_close(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        api._owns_session = True
        api._session.closed = False

        asyncio.run(api.close())

        api._session.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_information swallows errors
# ---------------------------------------------------------------------------

class TestGetInformationErrorSwallowing:
    """get_information() must return None on exception (lines 268-271)."""

    def test_get_information_returns_none_on_connection_error(self, cert_and_key_paths: tuple[str, str]) -> None:
        import aiohttp

        api = _make_api(cert_and_key_paths)
        api._session.get = MagicMock(
            side_effect=aiohttp.ClientConnectionError("refused")
        )

        result = asyncio.run(api.get_information())
        assert result is None


# ---------------------------------------------------------------------------
# get_userdefinedstates + get_messages (new in 0.2.127)
# ---------------------------------------------------------------------------

class TestNewAsyncMethods:
    """Cover get_userdefinedstates and get_messages added in 0.2.127."""

    def test_get_userdefinedstates_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"@type": "userDefinedState", "id": "uds1", "name": "MyState"}]
        )
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_userdefinedstates())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/userdefinedstates"
        assert result[0]["@type"] == "userDefinedState"

    def test_get_userdefinedstates_wrong_type_raises(
        self, cert_and_key_paths: tuple[str, str]
    ) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[{"@type": "device"}])
        api._session.get = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected @type"):
            asyncio.run(api.get_userdefinedstates())

    def test_get_messages_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"@type": "message", "id": "msg1", "messageCode": {"name": "TILT_DETECTED"}}]
        )
        api._session.get = MagicMock(return_value=resp)

        result = asyncio.run(api.get_messages())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/messages"
        assert result[0]["@type"] == "message"

    def test_get_messages_wrong_type_raises(
        self, cert_and_key_paths: tuple[str, str]
    ) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[{"@type": "device"}])
        api._session.get = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected @type"):
            asyncio.run(api.get_messages())
