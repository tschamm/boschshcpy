"""Tests for boschshcpy.rawscan and boschshcpy.register_client.

Style: mirrors test_reliability.py / test_certificate.py — no HA harness,
no real network.  HTTP/requests/socket calls are patched via unittest.mock.
"""

import base64
import json
import sys
import types
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, mock_open

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Helpers shared across suites
# ──────────────────────────────────────────────────────────────────────────────


def _fake_response(status_code=200, content=b"", ok=None):
    """Return a minimal fake requests.Response."""
    resp = SimpleNamespace()
    resp.status_code = status_code
    resp.content = content
    resp.ok = (status_code < 400) if ok is None else ok
    return resp


# ══════════════════════════════════════════════════════════════════════════════
# register_client.py tests
# ══════════════════════════════════════════════════════════════════════════════

from boschshcpy.register_client import (
    HostNameIgnoringAdapter,
    SHCRegisterClient,
    write_tls_asset,
)
from boschshcpy.exceptions import SHCRegistrationError


class TestHostNameIgnoringAdapter:
    def test_init_poolmanager_sets_assert_hostname_false(self):
        """PoolManager must be created with assert_hostname=False."""
        from requests.packages.urllib3.poolmanager import PoolManager

        adapter = HostNameIgnoringAdapter()
        created_kw = {}

        original_pm = PoolManager

        def capturing_pm(**kw):
            created_kw.update(kw)
            return original_pm(**kw)

        with patch(
            "boschshcpy.register_client.PoolManager", side_effect=capturing_pm
        ):
            adapter.init_poolmanager(connections=2, maxsize=5)

        assert created_kw.get("assert_hostname") is False
        assert created_kw["num_pools"] == 2
        assert created_kw["maxsize"] == 5


class TestSHCRegisterClientInit:
    def _make_client(self, ip="192.168.0.1", password="secret"):
        """Construct SHCRegisterClient, suppressing real requests.Session setup."""
        import urllib3

        with patch("boschshcpy.register_client.requests.Session") as mock_sess_cls, \
             patch("urllib3.disable_warnings"):
            mock_sess = MagicMock()
            mock_sess_cls.return_value = mock_sess
            client = SHCRegisterClient(ip, password)
            client._requests_session = mock_sess  # keep reference for inspection
            return client, mock_sess

    def test_url_construction(self):
        client, _ = self._make_client(ip="10.0.0.5")
        assert client._url == "https://10.0.0.5:8443/smarthome/clients"

    def test_controller_ip_stored(self):
        client, _ = self._make_client(ip="1.2.3.4")
        assert client._controller_ip == "1.2.3.4"

    def test_systempassword_header_is_base64_of_password(self):
        password = "myP@ssw0rd"
        expected_b64 = base64.b64encode(password.encode("utf-8")).decode("utf-8")

        with patch("boschshcpy.register_client.requests.Session") as mock_sess_cls, \
             patch("urllib3.disable_warnings"):
            mock_sess = MagicMock()
            mock_sess_cls.return_value = mock_sess
            SHCRegisterClient("1.2.3.4", password)

        # headers.update must have been called with the correct Systempassword
        calls = mock_sess.headers.update.call_args_list
        assert len(calls) >= 1
        headers_passed = calls[0][0][0]
        assert headers_passed["Systempassword"] == expected_b64

    def test_content_type_header(self):
        with patch("boschshcpy.register_client.requests.Session") as mock_sess_cls, \
             patch("urllib3.disable_warnings"):
            mock_sess = MagicMock()
            mock_sess_cls.return_value = mock_sess
            SHCRegisterClient("1.2.3.4", "pw")

        calls = mock_sess.headers.update.call_args_list
        headers_passed = calls[0][0][0]
        assert headers_passed["Content-Type"] == "application/json"


