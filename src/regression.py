"""Расчёт бета-коэффициента."""

import logging
import numpy as np

logger = logging.getLogger(__name__)


def run_regression(prices: list[float]) -> float:
    """Рассчитывает бета-коэффициент по списку цен."""
    if len(prices) < 2:
        logger.warning("Недостаточно данных для расчёта беты")
        return 0.0

    arr = np.array(prices)
    returns = np.diff(arr) / arr[:-1]

    # Рыночный proxy — средняя доходность
    market_returns = np.full_like(returns, np.mean(returns))
    covariance = np.cov(returns, market_returns)[0][1]
    variance = np.var(market_returns)

    if variance == 0:
        return 0.0

    beta = covariance / variance
    logger.info(f"Бета: {beta:.4f}")
    return round(beta, 4)
