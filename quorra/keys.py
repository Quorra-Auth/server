from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from jose import jwt
import json
import base64

from .database import vk


def prep_key():
    if vk.exists("oidc-rsa-key"):
        pem = vk.get("oidc-rsa-key").encode()
        key = serialization.load_pem_private_key(pem, password=None)
    else:
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        pem = key.private_bytes(encoding=serialization.Encoding.PEM,
              format=serialization.PrivateFormat.PKCS8,
              encryption_algorithm=serialization.NoEncryption()).decode("utf-8")
        vk.set("oidc-rsa-key", pem)
    return key


def int_to_base64url(n: int) -> str:
    """Encodes an integer as base64url (without padding)."""
    length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(length, "big")).decode("utf-8").rstrip("=")


def get_jwk(kid: str = "main-key") -> dict:
    """Converts an RSA public key to a JWK."""
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


def sign_jwt(payload):
    private_key = prep_key()
    return jwt.encode(
        payload,
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ),
        algorithm="RS256",
        headers={"kid": "main-key"}
    )
