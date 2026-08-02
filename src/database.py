from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


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


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    alert_type = Column(String, nullable=False, default="divergence")
    message = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

def get_engine(database_url: str):
    return create_async_engine(database_url, echo=False)

def get_session_maker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_recent_candles(session_maker, symbol: str, limit: int = 60):
    try:
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
    except Exception as e:
        logger.error(f"Ошибка загрузки свечей: {e}")
        return []

async def get_alerts(session_maker, limit: int = 100):
    try:
        async with session_maker() as session:
            from sqlalchemy import select
            stmt = select(Alert).order_by(Alert.timestamp.desc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
    except Exception as e:
        logger.error(f"Ошибка загрузки алертов: {e}")
        return []

async def clear_alerts(session_maker):
    try:
        async with session_maker() as session:
            from sqlalchemy import delete
            await session.execute(delete(Alert))
            await session.commit()
    except Exception as e:
        logger.error(f"Ошибка очистки алертов: {e}")

async def close_engine(engine):
    logger.info("Закрытие соединения с БЄ...")
    await engine.dispose()
    logger.info("БА отключена")

