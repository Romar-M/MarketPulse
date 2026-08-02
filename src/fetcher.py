import asyncio
import json
import logging
from typing import Callable, Awaitable

import websockets

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Подключается к Binance WebSocket и передаёт свечи в callback.
    Ожидается поток вида: {"stream":"ethusdt@kline_1m","data":{"k":{"o":"...","c":"...","x":true}}}
    """

    def __init__(
        self,
        symbols: list[str],
        on_candle: Callable[[str, float, float], Awaitable[None]],
    ):
        self.symbols = [s.lower() for s in symbols]
        self.on_candle = on_candle
        self._ws = None
        self.reconnect_attempts = 0
        self.max_reconnects = 10

    async def connect(self):
        streams = "/".join([f"{s}@kline_1m" for s in self.symbols])
        url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        while True:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
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
            logger.warning("Empty message received")
            return
        logger.debug(f"Raw message received: {message[:200]}...")
        try:
            data = json.loads(message)
            stream = data.get("stream", "")
            kline = data.get("data", {}).get("k", {})
            if not kline:
                logger.warning(f"No 'k' field in data: {list(data.get('data', {}).keys())}")
                return
            if not kline.get("x", False):
                logger.debug(f"Candle not closed yet for {stream}")
                return
            symbol = stream.split("@")[0].upper()
            close_price = float(kline["c"])
            timestamp = float(kline["T"]) / 1000
            logger.info(f"Processed candle: {symbol} close={close_price} ts={timestamp}")
            await self.on_candle(symbol, close_price, timestamp)
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Malformed message: {e}")

    async def close(self):
        if self._ws:
            await self._ws.close()

    async def disconnect(self):
        logger.info("Отключение WebSocket...")
        if self._ws:
            await self._ws.close()
            self._ws = None
        logger.info("WebSocket отключён")
