"""
Fernet decryption compatible with Django's EncryptedCharField / EncryptedTextField.

Derives the same Fernet key from SECRET_KEY as apps/core/crypto.py.
"""

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet

from .config import get_settings


@lru_cache
def _get_fernet_key() -> bytes:
    """Derive Fernet key from SECRET_KEY (same as Django's apps/core/crypto.py)."""
    secret = get_settings().secret_key
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_value(value: str | None) -> str | None:
    """
    Encrypt a string value with Fernet.
    Compatible with Django's EncryptedCharField.
    """
    if not value:
        return value

    fernet = Fernet(_get_fernet_key())
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(encrypted_value: str | None) -> str | None:
    """
    Decrypt a Fernet-encrypted value.
    Returns original string on failure (may be an old unencrypted value).
    """
    if not encrypted_value:
        return encrypted_value

    try:
        fernet = Fernet(_get_fernet_key())
        return fernet.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
    except Exception:
        # If decryption fails, return as-is (might be unencrypted)
        return encrypted_value
