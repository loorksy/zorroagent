"""Fill-rule coherence.

Ported from AiChart EXTRACTED doctrine (entrySemantics.validateEntryCoherence):
a CLOSE-based activation condition must NEVER be paired with a TOUCH fill on
the same level. Satisfying the close puts price on the far side; the touch
can never happen. Gates may refuse to publish; they never flip direction.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.enums import Direction, FillRule, InvalidationMode, PlanType


@dataclass(frozen=True)
class CoherenceProblem:
    code: str
    message: str


@dataclass
class ActivationRule:
    """Machine-checkable activation. Must agree with activation_condition text."""

    kind: str  # price_touch | candle_close_above | candle_close_below | return_to_zone | breakout_confirmed | rejection_confirmed | composite
    level: float | None = None
    timeframe: str | None = None
    zone_low: float | None = None
    zone_high: float | None = None
    rules: list["ActivationRule"] | None = None

    def leaves(self) -> list["ActivationRule"]:
        if self.kind == "composite" and self.rules:
            out: list[ActivationRule] = []
            for r in self.rules:
                out.extend(r.leaves())
            return out
        return [self]


CLOSE_KINDS = {
    "candle_close_above",
    "candle_close_below",
    "breakout_confirmed",
    "rejection_confirmed",
}


@dataclass
class EntryPlan:
    direction: Direction
    fill_rule: FillRule
    preferred_entry: float
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    take_profits: list[float]
    activation_rule: ActivationRule | None = None
    plan_type: PlanType = PlanType.IMMEDIATE
    invalidation_mode: InvalidationMode | None = None
    atr: float | None = None
    min_rr: float = 1.0


def _same_level(a: float, b: float, eps: float = 1e-8) -> bool:
    return abs(a - b) <= max(eps, abs(a) * 1e-8, abs(b) * 1e-8)


def validate_fill_coherence(plan: EntryPlan) -> list[CoherenceProblem]:
    problems: list[CoherenceProblem] = []

    if plan.direction not in (Direction.BUY, Direction.SELL):
        problems.append(CoherenceProblem("invalid_direction", "Direction must be BUY or SELL. WAIT is forbidden."))
        return problems

    if plan.fill_rule not in FillRule:
        problems.append(CoherenceProblem("invalid_fill_rule", "Unknown fill rule."))
        return problems

    if len(plan.take_profits) < 2:
        problems.append(CoherenceProblem("insufficient_targets", "At least two take-profit targets are required."))

    if plan.entry_zone_high < plan.entry_zone_low:
        problems.append(CoherenceProblem("inverted_zone", "entry_zone high is below low."))

    # Directional geometry
    if plan.direction == Direction.BUY:
        if plan.stop_loss >= plan.preferred_entry:
            problems.append(CoherenceProblem("stop_not_invalidation", "BUY stop must sit below entry (structural invalidation)."))
        if any(tp <= plan.preferred_entry for tp in plan.take_profits):
            problems.append(CoherenceProblem("target_wrong_side", "BUY targets must sit above entry."))
    else:
        if plan.stop_loss <= plan.preferred_entry:
            problems.append(CoherenceProblem("stop_not_invalidation", "SELL stop must sit above entry (structural invalidation)."))
        if any(tp >= plan.preferred_entry for tp in plan.take_profits):
            problems.append(CoherenceProblem("target_wrong_side", "SELL targets must sit below entry."))

    if plan.activation_rule:
        close_leaves = [l for l in plan.activation_rule.leaves() if l.kind in CLOSE_KINDS]
        if close_leaves and plan.fill_rule == FillRule.TOUCH:
            for leaf in close_leaves:
                if leaf.level is not None and _same_level(leaf.level, plan.preferred_entry):
                    problems.append(
                        CoherenceProblem(
                            "close_touch_conflict",
                            "NEVER pair a CLOSE condition with a TOUCH fill on the same level. "
                            "Satisfying the close puts price on the far side; the touch can never happen. "
                            "Use confirming_close (fill at the confirming candle close) or return_to_zone.",
                        )
                    )
        if close_leaves and plan.fill_rule == FillRule.MARKET:
            problems.append(
                CoherenceProblem(
                    "close_market_conflict",
                    "A close-based activation cannot fill as market at the current price.",
                )
            )

    if plan.fill_rule == FillRule.RETURN_TO_ZONE:
        if plan.entry_zone_low == plan.entry_zone_high:
            problems.append(CoherenceProblem("zone_required", "return_to_zone requires a real entry band."))

    if plan.fill_rule == FillRule.CONFIRMING_CLOSE and plan.activation_rule is None:
        problems.append(
            CoherenceProblem(
                "confirming_close_needs_rule",
                "confirming_close fill requires a machine-checkable close-based activation_rule.",
            )
        )

    if plan.plan_type == PlanType.CONDITIONAL and plan.activation_rule is None:
        problems.append(
            CoherenceProblem(
                "conditional_needs_rule",
                "Conditional plans require an activation_rule identical to the activation_condition text.",
            )
        )

    if plan.atr and plan.atr > 0:
        risk = abs(plan.preferred_entry - plan.stop_loss)
        if risk < plan.atr * 0.15:
            problems.append(
                CoherenceProblem(
                    "stop_too_tight",
                    "Stop must be structural invalidation PLUS an ATR buffer, not parked on the level.",
                )
            )

    return problems


def resolve_invalidation_mode(plan: EntryPlan) -> InvalidationMode:
    if plan.invalidation_mode:
        return plan.invalidation_mode
    if plan.activation_rule or plan.plan_type in (PlanType.CONDITIONAL, PlanType.ANTICIPATORY):
        return InvalidationMode.CLOSE
    return InvalidationMode.TOUCH if plan.fill_rule == FillRule.MARKET else InvalidationMode.CLOSE


def reward_to_risk(plan: EntryPlan, tp_index: int = 0) -> float | None:
    risk = abs(plan.preferred_entry - plan.stop_loss)
    if risk <= 0 or tp_index >= len(plan.take_profits):
        return None
    reward = abs(plan.take_profits[tp_index] - plan.preferred_entry)
    return reward / risk
