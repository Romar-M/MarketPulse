import asyncio
import logging
from src.config import settings
from src.database import get_engine, get_session_maker, init_db, get_recent_candles
from src.alerter import AlertHandler
from src.analyzer import PriceAnalyzer
from src.fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Инициализация БД (опционально)
    engine = get_engine(settings.database_url)
    await init_db(engine)
    session_maker = get_session_maker(engine)

    # Обработчик алертов
    alerter = AlertHandler(threshold=settings.threshold)

    # Анализатор
    analyzer = PriceAnalyzer(
        window_size=settings.window_minutes,
        recalc_interval=300,
        threshold=settings.threshold,
        alert_handler=alerter,
    )

    # Прогрев буфера из БД (если есть данные)
    # ...

    # Запуск WebSocket fetcher
    fetcher = DataFetcher(
        symbols=["ethusdt", "btcusdt"],
        on_candle=analyzer.add_candle,
    )

    try:
        await fetcher.connect()
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())