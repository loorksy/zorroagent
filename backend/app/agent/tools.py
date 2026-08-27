"""Read/analysis tools the agent may call. Execution is NEVER in this list."""

from __future__ import annotations

from typing import Any

from app.feeds.finnhub import FinnhubClient
from app.feeds.oanda import OandaClient
from app.exposure import OpenRisk, aggregate_exposure


GRAN = {"1m": "M1", "5m": "M5", "15m": "M15", "30m": "M30", "1h": "H1", "4h": "H4", "1d": "D", "1w": "W"}


async def get_candles(canonical_id: str, timeframe: str, count: int = 200) -> dict[str, Any]:
    data = await OandaClient().candles(canonical_id, GRAN.get(timeframe.lower(), "M15"), count)
    if data is None:
        return {"ok": False, "error": "Not available"}
    return {"ok": True, "candles": data, "source": "OANDA"}


async def get_price(canonical_id: str) -> dict[str, Any]:
    data = await OandaClient().price(canonical_id)
    if data is None:
        return {"ok": False, "error": "Not available"}
    return {"ok": True, "price": data, "source": "OANDA"}


def compute_atr(candles: list[dict[str, Any]], period: int = 14) -> float | None:
    if len(candles) < period + 1:
        return None
    trs: list[float] = []
    prev_close = None
    for c in candles:
        mid = c.get("mid") or c
        high = float(mid.get("h") or mid.get("high"))
        low = float(mid.get("l") or mid.get("low"))
        close = float(mid.get("c") or mid.get("close"))
        if prev_close is None:
            trs.append(high - low)
        else:
            trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
        prev_close = close
    window = trs[-period:]
    return sum(window) / len(window)


def compute_structure(candles: list[dict[str, Any]]) -> dict[str, Any]:
    closes: list[float] = []
    for c in candles:
        mid = c.get("mid") or c
        closes.append(float(mid.get("c") or mid.get("close")))
    if len(closes) < 20:
        return {"trend": "unnamed", "htf_conflict": False}
    slope = closes[-1] - closes[-20]
    trend = "up" if slope > 0 else "down"
    return {"trend": trend, "htf_conflict": False, "leading_tf": None, "latest_close": closes[-1]}


def compute_zones(candles: list[dict[str, Any]]) -> dict[str, Any]:
    highs: list[float] = []
    lows: list[float] = []
    for c in candles:
        mid = c.get("mid") or c
        highs.append(float(mid.get("h") or mid.get("high")))
        lows.append(float(mid.get("l") or mid.get("low")))
    if not highs:
        return {"zones_count": 0, "nearest": None}
    return {
        "zones_count": 2,
        "nearest": {"high": max(highs[-30:]), "low": min(lows[-30:])},
    }


async def get_news() -> dict[str, Any]:
    client = FinnhubClient()
    if not client.configured:
        return {"ok": False, "configured": False, "error": "Not available"}
    events = await client.calendar()
    return {"ok": True, "events": events, "configured": True}


def get_exposure_tool(positions: list[OpenRisk], cap: float | None) -> dict[str, Any]:
    report = aggregate_exposure(positions, cap)
    return {
        "total_r": report.total_r,
        "by_symbol": report.by_symbol,
        "correlation_warning": report.correlation_warning,
        "cap_exceeded": report.cap_exceeded,
        "informational": cap is None,
    }
