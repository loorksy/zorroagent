"""MetaApi execution. SL always attached. Idempotent. Never used for analysis candles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings
from app.enums import Direction, FeedStatus
from app.symbols.alias import AliasResolution


@dataclass
class OrderRequest:
    idempotency_key: str
    execution_symbol: str
    direction: Direction
    lots: float
    stop_loss: float
    take_profit: float | None
    comment: str


@dataclass
class OrderResult:
    ok: bool
    broker_order_id: str | None
    fill_price: float | None
    error: str | None


class MetaApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.metaapi_token)

    async def health(self) -> tuple[FeedStatus, str]:
        if not self.configured:
            return FeedStatus.DISCONNECTED, "MetaApi token not configured"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts",
                    headers={"auth-token": self.settings.metaapi_token},
                )
            if r.status_code < 500:
                return (FeedStatus.CONNECTED if r.status_code < 400 else FeedStatus.DISCONNECTED, f"HTTP {r.status_code}")
            return FeedStatus.DISCONNECTED, f"HTTP {r.status_code}"
        except httpx.HTTPError as exc:
            return FeedStatus.DISCONNECTED, str(exc)

    async def test_symbol(self, account_id: str, token: str, symbol: str) -> tuple[bool, str]:
        if not token:
            return False, "MetaApi token missing"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"https://mt-client-api-v1.{self.settings.metaapi_region}.agiliumtrade.ai"
                    f"/users/current/accounts/{account_id}/symbols/{symbol}/specification",
                    headers={"auth-token": token},
                )
            if r.status_code == 200:
                return True, "ok"
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
        except httpx.HTTPError as exc:
            return False, str(exc)

    async def place(self, account_id: str, token: str, alias: AliasResolution, order: OrderRequest) -> OrderResult:
        if not alias.can_execute:
            return OrderResult(False, None, None, alias.error or "Unmapped: execute NEVER.")
        if order.stop_loss is None or order.stop_loss <= 0:
            return OrderResult(False, None, None, "SL always attached; refusing order without stop loss.")
        if order.lots <= 0:
            return OrderResult(False, None, None, "Lot size must be positive.")
        if not self.configured and not token:
            return OrderResult(False, None, None, "MetaApi disconnected. Analysis still works; execution refused.")
        payload: dict[str, Any] = {
            "symbol": alias.execution_symbol,
            "actionType": "ORDER_TYPE_BUY" if order.direction == Direction.BUY else "ORDER_TYPE_SELL",
            "volume": order.lots,
            "stopLoss": order.stop_loss,
            "clientId": order.idempotency_key,
            "comment": order.comment[:30],
        }
        if order.take_profit:
            payload["takeProfit"] = order.take_profit
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    f"https://mt-client-api-v1.{self.settings.metaapi_region}.agiliumtrade.ai"
                    f"/users/current/accounts/{account_id}/trade",
                    headers={"auth-token": token, "Idempotency-Key": order.idempotency_key},
                    json=payload,
                )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            if r.status_code >= 400:
                return OrderResult(False, None, None, data.get("message") or r.text[:300])
            return OrderResult(True, str(data.get("orderId") or data.get("numericCode") or ""), data.get("fillPrice"), None)
        except httpx.HTTPError as exc:
            return OrderResult(False, None, None, str(exc))
