"""Тесты аутентификации."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src.auth import create_access_token, verify_token


class TestAuth:
    """Набор тестов для JWT аутентификации."""

    def test_create_token(self) -> None:
        """Создание токена возвращает строку."""
        token = create_access_token(data={"sub": "admin"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self) -> None:
        """Валидный токен содержит переданные данные."""
        token = create_access_token(data={"sub": "admin", "role": "admin"})
        payload = verify_token(token)
        assert payload.get("sub") == "admin"
        assert payload.get("role") == "admin"

    def test_verify_invalid_token(self) -> None:
        """Невалидный токен возвращает пустой словарь."""
        payload = verify_token("invalid.token.here")
        assert payload == {}

    def test_verify_expired_token(self) -> None:
        """Истёкший токен возвращает пустой словарь."""
        with patch("src.auth.ACCESS_TOKEN_EXPIRE_MINUTES", -1):
            token = create_access_token(data={"sub": "admin"})
            payload = verify_token(token)
            assert payload == {}
