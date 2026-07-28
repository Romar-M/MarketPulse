"""Тесты шифрования."""
from __future__ import annotations

import base64
import os
from unittest.mock import patch

import pytest

from src.encryption import encrypt_data, decrypt_data, get_or_create_key


class TestEncryption:
    """Набор тестов для шифрования."""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Зашифрованные данные расшифровываются обратно."""
        original = "secret_data_123"
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self) -> None:
        """Один и тот же текст даёт разный шифротекст (из-за соли)."""
        data = "test"
        e1 = encrypt_data(data)
        e2 = encrypt_data(data)
        assert e1 != e2

    def test_get_or_create_key_returns_bytes(self) -> None:
        """get_or_create_key возвращает ключ типа bytes."""
        key = get_or_create_key()
        assert isinstance(key, bytes)

    @patch.dict(os.environ, {"ENCRYPTION_KEY": base64.urlsafe_b64encode(b"a" * 32).decode()}, clear=True)
    def test_get_or_create_key_from_env(self) -> None:
        """Ключ из переменной окружения используется."""
        from importlib import reload
        import src.encryption
        reload(src.encryption)
        key = src.encryption.get_or_create_key()
        assert isinstance(key, bytes)

    def test_decrypt_invalid_data(self) -> None:
        """Невалидные данные при расшифровке вызывают ошибку."""
        with pytest.raises(Exception):
            decrypt_data("not-valid-base64!!")
