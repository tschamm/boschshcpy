"""Helper functions for Bosch SHC client certificate handling."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple, cast

from .exceptions import SHCCertificateError

try:
    from cryptography import x509
except Exception as exc:  # pragma: no cover - cryptography should exist in HA
    raise SHCCertificateError("cryptography library not available") from exc


class CertificateInfo(NamedTuple):
    """Parsed certificate info."""

    not_before: datetime
    not_after: datetime
    days_remaining: int


def parse_certificate(cert_path: str) -> CertificateInfo:
    """Parse a PEM certificate and return validity information.

    Raises HomeAssistantError if file missing or invalid.
    """
    path = Path(cert_path)
    if not path.is_file():
        raise SHCCertificateError(f"Certificate file missing: {cert_path}")

    data = path.read_bytes()
    try:
        cert = x509.load_pem_x509_certificate(data)
    except Exception as exc:  # pragma: no cover - defensive
        raise SHCCertificateError(f"Invalid certificate: {cert_path}") from exc

    now = datetime.now(timezone.utc)
    # cryptography >= 42 exposes timezone-aware *_utc properties; older releases
    # only have the (now deprecated) naive not_valid_* properties. Branch on
    # availability with hasattr. Do NOT use
    # getattr(cert, "not_valid_after_utc", cert.not_valid_after_utc): the default
    # expression is evaluated eagerly, so it raises AttributeError /
    # CryptographyDeprecationWarning even when the _utc property is present
    # (root cause of the Python 3.13+ startup crash).
    if hasattr(cert, "not_valid_before_utc"):
        _cert = cast(Any, cert)
        not_before = _cert.not_valid_before_utc
        not_after = _cert.not_valid_after_utc
    else:  # pragma: no cover - exercised only on cryptography < 42
        not_before = cert.not_valid_before.replace(tzinfo=timezone.utc)
        not_after = cert.not_valid_after.replace(tzinfo=timezone.utc)
    days_remaining = int((not_after - now).total_seconds() // 86400)
    return CertificateInfo(not_before, not_after, days_remaining)
