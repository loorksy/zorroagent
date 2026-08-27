"""OANDA catalog + candles. Sole source of truth for analysis numbers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings
from app.enums import AssetClass, FeedStatus


@dataclass
class InstrumentRow:
    canonical_id: str
    display_symbol: str
    asset_class: AssetClass
    tradable: bool
    pip_location: int | None = None
    display_precision: int | None = None
    extra: dict[str, Any] | None = None


def classify_instrument(name: str, type_: str | None) -> AssetClass:
    n = name.upper()
    t = (type_ or "").upper()
    if "XAU" in n or "XAG" in n or "GOLD" in n or "SILVER" in n or t == "METAL":
        return AssetClass.METAL
    if t in {"CFD", "CFD_INDEX"} or n.startswith("SPX") or n.startswith("NAS") or n.startswith("US30"):
        return AssetClass.INDEX
    if "BTC" in n or "ETH" in n or t == "CRYPTO":
        return AssetClass.CRYPTO
    if t == "CURRENCY" or "_" in n:
        return AssetClass.FOREX
    return AssetClass.OTHER


class OandaClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.oanda_api_key and self.settings.oanda_account_id)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.oanda_api_key}",
            "Accept-Datetime-Format": "RFC3339",
        }

    async def health(self) -> tuple[FeedStatus, str]:
        if not self.configured:
            return FeedStatus.DISCONNECTED, "OANDA API key not configured"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self.settings.oanda_base_url}/v3/accounts/{self.settings.oanda_account_id}",
                    headers=self._headers(),
                )
            if r.status_code == 200:
                return FeedStatus.CONNECTED, "ok"
            return FeedStatus.DISCONNECTED, f"HTTP {r.status_code}"
        except httpx.HTTPError as exc:
            return FeedStatus.DISCONNECTED, str(exc)

    async def fetch_instruments(self) -> list[InstrumentRow]:
        if not self.configured:
            return []
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.settings.oanda_base_url}/v3/accounts/{self.settings.oanda_account_id}/instruments",
                headers=self._headers(),
            )
            r.raise_for_status()
            data = r.json().get("instruments", [])
        rows: list[InstrumentRow] = []
        for item in data:
            name = item.get("name") or ""
            display = item.get("displayName") or name.replace("_", "/")
            rows.append(
                InstrumentRow(
                    canonical_id=name,
                    display_symbol=display,
                    asset_class=classify_instrument(name, item.get("type")),
                    tradable=item.get("type") is not None,
                    pip_location=item.get("pipLocation"),
                    display_precision=item.get("displayPrecision"),
                    extra={"type": item.get("type"), "marginRate": item.get("marginRate")},
                )
            )
        return rows

    async def candles(self, instrument: str, granularity: str, count: int = 200) -> list[dict[str, Any]] | None:
        if not self.configured:
            return None
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"{self.settings.oanda_base_url}/v3/instruments/{instrument}/candles",
                headers=self._headers(),
                params={"granularity": granularity, "count": count, "price": "MBA"},
            )
            if r.status_code != 200:
                return None
            return r.json().get("candles")

    async def price(self, instrument: str) -> dict[str, Any] | None:
        if not self.configured:
            return None
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{self.settings.oanda_base_url}/v3/accounts/{self.settings.oanda_account_id}/pricing",
                headers=self._headers(),
                params={"instruments": instrument},
            )
            if r.status_code != 200:
                return None
            prices = r.json().get("prices") or []
            return prices[0] if prices else None
