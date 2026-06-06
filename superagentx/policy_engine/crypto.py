import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature


def verify_signature(public_key_bytes: bytes, payload: str, signature_b64: str) -> bool:
    """
    Validates a cryptographic signature against a string payload using Ed25519.
    """
    try:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        signature_bytes = base64.b64decode(signature_b64)
        public_key.verify(signature_bytes, payload.encode('utf-8'))
        return True
    except (InvalidSignature, Exception):
        return False