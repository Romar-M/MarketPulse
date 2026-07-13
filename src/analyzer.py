import logging
from collections import deque
from datetime import datetime, timezone
import numpy as np
import math


last_recalc_time


class PriceAnalyzer:
    """
    Хранит последние 60 минут цен закрытия ETH и BTC.
    Периодически (каждые 5 мин) вычисляет β и проверяет порог изменения собственной цены ETH.
    """

    def __init__(self, window_size: int = 60, recalc_interval: int = 300,
                 threshold: float = 0.01, alert_handler=None):
        self.window_size = window_size
        self.min_data_points = 10
        self.recalc_interval = recalc_interval  # в секундах
        self.threshold = threshold
        self.alert_handler = alert_handler

        self.eth_prices = deque(maxlen=window_size)
        self.btc_prices = deque(maxlen=window_size)
        self.last_recalc_time: datetime | None = None
        self.min_data_points = 10
        self.last_alert_time = 0
        self.alert_cooldown = 300
        self.beta: float | None = None

    async def add_candle(self, symbol: str, close_price: float, timestamp: float):
        """Добавляет новую свечу в соответствующее окно."""
        # Валидация входных данных
        if close_price is None or close_price <= 0:
            logger.warning(f"Некорректная цена {symbol}: {close_price}")
            return

        if timestamp is None or timestamp <= 0:
            logger.warning(f"Некорректный timestamp {symbol}: {timestamp}")
            return

        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        if symbol.upper() == "ETHUSDT":
            self.eth_prices.append(close_price)
        elif symbol.upper() == "BTCUSDT":
            self.btc_prices.append(close_price)
        else:
            logger.warning(f"Неизвестный символ: {symbol}")
            return

        # Проверка минимального количества данных
        if len(self.eth_prices) < self.min_data_points or len(self.btc_prices) < self.min_data_points:
            logger.debug(
                f"ℹБуфер заполняется: ETH={len(self.eth_prices)}/{self.min_data_points}, BTC={len(self.btc_prices)}/{self.min_data_points}")
            return

        # Пересчёт β, если прошло достаточно времени и оба окна заполнены
        if self._should_recalc(dt):
            self._recalc_beta()
            self.last_recalc_time = dt

        # Проверка изменения за последние 60 минут (с защитой от частых алертов)
        await self._check_alert()

    def _should_recalc(self, current_time: datetime) -> bool:
        if self.last_recalc_time is None:
            return len(self.eth_prices) == self.window_size and len(self.btc_prices) == self.window_size
        elapsed = (current_time - self.last_recalc_time).total_seconds()
        return elapsed >= self.recalc_interval

    def _recalc_beta(self):
        """Пересчёт β с защитой от ошибок."""
        try:
            # Проверка длины массивов
            if len(self.eth_prices) < 2 or len(self.btc_prices) < 2:
                logger.warning("Недостаточно данных для расчёта β")
                return

            # Берём одинаковое количество данных
            n = min(len(self.eth_prices), len(self.btc_prices))
            eth = self.eth_prices[-n:]
            btc = self.btc_prices[-n:]

            # Расчёт доходностей
            eth_returns = [(eth[i] - eth[i - 1]) / eth[i - 1] for i in range(1, n)]
            btc_returns = [(btc[i] - btc[i - 1]) / btc[i - 1] for i in range(1, n)]

            # Защита от пустых массивов
            if not eth_returns or not btc_returns:
                logger.warning("Нулевые доходности")
                return

            # Расчёт ковариации и дисперсии
            mean_eth = sum(eth_returns) / len(eth_returns)
            mean_btc = sum(btc_returns) / len(btc_returns)

            cov = sum((e - mean_eth) * (b - mean_btc) for e, b in zip(eth_returns, btc_returns)) / len(eth_returns)
            var = sum((b - mean_btc)
            2
            for b in btc_returns) / len(btc_returns)

            # Защита от деления на ноль
            if var == 0:
                logger.warning("Дисперсия BTC = 0, β не определён")
                return

            beta = cov / var

            # Проверка на бесконечность/NaN
            if not math.isfinite(beta):
                logger.warning(f"β = {beta} (не число)")
                return

            self.beta = beta
            logger.info(f"β = {beta:.4f} (на {len(eth_returns)} точках)")

        except Exception as e:
            logger.error(f"Ошибка расчёта β: {e}")

    async def _check_alert(self):
        """Проверка с защитой от частых алертов."""
        import time
        now = time.time()

        # Защита от частых алертов
        if now - self.last_alert_time < self.alert_cooldown:
            return

        if self.beta is None:
            return

        # Здесь твоя логика проверки
        # Например:
        if abs(self.beta) > 0.5:  # порог
            self.last_alert_time = now
            logger.info(f"Алерт: β = {self.beta:.4f}")
            # Здесь можно вызвать alerter.trigger()

        delta_eth = eth_now - eth_60m_ago
        delta_btc = btc_now - btc_60m_ago
        clean_change = delta_eth - self.beta * delta_btc
        pct_change = clean_change / eth_60m_ago
        if abs(pct_change) >= self.threshold and self.alert_handler:
            self.alert_handler.trigger(pct_change, eth_now, btc_now)