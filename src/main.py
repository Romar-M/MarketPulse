import asyncio
import logging
from src.config import settings
from src.database import get_engine, get_session_maker, init_db, get_recent_candles, close_engine
from src.alerter import AlertHandler
from src.analyzer import PriceAnalyzer
from src.fetcher import DataFetcher
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Корректное завершение по Ctrl+C / SIGTERM"""

    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)

    def _handler(self, signum, frame):
        self.shutdown_requested = True
        logger.warning("Получен сигнал завершения")

    def is_shutdown_requested(self):
        return self.shutdown_requested

async def main():
    # Инициализация БД
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

    # Прогрев буфера из БД
    logger.info("Прогрев буфера из БД...")
    try:
        recent = await get_recent_candles(session_maker, symbol="ETHUSDT", limit=analyzer.window_size)
        if recent:
            for candle in recent:
                analyzer.add_candle(candle)
            logger.info(f"Буфер прогрет: {len(recent)} свечей загружено")
        else:
            logger.warning("Нет данных в БД для прогрева")
    except Exception as e:
        logger.error(f"Ошибка прогрева буфера: {e}")

    # Запуск WebSocket fetcher
    fetcher = DataFetcher(
        symbols=["ethusdt", "btcusdt"],
        on_candle=analyzer.add_candle,
    )

    shutdown = GracefulShutdown()

    try:
        await fetcher.connect()
    except KeyboardInterrupt:
        logger.warning("Завершение по Ctrl+C...")
    finally:
        logger.info("Очистка ресурсов...")
        await fetcher.disconnect()
        await close_engine(engine)
        logger.info("Приложение остановлено")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)