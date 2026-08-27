"""Ordered validation gates. NEVER flip BUY ↔ SELL.

Gate failure refuses to publish (or, for the cost gate, converts plan_type
to anticipatory). The model's analytical_bias is untouched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.domain.fill_rules import EntryPlan, validate_fill_coherence
from app.enums import FillRule, GateStatus, PlanType


@dataclass
class GateResult:
    gate_id: str
    name: str
    status: GateStatus
    reason: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    converted_plan_type: PlanType | None = None

    @property
    def ok(self) -> bool:
        return self.status in (GateStatus.PASS, GateStatus.CONVERT)


@dataclass
class GateContext:
    plan: EntryPlan
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
    atr: float
    vision_ok: bool
    vision_timeframes: list[str]
    cost_model: dict[str, Any] | None
    max_target_atr: float = 25.0
    spread_abnormal_mult: float = 3.0
    feed_unreliable: bool = False


HIGH_IMPACT_WINDOW_MINUTES = 30


def gate_news(ctx: GateContext) -> GateResult:
    if not ctx.news_provider_configured:
        return GateResult(
            "G1",
            "news_high_impact",
            GateStatus.UNAVAILABLE,
            "News calendar provider is not configured. Publication refused until the calendar can be verified.",
            {"configured": False},
        )
    if ctx.news is None:
        return GateResult(
            "G1",
            "news_high_impact",
            GateStatus.UNAVAILABLE,
            "News calendar unavailable. Named operational blocker: calendar timeout.",
        )
    if ctx.news.get("risk") == "unknown":
        return GateResult(
            "G1",
            "news_high_impact",
            GateStatus.UNAVAILABLE,
            ctx.news.get("reason") or "News window unconfirmed.",
        )
    blocking = ctx.news.get("blocking_event")
    if blocking:
        return GateResult(
            "G1",
            "news_high_impact",
            GateStatus.VETO,
            f"High-impact event window: {blocking.get('title', 'event')}.",
            {"event": blocking},
        )
    return GateResult("G1", "news_high_impact", GateStatus.PASS, evidence={"risk": ctx.news.get("risk")})


def gate_liquidity_session(ctx: GateContext) -> GateResult:
    if ctx.liquidity is None or ctx.session is None:
        return GateResult(
            "G2",
            "liquidity_session",
            GateStatus.UNAVAILABLE,
            "Liquidity / session data unavailable.",
        )
    if ctx.session.get("blocked"):
        return GateResult(
            "G2",
            "liquidity_session",
            GateStatus.VETO,
            ctx.session.get("reason") or "Session / liquidity blocked.",
            {"session": ctx.session},
        )
    if ctx.liquidity.get("illiquid"):
        return GateResult(
            "G2",
            "liquidity_session",
            GateStatus.VETO,
            "Market is illiquid; publication refused.",
            {"liquidity": ctx.liquidity},
        )
    return GateResult(
        "G2",
        "liquidity_session",
        GateStatus.PASS,
        evidence={"session": ctx.session.get("name"), "sweeps": ctx.liquidity.get("sweeps", 0)},
    )


def gate_supply_demand(ctx: GateContext) -> GateResult:
    if ctx.supply_demand is None:
        return GateResult(
            "G3",
            "supply_demand",
            GateStatus.UNAVAILABLE,
            "Supply/demand zones unavailable.",
        )
    return GateResult(
        "G3",
        "supply_demand",
        GateStatus.PASS,
        evidence={
            "zones": ctx.supply_demand.get("zones_count", 0),
            "nearest": ctx.supply_demand.get("nearest"),
        },
    )


def gate_structure(ctx: GateContext) -> GateResult:
    if ctx.structure is None:
        return GateResult(
            "G4",
            "market_structure",
            GateStatus.UNAVAILABLE,
            "Market structure unavailable.",
        )
    conflict = bool(ctx.structure.get("htf_conflict"))
    # Conflict names which TF leads — never deletes direction, never flips.
    reason = None
    if conflict:
        reason = (
            f"Higher-timeframe conflict: {ctx.structure.get('leading_tf')} leads; "
            f"{ctx.structure.get('context_tf')} is context. Direction unchanged."
        )
    return GateResult(
        "G4",
        "market_structure",
        GateStatus.PASS,
        reason=reason,
        evidence={
            "trend": ctx.structure.get("trend"),
            "htf_conflict": conflict,
            "leading_tf": ctx.structure.get("leading_tf"),
            "direction_unchanged": True,
        },
    )


def gate_live_price(ctx: GateContext) -> GateResult:
    if ctx.feed_unreliable:
        return GateResult(
            "G5",
            "live_price_reverification",
            GateStatus.VETO,
            "Price data unreliable. OANDA outage or OANDA vs Twelve Data divergence.",
            {"divergence_bps": ctx.divergence_bps, "feed_unreliable": True},
        )
    price = ctx.live_price if ctx.live_price is not None else ctx.oanda_price
    if price is None or price <= 0:
        return GateResult(
            "G5",
            "live_price_reverification",
            GateStatus.UNAVAILABLE,
            "Live OANDA price Not available. Never invent a number.",
        )
    if ctx.twelve_price is not None and ctx.oanda_price is not None and ctx.oanda_price > 0:
        bps = abs(ctx.twelve_price - ctx.oanda_price) / ctx.oanda_price * 10_000
        if bps > ctx.divergence_limit_bps:
            return GateResult(
                "G5",
                "live_price_reverification",
                GateStatus.VETO,
                "Price data unreliable (OANDA vs Twelve Data divergence).",
                {"divergence_bps": bps, "limit": ctx.divergence_limit_bps},
            )
    if ctx.spread is not None and ctx.typical_spread and ctx.typical_spread > 0:
        if ctx.spread > ctx.typical_spread * ctx.spread_abnormal_mult:
            return GateResult(
                "G5",
                "live_price_reverification",
                GateStatus.VETO,
                "Abnormal spread. Publication refused.",
                {"spread": ctx.spread, "typical": ctx.typical_spread},
            )

    problems = validate_fill_coherence(ctx.plan)
    if problems:
        return GateResult(
            "G5",
            "live_price_reverification",
            GateStatus.VETO,
            "Plan fill-rule incoherent: " + "; ".join(p.code for p in problems),
            {"problems": [p.code for p in problems]},
        )

    if ctx.atr and ctx.atr > 0:
        implausible = [
            tp
            for tp in ctx.plan.take_profits
            if abs(tp - ctx.plan.preferred_entry) / ctx.atr > ctx.max_target_atr
        ]
        if implausible:
            return GateResult(
                "G5",
                "live_price_reverification",
                GateStatus.VETO,
                "Target implausible (beyond ATR ceiling). Never stretch a target.",
                {"implausible": implausible, "atr": ctx.atr},
            )

    return GateResult(
        "G5",
        "live_price_reverification",
        GateStatus.PASS,
        evidence={"price": price, "source": "OANDA"},
    )


def gate_cost(ctx: GateContext) -> GateResult:
    """Reject or convert to anticipatory. Never fabricate a weaker entry. Never flip direction."""
    if ctx.cost_model is None:
        return GateResult(
            "G6",
            "cost",
            GateStatus.UNAVAILABLE,
            "Cost model unavailable.",
        )
    spread = float(ctx.cost_model.get("spread", 0) or 0)
    slippage = float(ctx.cost_model.get("slippage", 0) or 0)
    risk = abs(ctx.plan.preferred_entry - ctx.plan.stop_loss)
    if risk <= 0:
        return GateResult("G6", "cost", GateStatus.VETO, "Zero risk distance; refuse to publish.")

    cost = spread + slippage
    net_rr = None
    if ctx.plan.take_profits:
        reward = abs(ctx.plan.take_profits[0] - ctx.plan.preferred_entry)
        net_rr = (reward - cost) / risk

    if ctx.plan.fill_rule == FillRule.MARKET and net_rr is not None and net_rr < ctx.plan.min_rr:
        # Convert to anticipatory — keep direction, do not invent a weaker entry.
        return GateResult(
            "G6",
            "cost",
            GateStatus.CONVERT,
            "Costs consume the move at market. Plan converted to anticipatory; direction unchanged. "
            "Wait for a better level rather than shrinking the stop or stretching the target.",
            {"net_rr": net_rr, "direction_unchanged": True},
            converted_plan_type=PlanType.ANTICIPATORY,
        )
    return GateResult("G6", "cost", GateStatus.PASS, evidence={"net_rr": net_rr, "cost": cost})


GATE_ORDER: list[Callable[[GateContext], GateResult]] = [
    gate_news,
    gate_liquidity_session,
    gate_supply_demand,
    gate_structure,
    gate_live_price,
    gate_cost,
]


def require_vision_before_gates(ctx: GateContext) -> GateResult | None:
    if not ctx.vision_ok:
        return GateResult(
            "G0",
            "chart_vision",
            GateStatus.VETO,
            "Chart vision unavailable",
            {"timeframes": ctx.vision_timeframes},
        )
    required = {"15m", "1h", "4h"}
    have = {tf.lower() for tf in ctx.vision_timeframes}
    if not required.issubset(have):
        return GateResult(
            "G0",
            "chart_vision",
            GateStatus.VETO,
            "Chart vision unavailable (required frames: 15m, 1h, 4h plus operator TF).",
            {"timeframes": ctx.vision_timeframes},
        )
    return None


def run_gate_chain(ctx: GateContext, *, deep: bool) -> list[GateResult]:
    results: list[GateResult] = []
    if deep:
        vision = require_vision_before_gates(ctx)
        if vision is not None:
            return [vision]
    for fn in GATE_ORDER:
        result = fn(ctx)
        results.append(result)
        if result.status in (GateStatus.VETO, GateStatus.UNAVAILABLE):
            break
        if result.status == GateStatus.CONVERT and result.converted_plan_type:
            ctx.plan.plan_type = result.converted_plan_type
    return results


def first_failure(results: list[GateResult]) -> GateResult | None:
    for r in results:
        if r.status in (GateStatus.VETO, GateStatus.UNAVAILABLE):
            return r
    return None
