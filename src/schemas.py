from pydantic import BaseModel
from typing import Optional


class CandleResponse(BaseModel):
    id: int
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: str


class AlertResponse(BaseModel):
    id: int
    symbol: str
    alert_type: str
    message: str
    price: float
    timestamp: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    username: str


class RegressionResponse(BaseModel):
    symbol: str
    slope: float
    intercept: float
    r_squared: float
    last_price: float
    trend: str
