import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.api import app
    return TestClient(app)


class TestAuth:
    def test_login_success(self, client):
        r = client.post("/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_failure(self, client):
        r = client.post("/login", json={"username": "x", "password": "x"})
        assert r.status_code == 401


class TestCandles:
    @patch("src.api.get_recent_candles")
    def test_candles_empty(self, mock_get, client):
        mock_get.return_value = []
        r = client.get("/candles/ETH")
        assert r.status_code == 200
        assert r.json() == []

    @patch("src.api.get_recent_candles")
    def test_candles_with_data(self, mock_get, client):
        c = MagicMock()
        c.id = 1
        c.symbol = "ETHUSDT"
        c.open = 1.0
        c.high = 2.0
        c.low = 1.0
        c.close = 1.5
        c.volume = 100.0
        c.timestamp.isoformat.return_value = "2025-01-01T00:00:00"
        mock_get.return_value = [c]
        r = client.get("/candles/ETH")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "ETHUSDT"


class TestAlerts:
    @patch("src.api.db_get_alerts")
    def test_alerts_with_data(self, mock_get, client):
        a = MagicMock()
        a.id = 1
        a.symbol = "ETHUSDT"
        a.alert_type = "divergence"
        a.message = "test alert"
        a.price = 2000.0
        a.timestamp.isoformat.return_value = "2025-01-01T00:00:00"
        mock_get.return_value = [a]
        r = client.get("/alerts")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "ETHUSDT"


class TestRegression:
    @patch("src.api.get_recent_candles")
    def test_regression_no_data(self, mock_get, client):
        mock_get.return_value = []
        assert client.get("/regression/ETH").status_code == 404

    @patch("src.api.get_recent_candles")
    def test_regression_with_data(self, mock_get, client):
        c1 = MagicMock(spec=["close"]); c1.close = 100.0
        c2 = MagicMock(spec=["close"]); c2.close = 101.0
        mock_get.return_value = [c1, c2]
        r = client.get("/regression/ETH")
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "ETH"
        assert "slope" in data
        assert "trend" in data
