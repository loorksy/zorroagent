# Architecture

```
                    ┌─────────────────────────────────────────┐
                    │  React + Vite + Zustand + KLineChart Pro │
                    │  Capacitor Android · CopilotKit artifacts │
                    └──────────────────┬──────────────────────┘
                                       │ REST / SSE / WS
                    ┌──────────────────▼──────────────────────┐
                    │ FastAPI (async)  JWT single operator     │
                    │ Claude Agent SDK  READ tools only        │
                    │ Gates → publish or named refusal         │
                    └─┬─────────────┬─────────────┬───────────┘
                      │             │             │
               PostgreSQL+pgvector Redis/Arq   Feeds
                      │             │             │
                 recs, bots,     jobs: catalog   OANDA (truth)
                 executions*,    nightly BT      Twelve (check)
                 memory          bot ticks       Finnhub (news)
                                                 MetaApi (orders)
```

\* Executions are a **separate table**. They never write back into recommendations.

## Layers

1. **Analysis** — OANDA candles + chart vision (Deep) + Finnhub news + pgvector similar cases.
2. **Gates** — news → liquidity/session → S/D → structure → live-price (incl. divergence + spread) → cost.
   Gates never flip BUY ↔ SELL. They refuse to publish or convert plan_type.
3. **Execution** — operator names a saved recommendation or bot, confirms lot once (or PIN/canonical).
   MetaApi places the order with SL attached. Idempotent.

No MCP. No second agent runtime. TradingAgents / crewAI are **role patterns** only.

## Daily UI

Ask `/` · Scan Today `/today` · Build `/build` — see `docs/daily-modes.md`.
