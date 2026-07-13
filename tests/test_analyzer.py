import pytest
import random
from src.analyzer import PriceAnalyzer


class MockAlertHandler:
    def __init__(self):
        self.messages = []

    async def trigger(self, pct_change, eth_price, btc_price):
        self.messages.append((pct_change, eth_price, btc_price))


@pytest.fixture
def analyzer_low_threshold():
    ana = PriceAnalyzer(window_size=60, recalc_interval=0, threshold=0.01)
    handler = MockAlertHandler()
    ana.alert_handler = handler
    return ana, handler


@pytest.fixture
def analyzer_high_threshold():
    ana = PriceAnalyzer(window_size=60, recalc_interval=0, threshold=0.5)
    handler = MockAlertHandler()
    ana.alert_handler = handler
    return ana, handler


@pytest.mark.asyncio
async def test_beta_calculation(analyzer_low_threshold):
    ana, _ = analyzer_low_threshold
    random.seed(42)
    for i in range(60):
        noise = random.uniform(-0.001, 0.001)
        btc_price = 30000.0 * (1 + i * 0.0005 + noise)
        eth_price = 2000.0 * (1 + i * 0.0005 + noise)
        await ana.add_candle("BTCUSDT", btc_price, 1000 + i * 60)
        await ana.add_candle("ETHUSDT", eth_price, 1000 + i * 60)
    ana._recalc_beta()
    assert ana.beta is not None
    assert ana.beta == pytest.approx(1.0, rel=0.3)


@pytest.mark.asyncio
async def test_alert_triggered(analyzer_low_threshold):
    ana, handler = analyzer_low_threshold
    random.seed(42)
    for i in range(60):
        noise_btc = random.uniform(-0.001, 0.001)
        noise_eth = random.uniform(-0.001, 0.001)
        btc_price = 30000.0 * (1 + i * 0.0005 + noise_btc)
        eth_price = 2000.0 * (1 - i * 0.001 + noise_eth)
        await ana.add_candle("BTCUSDT", btc_price, 1000 + i * 60)
        await ana.add_candle("ETHUSDT", eth_price, 1000 + i * 60)
    ana._recalc_beta()
    await ana._check_alert()
    assert len(handler.messages) == 1
    msg = handler.messages[0]
    assert abs(msg[0]) > 0.01


@pytest.mark.asyncio
async def test_no_alert_below_threshold(analyzer_high_threshold):
    ana, handler = analyzer_high_threshold
    random.seed(42)
    for i in range(60):
        noise = random.uniform(-0.001, 0.001)
        btc_price = 30000.0 * (1 + i * 0.0005 + noise)
        eth_price = 2000.0 * (1 + i * 0.0005 + noise)
        await ana.add_candle("BTCUSDT", btc_price, 1000 + i * 60)
        await ana.add_candle("ETHUSDT", eth_price, 1000 + i * 60)
    ana._recalc_beta()
    await ana._check_alert()
    assert len(handler.messages) == 0
