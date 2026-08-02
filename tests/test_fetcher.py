"""Тесты загрузчика данных."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import json

from src.fetcher import DataFetcher


@pytest.mark.asyncio
async def test_process_message_normal() -> None:
    """Обычное сообщение с закрытой свечой."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt", "btcusdt"], on_candle=callback)
    msg = json.dumps({
        "stream": "ethusdt@kline_1m",
        "data": {
            "k": {
                "x": True,
                "c": "50000.00",
                "T": 1000000000000,
            }
        }
    })
    await fetcher._process_message(msg)
    callback.assert_awaited_once_with("ETHUSDT", 50000.0, 1000000000.0)


@pytest.mark.asyncio
async def test_process_message_not_closed() -> None:
    """Незакрытая свеча игнорируется."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt"], on_candle=callback)
    msg = json.dumps({
        "stream": "ethusdt@kline_1m",
        "data": {
            "k": {
                "x": False,
                "c": "50000.00",
                "T": 1000000000000,
            }
        }
    })
    await fetcher._process_message(msg)
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_empty() -> None:
    """Пустое сообщение игнорируется."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt"], on_candle=callback)
    await fetcher._process_message("")
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_malformed() -> None:
    """Битое сообщение не вызывает ошибок."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt"], on_candle=callback)
    await fetcher._process_message("not json")
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_missing_keys() -> None:
    """Сообщение без ключей игнорируется."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt"], on_candle=callback)
    msg = json.dumps({"stream": "ethusdt@kline_1m", "data": {}})
    await fetcher._process_message(msg)
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_close() -> None:
    """Закрытие не вызывает ошибок."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt"], on_candle=callback)
    await fetcher.close()


@pytest.mark.asyncio
async def test_disconnect() -> None:
    """Отключение не вызывает ошибок."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt"], on_candle=callback)
    await fetcher.disconnect()


@pytest.mark.asyncio
async def test_connect_with_reconnect() -> None:
    """connect пытается переподключиться при ошибке, затем выходит."""
    callback = AsyncMock()
    fetcher = DataFetcher(symbols=["ethusdt"], on_candle=callback)
    fetcher.max_reconnects = 1

    with patch("src.fetcher.websockets.connect", side_effect=Exception("ws error")):
        await fetcher.connect()
        # Достигнут лимит реконнектов — вышли без ошибки
        assert fetcher.reconnect_attempts >= 1
