"""Тесты утилит."""
from __future__ import annotations

from src.utils import export_to_csv


class TestUtils:
    """Набор тестов для утилит."""

    def test_export_to_csv_empty(self) -> None:
        """Пустой список → только заголовок."""
        csv_data = export_to_csv([])
        assert "id,ticker,price,timestamp" in csv_data
        assert csv_data.count("\n") == 1  # только заголовок

    def test_export_to_csv_single(self) -> None:
        """Одна запись."""
        records = [
            type("Record", (), {"id": 1, "ticker": "ETHUSDT", "price": 1000.0, "timestamp": "2024-01-01T00:00:00"})
        ]
        csv_data = export_to_csv(records)
        assert "ETHUSDT" in csv_data
        assert "1000.0" in csv_data
        assert csv_data.count("\n") == 2

    def test_export_to_csv_multiple(self) -> None:
        """Несколько записей."""
        records = [
            type("Record", (), {"id": i, "ticker": f"TICK{i}", "price": float(i * 100), "timestamp": f"2024-01-0{i % 30 + 1}"})
            for i in range(1, 4)
        ]
        csv_data = export_to_csv(records)
        lines = csv_data.strip().split("\n")
        assert len(lines) == 4  # заголовок + 3 записи
