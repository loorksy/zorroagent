"""B3.1 extra gate paths: pass/fail stored reason; never flip; WAIT invalid."""

from app.domain.fill_rules import ActivationRule, EntryPlan
from app.domain.schema import validate_recommendation_schema
from app.enums import Direction, FillRule, GateStatus, PlanType
from app.gates.chain import GateContext, first_failure, run_gate_chain


def _plan(**kwargs) -> EntryPlan:
    defaults = dict(
        direction=Direction.BUY,
        fill_rule=FillRule.MARKET,
        preferred_entry=2000.0,
        entry_zone_low=1998.0,
        entry_zone_high=2002.0,
        stop_loss=1980.0,
        take_profits=[2060.0, 2120.0],
        plan_type=PlanType.IMMEDIATE,
        atr=5.0,
    )
    defaults.update(kwargs)
    return EntryPlan(**defaults)


def _ctx(plan: EntryPlan | None = None, **over) -> GateContext:
    plan = plan or _plan()
    base = dict(
        plan=plan,
        now_ts=0,
        news_provider_configured=True,
        news={"risk": "low", "blocking_event": None},
        liquidity={"illiquid": False, "sweeps": 1},
        supply_demand={"zones_count": 2, "nearest": {"low": 1990, "high": 2005}},
        structure={"trend": "up", "htf_conflict": False},
        session={"blocked": False, "name": "london"},
        live_price=2000.0,
        oanda_price=2000.0,
        twelve_price=2000.1,
        spread=0.1,
        typical_spread=0.1,
        divergence_bps=0.5,
        divergence_limit_bps=15,
        atr=5.0,
        vision_ok=True,
        vision_timeframes=["15m", "1h", "4h"],
        cost_model={"spread": 0.1, "slippage": 0.05},
        feed_unreliable=False,
    )
    base.update(over)
    return GateContext(**base)


def _assert_pass_fail(gate_id: str, pass_ctx: GateContext, fail_ctx: GateContext):
    p = run_gate_chain(pass_ctx, deep=True)
    f = run_gate_chain(fail_ctx, deep=True)
    pr = next(r for r in p if r.gate_id == gate_id)
    fr = next((r for r in f if r.gate_id == gate_id), first_failure(f))
    assert pr.status in (GateStatus.PASS, GateStatus.CONVERT)
    assert fr is not None
    assert fr.status in (GateStatus.VETO, GateStatus.UNAVAILABLE)
    assert fr.reason


def test_g1_news_pass_and_fail_reason():
    _assert_pass_fail(
        "G1",
        _ctx(),
        _ctx(news={"risk": "high", "blocking_event": {"title": "NFP"}}),
    )


def test_g2_liquidity_pass_and_fail_reason():
    _assert_pass_fail("G2", _ctx(), _ctx(session={"blocked": True, "reason": "weekend"}))


def test_g2_weekend_session_blocks():
    results = run_gate_chain(_ctx(session={"blocked": True, "reason": "weekend"}), deep=True)
    fail = first_failure(results)
    assert fail and fail.gate_id == "G2"
    assert "weekend" in (fail.reason or "").lower()


def test_g3_supply_demand_pass_and_unavailable():
    _assert_pass_fail("G3", _ctx(), _ctx(supply_demand=None))


def test_g4_structure_unavailable_named():
    results = run_gate_chain(_ctx(structure=None), deep=True)
    fail = first_failure(results)
    assert fail and fail.gate_id == "G4"
    assert fail.reason


def test_g5_live_price_pass_and_fail():
    _assert_pass_fail("G5", _ctx(), _ctx(live_price=None, oanda_price=None))


def test_g6_cost_pass():
    results = run_gate_chain(_ctx(), deep=True)
    g6 = next(r for r in results if r.gate_id == "G6")
    assert g6.status is GateStatus.PASS
    assert g6.evidence.get("net_rr") is not None


def test_gate_never_flips_buy_to_sell_property():
    for news in (None, {"risk": "high", "blocking_event": {"title": "x"}}):
        plan = _plan(direction=Direction.BUY)
        ctx = _ctx(plan, news=news or {"risk": "low", "blocking_event": None}, news_provider_configured=news is not None)
        run_gate_chain(ctx, deep=True)
        assert plan.direction is Direction.BUY


def test_wait_not_valid_analytical_bias():
    plan = _plan()
    problems = validate_recommendation_schema(plan, activation_condition=None, analytical_bias="WAIT")
    assert any(p.code == "wait_forbidden" for p in problems)


def test_missing_tp2_rejected():
    plan = _plan(take_profits=[2060.0])
    problems = validate_recommendation_schema(plan, activation_condition=None, analytical_bias="BUY")
    assert any(p.code == "missing_tp2" for p in problems)


def test_stop_on_raw_level_without_atr_buffer_rejected():
    plan = _plan(stop_loss=1999.5, atr=5.0, preferred_entry=2000.0)
    problems = validate_recommendation_schema(plan, activation_condition=None, analytical_bias="BUY")
    assert any(p.code == "stop_on_raw_level" for p in problems)


def test_activation_text_vs_machine_mismatch():
    plan = _plan(
        fill_rule=FillRule.CONFIRMING_CLOSE,
        plan_type=PlanType.CONDITIONAL,
        activation_rule=ActivationRule(kind="candle_close_above", level=2000.0),
    )
    problems = validate_recommendation_schema(
        plan, activation_condition="touch 1.05 on the bid", analytical_bias="BUY"
    )
    assert any(p.code == "activation_mismatch" for p in problems)
