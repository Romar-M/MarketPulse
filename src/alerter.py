import logging
from datetime import datetime
import time
from collections import deque

from telegram_bot import TelegramBot, TOKEN, CHAT_ID
from database import Alert

logger = logging.getLogger(__name__)


class AlertHandler:
    def __init__(self, threshold=0.01, min_interval=300, session_maker=None):
        self.threshold = threshold
        self.min_interval = min_interval
        self.last_alert_time = 0
        self.alert_history = deque(maxlen=20)
        self.session_maker = session_maker
        self.telegram_bot = TelegramBot(token=TOKEN, chat_id=CHAT_ID)

    async def trigger(self, change_pct, eth_price, btc_price):
        now = time.time()
        if now - self.last_alert_time < self.min_interval:
            return None

        if abs(change_pct) >= self.threshold:
            self.last_alert_time = now
            percent = change_pct * 100
            msg = f"[{datetime.now()}] ALERT: ETH own move {percent:+.2f}% | ETH={eth_price:.2f} | BTC={btc_price:.2f}"

            # Save to DB
            if self.session_maker:
                try:
                    async with self.session_maker() as session:
                        alert = Alert(
                            pct_change=change_pct,
                            eth_price=eth_price,
                            btc_price=btc_price,
                        )
                        session.add(alert)
                        await session.commit()
                except Exception as e:
                    logger.error(f"Failed to save alert to DB: {e}")

            self.alert_history.append({
                "time": now,
                "change_pct": change_pct,
                "eth_price": eth_price,
                "btc_price": btc_price,
                "msg": msg,
            })

            logger.info(msg)
            print(msg)
            await self.telegram_bot.send_message(msg)
            return msg
        return None

    def get_stats(self):
        if not self.alert_history:
            return "Alerts: none"
        total = len(self.alert_history)
        last = self.alert_history[-1]
        return f"Alerts: {total} total, last: {last['msg']}"
