"""Tests for boschshcpy.api_async — Phase 1 async HTTP layer.

All tests are offline (no live SHC). aiohttp is mocked via unittest.mock so
these run in any environment that has aiohttp installed.

Run with:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_api_async.py -q -o addopts=""
"""

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
# Certificate / key helpers (same pattern as test_certificate.py)
# ---------------------------------------------------------------------------

def _build_selfsigned_cert_and_key() -> tuple[bytes, bytes]:
    """Return (cert_pem, key_pem) as separate byte strings."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "SHCTestClient")])
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
    """Write a self-signed cert+key to temp files; return (cert_path, key_path)."""
    tmp = tmp_path_factory.mktemp("certs")
    cert_pem, key_pem = _build_selfsigned_cert_and_key()
    cert_path = tmp / "client.crt"
    key_path = tmp / "client.key"
    cert_path.write_bytes(cert_pem)
    key_path.write_bytes(key_pem)
    return str(cert_path), str(key_path)


# ---------------------------------------------------------------------------
# build_ssl_context tests
# ---------------------------------------------------------------------------

class TestBuildSslContext:
    """Unit tests for build_ssl_context() — no network required."""

    def test_returns_ssl_context(self, cert_and_key_paths: tuple[str, str]) -> None:
        cert, key = cert_and_key_paths
        ctx = build_ssl_context(cert, key)
        assert isinstance(ctx, ssl.SSLContext)

    def test_check_hostname_is_false(self, cert_and_key_paths: tuple[str, str]) -> None:
        """check_hostname must be False — SHC cert CN/SAN doesn't match its IP."""
        cert, key = cert_and_key_paths
        ctx = build_ssl_context(cert, key)
        assert ctx.check_hostname is False

    def test_verify_mode_is_cert_required(self, cert_and_key_paths: tuple[str, str]) -> None:
        """verify_mode must be CERT_REQUIRED — still verifies the Bosch CA pin."""
        cert, key = cert_and_key_paths
        ctx = build_ssl_context(cert, key)
        assert ctx.verify_mode == ssl.CERT_REQUIRED

    def test_ca_chain_loaded(self, cert_and_key_paths: tuple[str, str]) -> None:
        """The bundled tls_ca_chain.pem must be loaded (context has CA certs)."""
        cert, key = cert_and_key_paths
        # We can't easily inspect loaded CAs, but if load_verify_locations failed
        # the call above would have raised — check indirectly via get_ca_certs()
        # which returns an empty list when nothing is loaded.
        ctx = build_ssl_context(cert, key)
        # A successfully loaded CA chain returns a non-empty list from get_ca_certs()
        ca_certs = ctx.get_ca_certs()
        assert isinstance(ca_certs, list)
        # The Bosch CA chain PEM is bundled in the package; it must load ≥1 cert.
        assert len(ca_certs) >= 1, "tls_ca_chain.pem appears to be empty or not loaded"

    def test_client_cert_loaded(self, cert_and_key_paths: tuple[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
        """Client cert must be loaded; mTLS requires load_cert_chain to succeed."""
        cert, key = cert_and_key_paths
        loaded_args: list[Any] = []
        original_load = ssl.SSLContext.load_cert_chain

        def spy_load_cert_chain(self: ssl.SSLContext, *args: Any, **kwargs: Any) -> None:
            loaded_args.append((args, kwargs))
            original_load(self, *args, **kwargs)

        monkeypatch.setattr(ssl.SSLContext, "load_cert_chain", spy_load_cert_chain)
        build_ssl_context(cert, key)
        assert len(loaded_args) == 1
        # certfile is the first positional or keyword argument
        call_args, call_kwargs = loaded_args[0]
        certfile = call_args[0] if call_args else call_kwargs.get("certfile")
        assert certfile == cert


class TestSSLContextParam:
    """ssl_context param lets the caller build the (blocking) SSLContext off-loop."""

    def _patch_aiohttp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sys
        import types
        fake = types.SimpleNamespace(
            TCPConnector=lambda **kw: MagicMock(),
            ClientSession=lambda **kw: MagicMock(),
        )
        monkeypatch.setitem(sys.modules, "aiohttp", fake)

    def test_passed_ssl_context_is_used_and_build_skipped(
        self, cert_and_key_paths: tuple[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import boschshcpy.api_async as mod
        cert, key = cert_and_key_paths
        self._patch_aiohttp(monkeypatch)
        calls: list[Any] = []
        monkeypatch.setattr(
            mod, "build_ssl_context", lambda c, k: calls.append((c, k))
        )
        sentinel = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        api = SHCAPIAsync("192.0.2.1", cert, key, ssl_context=sentinel)
        assert api._ssl_ctx is sentinel
        assert calls == []  # blocking build_ssl_context NOT invoked

    def test_builds_ssl_context_when_not_passed(
        self, cert_and_key_paths: tuple[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import boschshcpy.api_async as mod
        cert, key = cert_and_key_paths
        self._patch_aiohttp(monkeypatch)
        calls: list[Any] = []
        marker = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        monkeypatch.setattr(
            mod, "build_ssl_context",
            lambda c, k: (calls.append((c, k)), marker)[1],
        )
        api = SHCAPIAsync("192.0.2.1", cert, key)
        assert api._ssl_ctx is marker
        assert calls == [(cert, key)]


# ---------------------------------------------------------------------------
# Helpers for mocking aiohttp responses
# ---------------------------------------------------------------------------

def _make_mock_response(
    status: int = 200,
    body: Any = None,
    ok: bool = True,
) -> MagicMock:
    """Build a mock that behaves like an aiohttp ClientResponse used as async CM."""
    body_bytes = json.dumps(body).encode() if body is not None else b""
    resp = MagicMock()
    resp.ok = ok
    resp.status = status
    resp.read = AsyncMock(return_value=body_bytes)
    # async context manager support
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_api(cert_and_key_paths: tuple[str, str]) -> SHCAPIAsync:
    """Build an SHCAPIAsync with a mocked aiohttp.ClientSession."""
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
# URL / header construction tests
# ---------------------------------------------------------------------------

class TestUrlAndHeaders:
    """Verify that async methods build the correct URLs and pass required headers."""

    def test_get_information_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "None", "apiVersions": []})
        api._session.get = MagicMock(return_value=resp)

        asyncio.run(api.get_information())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/information"

    def test_get_devices_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[])
        api._session.get = MagicMock(return_value=resp)

        asyncio.run(api.get_devices())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/devices"

    def test_get_services_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[])
        api._session.get = MagicMock(return_value=resp)

        asyncio.run(api.get_services())

        called_url = api._session.get.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/services"

    def test_api_version_header_present(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body=[])
        api._session.get = MagicMock(return_value=resp)

        asyncio.run(api.get_devices())

        kwargs = api._session.get.call_args[1]
        headers = kwargs.get("headers", {})
        assert headers.get("api-version") == "3.2"
        assert headers.get("Content-Type") == "application/json"

    def test_put_device_service_state_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={})
        api._session.put = MagicMock(return_value=resp)

        asyncio.run(
            api.put_device_service_state("dev-1", "TemperatureLevel", {"@type": "temperatureLevelState", "temperature": 21.5})
        )

        called_url = api._session.put.call_args[0][0]
        assert called_url == (
            "https://192.0.2.1:8444/smarthome/devices/dev-1/services/TemperatureLevel/state"
        )

    def test_put_device_url_and_body(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={})
        api._session.put = MagicMock(return_value=resp)

        body = {"@type": "device", "id": "dev-1", "profile": "OUTDOOR"}
        asyncio.run(api.put_device("dev-1", body))

        called_url = api._session.put.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/smarthome/devices/dev-1"
        sent = api._session.put.call_args[1]["data"]
        assert '"profile": "OUTDOOR"' in sent

    def test_long_polling_subscribe_url(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "2.0", "result": "poll-id-abc"}]
        )
        api._session.post = MagicMock(return_value=resp)

        poll_id = asyncio.run(api.long_polling_subscribe())

        called_url = api._session.post.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/remote/json-rpc"
        assert poll_id == "poll-id-abc"

    def test_long_polling_poll_url_and_timeout(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "2.0", "result": [{"@type": "DeviceServiceData"}]}]
        )
        api._session.post = MagicMock(return_value=resp)

        result = asyncio.run(api.long_polling_poll("poll-id-xyz", wait_seconds=10))

        called_url = api._session.post.call_args[0][0]
        assert called_url == "https://192.0.2.1:8444/remote/json-rpc"
        # Body must encode the poll_id and wait_seconds
        body_str = api._session.post.call_args[1]["data"]
        body = json.loads(body_str)
        assert body[0]["method"] == "RE/longPoll"
        assert body[0]["params"] == ["poll-id-xyz", 10]
        assert result == [{"@type": "DeviceServiceData"}]


