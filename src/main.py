"""MarketPulse — точка входа: WebSocket-клиент, анализатор и периодические алерты."""

import asyncio
import logging
import signal
import sys

from .config import settings
from .database import get_engine, get_session_maker, init_db, get_recent_candles
from .alerter import AlertHandler
from .analyzer import PriceAnalyzer, analyzer_instance
from .fetcher import DataFetcher

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Ловит SIGINT/SIGTERM и выставляет флаг для корректного завершения."""

    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)

    def _handler(self, signum, frame):
        """Обработчик сигнала: помечает, что запрошено завершение."""
        self.shutdown_requested = True
        logger.warning("Shutdown signal received")

    def is_shutdown_requested(self):
        """Возвращает True, если пришёл сигнал завершения."""
        return self.shutdown_requested


async def alert_check_loop(analyzer, interval):
    """Фоновая задача: проверяет алерты каждые interval секунд."""
    while True:
        try:
            await analyzer.check_alert()
        except Exception as e:
            logger.error(f"Alert check error: {e}")
        await asyncio.sleep(interval)


async def main():
    """Запускает приложение: БД, прогрев буфера, WebSocket и фоновые задачи."""
    engine = get_engine(settings.resolved_database_url)
    await init_db(engine)
    session_maker = get_session_maker(engine)

    alerter = AlertHandler(threshold=settings.threshold, session_maker=session_maker)

    analyzer = PriceAnalyzer(
        window_size=settings.window_minutes,
        recalc_interval=300,
        threshold=settings.threshold,
        alert_handler=alerter,
        alert_check_interval=settings.alert_check_interval,
    )
    analyzer.session_maker = session_maker
    analyzer_instance.window_size = analyzer.window_size
    analyzer_instance.threshold = analyzer.threshold
    analyzer_instance.alert_handler = analyzer.alert_handler
    analyzer_instance.session_maker = session_maker

    logger.info("Warming up buffer from DB...")
    try:
        eth_recent = await get_recent_candles(session_maker, symbol="ETHUSDT", limit=analyzer.window_size)
        btc_recent = await get_recent_candles(session_maker, symbol="BTCUSDT", limit=analyzer.window_size)
        for candle in list(eth_recent) + list(btc_recent):
            await analyzer.add_candle(candle.symbol, candle.close, candle.timestamp.timestamp())
        logger.info(f"Warmup: {len(eth_recent)} ETH / {len(btc_recent)} BTC свечей загружено")
    except Exception as e:
        logger.error(f"Warmup error: {e}")

    fetcher = DataFetcher(
        symbols=["ethusdt", "btcusdt"],
        on_candle=analyzer.add_candle,
    )

    shutdown = GracefulShutdown()

    try:
        await asyncio.gather(
            fetcher.connect(),
            alert_check_loop(analyzer, settings.alert_check_interval),
        )
    except KeyboardInterrupt:
        logger.warning("Shutdown by Ctrl+C...")
    finally:
        logger.info("Cleaning up...")
        await fetcher.disconnect()
        await engine.dispose()
        logger.info("App stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)

