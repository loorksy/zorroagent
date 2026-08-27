"""Bot safety gates (16.9). Kill switch overrides everything. Mind may VETO, never flip."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SafetyContext:
    kill_switch: bool
    feed_unreliable: bool
    news_blocked: bool
    session_blocked: bool
    spread_abnormal: bool
    alias_mapped: bool
    demo_required_unmet: bool
    rationale_ok: bool
    rationale_veto: bool
    min_interval_ok: bool
    lots_positive: bool
    sl_attached: bool
    vision_required_failed: bool
    exposure_cap_exceeded: bool
    account_bound: bool
    code_version_active: bool
    duplicate_position: bool = False


SAFETY_NAMES = [
    "kill_switch",
    "feed_unreliable",
    "news_blocked",
    "session_blocked",
    "spread_abnormal",
    "alias_mapped",
    "demo_required_unmet",
    "rationale_ok",
    "rationale_veto",
    "min_interval_ok",
    "lots_positive",
    "sl_attached",
    "vision_required_failed",
    "exposure_cap_exceeded",
    "account_bound",
    "code_version_active",
    "duplicate_position",
]


@dataclass
class SafetyVerdict:
    ok: bool
    failed: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)


def promote_gate(demo_success: bool, confirmation: str, canonical_id: str, pin_ok: bool) -> tuple[bool, int, str]:
    """Promote-to-live without demo or PIN/typed symbol is blocked (403)."""
    if not demo_success:
        return False, 403, "Mandatory demo success before live"
    if not confirmation:
        return False, 403, "PIN or typed canonical symbol required"
    if confirmation != canonical_id and not pin_ok:
        return False, 403, "Type the canonical symbol or PIN"
    return True, 200, "ok"


def check_bot_safety(ctx: SafetyContext) -> SafetyVerdict:
    failed: list[str] = []
    if ctx.kill_switch:
        return SafetyVerdict(False, ["kill_switch"], {"override": True})
    checks = {
        "feed_unreliable": not ctx.feed_unreliable,
        "news_blocked": not ctx.news_blocked,
        "session_blocked": not ctx.session_blocked,
        "spread_abnormal": not ctx.spread_abnormal,
        "alias_mapped": ctx.alias_mapped,
        "demo_required_unmet": not ctx.demo_required_unmet,
        "rationale_ok": ctx.rationale_ok,
        "rationale_veto": not ctx.rationale_veto,
        "min_interval_ok": ctx.min_interval_ok,
        "lots_positive": ctx.lots_positive,
        "sl_attached": ctx.sl_attached,
        "vision_required_failed": not ctx.vision_required_failed,
        "exposure_cap_exceeded": not ctx.exposure_cap_exceeded,
        "account_bound": ctx.account_bound,
        "code_version_active": ctx.code_version_active,
        "duplicate_position": not ctx.duplicate_position,
    }
    for name, passed in checks.items():
        if not passed:
            failed.append(name)
    return SafetyVerdict(ok=not failed, failed=failed, evidence=checks)
