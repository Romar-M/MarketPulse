import logging  
from collections import deque  
from datetime import datetime, timezone  
import math  
  
logger = logging.getLogger(__name__)  
  
  
class PriceAnalyzer:  
    def __init__(self, window_size=60, recalc_interval=300, threshold=0.01, alert_handler=None):  
        self.window_size = window_size  
        self.min_data_points = 10  
        self.recalc_interval = recalc_interval  
        self.threshold = threshold  
        self.alert_handler = alert_handler  
        self.eth_prices = deque(maxlen=window_size)  
        self.btc_prices = deque(maxlen=window_size)  
        self.last_recalc_time = None  
        self.last_alert_time = 0.0  
        self.alert_cooldown = 300  
        self.beta = None  
  
    async def add_candle(self, symbol, close_price, timestamp):  
        if close_price is None or close_price <= 0:  
            return  
        if timestamp is None or timestamp <= 0:  
            return  
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)  
        if symbol.upper() == "ETHUSDT":  
            self.eth_prices.append(close_price)  
        elif symbol.upper() == "BTCUSDT":  
            self.btc_prices.append(close_price)  
        else:  
            return  
        if len(self.eth_prices) < self.min_data_points or len(self.btc_prices) < self.min_data_points:  
            return  
        if self._should_recalc(dt):  
            self._recalc_beta()  
            self.last_recalc_time = dt  
        await self._check_alert()  
  
    def _should_recalc(self, current_time):  
        if self.last_recalc_time is None:  
            return len(self.eth_prices) == self.window_size and len(self.btc_prices) == self.window_size  
        elapsed = (current_time - self.last_recalc_time).total_seconds()  
        return elapsed >= self.recalc_interval  
  
    def _recalc_beta(self):  
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
  
    async def _check_alert(self):  
        import time  
        now = time.time()  
        if now - self.last_alert_time < self.alert_cooldown:  
            return  
        if self.beta is None:  
            return  
        if len(self.eth_prices) < 2 or len(self.btc_prices) < 2:  
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
