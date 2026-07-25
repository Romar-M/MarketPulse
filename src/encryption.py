"""Шифрование чувствительных данных (Fernet)."""

from cryptography.fernet import Fernet
import os

KEY_ENV_VAR = "ENCRYPTION_KEY"


def get_or_create_key() -> bytes:
    key = os.getenv(KEY_ENV_VAR)
    if key:
        return key.encode()
    new_key = Fernet.generate_key()
    os.environ[KEY_ENV_VAR] = new_key.decode()
    return new_key


_cipher = Fernet(get_or_create_key())


def encrypt_data(data: str) -> str:
    return _cipher.encrypt(data.encode()).decode()


def decrypt_data(token: str) -> str:
    return _cipher.decrypt(token.encode()).decode()
