import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.config import settings

@pytest.fixture
def client():
    from src.api import app
    return TestClient(app)

def _make_token():
    from src.auth import create_access_token
    return create_access_token({"sub": "test"})

class TestUnauthorized:
    def test_beta_no_token(self, client):
        assert client.get("/beta/ETH").status_code == 401
    def test_prices_no_token(self, client):
        assert client.get("/prices/ETH").status_code == 401
    def test_alerts_no_token(self, client):
        assert client.get("/alerts").status_code == 401
    def test_export_no_token(self, client):
        assert client.get("/export/ETH").status_code == 401

class TestAuth:
    def test_login_success(self, client):
        r = client.post("/login", json={"username": "admin", "password": "secret"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
    def test_login_failure(self, client):
        r = client.post("/login", json={"username": "x", "password": "x"})
        assert r.status_code == 401

class TestBeta:
    @patch("src.api.get_recent_candles")
    def test_beta_not_enough_data(self, mock_get, client):
        mock_get.return_value = []
        tk = _make_token()
        r = client.get("/beta/ETH", headers={"Authorization": f"Bearer {tk}"})
        assert r.status_code == 404

    @patch("src.api.get_recent_candles")
    @patch("src.api.run_regression")
    def test_beta_with_data(self, mock_reg, mock_get, client):
        c1 = MagicMock(spec=["close"]); c1.close = 100.0
        c2 = MagicMock(spec=["close"]); c2.close = 101.0
        mock_get.return_value = [c1, c2]
        mock_reg.return_value = 0.75
        tk = _make_token()
        r = client.get("/beta/ETH", headers={"Authorization": f"Bearer {tk}"})
        assert r.status_code == 200
        assert r.json()["beta"] == 0.75

class TestPrices:
    @patch("src.api.get_recent_candles")
    def test_prices_with_data(self, mock_get, client):
        c1 = MagicMock(); c1.symbol = "ETH"; c1.close = 100.0; c1.timestamp.isoformat.return_value = "2025-01-01"
        mock_get.return_value = [c1]
        tk = _make_token()
        r = client.get("/prices/ETH", headers={"Authorization": f"Bearer {tk}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "ETH"

class TestAlerts:
    @patch("src.api.db_get_alerts")
    def test_alerts_with_data(self, mock_get, client):
        a = MagicMock(); a.id = 1; a.pct_change = 0.05; a.timestamp.isoformat.return_value = "2025-01-01"
        mock_get.return_value = [a]
        tk = _make_token()
        r = client.get("/alerts", headers={"Authorization": f"Bearer {tk}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1

class TestExport:
    @patch("src.api.get_recent_candles")
    def test_export_csv(self, mock_get, client):
        c = MagicMock(); c.symbol = "ETH"; c.timestamp.isoformat.return_value = "2025-01-01"; c.open=1; c.high=2; c.low=1; c.close=1.5; c.volume=100
        mock_get.return_value = [c]
        tk = _make_token()
        r = client.get("/export/ETH", headers={"Authorization": f"Bearer {tk}"})
        assert r.status_code == 200
        data = r.json()
        assert data["ticker"] == "ETH"
        assert data["records"] == 1
