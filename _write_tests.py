"""Тесты обработчика оповещений (асинхронные)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def handler():
    """Экземпляр AlertHandler с пустыми токенами (без отправки)."""
    with patch("src.telegram_bot.TOKEN", ""), patch("src.telegram_bot.CHAT_ID", ""):
        from src.database import AlertHandler
        yield AlertHandler(threshold=0.01, min_interval=300)


@pytest.mark.asyncio
async def test_trigger_below_threshold(handler) -> None:
    """Изменение меньше порога — без оповещения."""
    result = await handler.trigger(0.005, 1000.0, 20000.0)
    assert result is None


@pytest.mark.asyncio
async def test_trigger_above_threshold(handler) -> None:
    """Изменение больше порога — оповещение отправляется."""
    handler.telegram_bot.send_message = AsyncMock()
    result = await handler.trigger(0.02, 1000.0, 20000.0)
    assert result is not None
    assert "ALERT" in result
    handler.telegram_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_cooldown(handler) -> None:
    """Повторное оповещение в течение кулдауна блокируется."""
    handler.telegram_bot.send_message = AsyncMock()
    await handler.trigger(0.02, 1000.0, 20000.0)
    await handler.trigger(0.02, 1010.0, 20100.0)
    assert handler.telegram_bot.send_message.call_count == 1


@pytest.mark.asyncio
async def test_get_stats(handler) -> None:
    """get_stats возвращает строку."""
    stats = handler.get_stats()
    assert isinstance(stats, str)
    assert "Alerts:" in stats


@pytest.mark.asyncio
async def test_trigger_db_error(handler) -> None:
    """Ошибка БД не ломает отправку оповещения."""
    session_maker = MagicMock()
    session_maker.return_value.__aenter__.return_value.add.side_effect = Exception("db error")
    handler.session_maker = session_maker
    handler.telegram_bot.send_message = AsyncMock()

    result = await handler.trigger(0.02, 1000.0, 20000.0)
    assert result is not None
    handler.telegram_bot.send_message.assert_called_once()
