"""Utility functions for configuration generation."""

import secrets
import namegenerator
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from pydantic import BaseModel, Field


def generate_django_secret_key() -> str:
    """Generate a 50-character Django SECRET_KEY."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return "".join(secrets.choice(chars) for _ in range(50))


def generate_alpha_numeric_string(length: int = 40) -> str:
    """Generate a random alphanumeric string of a given length."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_name() -> str:
    """Generate a random name using the namegenerator library."""
    return namegenerator.gen()


class KeyPair(BaseModel):
    """Asymmetric key pair for signing/verifying tokens."""

    key_type: str = Field(
        default="RSA256",
        description="Type of the key pair (e.g. RSA256, Ed25519)",
    )
    public_key: str = Field(..., description="Public key")
    private_key: str = Field(..., description="Private key")


def build_key_pair() -> KeyPair:
    """Generate a new RSA key pair (PEM private key, OpenSSH public key)."""
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=crypto_default_backend(),
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    ).decode()

    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode()
    )

    return KeyPair(public_key=public_key, private_key=private_key)


def build_ed25519_key_pair() -> KeyPair:
    """Generate a new Ed25519 key pair (PEM private + public keys).

    Used for the Rekuest provenance (attestation) signing key.
    """
    key = ed25519.Ed25519PrivateKey.generate()

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption(),
    ).decode()

    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )

    return KeyPair(key_type="Ed25519", public_key=public_key, private_key=private_key)
