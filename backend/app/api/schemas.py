from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.enums import AnalysisTier, Direction, FillRule, PlanType


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InstrumentOut(BaseModel):
    canonical_id: str
    display_symbol: str
    asset_class: str
    tradable: bool


class AliasIn(BaseModel):
    canonical_id: str
    execution_symbol: str


class ChatIn(BaseModel):
    conversation_id: str | None = None
    message: str
    language: Literal["en", "tr", "ar"] | None = None
    model_id: str | None = None
    canonical_id: str | None = None
    timeframe: str = "15m"
    tier: AnalysisTier = AnalysisTier.QUICK


class AnalyzeIn(BaseModel):
    canonical_id: str
    timeframe: str = "15m"
    tier: AnalysisTier = AnalysisTier.DEEP
    model_id: str | None = None
    language: Literal["en", "tr", "ar"] = "en"
    direction: Direction
    fill_rule: FillRule
    preferred_entry: float
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    take_profits: list[float] = Field(min_length=2)
    plan_type: PlanType = PlanType.IMMEDIATE
    invalidation_rule: str
    activation_condition: str | None = None
    activation_rule: dict[str, Any] | None = None
    validity_candles: int = 30
    reasons: list[str] = Field(default_factory=list)
    next_action: str = ""

    @field_validator("direction")
    @classmethod
    def no_wait(cls, v: Direction) -> Direction:
        if v not in (Direction.BUY, Direction.SELL):
            raise ValueError("WAIT is not a valid analytical outcome")
        return v

    @field_validator("take_profits")
    @classmethod
    def need_tp2(cls, v: list[float]) -> list[float]:
        if len(v) < 2:
            raise ValueError("Missing TP2")
        return v


class ExecuteIn(BaseModel):
    source: Literal["recommendation", "bot"]
    source_id: str
    source_name: str
    account_id: str
    lots: float
    confirmation: str  # typed canonical symbol or PIN
    client_key: str | None = None
    is_demo: bool = True


class BotCreateIn(BaseModel):
    name: str
    canonical_id: str
    origin: Literal["library", "recommendation", "draw"]
    recommendation_id: str | None = None
    code: str
    description: str = ""
    account_id: str | None = None


class PromoteLiveIn(BaseModel):
    confirmation: str
    account_id: str


class KillSwitchIn(BaseModel):
    engaged: bool
    reason: str = ""


class SettingsIn(BaseModel):
    language: Literal["en", "tr", "ar"] | None = None
    theme: Literal["dark", "light"] | None = None
    quick_model: str | None = None
    deep_model: str | None = None
    exposure_cap_r: float | None = None
    pin: str | None = None


class WatchlistIn(BaseModel):
    canonical_id: str
    notes: str = ""


class StrategyOptimizeIn(BaseModel):
    param_grid: dict[str, list[Any]]
    canonical_id: str
