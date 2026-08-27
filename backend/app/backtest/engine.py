"""Mandatory cost model. Sample floor → 'Insufficient data'. Never fabricate %."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CostModel:
    spread: float
    slippage: float
    commission_per_lot: float = 0.0


@dataclass
class SimulatedTrade:
    direction: str
    entry: float
    exit: float
    stop: float
    r: float
    reason: str


@dataclass
class BacktestResult:
    sample_size: int
    trades: list[SimulatedTrade]
    equity_curve: list[float]
    max_dd: float | None
    profit_factor: float | None
    insufficient_data: bool
    label: str
    fragility_warning: str | None = None


def apply_costs(fill: float, direction: str, cost: CostModel) -> float:
    pad = cost.spread + cost.slippage
    return fill + pad if direction == "BUY" else fill - pad


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 0.0
    dd = 0.0
    for v in equity:
        peak = max(peak, v)
        dd = min(dd, v - peak)
    return abs(dd)


def profit_factor(rs: list[float]) -> float | None:
    gains = sum(x for x in rs if x > 0)
    losses = abs(sum(x for x in rs if x < 0))
    if losses == 0:
        return None if gains == 0 else float("inf")
    return gains / losses


def run_backtest(
    candles: list[dict],
    direction: str,
    entry: float,
    stop: float,
    targets: list[float],
    cost: CostModel,
    sample_floor: int = 30,
) -> BacktestResult:
    """Simple level-touch simulator. Indicators NEVER come from Twelve Data."""
    trades: list[SimulatedTrade] = []
    in_pos = False
    fill = None
    for c in candles:
        high = float(c["high"])
        low = float(c["low"])
        close = float(c["close"])
        if not in_pos:
            touched = (direction == "BUY" and low <= entry <= high) or (
                direction == "SELL" and low <= entry <= high
            )
            if touched:
                in_pos = True
                fill = apply_costs(entry, direction, cost)
            continue
        assert fill is not None
        risk = abs(fill - stop) or 1e-9
        hit_stop = (direction == "BUY" and low <= stop) or (direction == "SELL" and high >= stop)
        hit_tp = None
        for tp in targets:
            if (direction == "BUY" and high >= tp) or (direction == "SELL" and low <= tp):
                hit_tp = tp
                break
        if hit_stop:
            r = (stop - fill) / risk if direction == "BUY" else (fill - stop) / risk
            trades.append(SimulatedTrade(direction, fill, stop, stop, r, "stop"))
            in_pos = False
        elif hit_tp is not None:
            r = (hit_tp - fill) / risk if direction == "BUY" else (fill - hit_tp) / risk
            trades.append(SimulatedTrade(direction, fill, hit_tp, stop, r, "target"))
            in_pos = False
        else:
            _ = close

    rs = [t.r for t in trades]
    equity = [0.0]
    for r in rs:
        equity.append(equity[-1] + r)
    insufficient = len(trades) < sample_floor
    pf = profit_factor(rs) if rs else None
    dd = max_drawdown(equity) if len(equity) > 1 else None
    warning = None
    if not insufficient and pf is not None and pf > 5:
        warning = "Optimizer fragility warning: profit factor is unusually high; treat as curve-fit risk, not a promise."
    return BacktestResult(
        sample_size=len(trades),
        trades=trades,
        equity_curve=equity,
        max_dd=dd,
        profit_factor=None if insufficient else pf,
        insufficient_data=insufficient,
        label="Insufficient data" if insufficient else "ok",
        fragility_warning=warning,
    )
