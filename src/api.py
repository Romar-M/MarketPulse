import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.auth import create_access_token, verify_token, register_user
from src.schemas import (
    CandleResponse,
    AlertResponse,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RegressionResponse,
)
from src.config import settings
from src.database import (
    get_engine,
    get_session_maker,
    get_recent_candles,
    get_alerts as db_get_alerts,
    Candle,
    Alert,
)
from src.regression import run_regression

logger = logging.getLogger(__name__)

app = FastAPI(title="MarketPulse API", version="0.1.0")
security = HTTPBearer()


@app.on_event("startup")
async def startup():
    engine = get_engine(settings.database_url)
    session_maker = get_session_maker(engine)
    logger.info("API запущен")


@app.get("/candles/{symbol}", response_model=list[CandleResponse])
async def get_candles(symbol: str, limit: int = 100):
    engine = get_engine(settings.database_url)
    session_maker = get_session_maker(engine)
    candles = await get_recent_candles(session_maker, symbol, limit)
    await engine.dispose()
    return [
        CandleResponse(
            id=c.id,
            symbol=c.symbol,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
            timestamp=c.timestamp.isoformat(),
        )
        for c in candles
    ]


@app.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(limit: int = 50):
    engine = get_engine(settings.database_url)
    session_maker = get_session_maker(engine)
    alerts = await db_get_alerts(session_maker, limit)
    await engine.dispose()
    return [
        AlertResponse(
            id=a.id,
            symbol=a.symbol,
            alert_type=a.alert_type,
            message=a.message,
            price=a.price,
            timestamp=a.timestamp.isoformat(),
        )
        for a in alerts
    ]


@app.get("/regression/{symbol}", response_model=RegressionResponse)
async def regression(symbol: str):
    result = await run_regression(symbol)
    return RegressionResponse(
        symbol=result["symbol"],
        slope=result["slope"],
        intercept=result["intercept"],
        r_squared=result["r_squared"],
        last_price=result["last_price"],
        trend=result["trend"],
    )


@app.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest):
    token = await register_user(data.username, data.password)
    if not token:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    return TokenResponse(access_token=token, token_type="bearer")


@app.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    token = await create_access_token(data.username, data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    return TokenResponse(access_token=token, token_type="bearer")


@app.get("/me", response_model=UserResponse)
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Неверный токен")
    return UserResponse(username=payload.get("sub"))
