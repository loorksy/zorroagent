"""B3.5 CODE + MIND loop, kill switch shared path, demo vs live tables."""

from app.bots.kill import kill_blocks_orders
from app.bots.loop import CodeCandidate, MindResult, execution_table_for, run_code_mind_tick
from app.bots.safety import SafetyContext, check_bot_safety
from app.enums import Direction


def _safety(**over) -> SafetyContext:
    base = dict(
        kill_switch=False,
        feed_unreliable=False,
        news_blocked=False,
        session_blocked=False,
        spread_abnormal=False,
        alias_mapped=True,
        demo_required_unmet=False,
        rationale_ok=True,
        rationale_veto=False,
        min_interval_ok=True,
        lots_positive=True,
        sl_attached=True,
        vision_required_failed=False,
        exposure_cap_exceeded=False,
        account_bound=True,
        code_version_active=True,
    )
    base.update(over)
    return SafetyContext(**base)


def test_code_skip_no_order_no_rationale_required():
    out = run_code_mind_tick(CodeCandidate("skip"), None, _safety())
    assert out.order is False
    assert out.reason == "code_skip"
    assert out.rationale is None


def test_code_candidate_mind_fail_no_order():
    code = CodeCandidate("candidate", Direction.BUY, lots=0.1, stop_loss=1.0)
    out = run_code_mind_tick(code, MindResult(ok=False), _safety())
    assert out.order is False
    assert out.reason == "mind_fail"


def test_code_candidate_mind_veto_no_order_reason_logged():
    code = CodeCandidate("candidate", Direction.BUY, lots=0.1, stop_loss=1.0)
    mind = MindResult(ok=True, veto=True, rationale="News window")
    out = run_code_mind_tick(code, mind, _safety())
    assert out.order is False
    assert out.reason == "mind_veto"
    assert out.rationale == "News window"


def test_code_candidate_mind_rationale_gates_pass_order():
    code = CodeCandidate("candidate", Direction.BUY, lots=0.1, stop_loss=1.0)
    mind = MindResult(ok=True, veto=False, rationale="Structure holds.", attempted_direction=Direction.BUY)
    out = run_code_mind_tick(code, mind, _safety())
    assert out.order is True
    assert out.rationale == "Structure holds."
    assert out.direction is Direction.BUY


def test_mind_cannot_flip_direction_against_code():
    code = CodeCandidate("candidate", Direction.BUY, lots=0.1, stop_loss=1.0)
    mind = MindResult(ok=True, rationale="I prefer SELL", attempted_direction=Direction.SELL)
    out = run_code_mind_tick(code, mind, _safety())
    assert out.order is False
    assert out.reason == "mind_cannot_flip_direction"


def test_mind_cannot_place_trade_code_did_not_candidate():
    out = run_code_mind_tick(
        CodeCandidate("skip"),
        MindResult(ok=True, rationale="Let us buy anyway", attempted_direction=Direction.BUY),
        _safety(),
    )
    assert out.order is False


def test_demo_and_live_tables_are_separate():
    assert execution_table_for("demo") == "demo_executions"
    assert execution_table_for("live") == "executions"
    assert execution_table_for("demo") != execution_table_for("live")


def test_kill_switch_shared_predicate():
    assert kill_blocks_orders(True) is True
    assert kill_blocks_orders(False) is False
    v = check_bot_safety(_safety(kill_switch=True))
    assert v.ok is False
    assert v.failed == ["kill_switch"]
