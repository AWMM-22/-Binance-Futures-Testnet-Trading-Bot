from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from pydantic import BaseModel

from .constants import OrderSide, OrderType
from .exceptions import ValidationError
from .utils import format_decimal, quantize_to_step, to_decimal


class SymbolRules(BaseModel):
    symbol: str
    step_size: Decimal
    tick_size: Decimal
    min_qty: Decimal
    min_notional: Decimal | None = None


class ValidatedOrder(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: str
    price: str | None = None
    stop_price: str | None = None


class ExchangeInfoValidator:
    def __init__(self, exchange_info: dict[str, Any]):
        self._symbols = self._parse_exchange_info(exchange_info)

    @staticmethod
    def _parse_exchange_info(exchange_info: dict[str, Any]) -> Dict[str, SymbolRules]:
        symbols: Dict[str, SymbolRules] = {}
        for symbol_info in exchange_info.get("symbols", []):
            symbol = symbol_info.get("symbol")
            if not symbol:
                continue
            filters = {item["filterType"]: item for item in symbol_info.get("filters", [])}
            lot_filter = filters.get("LOT_SIZE") or filters.get("MARKET_LOT_SIZE")
            price_filter = filters.get("PRICE_FILTER")
            min_notional = filters.get("MIN_NOTIONAL")

            if not lot_filter or not price_filter:
                continue

            step_size = to_decimal(lot_filter.get("stepSize"))
            min_qty = to_decimal(lot_filter.get("minQty"))
            tick_size = to_decimal(price_filter.get("tickSize"))
            min_notional_value = None
            if min_notional and min_notional.get("notional"):
                min_notional_value = to_decimal(min_notional.get("notional"))

            symbols[symbol] = SymbolRules(
                symbol=symbol,
                step_size=step_size,
                tick_size=tick_size,
                min_qty=min_qty,
                min_notional=min_notional_value,
            )
        return symbols

    def validate_symbol(self, symbol: str) -> None:
        if symbol not in self._symbols:
            raise ValidationError(f"Invalid symbol: {symbol}")

    def validate_side(self, side: str) -> None:
        if side not in {OrderSide.BUY.value, OrderSide.SELL.value}:
            raise ValidationError("Side must be BUY or SELL")

    def validate_order_type(self, order_type: str) -> None:
        if order_type not in {item.value for item in OrderType}:
            raise ValidationError("Order type must be MARKET, LIMIT, or STOP_MARKET")

    def _validate_quantity(self, rules: SymbolRules, quantity: Decimal) -> Decimal:
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        adjusted = quantize_to_step(quantity, rules.step_size)
        if adjusted < rules.min_qty:
            raise ValidationError("Quantity is below minimum")
        return adjusted

    def _validate_price(self, rules: SymbolRules, price: Decimal) -> Decimal:
        if price <= 0:
            raise ValidationError("Price must be greater than 0")
        return quantize_to_step(price, rules.tick_size)

    def validate_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None,
        stop_price: float | None,
    ) -> ValidatedOrder:
        self.validate_symbol(symbol)
        self.validate_side(side)
        self.validate_order_type(order_type)

        rules = self._symbols[symbol]
        qty_decimal = self._validate_quantity(rules, to_decimal(quantity))

        price_decimal = None
        if order_type == OrderType.LIMIT.value:
            if price is None:
                raise ValidationError("Price is required for LIMIT orders")
            price_decimal = self._validate_price(rules, to_decimal(price))
        elif price is not None:
            price_decimal = self._validate_price(rules, to_decimal(price))

        stop_decimal = None
        if order_type == OrderType.STOP_MARKET.value:
            if stop_price is None:
                raise ValidationError("Stop price is required for STOP_MARKET orders")
            stop_decimal = self._validate_price(rules, to_decimal(stop_price))
        elif stop_price is not None:
            stop_decimal = self._validate_price(rules, to_decimal(stop_price))

        if rules.min_notional and price_decimal:
            notional = price_decimal * qty_decimal
            if notional < rules.min_notional:
                raise ValidationError("Notional value is below minimum")

        return ValidatedOrder(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=format_decimal(qty_decimal),
            price=format_decimal(price_decimal) if price_decimal else None,
            stop_price=format_decimal(stop_decimal) if stop_decimal else None,
        )