# ---------------------------------------------------------------------------
# Error mapping tests
# ---------------------------------------------------------------------------

class TestErrorMapping:
    """Non-OK HTTP responses must map to typed SHCSessionError."""

    def test_non_ok_get_raises_shcsessionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(status=403, body={"message": "Forbidden"}, ok=False)
        api._session.get = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError) as exc_info:
            asyncio.run(api._get_api_result_or_fail("https://192.0.2.1:8444/smarthome/devices"))

        assert "403" in str(exc_info.value)

    def test_non_ok_put_raises_shcsessionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(status=500, ok=False)
        api._session.put = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError) as exc_info:
            asyncio.run(api._put_api_or_fail("https://192.0.2.1:8444/smarthome/x", {}))

        assert "500" in str(exc_info.value)

    def test_non_ok_post_raises_shcsessionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(status=401, ok=False)
        api._session.post = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError):
            asyncio.run(api._post_api_or_fail("https://192.0.2.1:8444/remote/json-rpc", []))

    def test_ssl_error_raises_shcconnectionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        import aiohttp

        api = _make_api(cert_and_key_paths)
        # aiohttp 3.x ClientSSLError(connection_key, os_error)
        # conn_key must have a .ssl attribute for str() to work
        conn_key = MagicMock()
        conn_key.ssl = True
        ssl_err = aiohttp.ClientSSLError(conn_key, OSError("certificate verify failed"))
        api._session.get = MagicMock(side_effect=ssl_err)

        with pytest.raises(SHCConnectionError):
            asyncio.run(api._get_api_result_or_fail("https://192.0.2.1:8444/smarthome/devices"))

    def test_connection_error_raises_shcconnectionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        import aiohttp

        api = _make_api(cert_and_key_paths)
        conn_err = aiohttp.ClientConnectionError("refused")
        api._session.get = MagicMock(side_effect=conn_err)

        with pytest.raises(SHCConnectionError):
            asyncio.run(api._get_api_result_or_fail("https://192.0.2.1:8444/smarthome/devices"))

    def test_unexpected_type_raises_shcsessionerror(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(body={"@type": "wrong"})
        api._session.get = MagicMock(return_value=resp)

        with pytest.raises(SHCSessionError, match="Unexpected @type"):
            asyncio.run(
                api._get_api_result_or_fail(
                    "https://192.0.2.1:8444/smarthome/information",
                    expected_type="systemState",
                )
            )

    def test_jsonrpc_error_in_subscribe_raises(self, cert_and_key_paths: tuple[str, str]) -> None:
        from boschshcpy.api import JSONRPCError

        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "2.0", "error": {"code": -32001, "message": "stale poll"}}]
        )
        api._session.post = MagicMock(return_value=resp)

        with pytest.raises(JSONRPCError) as exc_info:
            asyncio.run(api.long_polling_subscribe())

        assert exc_info.value.code == -32001

    def test_jsonrpc_error_in_poll_raises(self, cert_and_key_paths: tuple[str, str]) -> None:
        from boschshcpy.api import JSONRPCError

        api = _make_api(cert_and_key_paths)
        resp = _make_mock_response(
            body=[{"jsonrpc": "2.0", "error": {"code": -32001, "message": "Unknown poll id"}}]
        )
        api._session.post = MagicMock(return_value=resp)

        with pytest.raises(JSONRPCError) as exc_info:
            asyncio.run(api.long_polling_poll("stale-id"))

        assert exc_info.value.code == -32001