class TestPostApiOrFail:
    """Unit-test _post_api_or_fail without real HTTP."""

    def _client(self):
        with patch("boschshcpy.register_client.requests.Session"), \
             patch("urllib3.disable_warnings"):
            c = SHCRegisterClient.__new__(SHCRegisterClient)
            c._controller_ip = "1.2.3.4"
            c._url = "https://1.2.3.4:8443/smarthome/clients"
            c._requests_session = MagicMock()
            return c

    def test_success_returns_parsed_json(self):
        client = self._client()
        body = {"token": "abc:hostname"}
        client._requests_session.post.return_value = _fake_response(
            200, json.dumps(body).encode()
        )
        result = client._post_api_or_fail({"key": "value"})
        assert result == body

    def test_empty_content_returns_empty_dict(self):
        client = self._client()
        client._requests_session.post.return_value = _fake_response(200, b"")
        result = client._post_api_or_fail({})
        assert result == {}

    def test_nok_result_raises_registration_error(self):
        client = self._client()
        client._requests_session.post.return_value = _fake_response(
            403, b"Forbidden", ok=False
        )
        with pytest.raises(SHCRegistrationError, match="403"):
            client._post_api_or_fail({})

    def test_ssl_error_raises_registration_error(self):
        import requests as req_mod

        client = self._client()
        client._requests_session.post.side_effect = req_mod.exceptions.SSLError(
            "bad cert"
        )
        with pytest.raises(SHCRegistrationError, match="pairing mode"):
            client._post_api_or_fail({})

    def test_post_called_with_json_encoded_body(self):
        client = self._client()
        body = {"@type": "client", "id": "x"}
        client._requests_session.post.return_value = _fake_response(200, b"")
        client._post_api_or_fail(body, timeout=10)
        client._requests_session.post.assert_called_once_with(
            client._url, data=json.dumps(body), timeout=10
        )


class TestProcessNokResult:
    def _client(self):
        c = SHCRegisterClient.__new__(SHCRegisterClient)
        return c

    def test_raises_with_status_code_in_message(self):
        client = self._client()
        fake_resp = _fake_response(401, b"Unauthorized", ok=False)
        with pytest.raises(SHCRegistrationError) as exc_info:
            client._process_nok_result(fake_resp)
        assert "401" in str(exc_info.value)

    def test_raises_with_content_in_message(self):
        client = self._client()
        fake_resp = _fake_response(400, b"Bad Request Body", ok=False)
        with pytest.raises(SHCRegistrationError) as exc_info:
            client._process_nok_result(fake_resp)
        assert b"Bad Request Body" in str(exc_info.value).encode()


class TestRegister:
    def _client(self):
        c = SHCRegisterClient.__new__(SHCRegisterClient)
        c._controller_ip = "1.2.3.4"
        c._url = "https://1.2.3.4:8443/smarthome/clients"
        c._requests_session = MagicMock()
        return c

    def _fake_cert_key(self):
        """Return fake PEM bytes for cert and key."""
        fake_cert = (
            b"-----BEGIN CERTIFICATE-----\nABCD\n-----END CERTIFICATE-----\n"
        )
        fake_key = b"-----BEGIN RSA PRIVATE KEY-----\nXYZ\n-----END RSA PRIVATE KEY-----\n"
        return fake_cert, fake_key

    def test_register_with_token_returns_dict(self):
        client = self._client()
        fake_cert, fake_key = self._fake_cert_key()

        with patch(
            "boschshcpy.register_client.generate_certificate",
            return_value=(fake_cert, fake_key),
        ):
            response_body = {"token": "abc:hostname1"}
            client._requests_session.post.return_value = _fake_response(
                200, json.dumps(response_body).encode()
            )
            result = client.register("my_id", "MyName")

        assert result is not None
        assert result["token"] == "abc:hostname1"
        assert result["cert"] == fake_cert
        assert result["key"] == fake_key

    def test_register_without_token_returns_none(self):
        client = self._client()
        fake_cert, fake_key = self._fake_cert_key()

        with patch(
            "boschshcpy.register_client.generate_certificate",
            return_value=(fake_cert, fake_key),
        ):
            response_body = {}  # no "token" key
            client._requests_session.post.return_value = _fake_response(
                200, json.dumps(response_body).encode()
            )
            result = client.register("my_id", "MyName")

        assert result is None

    def test_register_builds_correct_payload(self):
        """The POST body must match the SHC API shape, including cert formatting."""
        client = self._client()
        fake_cert = (
            b"-----BEGIN CERTIFICATE-----\nLINE1\nLINE2\n-----END CERTIFICATE-----\n"
        )
        fake_key = b"-----BEGIN RSA PRIVATE KEY-----\nKEY\n-----END RSA PRIVATE KEY-----\n"

        captured_body = {}

        def fake_post(url, data, timeout):
            captured_body.update(json.loads(data))
            return _fake_response(200, json.dumps({"token": "t:h"}).encode())

        client._requests_session.post.side_effect = fake_post

        with patch(
            "boschshcpy.register_client.generate_certificate",
            return_value=(fake_cert, fake_key),
        ):
            client.register("test_id", "TestName")

        assert captured_body["@type"] == "client"
        assert captured_body["id"] == "test_id"
        assert captured_body["name"] == "oss_TestName_Binding"
        assert captured_body["primaryRole"] == "ROLE_RESTRICTED_CLIENT"
        # Cert must have \r line-endings around the markers (not \n)
        assert "\r" in captured_body["certificate"]
        assert "-----BEGIN CERTIFICATE-----" in captured_body["certificate"]

    def test_register_propagates_ssl_error(self):
        import requests as req_mod

        client = self._client()
        fake_cert, fake_key = self._fake_cert_key()

        with patch(
            "boschshcpy.register_client.generate_certificate",
            return_value=(fake_cert, fake_key),
        ):
            client._requests_session.post.side_effect = req_mod.exceptions.SSLError(
                "ssl fail"
            )
            with pytest.raises(SHCRegistrationError, match="pairing mode"):
                client.register("id", "name")


