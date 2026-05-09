from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from .constants import OrderSide, OrderType, TIME_IN_FORCE_GTC
from .exceptions import ValidationError
from .utils import timed_call
from .validators import ExchangeInfoValidator


class OrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    order_type: OrderType = Field(alias="type")
    quantity: float
    price: float | None = None
    stop_price: float | None = Field(default=None, alias="stopPrice")

    model_config = {"populate_by_name": True}


@dataclass
class OrderResult:
    response: dict[str, Any]
    latency_ms: float


def build_order_payload(request: OrderRequest, validator: ExchangeInfoValidator) -> dict[str, Any]:
    validated = validator.validate_order(
        symbol=request.symbol,
        side=request.side.value,
        order_type=request.order_type.value,
        quantity=request.quantity,
        price=request.price,
        stop_price=request.stop_price,
    )

    payload: dict[str, Any] = {
        "symbol": validated.symbol,
        "side": validated.side,
        "type": validated.order_type,
        "quantity": validated.quantity,
    }
    if validated.price:
        payload["price"] = validated.price
    if validated.stop_price:
        payload["stopPrice"] = validated.stop_price
    if validated.order_type == OrderType.LIMIT.value:
        payload["timeInForce"] = TIME_IN_FORCE_GTC
    return payload


def place_order(
    client: Any,
    validator: ExchangeInfoValidator,
    request: OrderRequest,
    dry_run: bool,
) -> OrderResult:
    payload = build_order_payload(request, validator)
    if dry_run:
        simulated = {
            "orderId": "DRYRUN-0001",
            "status": "DRY_RUN",
            "executedQty": "0",
            "avgPrice": "0",
            "symbol": payload["symbol"],
            "side": payload["side"],
            "type": payload["type"],
        }
        return OrderResult(simulated, 0.0)

    if payload.get("type") == OrderType.LIMIT.value and not payload.get("price"):
        raise ValidationError("Price is required for LIMIT orders")

    response, latency_ms = timed_call(client.create_order, payload)
    return OrderResult(response, latency_ms)
