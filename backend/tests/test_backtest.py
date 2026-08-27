from app.backtest.engine import CostModel, run_backtest


def _candles():
    out = []
    price = 100.0
    for i in range(80):
        if i == 10:
            # touch entry 105
            out.append({"open": 104, "high": 106, "low": 103, "close": 105})
        elif 11 <= i <= 15:
            out.append({"open": 105, "high": 112, "low": 104, "close": 111})
        else:
            out.append({"open": price, "high": price + 1, "low": price - 1, "close": price})
        price += 0.1
    return out


def test_insufficient_data_literal():
    result = run_backtest(_candles(), "BUY", 105, 100, [111, 120], CostModel(0.1, 0.1), sample_floor=30)
    assert result.insufficient_data is True
    assert result.label == "Insufficient data"
    assert result.profit_factor is None


def test_cost_model_applied():
    candles = []
    for i in range(40):
        if i == 2:
            candles.append({"open": 10, "high": 11, "low": 9, "close": 10.5})
        elif i == 3:
            candles.append({"open": 10.5, "high": 20, "low": 10, "close": 19})
        else:
            candles.append({"open": 10, "high": 10.2, "low": 9.8, "close": 10})
    result = run_backtest(candles, "BUY", 10, 9, [19, 21], CostModel(spread=0.5, slippage=0.5), sample_floor=1)
    assert result.insufficient_data is False
    assert result.trades
    # fill is worsened by costs
    assert result.trades[0].entry > 10
