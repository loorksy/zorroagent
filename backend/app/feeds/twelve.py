"""Twelve Data = cross-validate only. NEVER compute indicators from it."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.enums import FeedStatus


class TwelveDataClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.twelve_data_api_key)

    async def health(self) -> tuple[FeedStatus, str]:
        if not self.configured:
            return FeedStatus.DISCONNECTED, "Twelve Data API key not configured"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self.settings.twelve_data_base_url}/quote",
                    params={"symbol": "EUR/USD", "apikey": self.settings.twelve_data_api_key},
                )
            if r.status_code == 200:
                return FeedStatus.CONNECTED, "ok"
            return FeedStatus.DISCONNECTED, f"HTTP {r.status_code}"
        except httpx.HTTPError as exc:
            return FeedStatus.DISCONNECTED, str(exc)

    async def quote(self, symbol: str) -> dict[str, Any] | None:
        if not self.configured:
            return None
        display = symbol.replace("_", "/")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{self.settings.twelve_data_base_url}/quote",
                params={"symbol": display, "apikey": self.settings.twelve_data_api_key},
            )
            if r.status_code != 200:
                return None
            return r.json()
