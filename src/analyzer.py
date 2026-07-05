import logging
from collections import deque
from datetime import datetime, timezone
import numpy as np

logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """
    Хранит последние 60 минут цен закрытия ETH и BTC.
    Периодически (каждые 5 мин) вычисляет β и проверяет порог изменения собственной цены ETH.
    """

    def __init__(self, window_size: int = 60, recalc_interval: int = 300,
                 threshold: float = 0.01, alert_handler=None):
        self.window_size = window_size
        self.recalc_interval = recalc_interval  # в секундах
        self.threshold = threshold
        self.alert_handler = alert_handler

        self.eth_prices = deque(maxlen=window_size)
        self.btc_prices = deque(maxlen=window_size)
        self.last_recalc_time: datetime | None = None
        self.beta: float | None = None

    async def add_candle(self, symbol: str, close_price: float, timestamp: float):
        """Добавляет новую свечу в соответствующее окно."""
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        if symbol.upper() == "ETHUSDT":
            self.eth_prices.append(close_price)
        elif symbol.upper() == "BTCUSDT":
            self.btc_prices.append(close_price)
        else:
            return

        # Пересчёт β, если прошло достаточно времени и оба окна заполнены
        if self._should_recalc(dt):
            self._recalc_beta()
            self.last_recalc_time = dt

        # Проверка изменения за последние 60 минут
        await self._check_alert()

    def _should_recalc(self, current_time: datetime) -> bool:
        if self.last_recalc_time is None:
            return len(self.eth_prices) == self.window_size and len(self.btc_prices) == self.window_size
        elapsed = (current_time - self.last_recalc_time).total_seconds()
        return elapsed >= self.recalc_interval

    def _recalc_beta(self):
        if len(self.eth_prices) < self.window_size or len(self.btc_prices) < self.window_size:
            return
        x = np.array(self.btc_prices)
        y = np.array(self.eth_prices)
        # Линейная регрессия: y = α + β*x, возвращает [β, α] для degree=1
        self.beta = np.polyfit(x, y, 1)[0]
        logger.debug(f"Recalculated beta: {self.beta:.4f}")

    async def _check_alert(self):
        if self.beta is None or len(self.eth_prices) < 2:
            return
        # Нужна цена 60 минут назад – первый элемент в deque
        eth_now = self.eth_prices[-1]
        eth_60m_ago = self.eth_prices[0]
        btc_now = self.btc_prices[-1] if self.btc_prices else 0
        btc_60m_ago = self.btc_prices[0] if self.btc_prices else 0
        if eth_60m_ago == 0:
            return

        delta_eth = eth_now - eth_60m_ago
        delta_btc = btc_now - btc_60m_ago
        clean_change = delta_eth - self.beta * delta_btc
        pct_change = clean_change / eth_60m_ago
        if abs(pct_change) >= self.threshold and self.alert_handler:
            self.alert_handler.trigger(pct_change, eth_now, btc_now)