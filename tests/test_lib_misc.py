"""Isolation-safe coverage tests for emma.py, exceptions.py, generate_cert.py.

Style: mirror test_reliability.py / test_emma.py — no HA harness, no network.
SHCEmma is instantiated normally (its __init__ is safe with api=None and
raw_device_services=None when deviceServiceIds=[]); for coverage of lines not
reached by test_emma.py we exercise: the fallback-raw-result branch (no
raw_result given), version/localizedTitles/localizedInformation properties,
the two localizedSubTitles spelling variants, the
update_emma_data path (incl. callback firing and the missing-shc_info guard),
and the summary() printer.
"""

from unittest.mock import MagicMock, patch
import pytest

# ===========================================================================
# emma.py — lines 33, 46, 50, 77-93
# ===========================================================================

from boschshcpy.emma import SHCEmma
from boschshcpy.exceptions import SHCException


def _shc_info_mock(mac="AA:BB:CC:DD:EE:FF"):
    shc_info = MagicMock()
    shc_info.macAddress = mac
    return shc_info


def _full_raw(
    version="2.0",
    title_en="Solar Overview",
    subtitle_en="Local Consumption",
    info_en="300 W",
    subtitle_key="localizedSubtitles",
):
    raw = {
        "version": version,
        "localizedTitles": {"en": title_en},
        "localizedInformation": {"en": info_en},
    }
    raw[subtitle_key] = {"en": subtitle_en}
    return raw


# --- line 33: default raw_result branch (no raw_result supplied) ---

def test_no_raw_result_defaults_version_empty():
    """When raw_result is omitted, version defaults to ''."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    assert emma.version == ""


def test_no_raw_result_defaults_localized_titles_empty():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    assert emma.localizedTitles == ""


def test_no_raw_result_defaults_localized_information():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    assert emma.localizedInformation == "0 W"


def test_no_raw_result_status_unavailable():
    """With shc_info present but no raw_result → status UNAVAILABLE."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    assert emma.status == "UNAVAILABLE"


def test_no_shc_info_no_raw_result_status_undefined():
    """No shc_info, no raw_result → status UNDEFINED."""
    emma = SHCEmma(api=None, shc_info=None)
    assert emma.status == "UNDEFINED"


def test_with_raw_result_status_available():
    """raw_result present → status AVAILABLE."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw())
    assert emma.status == "AVAILABLE"


# --- line 46: version property ---

def test_version_property_returns_value():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw(version="9.10.3"))
    assert emma.version == "9.10.3"


def test_version_property_empty_string():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw(version=""))
    assert emma.version == ""


# --- line 50: localizedTitles property ---

def test_localized_titles_property():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw(title_en="My Title"))
    assert emma.localizedTitles == "My Title"


def test_localized_titles_empty():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw(title_en=""))
    assert emma.localizedTitles == ""


# --- localizedInformation property ---

def test_localized_information_property():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw(info_en="750 W"))
    assert emma.localizedInformation == "750 W"


# --- localizedSubtitles fallback: both spelling variants ---

def test_localized_subtitles_lowercase_t():
    """Standard API spelling: localizedSubtitles (lowercase t)."""
    raw = _full_raw(subtitle_key="localizedSubtitles", subtitle_en="Grid Feed-In")
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    assert emma.localizedSubtitles == "Grid Feed-In"


def test_localized_subtitles_capital_T_fallback():
    """Alternative API spelling: localizedSubTitles (capital T) must not raise."""
    raw = _full_raw(subtitle_key="localizedSubTitles", subtitle_en="Grid Supply")
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    assert emma.localizedSubtitles == "Grid Supply"


def test_localized_subtitles_absent_returns_empty_string():
    """Neither key present → empty string, no KeyError."""
    raw = {
        "version": "1.0",
        "localizedTitles": {"en": ""},
        "localizedInformation": {"en": "0 W"},
    }
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    assert emma.localizedSubtitles == ""


def test_localized_subtitles_missing_en_returns_empty_string():
    """Key present but 'en' missing → empty string."""
    raw = {
        "version": "1.0",
        "localizedTitles": {"en": ""},
        "localizedInformation": {"en": "0 W"},
        "localizedSubtitles": {"de": "Netzbezug"},
    }
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    assert emma.localizedSubtitles == ""


# --- value property edge cases (beyond test_emma.py) ---

def test_value_zero_with_capital_T_subtitle():
    """0 W + capitalT subtitle key must not raise."""
    raw = _full_raw(subtitle_key="localizedSubTitles", subtitle_en="Local Consumption", info_en="0 W")
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    assert emma.value == 0.0


def test_value_none_when_no_subtitle_key():
    """Missing subtitle → "" → not 'Grid Supply' → positive sign → normal parse."""
    raw = {
        "version": "1.0",
        "localizedTitles": {"en": ""},
        "localizedInformation": {"en": "100 W"},
    }
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    assert emma.value == 100.0


def test_value_none_for_non_numeric_watt_string():
    """Completely non-numeric info string → None."""
    raw = _full_raw(info_en="--- W", subtitle_en="Local Consumption")
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    assert emma.value is None


# --- line 77-84: update_emma_data ---

def test_update_emma_data_raises_when_no_shc_info():
    """update_emma_data without shc_info → SHCException."""
    emma = SHCEmma(api=None, shc_info=None)
    with pytest.raises(SHCException) as exc_info:
        emma.update_emma_data({"version": "1.0", "localizedTitles": {"en": ""}, "localizedInformation": {"en": "0 W"}})
    assert "initialization" in exc_info.value.message.lower()


def test_update_emma_data_updates_raw_result():
    """update_emma_data replaces _raw_result and sets status AVAILABLE."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    new_raw = _full_raw(version="3.0", info_en="500 W", subtitle_en="Local Consumption")
    emma.update_emma_data(new_raw)
    assert emma.version == "3.0"
    assert emma.status == "AVAILABLE"
    assert emma.localizedInformation == "500 W"


