"""Recommendation pipeline: roles → vision (Deep) → gates → publish or named refusal."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.agent.runtime import resolve_model, role_order, system_prompt
from app.agent.vision import VisionCapture, capture_pngs, validate_vision
from app.domain.fill_rules import ActivationRule, EntryPlan
from app.enums import (
    AnalysisTier,
    Direction,
    ExecutionStatus,
    FillRule,
    GateStatus,
    PlanType,
)
from app.gates.chain import GateContext, GateResult, first_failure, run_gate_chain


@dataclass
class SimilarCases:
    count: int
    sample_floor: int
    items: list[dict[str, Any]] = field(default_factory=list)

    def card_payload(self) -> dict[str, Any]:
        if self.count < self.sample_floor:
            return {
                "count": self.count,
                "win_rate": None,
                "label": "Insufficient data",
                "note": "Historical observation only; never a win-rate.",
            }
        wins = sum(1 for i in self.items if i.get("outcome") in {"win_tp1", "win_tp2", "win_tp3"})
        return {
            "count": self.count,
            "win_rate": wins / self.count if self.count else None,
            "label": "historical_observation",
            "note": "Historical observation, never sold as win-rate for this plan.",
        }


@dataclass
class PipelineInput:
    canonical_id: str
    timeframe: str
    tier: AnalysisTier
    model_id: str | None
    language: str
    direction: Direction
    fill_rule: FillRule
    preferred_entry: float
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    take_profits: list[float]
    plan_type: PlanType
    invalidation_rule: str
    activation_condition: str | None
    activation_rule: ActivationRule | None
    validity_candles: int
    reasons: list[str]
    next_action: str
    atr: float
    now_ts: float
    news_provider_configured: bool
    news: dict[str, Any] | None
    liquidity: dict[str, Any] | None
    supply_demand: dict[str, Any] | None
    structure: dict[str, Any] | None
    session: dict[str, Any] | None
    live_price: float | None
    oanda_price: float | None
    twelve_price: float | None
    spread: float | None
    typical_spread: float | None
    divergence_bps: float
    divergence_limit_bps: float
    vision_timeframes: list[str]
    vision_ok: bool
    cost_model: dict[str, Any] | None
    similar: SimilarCases
    feed_unreliable: bool = False
    operator_defaults: dict[str, str] | None = None


@dataclass
class PipelineOutput:
    published: bool
    recommendation: dict[str, Any] | None
    gates: list[GateResult]
    refused_gate: str | None
    refused_reason: str | None
    model_id: str
    tradeable: bool
    agent_run_id: str


def _plan(inp: PipelineInput) -> EntryPlan:
    return EntryPlan(
        direction=inp.direction,
        fill_rule=inp.fill_rule,
        preferred_entry=inp.preferred_entry,
        entry_zone_low=inp.entry_zone_low,
        entry_zone_high=inp.entry_zone_high,
        stop_loss=inp.stop_loss,
        take_profits=inp.take_profits,
        activation_rule=inp.activation_rule,
        plan_type=inp.plan_type,
        atr=inp.atr,
    )


async def ensure_vision(inp: PipelineInput) -> VisionCapture:
    if inp.tier != AnalysisTier.DEEP:
        return VisionCapture(False, [], [], "Quick Scan is numbers-only and non-tradeable")
    frames = list(dict.fromkeys([*inp.vision_timeframes, "15m", "1h", "4h", inp.timeframe]))
    captured = await capture_pngs(inp.canonical_id, frames)
    if not captured.ok:
        return captured
    return validate_vision(captured.timeframes, inp.timeframe)


def publish(inp: PipelineInput) -> PipelineOutput:
    model_id = resolve_model(inp.model_id, inp.tier, inp.operator_defaults)
    agent_run_id = str(uuid.uuid4())
    _ = system_prompt(inp.tier, inp.language)
    _ = role_order(inp.tier)

    if inp.tier == AnalysisTier.QUICK:
        rec = _card(inp, model_id, agent_run_id, tradeable=False, execution_status=ExecutionStatus.BLOCKED)
        rec["label"] = "non-tradeable"
        rec["note"] = "Quick Scan is numbers-only and non-tradeable. Deep Analysis is required for a tradeable card."
        return PipelineOutput(True, rec, [], None, None, model_id, False, agent_run_id)

    ctx = GateContext(
        plan=_plan(inp),
        now_ts=inp.now_ts,
        news_provider_configured=inp.news_provider_configured,
        news=inp.news,
        liquidity=inp.liquidity,
        supply_demand=inp.supply_demand,
        structure=inp.structure,
        session=inp.session,
        live_price=inp.live_price,
        oanda_price=inp.oanda_price,
        twelve_price=inp.twelve_price,
        spread=inp.spread,
        typical_spread=inp.typical_spread,
        divergence_bps=inp.divergence_bps,
        divergence_limit_bps=inp.divergence_limit_bps,
        atr=inp.atr,
        vision_ok=inp.vision_ok,
        vision_timeframes=inp.vision_timeframes,
        cost_model=inp.cost_model,
        feed_unreliable=inp.feed_unreliable,
    )
    gates = run_gate_chain(ctx, deep=True)
    fail = first_failure(gates)
    if fail:
        return PipelineOutput(
            False,
            None,
            gates,
            fail.name,
            fail.reason,
            model_id,
            False,
            agent_run_id,
        )
    plan_type = ctx.plan.plan_type
    status = (
        ExecutionStatus.AWAITING_ACTIVATION
        if plan_type in (PlanType.CONDITIONAL, PlanType.ANTICIPATORY)
        else ExecutionStatus.ACTIVE_NOW
    )
    rec = _card(inp, model_id, agent_run_id, True, status, plan_type)
    return PipelineOutput(True, rec, gates, None, None, model_id, True, agent_run_id)


def _card(
    inp: PipelineInput,
    model_id: str,
    agent_run_id: str,
    tradeable: bool,
    execution_status: ExecutionStatus,
    plan_type: PlanType | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "name": f"{inp.canonical_id} {inp.direction.value} {inp.timeframe}",
        "canonical_id": inp.canonical_id,
        "timeframe": inp.timeframe,
        "direction": inp.direction.value,
        "analytical_bias": inp.direction.value,
        "plan_type": (plan_type or inp.plan_type).value,
        "execution_status": execution_status.value,
        "fill_rule": inp.fill_rule.value,
        "entry_zone": {"low": inp.entry_zone_low, "high": inp.entry_zone_high},
        "preferred_entry": inp.preferred_entry,
        "stop_loss": inp.stop_loss,
        "take_profits": inp.take_profits,
        "invalidation_rule": inp.invalidation_rule,
        "activation_condition": inp.activation_condition,
        "activation_rule": None if not inp.activation_rule else inp.activation_rule.__dict__,
        "validity_candles": inp.validity_candles,
        "similar_past_cases": inp.similar.card_payload(),
        "reasons": inp.reasons,
        "next_action": inp.next_action,
        "model_id": model_id,
        "tier": inp.tier.value,
        "tradeable": tradeable,
        "agent_run_id": agent_run_id,
        "gates": "see confirmation modal",
    }
