"""Gate chain: never flips direction; WAIT is not a valid outcome."""

from app.domain.fill_rules import ActivationRule, EntryPlan, validate_fill_coherence
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


def test_wait_is_not_a_direction():
    assert list(Direction) == [Direction.BUY, Direction.SELL]


def test_close_touch_same_level_refused():
    plan = _plan(
        fill_rule=FillRule.TOUCH,
        plan_type=PlanType.CONDITIONAL,
        activation_rule=ActivationRule(kind="candle_close_below", level=2000.0),
        direction=Direction.SELL,
        preferred_entry=2000.0,
        entry_zone_low=1995,
        entry_zone_high=2000,
        stop_loss=2010,
        take_profits=[1980, 1960],
    )
    problems = validate_fill_coherence(plan)
    assert any(p.code == "close_touch_conflict" for p in problems)


def test_confirming_close_ok():
    plan = _plan(
        fill_rule=FillRule.CONFIRMING_CLOSE,
        plan_type=PlanType.CONDITIONAL,
        activation_rule=ActivationRule(kind="candle_close_above", level=2000.0),
    )
    assert validate_fill_coherence(plan) == []


def test_gates_never_flip_direction():
    plan = _plan(direction=Direction.SELL, preferred_entry=2000, stop_loss=2015, take_profits=[1980, 1960])
    ctx = _ctx(plan, news={"risk": "high", "blocking_event": {"title": "NFP"}})
    results = run_gate_chain(ctx, deep=True)
    fail = first_failure(results)
    assert fail is not None
    assert plan.direction is Direction.SELL


def test_news_unconfigured_is_unavailable_not_pass():
    ctx = _ctx(news_provider_configured=False, news=None)
    results = run_gate_chain(ctx, deep=True)
    assert results[0].status is GateStatus.UNAVAILABLE
    assert "calendar" in (results[0].reason or "").lower() or "not configured" in (results[0].reason or "").lower()


def test_vision_required_before_deep_gates():
    ctx = _ctx(vision_ok=False, vision_timeframes=[])
    results = run_gate_chain(ctx, deep=True)
    assert results[0].gate_id == "G0"
    assert results[0].reason == "Chart vision unavailable"


def test_divergence_blocks_publish():
    ctx = _ctx(feed_unreliable=True)
    results = run_gate_chain(ctx, deep=True)
    fail = first_failure(results)
    assert fail is not None
    assert "unreliable" in (fail.reason or "").lower()


def test_cost_converts_to_anticipatory_without_flipping():
    plan = _plan(fill_rule=FillRule.MARKET, take_profits=[2001.0, 2002.0], stop_loss=1990.0)
    ctx = _ctx(plan, cost_model={"spread": 5.0, "slippage": 5.0})
    results = run_gate_chain(ctx, deep=True)
    convert = [r for r in results if r.status is GateStatus.CONVERT]
    assert convert
    assert plan.plan_type is PlanType.ANTICIPATORY
    assert plan.direction is Direction.BUY


def test_htf_conflict_does_not_delete_direction():
    plan = _plan()
    ctx = _ctx(plan, structure={"trend": "up", "htf_conflict": True, "leading_tf": "4h", "context_tf": "15m"})
    results = run_gate_chain(ctx, deep=True)
    g4 = next(r for r in results if r.gate_id == "G4")
    assert g4.status is GateStatus.PASS
    assert g4.evidence["direction_unchanged"] is True
    assert plan.direction is Direction.BUY


def test_implausible_target_veto():
    plan = _plan(take_profits=[4000.0, 5000.0], atr=5.0)
    ctx = _ctx(plan, atr=5.0)
    results = run_gate_chain(ctx, deep=True)
    fail = first_failure(results)
    assert fail is not None
    assert "implausible" in (fail.reason or "").lower()
