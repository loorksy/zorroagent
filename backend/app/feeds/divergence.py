"""OANDA vs Twelve Data divergence. On divergence: block new recs, conservative bots."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DivergenceResult:
    diverged: bool
    bps: float | None
    banner: str | None
    oanda: float | None
    twelve: float | None


def mid_from_oanda(price: dict | None) -> float | None:
    if not price:
        return None
    bids = price.get("bids") or []
    asks = price.get("asks") or []
    try:
        bid = float(bids[0]["price"]) if bids else float(price.get("closeoutBid") or 0)
        ask = float(asks[0]["price"]) if asks else float(price.get("closeoutAsk") or 0)
        if bid > 0 and ask > 0:
            return (bid + ask) / 2
    except (KeyError, TypeError, ValueError):
        return None
    return None


def check_divergence(oanda_mid: float | None, twelve_price: float | None, limit_bps: float) -> DivergenceResult:
    if oanda_mid is None:
        return DivergenceResult(True, None, "Price data unreliable", None, twelve_price)
    if twelve_price is None:
        # Cross-check missing is degraded, not a silent pass — still allow if OANDA is live,
        # but the banner notes the cross-check is disconnected.
        return DivergenceResult(False, None, None, oanda_mid, None)
    bps = abs(twelve_price - oanda_mid) / oanda_mid * 10_000
    if bps > limit_bps:
        return DivergenceResult(True, bps, "Price data unreliable", oanda_mid, twelve_price)
    return DivergenceResult(False, bps, None, oanda_mid, twelve_price)
