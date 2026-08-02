import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import time
import logging
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from src.config import settings
from src.database import get_engine, get_session_maker, get_recent_candles, get_alerts
from src.regression import run_regression

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="MarketPulse", layout="wide")
st.title("📊 MarketPulse Dashboard")

# Инициализация БД
@st.cache_resource
def init_db():
    engine = get_engine(settings.resolved_database_url)
    return get_session_maker(engine)

session_maker = init_db()

SYMBOLS = ["ETHUSDT", "BTCUSDT"]
INTERVALS = {"1 минута": 60, "5 минут": 30, "15 минут": 20, "1 час": 24}


# ======================= Боковая панель
st.sidebar.header("⚙️ Настройки")
symbol = st.sidebar.selectbox("Тикер", SYMBOLS)
interval_label = st.sidebar.selectbox("Интервал", list(INTERVALS.keys()))
limit = INTERVALS[interval_label]
auto_refresh = st.sidebar.checkbox("Автообновление (10 сек)", value=True)

# ======================= Загрузка данных
async def load_data():
    candles = await get_recent_candles(session_maker, symbol, limit=limit)
    alerts = await get_alerts(session_maker, limit=20)
    return candles, alerts

candles, alerts = asyncio.run(load_data())

# ======================= Метрики
col1, col2, col3, col4 = st.columns(4)

if candles:
    latest = candles[-1]
    prices = [c.close for c in candles]
    beta = run_regression(prices)
    change = ((prices[-1] - prices[0]) / prices[0]) * 100 if len(prices) > 1 else 0

    col1.metric("💰 Цена", f"${latest.close:,.2f}")
    col2.metric("📈 Изменение", f"{change:+.2f}%")
    col3.metric("β Бета", f"{beta:.4f}")
    col4.metric("🕯️ Свечей", len(candles))
else:
    for col in [col1, col2, col3, col4]:
        col.metric("—", "Нет данных")

# ======================= График цен
st.subheader(f"📈 {symbol} — Цена закрытия")

if candles:
    fig_price = go.Figure()
    timestamps = [c.timestamp for c in candles]
    closes = [c.close for c in candles]

    fig_price.add_trace(go.Scatter(
        x=timestamps, y=closes,
        mode="lines+markers",
        name="Close",
        line=dict(color="#00ff88", width=2),
        marker=dict(size=4),
    ))
    fig_price.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title="Время",
        yaxis_title="Цена (USD)",
        template="plotly_dark",
    )
    st.plotly_chart(fig_price, use_container_width=True)
else:
    st.warning("Нет данных для отображения. Запустите scheduler.")

# ======================= Бета-график
st.subheader(f"📉 Скользящая β для {symbol}")

if len(candles) >= 10:
    betas = []
    window = min(10, len(candles) // 2)
    for i in range(len(candles) - window + 1):
        segment = [c.close for c in candles[i:i + window]]
        betas.append(run_regression(segment))

    fig_beta = go.Figure()
    fig_beta.add_trace(go.Bar(
        x=list(range(len(betas))),
        y=betas,
        marker=dict(color=["#ff4444" if b < 0 else "#00ff88" for b in betas]),
    ))
    fig_beta.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        template="plotly_dark",
    )
    st.plotly_chart(fig_beta, use_container_width=True)
else:
    st.info("Недостаточно данных для беты (нужно ≥10 свечей).")

# ======================= Таблица алертов
st.subheader("🚨 Последние алерты")

if alerts:
    alert_data = [
        {
            "ID": a.id,
            "Тип": a.alert_type,
            "Сообщение": a.message,
            "Цена": f"${a.price:,.2f}",
            "Время": a.timestamp.strftime("%H:%M:%S"),
        }
        for a in alerts
    ]
    st.dataframe(alert_data, use_container_width=True, hide_index=True)
else:
    st.info("Алертов пока нет.")

# ======================= Автообновление
if auto_refresh:
    st.sidebar.caption(f"Обновлено: {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(10)
    st.rerun()