class TestWriteTlsAsset:
    def test_write_decodes_bytes_to_utf8(self, tmp_path):
        asset_bytes = b"-----BEGIN CERTIFICATE-----\nABC\n-----END CERTIFICATE-----\n"
        out_file = tmp_path / "cert.pem"
        write_tls_asset(str(out_file), asset_bytes)
        written = out_file.read_text(encoding="utf8")
        assert written == asset_bytes.decode("utf-8")

    def test_write_creates_file_if_not_exists(self, tmp_path):
        out_file = tmp_path / "subdir" / "key.pem"
        out_file.parent.mkdir()
        write_tls_asset(str(out_file), b"KEY DATA")
        assert out_file.exists()

    def test_write_creates_file_with_owner_only_permissions(self, tmp_path):
        """The private key must not be created world/group-readable under the
        common 022 umask — os.open(..., 0o600) instead of the bare open()
        builtin (which honors the process umask)."""
        import stat

        out_file = tmp_path / "key.pem"
        write_tls_asset(str(out_file), b"KEY DATA")
        mode = stat.S_IMODE(out_file.stat().st_mode)
        assert mode == 0o600


# ══════════════════════════════════════════════════════════════════════════════
# rawscan.py tests
# ══════════════════════════════════════════════════════════════════════════════
# rawscan.main() is a CLI entry-point. We test it by patching sys.argv,
# SHCSession, and capturing sys.exit / stdout.
# ══════════════════════════════════════════════════════════════════════════════

from boschshcpy import rawscan
from boschshcpy.exceptions import SHCAuthenticationError


def _make_fake_session(subcommand_data=None):
    """Return a mock SHCSession whose api returns canned JSON-serialisable data."""
    data = subcommand_data if subcommand_data is not None else {"ok": True}
    api = MagicMock()
    api.get_devices.return_value = data
    api.get_services.return_value = data
    api.get_userdefinedstates.return_value = data
    api.get_rooms.return_value = data
    api.get_scenarios.return_value = data
    api.get_device.return_value = data
    api.get_device_services.return_value = data
    api.get_device_service.return_value = data
    api.get_information.return_value = data
    api.get_public_information.return_value = data
    api.get_domain_intrusion_detection.return_value = data

    session = MagicMock()
    session.api = api
    return session


_COMMON_ARGV = [
    "rawscan",
    "--certificate", "/tmp/cert.pem",
    "--key", "/tmp/key.pem",
    "--ip_address", "1.2.3.4",
]


def _run_main(extra_argv, fake_session):
    """Patch sys.argv + SHCSession, run main(), capture SystemExit."""
    argv = _COMMON_ARGV + extra_argv
    with patch.object(sys, "argv", argv), \
         patch("boschshcpy.rawscan.SHCSession", return_value=fake_session):
        with pytest.raises(SystemExit):
            rawscan.main()


