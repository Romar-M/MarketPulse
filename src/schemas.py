"""Pydantic схемы для API."""

from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BetaRequest(BaseModel):
    ticker: str
    period: Optional[int] = 30


class BetaResponse(BaseModel):
    ticker: str
    beta: float
    period: int


class PriceResponse(BaseModel):
    ticker: str
    price: float
    timestamp: str


class AlertResponse(BaseModel):
    id: int
    ticker: str
    alert_type: str
    message: str
    created_at: str


class ExportResponse(BaseModel):
    ticker: str
    records: int
    csv: str
