from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_certificate(client_id, orgname) -> x509.Certificate:
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, client_id),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, orgname),
        ]
    )

    utc_now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .serial_number(1000)
        .issuer_name(name)
        .subject_name(name)
        .public_key(key.public_key())
        .not_valid_before(utc_now)
        .not_valid_after(utc_now + timedelta(days=10 * 365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), True)
        .sign(key, hashes.SHA256(), default_backend())
    )
    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)

    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return cert_pem, key_pem
