from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet(scope: str) -> Fernet:
    material = f"{get_settings().enc_key()}:{scope}".encode("utf-8")
    digest = hashlib.sha256(material).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def house_scope(household_id: int) -> str:
    return f"house:{household_id}"


def private_scope(household_id: int, person_id: int) -> str:
    return f"private:{household_id}:{person_id}"


def encrypt(scope: str, plaintext: str) -> str:
    token = _fernet(scope).encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt(scope: str, ciphertext: str) -> str:
    try:
        return _fernet(scope).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""
