import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.database import Candle, Alert, init_db, get_recent_candles, get_alerts, clear_alerts, close_engine, get_engine, get_session_maker

@pytest.mark.asyncio
async def test_init_db():
    conn_mock = AsyncMock()
    engine_mock = MagicMock()
    engine_mock.begin.return_value.__aenter__.return_value = conn_mock
    await init_db(engine_mock)
    conn_mock.run_sync.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_recent_candles_empty():
    maker = MagicMock()
    ses = AsyncMock()
    res = MagicMock(); res.scalars.return_value.all.return_value = []
    ses.execute.return_value = res; ses.__aenter__.return_value = ses
    maker.return_value = ses
    candles = await get_recent_candles(maker, "ETH", limit=10)
    assert candles == []

@pytest.mark.asyncio
async def test_get_recent_candles_with_data():
    maker = MagicMock()
    ses = AsyncMock()
    c = Candle(symbol="ETH", timestamp=MagicMock(), open=1, high=2, low=1, close=1.5, volume=100)
    res = MagicMock(); res.scalars.return_value.all.return_value = [c]
    ses.execute.return_value = res; ses.__aenter__.return_value = ses
    maker.return_value = ses
    candles = await get_recent_candles(maker, "ETH", limit=10)
    assert len(candles) == 1
    assert candles[0].symbol == "ETH"

@pytest.mark.asyncio
async def test_get_recent_candles_error():
    maker = MagicMock()
    ses = AsyncMock()
    ses.__aenter__.return_value.execute.side_effect = Exception("db error")
    maker.return_value = ses
    candles = await get_recent_candles(maker, "ETH", limit=10)
    assert candles == []

@pytest.mark.asyncio
async def test_get_alerts_empty():
    maker = MagicMock()
    ses = AsyncMock()
    res = MagicMock(); res.scalars.return_value.all.return_value = []
    ses.execute.return_value = res; ses.__aenter__.return_value = ses
    maker.return_value = ses
    alerts = await get_alerts(maker, limit=10)
    assert alerts == []

@pytest.mark.asyncio
async def test_get_alerts_with_data():
    maker = MagicMock()
    ses = AsyncMock()
    a = Alert(pct_change=0.05, eth_price=1000, btc_price=20000)
    res = MagicMock(); res.scalars.return_value.all.return_value = [a]
    ses.execute.return_value = res; ses.__aenter__.return_value = ses
    maker.return_value = ses
    alerts = await get_alerts(maker, limit=10)
    assert len(alerts) == 1
    assert alerts[0].pct_change == 0.05

@pytest.mark.asyncio
async def test_get_alerts_error():
    maker = MagicMock()
    ses = AsyncMock()
    ses.__aenter__.return_value.execute.side_effect = Exception("db error")
    maker.return_value = ses
    alerts = await get_alerts(maker, limit=10)
    assert alerts == []

@pytest.mark.asyncio
async def test_clear_alerts():
    maker = MagicMock()
    ses = AsyncMock()
    ses.__aenter__.return_value = ses
    maker.return_value = ses
    await clear_alerts(maker)
    ses.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_close_engine():
    engine_mock = AsyncMock()
    await close_engine(engine_mock)
    engine_mock.dispose.assert_awaited_once()

def test_get_engine():
    with patch("src.database.create_async_engine") as mock:
        e = get_engine("sqlite+aiosqlite:///test.db")
        mock.assert_called_once_with("sqlite+aiosqlite:///test.db", echo=False)

def test_get_session_maker():
    engine = MagicMock()
    with patch("src.database.async_sessionmaker") as mock:
        m = get_session_maker(engine)
        mock.assert_called_once()
