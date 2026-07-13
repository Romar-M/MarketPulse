
# MarketPulse — Приложение для анализа цен фьючерса

## 📋 Описание

**MarketPulse** — это приложение для анализа цен фьючерсов в реальном времени. Оно подключается к WebSocket биржи, 
получает котировки, рассчитывает коэффициент β (бета) и отправляет алерты при достижении заданных порогов.

## 🚀 Функционал

- ✅ **WebSocket-клиент** — подключение к потоку котировок в реальном времени
- ✅ **Расчёт β (бета)** — коэффициент волатильности относительно рынка
- ✅ **Система алертов** — уведомления при превышении порогов
- ✅ **Авто-переподключение** — при обрыве соединения
- ✅ **Логирование** — запись событий и ошибок
- ✅ **Graceful shutdown** — корректное завершение по Ctrl+C

## 🛠️ Технологии

- **Python 3.10+**
- **WebSocket** (websockets / websocket-client)
- **Asyncio** — асинхронная архитектура
- **Pytest** — тестирование

## 📁 Структура проекта

```
MarketPulse/
├── src/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── websocket_client.py   # WebSocket-клиент
│   ├── beta_calculator.py    # Расчёт β
│   ├── alert_manager.py      # Система алертов
│   └── config.py             # Конфигурация
├── tests/
│   ├── __init__.py
│   ├── test_websocket.py
│   ├── test_beta.py
│   └── test_alerts.py
├── requirements.txt
├── README.md
└── .gitignore
```

## ⚙️ Установка и запуск

```bash
# Клонировать репозиторий
git clone https://github.com/Romar-M/MarketPulse.git
cd MarketPulse

# Установить зависимости
pip install -r requirements.txt

# Запустить приложение
python src/main.py
```

## 🧪 Тестирование

```bash
pytest tests/ -v
