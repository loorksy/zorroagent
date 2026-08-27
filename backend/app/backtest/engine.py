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


class CostModelRequired(ValueError):
    """Raised when a backtest is requested without a cost model."""


def oos_fragility_tag(in_sample_pf: float | None, oos_pf: float | None) -> str | None:
    """Optimizer tag when out-of-sample collapses versus in-sample."""
    if in_sample_pf is None or oos_pf is None:
        return None
    if in_sample_pf > 0 and oos_pf < in_sample_pf * 0.5:
        return "Fragile"
    return None


@dataclass
class IncrementState:
    watermark: int = 0
    trades: list[SimulatedTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=lambda: [0.0])

    def as_dict(self) -> dict:
        return {
            "watermark": self.watermark,
            "trade_count": len(self.trades),
            "equity_last": self.equity_curve[-1] if self.equity_curve else 0.0,
        }


def run_backtest(
    candles: list[dict],
    direction: str,
    entry: float,
    stop: float,
    targets: list[float],
    cost: CostModel | None,
    sample_floor: int = 30,
    oos_profit_factor: float | None = None,
) -> BacktestResult:
    """Simple level-touch simulator. Indicators NEVER come from Twelve Data."""
    if cost is None:
        raise CostModelRequired("Run without cost model → rejected.")
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
    fragile = oos_fragility_tag(None if insufficient else pf, oos_profit_factor)
    if fragile:
        warning = f"{warning + ' ' if warning else ''}{fragile}"
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


def incremental_backtest(
    state: IncrementState,
    new_candles: list[dict],
    direction: str,
    entry: float,
    stop: float,
    targets: list[float],
    cost: CostModel,
    sample_floor: int = 30,
) -> tuple[BacktestResult, IncrementState]:
    """Nightly job: process only candles after the watermark. Never full-replay from zero."""
    if cost is None:
        raise CostModelRequired("Run without cost model → rejected.")
    sliced = new_candles[state.watermark :]
    if not sliced:
        result = BacktestResult(
            sample_size=len(state.trades),
            trades=list(state.trades),
            equity_curve=list(state.equity_curve),
            max_dd=max_drawdown(state.equity_curve) if len(state.equity_curve) > 1 else None,
            profit_factor=profit_factor([t.r for t in state.trades]) if state.trades else None,
            insufficient_data=len(state.trades) < sample_floor,
            label="Insufficient data" if len(state.trades) < sample_floor else "ok",
        )
        return result, state
    piece = run_backtest(sliced, direction, entry, stop, targets, cost, sample_floor=1)
    merged_trades = list(state.trades) + list(piece.trades)
    equity = list(state.equity_curve)
    for t in piece.trades:
        equity.append(equity[-1] + t.r)
    new_state = IncrementState(watermark=len(new_candles), trades=merged_trades, equity_curve=equity)
    rs = [t.r for t in merged_trades]
    insufficient = len(merged_trades) < sample_floor
    result = BacktestResult(
        sample_size=len(merged_trades),
        trades=merged_trades,
        equity_curve=equity,
        max_dd=max_drawdown(equity) if len(equity) > 1 else None,
        profit_factor=None if insufficient else profit_factor(rs),
        insufficient_data=insufficient,
        label="Insufficient data" if insufficient else "ok",
        fragility_warning=piece.fragility_warning,
    )
    return result, new_state
