from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class Candle(Base):
    __tablename__ = "candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)


def get_engine(database_url: str):
    return create_async_engine(database_url, echo=False)


def get_session_maker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(engine):
    """Создаёт все таблицы (если их нет)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_recent_candles(session_maker, symbol: str, limit: int = 60):
    """Возвращает последние `limit` свечей для указанного символа, упорядоченных по возрастанию времени."""
    async with session_maker() as session:
        from sqlalchemy import select
        stmt = (
            select(Candle)
            .where(Candle.symbol == symbol)
            .order_by(Candle.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return list(reversed(rows))
