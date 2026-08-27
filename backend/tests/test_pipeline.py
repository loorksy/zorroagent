from app.agent.pipeline import PipelineInput, SimilarCases, publish
from app.domain.fill_rules import ActivationRule
from app.enums import AnalysisTier, Direction, ExecutionStatus, FillRule, PlanType
from app.exposure import OpenRisk, aggregate_exposure


def test_quick_scan_is_non_tradeable():
    inp = _inp(tier=AnalysisTier.QUICK, vision_ok=False, vision_timeframes=[])
    out = publish(inp)
    assert out.published is True
    assert out.tradeable is False
    assert out.recommendation["label"] == "non-tradeable"


def test_deep_without_vision_refuses():
    inp = _inp(tier=AnalysisTier.DEEP, vision_ok=False, vision_timeframes=["15m"])
    out = publish(inp)
    assert out.published is False
    assert out.refused_reason == "Chart vision unavailable"


def test_similar_cases_insufficient_data():
    card = SimilarCases(count=3, sample_floor=30, items=[]).card_payload()
    assert card["label"] == "Insufficient data"
    assert card["win_rate"] is None


def test_exposure_correlation_warning():
    report = aggregate_exposure(
        [
            OpenRisk("EUR_USD", "BUY", 1.0, "forex"),
            OpenRisk("GBP_USD", "BUY", 1.0, "forex"),
        ],
        cap_r=None,
    )
    assert report.correlation_warning
    assert report.cap_exceeded is False
    assert report.total_r == 2.0


def _inp(**over) -> PipelineInput:
    base = dict(
        canonical_id="EUR_USD",
        timeframe="15m",
        tier=AnalysisTier.DEEP,
        model_id="claude-fable-5",
        language="en",
        direction=Direction.BUY,
        fill_rule=FillRule.MARKET,
        preferred_entry=1.10,
        entry_zone_low=1.099,
        entry_zone_high=1.101,
        stop_loss=1.09,
        take_profits=[1.12, 1.14],
        plan_type=PlanType.IMMEDIATE,
        invalidation_rule="15m close below 1.09",
        activation_condition=None,
        activation_rule=None,
        validity_candles=30,
        reasons=["structure"],
        next_action="watch 1.10",
        atr=0.002,
        now_ts=0,
        news_provider_configured=True,
        news={"risk": "low", "blocking_event": None},
        liquidity={"illiquid": False, "sweeps": 0},
        supply_demand={"zones_count": 1, "nearest": {}},
        structure={"trend": "up", "htf_conflict": False},
        session={"blocked": False, "name": "ny"},
        live_price=1.10,
        oanda_price=1.10,
        twelve_price=1.1001,
        spread=0.0001,
        typical_spread=0.0001,
        divergence_bps=1.0,
        divergence_limit_bps=15,
        vision_timeframes=["15m", "1h", "4h"],
        vision_ok=True,
        cost_model={"spread": 0.0001, "slippage": 0.00005},
        similar=SimilarCases(count=0, sample_floor=30),
        feed_unreliable=False,
    )
    base.update(over)
    return PipelineInput(**base)