# ---------------------------------------------------------------------------
# Lifecycle / session management tests
# ---------------------------------------------------------------------------

class TestLifecycle:
    """Session creation, close, and external-session passthrough."""

    def test_close_owned_session(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        api._owns_session = True
        asyncio.run(api.close())
        api._session.close.assert_awaited_once()

    def test_close_external_session_not_called(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        api._owns_session = False
        asyncio.run(api.close())
        api._session.close.assert_not_awaited()

    def test_controller_ip_property(self, cert_and_key_paths: tuple[str, str]) -> None:
        api = _make_api(cert_and_key_paths)
        assert api.controller_ip == "192.0.2.1"


# ---------------------------------------------------------------------------
# Import safety: boschshcpy importable without touching aiohttp at import time
# ---------------------------------------------------------------------------

class TestImportSafety:
    """Ensure importing boschshcpy does NOT require aiohttp."""

    def test_boschshcpy_imports_without_aiohttp(self) -> None:
        """boschshcpy package must import cleanly even if aiohttp is absent."""
        import importlib
        import sys

        # Temporarily hide aiohttp from sys.modules
        aiohttp_backup = sys.modules.pop("aiohttp", None)
        try:
            # Reload boschshcpy top-level — must not crash
            import boschshcpy
            importlib.reload(boschshcpy)
        finally:
            if aiohttp_backup is not None:
                sys.modules["aiohttp"] = aiohttp_backup

    def test_api_async_import_without_aiohttp_import_error(self, cert_and_key_paths: tuple[str, str]) -> None:
        """Constructing SHCAPIAsync without aiohttp installed must raise ImportError.

        The lazy import inside __init__ means we can simulate absence by
        patching the builtins import so 'import aiohttp' raises ImportError.
        """
        import builtins
        real_import = builtins.__import__

        def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "aiohttp":
                raise ImportError("No module named 'aiohttp'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with pytest.raises(ImportError, match="aiohttp"):
                SHCAPIAsync("192.0.2.1", "cert.pem", "key.pem")
