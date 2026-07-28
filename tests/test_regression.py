"""Тесты регрессионного модуля."""
from __future__ import annotations

from src.regression import run_regression


class TestRegression:
    """Набор тестов для регрессии."""

    def test_run_regression_basic(self) -> None:
        """Обычный расчёт возвращает beta."""
        prices = [1000.0, 1010.0, 1020.0, 1030.0, 1040.0]
        beta = run_regression(prices)
        assert isinstance(beta, float)
        assert abs(beta) < 2.0

    def test_run_regression_flat(self) -> None:
        """Плоские цены — beta = 0."""
        prices = [1000.0, 1000.0, 1000.0, 1000.0]
        beta = run_regression(prices)
        assert beta == 0.0

    def test_run_regression_insufficient_data(self) -> None:
        """Меньше 2 точек — beta = 0."""
        beta = run_regression([1000.0])
        assert beta == 0.0

    def test_run_regression_empty(self) -> None:
        """Пустой список — beta = 0."""
        beta = run_regression([])
        assert beta == 0.0
