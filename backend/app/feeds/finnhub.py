"""Finnhub news ranked by impact. Missing provider = gate UNAVAILABLE (not silent pass).

Credentials resolve through the Settings overlay (get_setting), never raw os.environ.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

from app.enums import FeedStatus
from app.runtime_config import get_setting

IMPACT_RANK = {"1": "low", "2": "medium", "3": "high"}


class FinnhubClient:
    def __init__(self, *, api_key: str | None = None) -> None:
        self._api_key = api_key

    @property
    def api_key(self) -> str:
        return self._api_key if self._api_key is not None else get_setting("FINNHUB_API_KEY")

    @property
    def base_url(self) -> str:
        return os.environ.get("FINNHUB_BASE_URL") or "https://finnhub.io/api/v1"

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def health(self) -> tuple[FeedStatus, str]:
        if not self.configured:
            return FeedStatus.DISCONNECTED, "Finnhub API key not configured"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self.base_url}/news",
                    params={"category": "forex", "token": self.api_key},
                )
            if r.status_code == 200:
                return FeedStatus.CONNECTED, "ok"
            return FeedStatus.DISCONNECTED, f"HTTP {r.status_code}"
        except httpx.HTTPError as exc:
            return FeedStatus.DISCONNECTED, str(exc)

    async def calendar(self) -> list[dict[str, Any]]:
        if not self.configured:
            return []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self.base_url}/calendar/economic",
                params={"from": today, "to": today, "token": self.api_key},
            )
            if r.status_code != 200:
                return []
            return r.json().get("economicCalendar") or []

    def blocking_event(self, events: list[dict[str, Any]], now: datetime, window_minutes: int = 30) -> dict[str, Any] | None:
        for ev in events:
            impact = str(ev.get("impact") or "")
            rank = IMPACT_RANK.get(impact, str(ev.get("impact") or "")).lower()
            if rank != "high":
                continue
            raw = ev.get("time") or ev.get("datetime")
            if not raw:
                continue
            try:
                if isinstance(raw, (int, float)):
                    ts = datetime.fromtimestamp(int(raw), tz=timezone.utc)
                else:
                    ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            delta = abs((ts - now).total_seconds()) / 60
            if delta <= window_minutes:
                return {"title": ev.get("event") or ev.get("title"), "time": str(raw), "impact": "high"}
        return None
