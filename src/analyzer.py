"""Анализатор цен: хранение буфера, расчёт бета и проверка расхождения ETH vs BTC."""

import logging
import time
from collections import deque
from datetime import datetime, timezone
import math

logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """Хранит окно цен закрытия ETH и BTC, считает бета и генерирует алерты.

    Буфер наполняется через add_candle, бета пересчитывается раз в
    recalc_interval секунд, а check_alert (вызываемый извне по расписанию)
    проверяет, не отклонилась ли цена ETH от предсказанной по бета более
    чем на threshold.
    """

    def __init__(self, window_size=60, recalc_interval=300, threshold=0.01,
                 alert_handler=None, alert_check_interval=30):
        """Инициализирует анализатор.

        Args:
            window_size: размер окна (минут) для хранения цен.
            recalc_interval: как часто пересчитывать бета, в секундах.
            threshold: порог расхождения в долях (0.01 = 1%).
            alert_handler: объект с методом trigger(pct_change, eth_price, btc_price).
            alert_check_interval: как часто вызывается check_alert, в секундах.
        """
        self.window_size = window_size
        self.min_data_points = min(30, window_size)
        self.recalc_interval = recalc_interval
        self.threshold = threshold
        self.alert_handler = alert_handler
        self.alert_check_interval = alert_check_interval
        self.eth_prices = deque(maxlen=window_size)
        self.btc_prices = deque(maxlen=window_size)
        self.last_recalc_time = None
        self.last_alert_time = 0.0
        self.alert_cooldown = 300
        self.beta = None
        self.session_maker = None

    async def add_candle(self, symbol, close_price, timestamp):
        """Добавляет свечу в буфер и сохраняет её в БД.

        Args:
            symbol: тикер (ETHUSDT или BTCUSDT).
            close_price: цена закрытия свечи.
            timestamp: unix-время закрытия свечи в секундах.
        """
        if close_price is None or close_price <= 0:
            return
        if timestamp is None or timestamp <= 0:
            return
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        symbol_upper = symbol.upper()

        if symbol_upper == "ETHUSDT":
            self.eth_prices.append(close_price)
        elif symbol_upper == "BTCUSDT":
            self.btc_prices.append(close_price)
        else:
            return

        # Сохраняем свечу в БД
        if self.session_maker:
            try:
                from .database import Candle
                async with self.session_maker() as session:
                    candle = Candle(
                        symbol=symbol_upper,
                        timestamp=dt,
                        open=close_price,
                        high=close_price,
                        low=close_price,
                        close=close_price,
                        volume=0.0,
                    )
                    session.add(candle)
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to save candle to DB: {e}")

        if len(self.eth_prices) < self.min_data_points or len(self.btc_prices) < self.min_data_points:
            return
        if self._should_recalc(dt):
            self._recalc_beta()
            self.last_recalc_time = dt

    def _should_recalc(self, current_time):
        """Возвращает True, если пора пересчитать бета."""
        if self.last_recalc_time is None:
            return len(self.eth_prices) == self.window_size and len(self.btc_prices) == self.window_size
        elapsed = (current_time - self.last_recalc_time).total_seconds()
        return elapsed >= self.recalc_interval

    def _recalc_beta(self):
        """Пересчитывает бета = Cov(R_eth, R_btc) / Var(R_btc) по доходностям.

        Защищается от недостатка данных, деления на ноль и нечисловых значений.
        """
        try:
            if len(self.eth_prices) < 2 or len(self.btc_prices) < 2:
                return
            n = min(len(self.eth_prices), len(self.btc_prices))
            eth = list(self.eth_prices)[-n:]
            btc = list(self.btc_prices)[-n:]
            eth_returns = [(eth[i] - eth[i-1]) / eth[i-1] for i in range(1, n)]
            btc_returns = [(btc[i] - btc[i-1]) / btc[i-1] for i in range(1, n)]
            if not eth_returns or not btc_returns:
                return
            mean_eth = sum(eth_returns) / len(eth_returns)
            mean_btc = sum(btc_returns) / len(btc_returns)
            cov = sum((e - mean_eth) * (b - mean_btc) for e, b in zip(eth_returns, btc_returns)) / len(eth_returns)
            var = sum((b - mean_btc) ** 2 for b in btc_returns) / len(btc_returns)
            if var == 0:
                return
            beta = cov / var
            if not math.isfinite(beta):
                return
            self.beta = beta
        except Exception as e:
            logger.error(f"Beta calc error: {e}")

    async def check_alert(self):
        """Периодическая проверка: сработало ли расхождение ETH vs BTC.

        Считает «чистое» изменение ETH (за вычетом движения по бета) за окно
        и, если оно превышает threshold, вызывает alert_handler.trigger().
        Не чаще одного раза за alert_cooldown секунд.
        """
        now = time.time()
        if now - self.last_alert_time < self.alert_cooldown:
            return
        if self.beta is None:
            return
        if len(self.eth_prices) < self.min_data_points or len(self.btc_prices) < self.min_data_points:
            logger.debug(
                f"Буфер не прогрет: eth={len(self.eth_prices)}/{self.min_data_points}, "
                f"btc={len(self.btc_prices)}/{self.min_data_points}"
            )
            return
        eth_now = self.eth_prices[-1]
        eth_60m_ago = self.eth_prices[0]
        btc_now = self.btc_prices[-1]
        btc_60m_ago = self.btc_prices[0]
        delta_eth = eth_now - eth_60m_ago
        delta_btc = btc_now - btc_60m_ago
        clean_change = delta_eth - self.beta * delta_btc
        pct_change = clean_change / eth_60m_ago
        if abs(pct_change) >= self.threshold and self.alert_handler:
            self.last_alert_time = now
            await self.alert_handler.trigger(pct_change, eth_now, btc_now)


analyzer_instance = PriceAnalyzer()

