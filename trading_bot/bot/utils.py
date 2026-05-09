from __future__ import annotations

import time
from contextlib import contextmanager
from decimal import Decimal, ROUND_DOWN
from typing import Any, Callable, Generator, Tuple, TypeVar

T = TypeVar("T")


def to_decimal(value: float | str | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step == 0:
        return value
    scaled = (value / step).to_integral_value(rounding=ROUND_DOWN)
    return scaled * step


def format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    as_str = format(normalized, "f")
    if "." in as_str:
        as_str = as_str.rstrip("0").rstrip(".")
    return as_str or "0"


@contextmanager
def latency_timer() -> Generator[Callable[[], float], None, None]:
    start = time.perf_counter()

    def elapsed_ms() -> float:
        return (time.perf_counter() - start) * 1000

    yield elapsed_ms


def timed_call(func: Callable[..., T], *args: Any, **kwargs: Any) -> Tuple[T, float]:
    with latency_timer() as elapsed:
        result = func(*args, **kwargs)
    return result, elapsed()
