from __future__ import annotations

import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bot.client import FuturesClient
from bot.config import get_settings
from bot.exceptions import ApiError, NetworkError, TradingBotError, ValidationError
from bot.orders import OrderRequest, place_order
from bot.validators import ExchangeInfoValidator


class OrderPayload(BaseModel):
    symbol: str
    side: str
    type: str
    quantity: float
    price: float | None = None
    stopPrice: float | None = None
    dry_run: bool = False


load_dotenv()
settings = get_settings()
client = FuturesClient(settings)
exchange_info = client.exchange_info()
validator = ExchangeInfoValidator(exchange_info)
has_api_credentials = bool(settings.api_key and settings.api_secret)


def _sorted_market_tickers(limit: int) -> list[dict[str, Any]]:
    tickers = client.market_tickers()

    def quote_volume(row: dict[str, Any]) -> float:
        try:
            return float(row.get("quoteVolume", 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    tickers.sort(key=quote_volume, reverse=True)
    return tickers[:limit]

app = FastAPI(title="Trading Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    start = time.perf_counter()
    try:
        result = client.ping()
    except TradingBotError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    latency_ms = (time.perf_counter() - start) * 1000
    return {"ok": True, "latency_ms": round(latency_ms, 2), "result": result}


@app.get("/balance")
def balance() -> list[dict[str, Any]]:
    if not has_api_credentials:
        return []
    try:
        return list(client.account_balance())
    except TradingBotError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/positions")
def positions() -> list[dict[str, Any]]:
    if not has_api_credentials:
        return []
    try:
        rows = client.positions()
        return [row for row in rows if float(row.get("positionAmt", 0)) != 0]
    except TradingBotError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/history")
def history(limit: int = 20, symbol: str = "BTCUSDT") -> list[dict[str, Any]]:
    if not has_api_credentials:
        return []
    try:
        return list(client.order_history(symbol=symbol, limit=limit))
    except TradingBotError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/market/summary")
def market_summary(limit: int = 5) -> list[dict[str, Any]]:
    rows = []
    for row in _sorted_market_tickers(limit):
        rows.append(
            {
                "symbol": row.get("symbol"),
                "lastPrice": row.get("lastPrice"),
                "priceChangePercent": row.get("priceChangePercent"),
                "quoteVolume": row.get("quoteVolume"),
            }
        )
    return rows


@app.get("/market/trades")
def market_trades(symbol: str = "BTCUSDT", limit: int = 10) -> list[dict[str, Any]]:
    rows = []
    for row in client.recent_trades(symbol=symbol, limit=limit):
        rows.append(
            {
                "id": row.get("id"),
                "price": row.get("price"),
                "qty": row.get("qty"),
                "time": row.get("time"),
                "isBuyerMaker": row.get("isBuyerMaker"),
            }
        )
    return rows


@app.get("/market/symbol")
def market_symbol(symbol: str) -> dict[str, Any]:
    symbol = symbol.strip().upper()
    validator.validate_symbol(symbol)
    try:
        snapshot = client.symbol_snapshot(symbol)
    except TradingBotError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    symbol_info = next(
        (item for item in exchange_info.get("symbols", []) if item.get("symbol") == symbol),
        {},
    )
    return {
        **snapshot,
        "status": symbol_info.get("status"),
        "contractType": symbol_info.get("contractType"),
        "baseAsset": symbol_info.get("baseAsset"),
        "quoteAsset": symbol_info.get("quoteAsset"),
        "pricePrecision": symbol_info.get("pricePrecision"),
        "quantityPrecision": symbol_info.get("quantityPrecision"),
    }


@app.post("/orders")
def create_order(payload: OrderPayload) -> dict[str, Any]:
    if not has_api_credentials:
        raise HTTPException(
            status_code=400,
            detail="Binance API credentials are required for order placement.",
        )
    try:
        request = OrderRequest(
            symbol=payload.symbol,
            side=payload.side,
            type=payload.type,
            quantity=payload.quantity,
            price=payload.price,
            stopPrice=payload.stopPrice,
        )
        result = place_order(client, validator, request, payload.dry_run)
        return {"order": result.response, "latency_ms": result.latency_ms}
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ApiError, NetworkError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except TradingBotError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
