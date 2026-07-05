import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertHandler:
    def __init__(self, threshold: float = 0.01) -> None:
        self.threshold = threshold

    def trigger(
        self, change_pct: float, eth_price: float, btc_price: float
    ) -> str | None:
        if abs(change_pct) >= self.threshold:
            # умножаем на 100 для отображения процентов
            percent = change_pct * 100
            msg = (
                f"[{datetime.now()}] ALERT: ETH own move {percent:+.2f}% "
                f"| ETH={eth_price:.2f} | BTC={btc_price:.2f}"
            )
            logger.info(msg)
            print(msg)
            return msg
        return None