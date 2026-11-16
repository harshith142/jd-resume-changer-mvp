import base64
import hashlib
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from uuid import UUID


def derive_master_key(app_secret: str, user_id: UUID) -> bytes:
    """
    Derive a per-user encryption key from the app secret and user ID.
    Uses HKDF-SHA256 for key derivation.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits for AES-256
        salt=user_id.bytes,
        info=b"jd-resume-changer-api-key-encryption",
    )
    return hkdf.derive(app_secret.encode())


def encrypt_api_key(key: str, user_id: UUID, app_secret: str) -> tuple[bytes, bytes]:
    """
    Encrypt an API key using AES-256-GCM.
    Returns (encrypted_key, nonce).
    """
    master_key = derive_master_key(app_secret, user_id)
    nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
    cipher = AESGCM(master_key)
    encrypted = cipher.encrypt(nonce, key.encode(), None)
    return encrypted, nonce


def decrypt_api_key(encrypted: bytes, nonce: bytes, user_id: UUID, app_secret: str) -> str:
    """
    Decrypt an API key using AES-256-GCM.
    Returns the decrypted key string.
    """
    master_key = derive_master_key(app_secret, user_id)
    cipher = AESGCM(master_key)
    decrypted = cipher.decrypt(nonce, encrypted, None)
    return decrypted.decode()


def generate_key_fingerprint(key: str) -> str:
    """
    Generate a short fingerprint of the API key for display purposes.
    Shows first 4 and last 4 characters with hash in middle.
    """
    if len(key) <= 8:
        return "****"
    prefix = key[:4]
    suffix = key[-4:]
    hash_middle = hashlib.sha256(key.encode()).hexdigest()[:8]
    return f"{prefix}...{hash_middle}...{suffix}"