import pytest
from src.analyzer import PriceAnalyzer
from src.alerter import AlertHandler


class MockAlertHandler:
    def __init__(self):
        self.messages = []

    def trigger(self, change_pct, eth_price, btc_price):
        self.messages.append((change_pct, eth_price, btc_price))


@pytest.fixture
def analyzer():
    handler = MockAlertHandler()
    return PriceAnalyzer(window_size=5, recalc_interval=300, threshold=0.01,
                         alert_handler=handler), handler


@pytest.mark.asyncio
async def test_beta_calculation(analyzer):
    ana, handler = analyzer
    # Заполняем синтетическими данными: btc линейно растёт, eth = 2*btc
    for i in range(5):
        await ana.add_candle("BTCUSDT", 100.0 + i * 10, 1000 + i * 60)
        await ana.add_candle("ETHUSDT", 200.0 + i * 20, 1000 + i * 60)
    assert ana.beta is not None
    assert abs(ana.beta - 2.0) < 0.001


@pytest.mark.asyncio
async def test_alert_triggered(analyzer):
    ana, handler = analyzer
    # Заполняем окно одинаковыми ценами, потом резко меняем ETH
    for i in range(5):
        await ana.add_candle("BTCUSDT", 30000.0, 1000 + i * 60)
        await ana.add_candle("ETHUSDT", 2000.0, 1000 + i * 60)
    # Теперь beta должна быть ~0 (цены не коррелируют), но после расчёта
    # Добавим новую свечу с резким ростом ETH при неизменном BTC
    # окно теперь: первые 4 свечи старые, последняя новая
    # Чтобы сымитировать изменение за 60 мин, нужно чтобы последняя сильно отличалась от первой
    # Уменьшим window_size до 2 для простоты? Но у нас 5. Мы можем задать цены так:
    # первые 4 свечи: eth=2000, btc=30000; последняя: eth=2200 (рост 10%),
    # тогда изменение от первого до последнего: eth_first=2000, eth_last=2200 => 10%.
    # Но beta=0, поэтому alert сработает.
    ana.eth_prices[-1] = 2200.0  # напрямую меняем последний элемент для теста
    await ana._check_alert()
    assert len(handler.messages) == 1
    assert handler.messages[0][0] == 0.1  # 10%


@pytest.mark.asyncio
async def test_no_alert_below_threshold(analyzer):
    ana, handler = analyzer
    for i in range(5):
        await ana.add_candle("BTCUSDT", 30000.0, 1000 + i * 60)
        await ana.add_candle("ETHUSDT", 2000.0, 1000 + i * 60)
    ana.eth_prices[-1] = 2010.0  # рост 0.5%
    await ana._check_alert()
    assert len(handler.messages) == 0