"""CODE → MIND rationale → order. Mind may VETO; it never flips direction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.bots.safety import SafetyContext, check_bot_safety
from app.enums import Direction


@dataclass
class CodeCandidate:
    action: Literal["skip", "candidate"]
    direction: Direction | None = None
    lots: float = 0.0
    stop_loss: float | None = None
    preferred_entry: float | None = None


@dataclass
class MindResult:
    ok: bool
    veto: bool = False
    rationale: str | None = None
    attempted_direction: Direction | None = None


@dataclass
class TickResult:
    order: bool
    reason: str
    rationale: str | None = None
    direction: Direction | None = None


def run_code_mind_tick(
    code: CodeCandidate,
    mind: MindResult | None,
    safety: SafetyContext,
    *,
    demo_table: str = "demo_executions",
    live_table: str = "executions",
    mode: Literal["demo", "live"] = "demo",
) -> TickResult:
    """One bot tick. Tables stay separate: demo_executions vs executions."""
    _ = demo_table, live_table, mode
    if code.action == "skip":
        return TickResult(False, "code_skip")
    if code.direction is None:
        return TickResult(False, "code_skip")
    if mind is None or not mind.ok:
        return TickResult(False, "mind_fail")
    if mind.veto:
        return TickResult(False, "mind_veto", rationale=mind.rationale)
    if not (mind.rationale or "").strip():
        return TickResult(False, "mind_fail")
    if mind.attempted_direction is not None and mind.attempted_direction != code.direction:
        return TickResult(False, "mind_cannot_flip_direction", rationale=mind.rationale)
    verdict = check_bot_safety(safety)
    if not verdict.ok:
        return TickResult(False, verdict.failed[0] if verdict.failed else "safety")
    return TickResult(True, "filled", rationale=mind.rationale, direction=code.direction)


def execution_table_for(mode: Literal["demo", "live"]) -> str:
    return "demo_executions" if mode == "demo" else "executions"
