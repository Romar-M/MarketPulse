"""Circuit Breaker для WebSocket подключения."""

import asyncio
import logging
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    async def call(self, coro):
        if self.state == CircuitState.OPEN:
            if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit: OPEN -> HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await coro
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit: HALF_OPEN -> CLOSED")

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit: CLOSED -> OPEN (failures={self.failure_count})")
