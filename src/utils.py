"""Утилиты для экспорта и форматирования."""

import csv
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def export_to_csv(records: list) -> str:
    """Преобразует список записей в CSV-строку."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "ticker", "price", "timestamp"])

    for r in records:
        writer.writerow([
            r.id,
            r.ticker,
            r.price,
            r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp),
        ])

    csv_data = output.getvalue()
    output.close()
    logger.info(f"Экспортировано {len(records)} записей в CSV")
    return csv_data
