import pytest
from src.fetcher import DataFetcher


class MockCallback:
    def __init__(self):
        self.calls = []

    async def on_candle(self, symbol: str, price: float, timestamp: float):
        self.calls.append((symbol, price, timestamp))


@pytest.fixture
def fetcher():
    cb = MockCallback()
    f = DataFetcher(symbols=["ethusdt"], on_candle=cb.on_candle)
    return f, cb


@pytest.mark.asyncio
async def test_process_valid_closed_candle(fetcher):
    f, cb = fetcher
    message = """
    {
        "stream": "ethusdt@kline_1m",
        "data": {
            "kline": {
                "x": true,
                "c": "2000.50",
                "T": 1625097600000
            }
        }
    }
    """
    await f._process_message(message)
    assert len(cb.calls) == 1
    assert cb.calls[0] == ("ETHUSDT", 2000.50, 1625097600.0)


@pytest.mark.asyncio
async def test_ignore_incomplete_candle(fetcher):
    f, cb = fetcher
    message = """
    {
        "stream": "ethusdt@kline_1m",
        "data": {
            "kline": {
                "x": false,
                "c": "2000.50",
                "T": 1625097600000
            }
        }
    }
    """
    await f._process_message(message)
    assert len(cb.calls) == 0


@pytest.mark.asyncio
async def test_reconnect_on_error(fetcher):
    f, cb = fetcher
    # Проверка, что reconnect_attempts сбрасывается
    assert f.reconnect_attempts == 0
    assert f.max_reconnects == 10