class TestRawscanSubcommands:
    def test_devices_calls_get_devices(self, capsys):
        sess = _make_fake_session({"dev": "list"})
        _run_main(["devices"], sess)
        sess.api.get_devices.assert_called_once()

    def test_services_calls_get_services(self):
        sess = _make_fake_session()
        _run_main(["services"], sess)
        sess.api.get_services.assert_called_once()

    def test_userdefinedstates_calls_get_userdefinedstates(self):
        sess = _make_fake_session()
        _run_main(["userdefinedstates"], sess)
        sess.api.get_userdefinedstates.assert_called_once()

    def test_rooms_calls_get_rooms(self):
        sess = _make_fake_session()
        _run_main(["rooms"], sess)
        sess.api.get_rooms.assert_called_once()

    def test_scenarios_calls_get_scenarios(self):
        sess = _make_fake_session()
        _run_main(["scenarios"], sess)
        sess.api.get_scenarios.assert_called_once()

    def test_device_calls_get_device_with_id(self):
        sess = _make_fake_session()
        _run_main(["device", "hdm:ZigBee:abc123"], sess)
        sess.api.get_device.assert_called_once_with("hdm:ZigBee:abc123")

    def test_device_services_calls_get_device_services(self):
        sess = _make_fake_session()
        _run_main(["device_services", "hdm:ZigBee:abc123"], sess)
        sess.api.get_device_services.assert_called_once_with("hdm:ZigBee:abc123")

    def test_device_service_calls_get_device_service(self):
        sess = _make_fake_session()
        _run_main(["device_service", "hdm:ZigBee:abc123", "TemperatureLevel"], sess)
        sess.api.get_device_service.assert_called_once_with(
            "hdm:ZigBee:abc123", "TemperatureLevel"
        )

    def test_info_calls_get_information(self):
        sess = _make_fake_session()
        _run_main(["info"], sess)
        sess.api.get_information.assert_called_once()

    def test_information_alias_calls_get_information(self):
        sess = _make_fake_session()
        _run_main(["information"], sess)
        sess.api.get_information.assert_called_once()

    def test_public_information_calls_get_public_information(self):
        sess = _make_fake_session()
        _run_main(["public_information"], sess)
        sess.api.get_public_information.assert_called_once()

    def test_intrusion_detection_calls_get_domain_intrusion_detection(self):
        sess = _make_fake_session()
        _run_main(["intrusion_detection"], sess)
        sess.api.get_domain_intrusion_detection.assert_called_once()


class TestRawscanOutput:
    def test_output_is_valid_json(self, capsys):
        sess = _make_fake_session({"foo": "bar", "n": 42})
        _run_main(["devices"], sess)
        out, _ = capsys.readouterr()
        # main() prints then sys.exit(); first non-empty line is the JSON
        parsed = json.loads(out.strip())
        assert parsed == {"foo": "bar", "n": 42}


class TestRawscanAuthError:
    def test_authentication_error_prints_and_exits(self, capsys):
        """SHCAuthenticationError must be caught; program must exit cleanly."""
        argv = _COMMON_ARGV + ["devices"]
        with patch.object(sys, "argv", argv), \
             patch(
                 "boschshcpy.rawscan.SHCSession",
                 side_effect=SHCAuthenticationError("bad creds"),
             ):
            with pytest.raises(SystemExit):
                rawscan.main()
        out, _ = capsys.readouterr()
        assert "bad creds" in out


class TestRawscanNoArgs:
    def test_no_subcommand_exits(self, capsys):
        """Calling with only required args but no subcommand should exit (argparse error)."""
        argv = [
            "rawscan",
            "--certificate", "/tmp/cert.pem",
            "--key", "/tmp/key.pem",
            "--ip_address", "1.2.3.4",
        ]
        with patch.object(sys, "argv", argv):
            with pytest.raises(SystemExit):
                rawscan.main()


# ══════════════════════════════════════════════════════════════════════════════
# register_client.main() tests
# ══════════════════════════════════════════════════════════════════════════════

from boschshcpy import register_client as reg_mod


_REG_ARGV = [
    "register_client",
    "--ip_address", "1.2.3.4",
    "--password", "supersecret",
    "--name", "TestClient",
    "--id", "test_client_id",
]


