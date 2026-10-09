from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from jose import jwt
import base64
from functools import lru_cache

from .database import vk


@lru_cache(maxsize=1)
def prep_key():
    """Loads the signing key once per process. Parsing a 4096-bit key on every request is very expensive."""
    pem = vk.get("oidc-rsa-key")
    if pem is None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        new_pem = key.private_bytes(encoding=serialization.Encoding.PEM,
              format=serialization.PrivateFormat.PKCS8,
              encryption_algorithm=serialization.NoEncryption()).decode("utf-8")
        # NX: if another worker/pod generated a key first, theirs wins and we use it
        vk.set("oidc-rsa-key", new_pem, nx=True)
        pem = vk.get("oidc-rsa-key")
    return serialization.load_pem_private_key(pem.encode(), password=None)


@lru_cache(maxsize=1)
def _private_pem() -> bytes:
    return prep_key().private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )


def int_to_base64url(n: int) -> str:
    """Encodes an integer as base64url (without padding)."""
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).decode("utf-8").rstrip("=")


@lru_cache(maxsize=None)
def _jwk(kid: str) -> dict:
    private_key = prep_key()
    public_key = private_key.public_key()
    numbers = public_key.public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": int_to_base64url(numbers.n),
        "e": int_to_base64url(numbers.e),
    }
    return jwk


def get_jwk(kid: str = "main-key") -> dict:
    """Converts an RSA public key to a JWK."""
    return dict(_jwk(kid))


def sign_jwt(payload):
    return jwt.encode(
        payload,
        _private_pem(),
        algorithm="RS256",
        headers={"kid": "main-key"}
    )
