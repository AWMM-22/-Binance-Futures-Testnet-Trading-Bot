from __future__ import annotations

from typing import Any, Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


BANNER = r"""
 ____  _                   _           ____        _
|  _ \(_)_ __   ___   __ _| |_ ___    | __ )  ___ | |_ ___
| |_) | | '_ \ / _ \ / _` | __/ _ \   |  _ \ / _ \| __/ __|
|  __/| | | | | (_) | (_| | || (_) |  | |_) | (_) | |_\__ \
|_|   |_|_| |_|\___/ \__,_|\__\___/   |____/ \___/ \__|___/
"""


def print_banner() -> None:
    console.print(Panel.fit(BANNER, title="Binance Futures Testnet Bot", style="bold cyan"))


def print_env_banner() -> None:
    console.print(Panel.fit("TESTNET MODE", style="bold magenta"))


def order_summary(data: dict[str, Any]) -> None:
    lines = [
        f"Symbol: {data['symbol']}",
        f"Side: {data['side']}",
        f"Type: {data['type']}",
        f"Quantity: {data['quantity']}",
    ]
    if data.get("price"):
        lines.append(f"Price: {data['price']}")
    if data.get("stopPrice"):
        lines.append(f"Stop Price: {data['stopPrice']}")
    console.print(Panel.fit("\n".join(lines), title="ORDER SUMMARY", style="bold blue"))


def order_result(result: dict[str, Any], latency_ms: float) -> None:
    avg_price = result.get("avgPrice") or result.get("price") or "N/A"
    lines = [
        f"Order ID: {result.get('orderId')}",
        f"Status: {result.get('status')}",
        f"Executed Qty: {result.get('executedQty')}",
        f"Average Price: {avg_price}",
        f"Execution Time: {latency_ms:.0f}ms",
    ]
    console.print(Panel.fit("\n".join(lines), title="SUCCESS", style="bold green"))


def error_panel(message: str) -> None:
    console.print(Panel.fit(message, title="ERROR", style="bold red"))


def info_panel(title: str, message: str) -> None:
    console.print(Panel.fit(message, title=title, style="bold cyan"))


def balance_table(rows: Iterable[dict[str, Any]]) -> None:
    table = Table(title="Account Balance", header_style="bold cyan")
    table.add_column("Asset")
    table.add_column("Balance")
    table.add_column("Available")
    for row in rows:
        table.add_row(str(row.get("asset")), str(row.get("balance")), str(row.get("availableBalance")))
    console.print(table)


def positions_table(rows: Iterable[dict[str, Any]]) -> None:
    table = Table(title="Open Positions", header_style="bold cyan")
    table.add_column("Symbol")
    table.add_column("Position")
    table.add_column("Entry Price")
    table.add_column("Unrealized PnL")
    for row in rows:
        if float(row.get("positionAmt", 0)) == 0:
            continue
        table.add_row(
            str(row.get("symbol")),
            str(row.get("positionAmt")),
            str(row.get("entryPrice")),
            str(row.get("unRealizedProfit")),
        )
    console.print(table)


def history_table(rows: Iterable[dict[str, Any]]) -> None:
    table = Table(title="Recent Orders", header_style="bold cyan")
    table.add_column("Order ID")
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Qty")
    for row in rows:
        table.add_row(
            str(row.get("orderId")),
            str(row.get("symbol")),
            str(row.get("side")),
            str(row.get("type")),
            str(row.get("status")),
            str(row.get("origQty")),
        )
    console.print(table)
