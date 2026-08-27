"""Indicators computed from OANDA candles only. Twelve Data is never an input."""

from __future__ import annotations

from typing import Any


def atr(candles: list[dict[str, Any]], period: int = 14) -> float | None:
    from app.agent.tools import compute_atr

    return compute_atr(candles, period)
