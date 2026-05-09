from __future__ import annotations

import sys
from typing import Any, Optional

import typer
from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from bot.client import FuturesClient
from bot.config import get_settings
from bot.exceptions import TradingBotError
from bot.formatter import (
    balance_table,
    error_panel,
    history_table,
    info_panel,
    order_result,
    order_summary,
    positions_table,
    print_banner,
    print_env_banner,
)
from bot.logging_config import init_logging
from bot.orders import OrderRequest, place_order
from bot.validators import ExchangeInfoValidator

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _get_state(ctx: typer.Context) -> dict[str, Any]:
    if ctx.obj is None:
        ctx.obj = {}
    return ctx.obj


@app.callback()
def main(ctx: typer.Context, verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    load_dotenv()
    init_logging(verbose)
    print_banner()
    print_env_banner()

    settings = get_settings()
    client = FuturesClient(settings)
    exchange_info = client.exchange_info()
    validator = ExchangeInfoValidator(exchange_info)

    state = _get_state(ctx)
    state["client"] = client
    state["validator"] = validator


@app.command()
def order(
    ctx: typer.Context,
    symbol: str = typer.Option(..., "--symbol"),
    side: str = typer.Option(..., "--side"),
    order_type: str = typer.Option(..., "--type"),
    quantity: float = typer.Option(..., "--quantity"),
    price: Optional[float] = typer.Option(None, "--price"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    state = _get_state(ctx)
    client: FuturesClient = state["client"]
    validator: ExchangeInfoValidator = state["validator"]

    try:
        request = OrderRequest(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
            price=price,
            stopPrice=stop_price,
        )
        payload = {
            "symbol": request.symbol,
            "side": request.side.value,
            "type": request.order_type.value,
            "quantity": request.quantity,
            "price": request.price,
            "stopPrice": request.stop_price,
        }
        order_summary(payload)
        if dry_run:
            info_panel("DRY RUN", "Order will not be sent to Binance")
        info_panel("STATUS", "Submitting order...")
        result = place_order(client, validator, request, dry_run)
        order_result(result.response, result.latency_ms)
    except KeyboardInterrupt:
        error_panel("Interrupted by user")
        raise typer.Exit(code=1)
    except TradingBotError as exc:
        error_panel(str(exc))
        raise typer.Exit(code=1)
    except PydanticValidationError as exc:
        error_panel(str(exc))
        raise typer.Exit(code=1)
    except Exception as exc:  # pragma: no cover - safety net
        logger.exception("Unexpected error")
        error_panel(f"Unexpected error: {exc}")
        raise typer.Exit(code=1)


@app.command()
def balance(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    client: FuturesClient = state["client"]
    try:
        rows = client.account_balance()
        balance_table(rows)
    except KeyboardInterrupt:
        error_panel("Interrupted by user")
        raise typer.Exit(code=1)
    except TradingBotError as exc:
        error_panel(str(exc))
        raise typer.Exit(code=1)


@app.command()
def positions(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    client: FuturesClient = state["client"]
    try:
        rows = client.positions()
        positions_table(rows)
    except KeyboardInterrupt:
        error_panel("Interrupted by user")
        raise typer.Exit(code=1)
    except TradingBotError as exc:
        error_panel(str(exc))
        raise typer.Exit(code=1)


@app.command()
def history(ctx: typer.Context, limit: int = typer.Option(20, "--limit")) -> None:
    state = _get_state(ctx)
    client: FuturesClient = state["client"]
    try:
        rows = client.order_history(limit=limit)
        history_table(rows)
    except KeyboardInterrupt:
        error_panel("Interrupted by user")
        raise typer.Exit(code=1)
    except TradingBotError as exc:
        error_panel(str(exc))
        raise typer.Exit(code=1)


@app.command()
def ping(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    client: FuturesClient = state["client"]
    try:
        result = client.ping()
        info_panel("PING", f"Success: {result}")
    except KeyboardInterrupt:
        error_panel("Interrupted by user")
        raise typer.Exit(code=1)
    except TradingBotError as exc:
        error_panel(str(exc))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required")
    app()
