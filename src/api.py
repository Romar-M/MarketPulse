"""REST API для MarketPulse."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.auth import create_access_token, verify_token
from src.schemas import (
    TokenResponse,
    LoginRequest,
    BetaResponse,
    PriceResponse,
    AlertResponse,
    ExportResponse,
)
from src.config import settings
from src.database import get_engine, get_session_maker, get_recent_candles, get_alerts as db_get_alerts, Candle, Alert
from src.regression import run_regression

logger = logging.getLogger(__name__)

app = FastAPI(title="MarketPulse API", version="1.0.0")
security = HTTPBearer()

# Инициализация БД
engine = get_engine(settings.database_url)
session_maker = get_session_maker(engine)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload


@app.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    if request.username == "admin" and request.password == "secret":
        token = create_access_token(data={"sub": request.username})
        return TokenResponse(access_token=token, token_type="bearer")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@app.get("/beta/{ticker}", response_model=BetaResponse)
async def get_beta(ticker: str, period: Optional[int] = 30, user=Depends(get_current_user)):
    candles = await get_recent_candles(session_maker, ticker, limit=period)
    if len(candles) < 2:
        raise HTTPException(status_code=404, detail="Not enough data")
    prices = [c.close for c in candles]
    beta_value = run_regression(prices)
    return BetaResponse(ticker=ticker, beta=beta_value, period=period)


@app.get("/prices/{ticker}", response_model=list[PriceResponse])
async def get_prices(ticker: str, limit: int = 100, user=Depends(get_current_user)):
    candles = await get_recent_candles(session_maker, ticker, limit=limit)
    return [
        PriceResponse(
            ticker=c.symbol,
            price=c.close,
            timestamp=c.timestamp.isoformat(),
        )
        for c in candles
    ]


@app.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(user=Depends(get_current_user)):
    alerts = await db_get_alerts(session_maker, limit=50)
    return [
        AlertResponse(
            id=a.id,
            ticker="",
            alert_type="price",
            message=f"Change: {a.pct_change:.2f}%",
            created_at=a.timestamp.isoformat(),
        )
        for a in alerts
    ]


@app.get("/export/{ticker}", response_model=ExportResponse)
async def export_prices(ticker: str, days: int = 30, user=Depends(get_current_user)):
    candles = await get_recent_candles(session_maker, ticker, limit=days * 24)
    csv_lines = ["symbol,timestamp,open,high,low,close,volume"]
    for c in candles:
        csv_lines.append(f"{c.symbol},{c.timestamp.isoformat()},{c.open},{c.high},{c.low},{c.close},{c.volume}")
    csv_data = "\n".join(csv_lines)
    return ExportResponse(ticker=ticker, records=len(candles), csv=csv_data)
