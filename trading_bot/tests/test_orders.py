from decimal import Decimal

from bot.orders import OrderRequest, build_order_payload, place_order
from bot.utils import format_decimal, quantize_to_step
from bot.validators import ExchangeInfoValidator


def sample_exchange_info() -> dict:
    return {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "filters": [
                    {"filterType": "LOT_SIZE", "minQty": "0.001", "stepSize": "0.001"},
                    {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                ],
            }
        ]
    }


class FakeClient:
    def create_order(self, payload):
        return {"orderId": "1", "status": "FILLED", "executedQty": payload["quantity"]}


def test_build_order_payload_limit():
    validator = ExchangeInfoValidator(sample_exchange_info())
    request = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        type="LIMIT",
        quantity=0.002,
        price=30000.12,
    )
    payload = build_order_payload(request, validator)
    assert payload["type"] == "LIMIT"
    assert payload["timeInForce"] == "GTC"


def test_place_order_dry_run():
    validator = ExchangeInfoValidator(sample_exchange_info())
    request = OrderRequest(
        symbol="BTCUSDT",
        side="BUY",
        type="MARKET",
        quantity=0.002,
    )
    result = place_order(FakeClient(), validator, request, dry_run=True)
    assert result.response["status"] == "DRY_RUN"


def test_utils_quantize_and_format():
    value = quantize_to_step(Decimal("1.2345"), Decimal("0.01"))
    assert format_decimal(value) == "1.23"
