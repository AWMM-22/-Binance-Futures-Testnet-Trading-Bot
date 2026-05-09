import pytest

from bot.validators import ExchangeInfoValidator


def sample_exchange_info() -> dict:
    return {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "filters": [
                    {"filterType": "LOT_SIZE", "minQty": "0.001", "stepSize": "0.001"},
                    {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                    {"filterType": "MIN_NOTIONAL", "notional": "5"},
                ],
            }
        ]
    }


def test_validate_order_rounding():
    validator = ExchangeInfoValidator(sample_exchange_info())
    result = validator.validate_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        quantity=0.0027,
        price=30000.123,
        stop_price=None,
    )
    assert result.quantity == "0.002"
    assert result.price == "30000.1"


def test_invalid_symbol():
    validator = ExchangeInfoValidator(sample_exchange_info())
    with pytest.raises(Exception):
        validator.validate_order(
            symbol="BAD",
            side="BUY",
            order_type="MARKET",
            quantity=0.001,
            price=None,
            stop_price=None,
        )
