import asyncio
import json
import logging
from typing import Callable, Awaitable

import websockets

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Подключается к Binance WebSocket и передаёт свечи в callback.
    Ожидается поток вида: {"stream":"ethusdt@kline_1m","data":{...}}
    """

    def __init__(
        self,
        symbols: list[str],
        on_candle: Callable[[str, float, float], Awaitable[None]],
    ):
        """
        :param symbols: список символов в нижнем регистре, например ['ethusdt', 'btcusdt']
        :param on_candle: async функция, принимающая (symbol, close_price, timestamp)
        """
        self.symbols = [s.lower() for s in symbols]
        self.on_candle = on_candle
        self._ws = None
        self.reconnect_attempts = 0
        self.max_reconnects = 10

    async def connect(self):
        """Запускает вечное прослушивание WebSocket с авто-переподключением."""
        streams = "/".join([f"{s}@kline_1m" for s in self.symbols])
        url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    self._ws = ws
                    logger.info("WebSocket connected")
                    async for message in ws:
                        await self._process_message(message)
            except asyncio.CancelledError:
                logger.info("Fetcher cancelled")
                break
            except Exception as e:
                self.reconnect_attempts += 1
                logger.error(
                    f"WebSocket error: {e} (попытка {self.reconnect_attempts}/{self.max_reconnects})"
                )

                if self.reconnect_attempts >= self.max_reconnects:
                    logger.critical("Превышено число попыток реконнекта")
                    break

                await asyncio.sleep(5)

    async def _process_message(self, message: str):
        if not message:
            return
        """Парсит JSON и вызывает callback, если свеча закрыта."""
        try:
            data = json.loads(message)
            stream = data.get("stream", "")
            kline = data.get("data", {}).get("kline", {})
            if not kline.get("x", False):  # пропускаем незакрытые свечи
                return
            symbol = stream.split("@")[0].upper()
            close_price = float(kline["c"])
            timestamp = float(kline["T"]) / 1000  # миллисекунды -> секунды
            await self.on_candle(symbol, close_price, timestamp)
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Malformed message: {e}")

    async def close(self):
        if self._ws:
            await self._ws.close()

    async def disconnect(self):
        """Корректное отключение WebSocket."""
        logger.info("🔌 Отключение WebSocket...")
        if self._ws:
            await self._ws.close()
            self._ws = None
        logger.info("✅ WebSocket отключён")
