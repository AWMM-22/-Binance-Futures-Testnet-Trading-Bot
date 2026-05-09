from __future__ import annotations

from typing import Any, Iterable

import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException, BinanceRequestException
from loguru import logger
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import Settings
from .exceptions import ApiError, NetworkError


class FuturesClient:
    def __init__(self, settings: Settings, retries: int = 3) -> None:
        self._client = Client(settings.api_key, settings.api_secret)
        self._client.FUTURES_URL = f"{settings.base_url}/fapi"
        self._retryer = Retrying(
            stop=stop_after_attempt(retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            retry=retry_if_exception_type(
                (BinanceRequestException, requests.exceptions.RequestException, TimeoutError)
            ),
            reraise=True,
            before_sleep=before_sleep_log(logger, "WARNING"),
        )

    def _call(self, func, *args, **kwargs):
        try:
            return self._retryer(func, *args, **kwargs)
        except BinanceAPIException as exc:
            raise ApiError(f"Binance API error: {exc.message}") from exc
        except BinanceOrderException as exc:
            raise ApiError(f"Order error: {exc.message}") from exc
        except BinanceRequestException as exc:
            raise NetworkError(f"Request error: {exc.message}") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError("Network error") from exc

    def ping(self) -> dict[str, Any]:
        logger.debug("Ping Binance Futures")
        result = self._call(self._client.futures_ping)
        logger.debug("Ping response: {}", result)
        return result

    def exchange_info(self) -> dict[str, Any]:
        logger.debug("Fetch exchange info")
        result = self._call(self._client.futures_exchange_info)
        logger.debug("Exchange info symbols: {}", len(result.get("symbols", [])))
        return result

    def market_tickers(self) -> list[dict[str, Any]]:
        logger.debug("Fetch market tickers")
        result = self._call(self._client.futures_ticker)
        logger.debug("Market tickers entries: {}", len(result))
        return list(result)

    def symbol_snapshot(self, symbol: str) -> dict[str, Any]:
        logger.debug("Fetch symbol snapshot for {}", symbol)
        ticker = self._call(self._client.futures_symbol_ticker, symbol=symbol)
        stats = self._call(self._client.futures_ticker, symbol=symbol)
        mark_price = self._call(self._client.futures_mark_price, symbol=symbol)
        open_interest = self._call(self._client.futures_open_interest, symbol=symbol)
        snapshot = {
            "symbol": symbol,
            "lastPrice": ticker.get("price"),
            "priceChangePercent": stats.get("priceChangePercent"),
            "priceChange": stats.get("priceChange"),
            "highPrice": stats.get("highPrice"),
            "lowPrice": stats.get("lowPrice"),
            "openPrice": stats.get("openPrice"),
            "volume": stats.get("volume"),
            "quoteVolume": stats.get("quoteVolume"),
            "weightedAvgPrice": stats.get("weightedAvgPrice"),
            "markPrice": mark_price.get("markPrice"),
            "indexPrice": mark_price.get("indexPrice"),
            "fundingRate": mark_price.get("lastFundingRate"),
            "nextFundingTime": mark_price.get("nextFundingTime"),
            "openInterest": open_interest.get("openInterest"),
        }
        logger.debug("Symbol snapshot ready for {}", symbol)
        return snapshot

    def recent_trades(self, symbol: str, limit: int = 10) -> list[dict[str, Any]]:
        logger.debug("Fetch recent trades for {}", symbol)
        result = self._call(self._client.futures_recent_trades, symbol=symbol, limit=limit)
        logger.debug("Recent trades entries: {}", len(result))
        return list(result)

    def account_balance(self) -> Iterable[dict[str, Any]]:
        logger.debug("Fetch account balance")
        result = self._call(self._client.futures_account_balance)
        logger.debug("Balance entries: {}", len(result))
        return result

    def positions(self) -> Iterable[dict[str, Any]]:
        logger.debug("Fetch open positions")
        result = self._call(self._client.futures_position_information)
        logger.debug("Positions entries: {}", len(result))
        return result

    def order_history(self, symbol: str, limit: int = 20) -> Iterable[dict[str, Any]]:
        logger.debug("Fetch order history")
        result = self._call(self._client.futures_get_all_orders, symbol=symbol, limit=limit)
        logger.debug("Order history entries: {}", len(result))
        return result

    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Create order: {}", payload)
        result = self._call(self._client.futures_create_order, **payload)
        logger.debug("Create order response: {}", result)
        return result
