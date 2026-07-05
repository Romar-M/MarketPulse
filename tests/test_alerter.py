from src.alerter import AlertHandler


def test_alert_triggered():
    """При изменении >= 1% должно возвращаться сообщение."""
    alerter = AlertHandler(threshold=0.01)
    msg = alerter.trigger(change_pct=-0.015, eth_price=2000.0, btc_price=30000.0)
    assert msg is not None
    assert "-1.50%" in msg
    assert "ETH=2000.00" in msg
    assert "BTC=30000.00" in msg


def test_no_alert_below_threshold():
    """При изменении меньше 1% метод должен вернуть None."""
    alerter = AlertHandler(threshold=0.01)
    msg = alerter.trigger(change_pct=0.005, eth_price=2000.0, btc_price=30000.0)
    assert msg is None