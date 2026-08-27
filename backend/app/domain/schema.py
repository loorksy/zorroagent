"""Recommendation schema guards. WAIT is not an analytical_bias. Fail closed."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.fill_rules import ActivationRule, CLOSE_KINDS, EntryPlan, validate_fill_coherence
from app.enums import AnalyticalBias, Direction, FillRule


@dataclass
class SchemaProblem:
    code: str
    message: str


def analytical_bias_ok(value: str) -> bool:
    return value in {AnalyticalBias.BUY.value, AnalyticalBias.SELL.value, Direction.BUY.value, Direction.SELL.value}


def activation_text_matches_rule(text: str | None, rule: ActivationRule | None) -> bool:
    """Human activation_condition must agree with the machine rule."""
    if not text and not rule:
        return True
    if bool(text) != bool(rule):
        return False
    assert text is not None and rule is not None
    blob = text.lower()
    if rule.kind in CLOSE_KINDS:
        if "close" not in blob and "kapanış" not in blob and "إغلاق" not in blob:
            return False
        if rule.kind.endswith("above") and "below" in blob and "above" not in blob:
            return False
        if rule.kind.endswith("below") and "above" in blob and "below" not in blob:
            return False
    if rule.kind == "price_touch" and "touch" not in blob and "dokun" not in blob:
        return False
    if rule.level is not None and f"{rule.level}".rstrip("0").rstrip(".") not in blob.replace(",", ""):
        # Level must appear in the prose (string form).
        if str(int(rule.level)) not in blob and f"{rule.level}" not in blob:
            return False
    return True


def validate_recommendation_schema(plan: EntryPlan, *, activation_condition: str | None, analytical_bias: str) -> list[SchemaProblem]:
    problems: list[SchemaProblem] = []
    if not analytical_bias_ok(analytical_bias):
        problems.append(SchemaProblem("wait_forbidden", "WAIT is not a valid analytical_bias"))
    if len(plan.take_profits) < 2:
        problems.append(SchemaProblem("missing_tp2", "Missing TP2: at least two take-profit targets are required."))
    if plan.atr and plan.atr > 0:
        risk = abs(plan.preferred_entry - plan.stop_loss)
        if risk < plan.atr * 0.15:
            problems.append(
                SchemaProblem(
                    "stop_on_raw_level",
                    "Stop exactly on the raw level without an ATR buffer is rejected.",
                )
            )
    if plan.activation_rule and not activation_text_matches_rule(activation_condition, plan.activation_rule):
        problems.append(
            SchemaProblem(
                "activation_mismatch",
                "activation_condition text vs machine rule mismatch rejected.",
            )
        )
    for p in validate_fill_coherence(plan):
        problems.append(SchemaProblem(p.code, p.message))
    if plan.fill_rule == FillRule.TOUCH and plan.activation_rule and plan.activation_rule.kind in CLOSE_KINDS:
        problems.append(SchemaProblem("close_touch_conflict", "Close-condition + touch-fill on the same level is REJECTED."))
    return problems
