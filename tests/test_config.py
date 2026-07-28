"""Тесты конфигурации."""
from __future__ import annotations

from unittest.mock import patch

from src.config import settings


class TestConfig:
    """Набор тестов для конфигурации."""

    def test_threshold_default(self) -> None:
        """Порог по умолчанию 0.01."""
        assert settings.threshold == 0.01

    def test_window_minutes(self) -> None:
        """Окно положительное."""
        assert settings.window_minutes > 0

    def test_database_url(self) -> None:
        """URL базы данных задан."""
        assert settings.database_url is not None
        assert "sqlite" in settings.database_url

    @patch.dict("os.environ", {"TELEGRAM_TOKEN": "", "TELEGRAM_CHAT_ID": ""}, clear=True)
    def test_telegram_token_default(self) -> None:
        """Токен Telegram пустой по умолчанию."""
        # Перезагружаем settings с новым окружением
        from importlib import reload
        import src.config
        reload(src.config)
        from src.config import settings
        assert settings.telegram_token == ""
