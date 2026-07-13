import logging
from datetime import datetime
import time
from collections import deque

logger = logging.getLogger(__name__)


class AlertHandler:
    def __init__(self, threshold: float = 0.01, min_interval: int = 300) -> None:
        self.threshold = threshold
        self.min_interval = min_interval  # 5 минут между алертами
        self.last_alert_time = 0
        self.alert_history = deque(maxlen=20)

    def trigger(
        self, change_pct: float, eth_price: float, btc_price: float
    ) -> str | None:
        # Защита от частых алертов
        now = time.time()
        if now - self.last_alert_time < self.min_interval:
            return None

        if abs(change_pct) >= self.threshold:
            self.last_alert_time = now
            percent = change_pct * 100

            msg = (
                f"[{datetime.now()}] ALERT: ETH own move {percent:+.2f}% "
                f"| ETH={eth_price:.2f} | BTC={btc_price:.2f}"
            )

            # Сохраняем в историю
            self.alert_history.append(
                {
                    "time": now,
                    "change_pct": change_pct,
                    "eth_price": eth_price,
                    "btc_price": btc_price,
                    "msg": msg,
                }
            )

            logger.info(msg)
            print(msg)
            return msg
        return None

    def get_stats(self) -> str:
        """Статистика алертов для логирования"""
        if not self.alert_history:
            return "📊 Алерты: нет"

        total = len(self.alert_history)
        last = self.alert_history[-1]
        return (
            f"📊 Алерты: {total} всего\n"
            f"   • Последний: {last['msg']}\n"
            f"   • Интервал: {self.min_interval} сек"
        )
