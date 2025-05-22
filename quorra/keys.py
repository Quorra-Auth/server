from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import json
import base64

# Generate RSA keypair
# TODO: Store somewhere for load-balancing
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
private_key = key
public_key = key.public_key()

def get_jwk():
    numbers = public_key.public_numbers()
    e = base64.urlsafe_b64encode(numbers.e.to_bytes(3, 'big')).decode().rstrip('=')
    n = base64.urlsafe_b64encode(numbers.n.to_bytes(256, 'big')).decode().rstrip('=')
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": "dev-key",
        "n": n,
        "e": e,
    }

def sign_jwt(payload):
    from jose import jwt
    return jwt.encode(
        payload,
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ),
        algorithm="RS256",
        headers={"kid": "dev-key"}
    )
