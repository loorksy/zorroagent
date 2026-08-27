# Database schema

PostgreSQL + pgvector.

| Table | Purpose |
|---|---|
| operators | Single operator. Language, theme, model defaults, PIN hash, exposure cap. |
| instruments | OANDA catalog: canonical_id, display_symbol, asset_class, tradable. |
| broker_accounts | MetaApi accounts (demo+live OK). Encrypted token. |
| alias_maps | canonical_id → execution_symbol per account. Test-resolved. |
| conversations / messages | Ask mode. Per-conversation model_id. |
| recommendations | Full card fields. **No execution columns.** |
| recommendation_gates | Per-gate pass/fail/unavailable/convert. |
| executions | Broker fills. Separate from recs. Idempotency key. |
| strategies / strategy_versions | Versioned Python. |
| bots / bot_versions / bot_rationales | CODE + MIND. One account per bot. |
| watchlist | Canonical ids. |
| memory_cases / lessons | Similar cases + nightly lessons. Memory never flips direction. |
| backtest_runs | Cost model, equity curve, trade list, sample floor. |
| agent_runs | model_id + collapsed transcript. |
| kill_switch | Global override. |
| feed_health | OANDA / Twelve / Finnhub / MetaApi. |
| encrypted_secrets | Credentials at rest. |

Alembic: `backend/alembic/versions/0001_initial.py`. API also `create_all` on boot.
