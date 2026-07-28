"""Тесты Telegram-бота."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot import TelegramBot


class TestTelegramBot:
    """Набор тестов для TelegramBot."""

    @pytest.fixture
    def bot(self) -> TelegramBot:
        """Бот с тестовым токеном."""
        return TelegramBot(token="test:token", chat_id="12345")

    @pytest.mark.asyncio
    async def test_send_message_success(self, bot: TelegramBot) -> None:
        """Успешная отправка."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value.raise_for_status.return_value = None
            result = await bot.send_message("Hello")
            assert result is True

    @pytest.mark.asyncio
    async def test_send_message_no_chat_id(self, bot: TelegramBot) -> None:
        """Без chat_id — False."""
        bot.chat_id = None
        result = await bot.send_message("Hello")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_message_http_error(self, bot: TelegramBot) -> None:
        """Ошибка HTTP — False."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("http error")
            result = await bot.send_message("Hello")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_updates(self, bot: TelegramBot) -> None:
        """get_updates возвращает список."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": [{"update_id": 1}]}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            updates = await bot.get_updates()
            assert len(updates) == 1
            assert updates[0]["update_id"] == 1

    @pytest.mark.asyncio
    async def test_get_updates_error(self, bot: TelegramBot) -> None:
        """Ошибка HTTP — пустой список."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("error")
            updates = await bot.get_updates()
            assert updates == []

    def test_extract_chat_id_found(self, bot: TelegramBot) -> None:
        """Извлечение chat_id из сообщения."""
        updates = [{"message": {"chat": {"id": 67890}}}]
        chat_id = bot.extract_chat_id(updates)
        assert chat_id == "67890"

    def test_extract_chat_id_not_found(self, bot: TelegramBot) -> None:
        """Нет сообщений — None."""
        chat_id = bot.extract_chat_id([])
        assert chat_id is None