class TestRegisterClientMain:
    def _run_main(self, fake_register_result, extra_argv=None):
        argv = _REG_ARGV + (extra_argv or [])
        fake_helper = MagicMock()
        fake_helper.register.return_value = fake_register_result

        with patch.object(sys, "argv", argv), \
             patch("boschshcpy.register_client.SHCRegisterClient", return_value=fake_helper), \
             patch("boschshcpy.register_client.write_tls_asset") as mock_write:
            try:
                reg_mod.main()
            except SystemExit:
                pass
            return fake_helper, mock_write

    def test_main_success_writes_cert_and_key(self, tmp_path, capsys):
        """When register returns a token, main() writes two TLS asset files."""
        fake_cert = b"-----BEGIN CERTIFICATE-----\nABC\n-----END CERTIFICATE-----\n"
        fake_key = b"-----BEGIN RSA PRIVATE KEY-----\nKEY\n-----END RSA PRIVATE KEY-----\n"
        result = {"token": "abc:myhostname", "cert": fake_cert, "key": fake_key}

        _, mock_write = self._run_main(result)

        assert mock_write.call_count == 2
        call_names = [c[0][0] for c in mock_write.call_args_list]
        assert any("cert.pem" in name for name in call_names)
        assert any("key.pem" in name for name in call_names)
        # Token hostname must appear in filenames
        assert all("myhostname" in name for name in call_names)

    def test_main_success_prints_token(self, capsys):
        fake_cert = b"CERT"
        fake_key = b"KEY"
        result = {"token": "tok:host123", "cert": fake_cert, "key": fake_key}
        self._run_main(result)
        out, _ = capsys.readouterr()
        assert "tok:host123" in out

    def test_main_no_token_prints_no_valid_token(self, capsys):
        """When register returns None, main() prints the no-token message and exits."""
        _, _ = self._run_main(None)
        out, _ = capsys.readouterr()
        assert "No valid token" in out

    def test_main_does_not_print_cert_or_key_material(self, capsys):
        """Fix: cert/key must not be printed to stdout — they'd end up in
        terminal scrollback/shell history/CI logs. Files (0o600) are the
        source of truth, not stdout."""
        fake_cert = b"-----BEGIN CERTIFICATE-----\nSECRETCERTDATA\n-----END CERTIFICATE-----\n"
        fake_key = b"-----BEGIN RSA PRIVATE KEY-----\nSECRETKEYDATA\n-----END RSA PRIVATE KEY-----\n"
        result = {"token": "tok:host123", "cert": fake_cert, "key": fake_key}
        self._run_main(result)
        out, _ = capsys.readouterr()
        assert "SECRETCERTDATA" not in out
        assert "SECRETKEYDATA" not in out

    def test_main_prompts_for_password_when_omitted(self):
        """Fix: password must not be required as a CLI arg (visible in
        `ps`/shell history) — prompt via getpass when -pw is omitted."""
        argv = [
            "register_client",
            "--ip_address", "1.2.3.4",
            "--name", "TestClient",
            "--id", "test_client_id",
        ]
        fake_helper = MagicMock()
        fake_helper.register.return_value = None

        with patch.object(sys, "argv", argv), \
             patch("boschshcpy.register_client.getpass.getpass", return_value="prompted-pw") as mock_getpass, \
             patch("boschshcpy.register_client.SHCRegisterClient", return_value=fake_helper) as mock_client:
            try:
                reg_mod.main()
            except SystemExit:
                pass

        mock_getpass.assert_called_once()
        mock_client.assert_called_once_with("1.2.3.4", "prompted-pw")

    def test_main_uses_cli_password_without_prompting(self):
        """When -pw is given, getpass must not be invoked."""
        fake_helper = MagicMock()
        fake_helper.register.return_value = None

        with patch.object(sys, "argv", _REG_ARGV), \
             patch("boschshcpy.register_client.getpass.getpass") as mock_getpass, \
             patch("boschshcpy.register_client.SHCRegisterClient", return_value=fake_helper) as mock_client:
            try:
                reg_mod.main()
            except SystemExit:
                pass

        mock_getpass.assert_not_called()
        mock_client.assert_called_once_with("1.2.3.4", "supersecret")

    def test_main_registration_error_is_printed(self, capsys):
        """SHCRegistrationError inside register() must be caught and printed."""
        argv = _REG_ARGV
        fake_helper = MagicMock()
        fake_helper.register.side_effect = SHCRegistrationError("button not pressed")

        with patch.object(sys, "argv", argv), \
             patch("boschshcpy.register_client.SHCRegisterClient", return_value=fake_helper):
            try:
                reg_mod.main()
            except SystemExit:
                pass

        out, _ = capsys.readouterr()
        assert "button not pressed" in out

    def test_main_hostname_derived_from_token(self, capsys):
        """The hostname part (after ':') of the token must appear in filenames."""
        fake_cert = b"C"
        fake_key = b"K"
        result = {"token": "myclient:uniquehostXYZ", "cert": fake_cert, "key": fake_key}
        _, mock_write = self._run_main(result)
        call_names = [c[0][0] for c in mock_write.call_args_list]
        assert all("uniquehostXYZ" in n for n in call_names)


# ---------------------------------------------------------------------------
# Regression: help-on-no-args (the len(sys.argv)==1 branch must run BEFORE
# parse_args, otherwise argparse's required-subparser exits first / the branch
# is dead). Fixed by moving the check ahead of parser.parse_args().
# ---------------------------------------------------------------------------
import argparse as _argparse


def test_rawscan_main_no_args_prints_help_and_exits():
    """rawscan with only the program name → print help, then exit (branch reachable)."""
    with patch.object(sys, "argv", ["rawscan"]), \
         patch.object(_argparse.ArgumentParser, "print_help") as mock_help:
        with pytest.raises(SystemExit):
            rawscan.main()
    assert mock_help.called


def test_register_main_no_args_prints_help_and_exits():
    """register_client with only the program name → print help, then exit."""
    with patch.object(sys, "argv", ["register_client"]), \
         patch.object(_argparse.ArgumentParser, "print_help") as mock_help:
        with pytest.raises(SystemExit):
            reg_mod.main()
    assert mock_help.called
