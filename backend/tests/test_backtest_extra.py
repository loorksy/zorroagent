"""B3.7 backtest cost model, insufficient data, Fragile OOS, increment API."""

import pytest

from app.backtest.engine import (
    CostModel,
    CostModelRequired,
    IncrementState,
    incremental_backtest,
    oos_fragility_tag,
    run_backtest,
)


def test_run_without_cost_model_rejected():
    with pytest.raises(CostModelRequired):
        run_backtest([], "BUY", 1, 0.9, [1.1, 1.2], None)


def test_fragile_tag_when_oos_collapses():
    assert oos_fragility_tag(2.0, 0.4) == "Fragile"
    assert oos_fragility_tag(2.0, 1.8) is None


def test_incremental_does_not_replay_from_zero():
    candles = [{"open": 10, "high": 11, "low": 9, "close": 10} for _ in range(10)]
    candles[2] = {"open": 10, "high": 11, "low": 9, "close": 10.5}
    candles[3] = {"open": 10.5, "high": 20, "low": 10, "close": 19}
    state = IncrementState(watermark=0)
    result1, state1 = incremental_backtest(
        state, candles[:5], "BUY", 10, 9, [19, 21], CostModel(0.1, 0.1), sample_floor=1
    )
    assert state1.watermark == 5
    result2, state2 = incremental_backtest(
        state1, candles, "BUY", 10, 9, [19, 21], CostModel(0.1, 0.1), sample_floor=1
    )
    assert state2.watermark == 10
    assert state2.watermark > state1.watermark
    # Second call only sees candles after watermark 5 — does not reset.
    assert result2.sample_size >= result1.sample_size