def test_update_emma_data_fires_callbacks():
    """update_emma_data must invoke all subscribed callbacks."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    fired = []
    emma.subscribe_callback("cb1", lambda: fired.append("cb1"))
    emma.subscribe_callback("cb2", lambda: fired.append("cb2"))
    emma.update_emma_data(_full_raw())
    assert "cb1" in fired
    assert "cb2" in fired


def test_update_emma_data_no_callbacks_no_error():
    """update_emma_data with zero callbacks must not raise."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    emma.update_emma_data(_full_raw())  # should not raise


def test_update_emma_data_value_reflects_new_data():
    """After update, value property reflects the new raw_result."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    new_raw = _full_raw(info_en="200 W", subtitle_en="Grid Supply")
    emma.update_emma_data(new_raw)
    assert emma.value == -200.0


def test_update_emma_data_sequential():
    """Multiple updates → last one wins."""
    emma = SHCEmma(api=None, shc_info=_shc_info_mock())
    emma.update_emma_data(_full_raw(info_en="100 W", subtitle_en="Local Consumption"))
    emma.update_emma_data(_full_raw(info_en="400 W", subtitle_en="Grid Supply"))
    assert emma.value == -400.0


# --- lines 86-93: summary() ---

def test_summary_prints_id(capsys):
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw())
    emma.summary()
    out = capsys.readouterr().out
    assert "com.bosch.tt.emma.applink" in out


def test_summary_prints_name(capsys):
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw())
    emma.summary()
    out = capsys.readouterr().out
    assert "EMMA" in out


def test_summary_prints_version(capsys):
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw(version="7.7.7"))
    emma.summary()
    out = capsys.readouterr().out
    assert "7.7.7" in out


def test_summary_prints_title(capsys):
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=_full_raw(title_en="Solar"))
    emma.summary()
    out = capsys.readouterr().out
    assert "Solar" in out


def test_summary_prints_subtitle(capsys):
    raw = _full_raw(subtitle_en="Grid Feed-In")
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    emma.summary()
    out = capsys.readouterr().out
    assert "Grid Feed-In" in out


def test_summary_prints_value(capsys):
    raw = _full_raw(info_en="500 W", subtitle_en="Local Consumption")
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(), raw_result=raw)
    emma.summary()
    out = capsys.readouterr().out
    # value = 500.0
    assert "500" in out


# --- SHCEmma construction edge: no shc_info, has raw_result ---

def test_no_shc_info_with_raw_result_serial_empty():
    raw = _full_raw()
    emma = SHCEmma(api=None, shc_info=None, raw_result=raw)
    assert emma.serial == ""


def test_no_shc_info_with_raw_result_root_device_id_empty():
    emma = SHCEmma(api=None, shc_info=None, raw_result=_full_raw())
    assert emma.root_device_id == ""


def test_shc_info_macAddress_used_in_serial():
    emma = SHCEmma(api=None, shc_info=_shc_info_mock(mac="DE:AD:BE:EF:01:02"))
    assert "DE:AD:BE:EF:01:02" in emma.serial


# ===========================================================================
# exceptions.py — cover every class
# ===========================================================================

from boschshcpy.exceptions import (
    JSONRPCError,
    SHCConnectionError,
    SHCAuthenticationError,
    SHCRegistrationError,
    SHCSessionError,
    SHCCertificateError,
)


# --- JSONRPCError ---

def test_jsonrpc_error_code():
    err = JSONRPCError(code=-32600, message="Invalid Request")
    assert err.code == -32600


def test_jsonrpc_error_message_property():
    err = JSONRPCError(code=404, message="Not found")
    assert err.message == "Not found"


def test_jsonrpc_error_str():
    err = JSONRPCError(code=500, message="Server error")
    assert str(err) == "JSONRPCError (code: 500, message: Server error)"


def test_jsonrpc_error_is_exception():
    err = JSONRPCError(code=0, message="x")
    assert isinstance(err, Exception)


def test_jsonrpc_error_raise_and_catch():
    with pytest.raises(JSONRPCError) as exc_info:
        raise JSONRPCError(code=-1, message="boom")
    assert exc_info.value.code == -1
    assert exc_info.value.message == "boom"


# --- SHCException ---

def test_shcexception_message_property():
    exc = SHCException("something broke")
    assert exc.message == "something broke"


def test_shcexception_str():
    exc = SHCException("oops")
    assert str(exc) == "SHC Error (message: oops)"


def test_shcexception_is_exception():
    assert isinstance(SHCException("x"), Exception)


def test_shcexception_raise_and_catch():
    with pytest.raises(SHCException) as exc_info:
        raise SHCException("test error")
    assert exc_info.value.message == "test error"


# --- SHCConnectionError ---

def test_shcconnectionerror_is_exception():
    err = SHCConnectionError("no connection")
    assert isinstance(err, Exception)


def test_shcconnectionerror_raise_and_catch():
    with pytest.raises(SHCConnectionError):
        raise SHCConnectionError("no connection")


def test_shcconnectionerror_str_contains_arg():
    err = SHCConnectionError("offline")
    assert "offline" in str(err)


# --- SHCAuthenticationError ---

def test_shcauthenticationerror_is_exception():
    err = SHCAuthenticationError("bad creds")
    assert isinstance(err, Exception)


def test_shcauthenticationerror_raise_and_catch():
    with pytest.raises(SHCAuthenticationError):
        raise SHCAuthenticationError("unauthorized")


def test_shcauthenticationerror_str_contains_arg():
    err = SHCAuthenticationError("unauthorized")
    assert "unauthorized" in str(err)


# --- SHCRegistrationError (subclass of SHCException) ---

def test_shcregistrationerror_message():
    err = SHCRegistrationError("registration failed")
    assert err.message == "registration failed"


def test_shcregistrationerror_str():
    err = SHCRegistrationError("reg error")
    assert str(err) == "SHC Error (message: reg error)"


def test_shcregistrationerror_is_shcexception():
    err = SHCRegistrationError("x")
    assert isinstance(err, SHCException)


def test_shcregistrationerror_raise_and_catch_as_shcexception():
    with pytest.raises(SHCException):
        raise SHCRegistrationError("catch me as parent")


def test_shcregistrationerror_raise_and_catch_directly():
    with pytest.raises(SHCRegistrationError) as exc_info:
        raise SHCRegistrationError("direct")
    assert exc_info.value.message == "direct"


# --- SHCSessionError (subclass of SHCException) ---

def test_shcsessionerror_message():
    err = SHCSessionError("session lost")
    assert err.message == "session lost"


def test_shcsessionerror_str():
    err = SHCSessionError("sess err")
    assert str(err) == "SHC Error (message: sess err)"


def test_shcsessionerror_is_shcexception():
    err = SHCSessionError("x")
    assert isinstance(err, SHCException)


def test_shcsessionerror_raise_and_catch_as_shcexception():
    with pytest.raises(SHCException):
        raise SHCSessionError("catch me as parent")


def test_shcsessionerror_raise_and_catch_directly():
    with pytest.raises(SHCSessionError) as exc_info:
        raise SHCSessionError("direct")
    assert exc_info.value.message == "direct"


# --- SHCCertificateError (subclass of SHCException) ---

def test_shccertificateerror_message():
    err = SHCCertificateError("cert expired")
    assert err.message == "cert expired"


def test_shccertificateerror_str():
    err = SHCCertificateError("cert err")
    assert str(err) == "SHC Error (message: cert err)"


def test_shccertificateerror_is_shcexception():
    err = SHCCertificateError("x")
    assert isinstance(err, SHCException)


def test_shccertificateerror_raise_and_catch_as_shcexception():
    with pytest.raises(SHCException):
        raise SHCCertificateError("catch me as parent")


def test_shccertificateerror_raise_and_catch_directly():
    with pytest.raises(SHCCertificateError) as exc_info:
        raise SHCCertificateError("direct")
    assert exc_info.value.message == "direct"


# ===========================================================================
# generate_cert.py — cover generate_certificate()
# ===========================================================================

from boschshcpy.generate_cert import generate_certificate


def test_generate_certificate_returns_two_bytes_objects():
    cert_pem, key_pem = generate_certificate("test-client", "TestOrg")
    assert isinstance(cert_pem, bytes)
    assert isinstance(key_pem, bytes)


def test_generate_certificate_cert_pem_header():
    cert_pem, _ = generate_certificate("test-client", "TestOrg")
    assert cert_pem.startswith(b"-----BEGIN CERTIFICATE-----")


def test_generate_certificate_key_pem_header():
    _, key_pem = generate_certificate("test-client", "TestOrg")
    # TraditionalOpenSSL RSA key → RSA PRIVATE KEY header
    assert b"PRIVATE KEY" in key_pem


def test_generate_certificate_pem_parseable():
    """The returned cert must be parseable by the cryptography library."""
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    cert_pem, _ = generate_certificate("parseable-client", "ParseOrg")
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    assert cert.serial_number == 1000


def test_generate_certificate_common_name():
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.x509.oid import NameOID
    cert_pem, _ = generate_certificate("my-client-id", "MyOrg")
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    assert cn == "my-client-id"


def test_generate_certificate_organization_name():
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.x509.oid import NameOID
    cert_pem, _ = generate_certificate("client", "BoschSHC")
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    org = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
    assert org == "BoschSHC"


def test_generate_certificate_issuer_equals_subject():
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    cert_pem, _ = generate_certificate("client", "MyOrg")
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    assert cert.issuer == cert.subject


def test_generate_certificate_serial_number():
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    cert_pem, _ = generate_certificate("client", "MyOrg")
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    assert cert.serial_number == 1000


def test_generate_certificate_validity_roughly_10_years():
    """not_valid_after must be ~10 years in the future (>3000 days)."""
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from datetime import datetime, timezone
    cert_pem, _ = generate_certificate("client", "MyOrg")
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    # support both old (<42) naive and new (>=42) aware not_valid_after
    not_after = cert.not_valid_after_utc if hasattr(cert, "not_valid_after_utc") else cert.not_valid_after.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta_days = (not_after - now).days
    assert delta_days > 3000


def test_generate_certificate_basic_constraints_ca():
    """The cert must have the BasicConstraints extension with ca=True."""
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    cert_pem, _ = generate_certificate("client", "MyOrg")
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    bc = cert.extensions.get_extension_for_class(x509.BasicConstraints)
    assert bc.value.ca is True


def test_generate_certificate_different_client_ids_produce_different_certs():
    """Two calls with different client_id values must differ."""
    pem1, _ = generate_certificate("client-A", "Org")
    pem2, _ = generate_certificate("client-B", "Org")
    assert pem1 != pem2


def test_generate_certificate_key_not_same_as_cert():
    cert_pem, key_pem = generate_certificate("client", "Org")
    assert cert_pem != key_pem


def test_generate_certificate_key_parseable():
    """The returned private key must be parseable."""
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.backends import default_backend
    _, key_pem = generate_certificate("client", "Org")
    key = load_pem_private_key(key_pem, password=None, backend=default_backend())
    assert key.key_size == 2048
