"""
Fernet-based encryption for database credentials.

Uses ENCRYPTION_KEY from environment. Credentials are serialized
to JSON, encrypted, and stored as a base64 string.
"""

import json
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    try:
        return Fernet(settings.ENCRYPTION_KEY.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "ENCRYPTION_KEY is not a valid Fernet key. Generate one with: "
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        ) from exc


def encryption_key_is_valid() -> bool:
    try:
        _get_fernet()
        return True
    except RuntimeError:
        return False


def encrypt_json(data: dict) -> str:
    """Encrypt a dict to a Fernet-encrypted string."""
    raw = json.dumps(data).encode()
    return _get_fernet().encrypt(raw).decode()


def decrypt_json(encrypted: str) -> dict:
    """Decrypt a Fernet-encrypted string back to a dict."""
    raw = _get_fernet().decrypt(encrypted.encode())
    return json.loads(raw)
