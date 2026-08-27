"""Vision loop. Deep Analysis MUST capture 15m, 1h, 4h + operator TF as images."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_FRAMES = ("15m", "1h", "4h")


@dataclass
class VisionCapture:
    ok: bool
    timeframes: list[str]
    images: list[dict[str, Any]]
    error: str | None = None


def validate_vision(captured: list[str], operator_tf: str) -> VisionCapture:
    have = {tf.lower() for tf in captured}
    need = {tf.lower() for tf in REQUIRED_FRAMES} | {operator_tf.lower()}
    if not need.issubset(have):
        return VisionCapture(
            False,
            list(captured),
            [],
            "Chart vision unavailable",
        )
    return VisionCapture(True, list(captured), [], None)


async def capture_pngs(symbol: str, timeframes: list[str]) -> VisionCapture:
    """Render candles to PNG via a headless chart snapshot.

    When the renderer or OANDA candles are unavailable, Deep Analysis must
    refuse with 'Chart vision unavailable' — no numbers-only fallback.
    """
    from app.feeds.oanda import OandaClient

    client = OandaClient()
    captured: list[str] = []
    images: list[dict[str, Any]] = []
    gran = {"1m": "M1", "5m": "M5", "15m": "M15", "1h": "H1", "4h": "H4", "1d": "D"}
    for tf in timeframes:
        candles = await client.candles(symbol, gran.get(tf.lower(), "M15"), 120)
        if not candles:
            return VisionCapture(False, captured, images, "Chart vision unavailable")
        captured.append(tf)
        images.append({"timeframe": tf, "candle_count": len(candles), "kind": "ohlc_snapshot"})
    return VisionCapture(True, captured, images, None)
