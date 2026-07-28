"""Тесты Circuit Breaker."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from src.circuit_breaker import CircuitBreaker, CircuitState


@pytest.mark.asyncio
async def test_initial_state_closed() -> None:
    """Начальное состояние CLOSED."""
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_call_success() -> None:
    """Успешный вызов — состояние остаётся CLOSED."""
    cb = CircuitBreaker()
    mock = AsyncMock(return_value="ok")
    result = await cb.call(mock())
    assert result == "ok"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_call_failure_opens_after_threshold() -> None:
    """N ошибок подряд → OPEN."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    failing_mock = AsyncMock(side_effect=Exception("fail"))

    for _ in range(3):
        with pytest.raises(Exception):
            await cb.call(failing_mock())

    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_open_raises_exception() -> None:
    """В состоянии OPEN вызов кидает исключение."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
    failing_mock = AsyncMock(side_effect=Exception("fail"))

    with pytest.raises(Exception):
        await cb.call(failing_mock())

    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        await cb.call(AsyncMock()())


@pytest.mark.asyncio
async def test_half_open_transition() -> None:
    """После recovery_timeout → HALF_OPEN, успешный вызов закрывает."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
    failing_mock = AsyncMock(side_effect=Exception("fail"))

    with pytest.raises(Exception):
        await cb.call(failing_mock())

    assert cb.state == CircuitState.OPEN

    success_mock = AsyncMock(return_value="recovered")
    result = await cb.call(success_mock())
    assert result == "recovered"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_half_open_success_closes() -> None:
    """Успех в HALF_OPEN → CLOSED."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
    failing_mock = AsyncMock(side_effect=Exception("fail"))

    with pytest.raises(Exception):
        await cb.call(failing_mock())

    assert cb.state == CircuitState.OPEN

    success_mock = AsyncMock(return_value="recovered")
    result = await cb.call(success_mock())
    assert result == "recovered"
    assert cb.state == CircuitState.CLOSED
