"""Twelve Data = cross-validate only. NEVER compute indicators from it.

Credentials resolve through the Settings overlay (get_setting), never raw os.environ.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from app.enums import FeedStatus
from app.runtime_config import get_setting


class TwelveDataClient:
    def __init__(self, *, api_key: str | None = None) -> None:
        self._api_key = api_key

    @property
    def api_key(self) -> str:
        return self._api_key if self._api_key is not None else get_setting("TWELVE_DATA_API_KEY")

    @property
    def base_url(self) -> str:
        return os.environ.get("TWELVE_DATA_BASE_URL") or "https://api.twelvedata.com"

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def health(self) -> tuple[FeedStatus, str]:
        if not self.configured:
            return FeedStatus.DISCONNECTED, "Twelve Data API key not configured"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": "EUR/USD", "apikey": self.api_key},
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
                f"{self.base_url}/quote",
                params={"symbol": display, "apikey": self.api_key},
            )
            if r.status_code != 200:
                return None
            return r.json()
