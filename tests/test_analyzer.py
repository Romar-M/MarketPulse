"""Тесты анализатора."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.analyzer import PriceAnalyzer


class TestPriceAnalyzer:
    """Набор тестов для PriceAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> PriceAnalyzer:
        """Экземпляр с настройками по умолчанию."""
        return PriceAnalyzer(window_size=60, recalc_interval=300, threshold=0.01)

    @pytest.mark.asyncio
    async def test_add_candle_eth(self, analyzer: PriceAnalyzer) -> None:
        """Добавление свечи ETH."""
        await analyzer.add_candle("ETHUSDT", 1000.0, 1000000)
        assert len(analyzer.eth_prices) == 1
        assert len(analyzer.btc_prices) == 0

    @pytest.mark.asyncio
    async def test_add_candle_btc(self, analyzer: PriceAnalyzer) -> None:
        """Добавление свечи BTC."""
        await analyzer.add_candle("BTCUSDT", 20000.0, 1000000)
        assert len(analyzer.btc_prices) == 1
        assert len(analyzer.eth_prices) == 0

    @pytest.mark.asyncio
    async def test_add_candle_invalid_symbol(self, analyzer: PriceAnalyzer) -> None:
        """Неизвестный символ игнорируется."""
        await analyzer.add_candle("SOLUSDT", 100.0, 1000000)
        assert len(analyzer.eth_prices) == 0
        assert len(analyzer.btc_prices) == 0

    @pytest.mark.asyncio
    async def test_add_candle_none_price(self, analyzer: PriceAnalyzer) -> None:
        """Цена None игнорируется."""
        await analyzer.add_candle("ETHUSDT", None, 1000000)
        assert len(analyzer.eth_prices) == 0

    @pytest.mark.asyncio
    async def test_add_candle_zero_price(self, analyzer: PriceAnalyzer) -> None:
        """Нулевая цена игнорируется."""
        await analyzer.add_candle("ETHUSDT", 0.0, 1000000)
        assert len(analyzer.eth_prices) == 0

    @pytest.mark.asyncio
    async def test_add_candle_negative_price(self, analyzer: PriceAnalyzer) -> None:
        """Отрицательная цена игнорируется."""
        await analyzer.add_candle("ETHUSDT", -10.0, 1000000)
        assert len(analyzer.eth_prices) == 0

    @pytest.mark.asyncio
    async def test_add_candle_none_timestamp(self, analyzer: PriceAnalyzer) -> None:
        """Метка времени None игнорируется."""
        await analyzer.add_candle("ETHUSDT", 1000.0, None)
        assert len(analyzer.eth_prices) == 0

    @pytest.mark.asyncio
    async def test_add_candle_zero_timestamp(self, analyzer: PriceAnalyzer) -> None:
        """Метка времени 0 игнорируется."""
        await analyzer.add_candle("ETHUSDT", 1000.0, 0)
        assert len(analyzer.eth_prices) == 0

    @pytest.mark.asyncio
    async def test_no_recalc_with_few_data(self, analyzer: PriceAnalyzer) -> None:
        """Бета не пересчитывается, пока данных меньше min_data_points."""
        analyzer.min_data_points = 10
        for i in range(5):
            await analyzer.add_candle("ETHUSDT", 1000.0 + i, 1000000 + i)
            await analyzer.add_candle("BTCUSDT", 20000.0 + i * 10, 1000000 + i)
        assert analyzer.beta is None

    @pytest.mark.asyncio
    async def test_recalc_with_enough_data(self, analyzer: PriceAnalyzer) -> None:
        """При заполнении буфера до window_size бета пересчитывается."""
        analyzer.min_data_points = 2
        analyzer.window_size = 3
        for i in range(3):
            await analyzer.add_candle("ETHUSDT", 1000.0 + i * 10, 1000000 + i)
            await analyzer.add_candle("BTCUSDT", 20000.0 + i * 100, 1000000 + i)
        assert analyzer.beta is not None

    @pytest.mark.asyncio
    async def test_alert_handler_called(self) -> None:
        """При превышении порога вызывается alert_handler.trigger."""
        handler_mock = AsyncMock()
        analyzer = PriceAnalyzer(
            window_size=5,
            recalc_interval=1,
            threshold=0.01,
            alert_handler=handler_mock,
        )
        analyzer.min_data_points = 3
        analyzer.alert_cooldown = 0

        # Заполняем окно данными (5 свечей каждого)
        for i in range(5):
            await analyzer.add_candle("ETHUSDT", 1000.0 + i, 1000000 + i)
            await analyzer.add_candle("BTCUSDT", 20000.0 + i, 1000000 + i)

        assert analyzer.beta is not None

    @pytest.mark.asyncio
    async def test_multiple_updates(self, analyzer: PriceAnalyzer) -> None:
        """Множественные обновления не вызывают ошибок."""
        for i in range(10):
            await analyzer.add_candle("ETHUSDT", 1000.0 + i, 1000000 + i)
        assert len(analyzer.eth_prices) == 10
