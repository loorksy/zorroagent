# Backtest methodology

- Candles: **OANDA only**. Twelve Data is never used to compute indicators or fills.
- Cost model is **mandatory**: spread + slippage (+ optional commission).
- Simulator: level-touch entries, stop vs targets, R from cost-adjusted fill.
- Outputs: equity curve (R), trade list, max drawdown, profit factor.
- Sample floor (default 30): display the literal string **Insufficient data**.
  Never a fabricated win-rate or monthly return %.
- Optimizer fragility warning when profit factor is implausibly high.
- Nightly incremental job: `nightly_backtest` in Arq.
- Informational weekly/monthly review uses the same floor (`/review`).
