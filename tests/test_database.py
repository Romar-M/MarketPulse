import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.database import Base, Candle, init_db, get_recent_candles
from datetime import datetime, timezone


@pytest.fixture(scope="function")
async def engine_and_session():
    """Создаёт движок SQLite в памяти и возвращает engine + session_maker."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    yield engine, session_maker
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_candle(engine_and_session):
    engine, session_maker = engine_and_session
    async with session_maker() as session:
        candle = Candle(
            symbol="ETHUSDT",
            timestamp=datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc),
            open=2000.0,
            high=2010.0,
            low=1995.0,
            close=2005.0,
            volume=100.0,
        )
        session.add(candle)
        await session.commit()

    candles = await get_recent_candles(session_maker, "ETHUSDT", limit=1)
    assert len(candles) == 1
    assert candles[0].close == 2005.0


@pytest.mark.asyncio
async def test_get_recent_candles_ordering(engine_and_session):
    engine, session_maker = engine_and_session
    async with session_maker() as session:
        for i in range(5):
            session.add(
                Candle(
                    symbol="BTCUSDT",
                    timestamp=datetime(2026, 7, 5, 12, i, tzinfo=timezone.utc),
                    open=30000 + i,
                    high=30010 + i,
                    low=29990 + i,
                    close=30005 + i,
                    volume=10.0,
                )
            )
        await session.commit()

    candles = await get_recent_candles(session_maker, "BTCUSDT", limit=3)
    assert len(candles) == 3
    # должны быть в порядке возрастания времени
    assert candles[0].timestamp < candles[1].timestamp < candles[2].timestamp
