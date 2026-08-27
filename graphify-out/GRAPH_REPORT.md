# Graph Report - workspace  (2026-08-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 566 nodes · 1478 edges · 30 communities (27 shown, 3 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 219 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `24ba9003`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- pipeline.py
- app/main.py
- App.tsx
- OandaClient
- models.py
- dependencies
- devDependencies
- handle_telegram_update
- compilerOptions
- tools.py
- run_backtest
- check_bot_safety
- resolve_alias
- MainActivity.java
- logging_conf.py
- test_api_auth.py
- vite-env.d.ts
- zorro-backend

## God Nodes (most connected - your core abstractions)
1. `Operator` - 41 edges
2. `Base` - 28 edges
3. `analyze()` - 27 edges
4. `useDesk` - 26 edges
5. `Direction` - 24 edges
6. `OandaClient` - 24 edges
7. `PlanType` - 23 edges
8. `get_settings()` - 22 edges
9. `FillRule` - 20 edges
10. `publish()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `ChatIn` --uses--> `AnalysisTier`  [INFERRED]
  backend/app/api/schemas.py → backend/app/enums.py
- `create_bot()` --uses--> `BotStatus`  [INFERRED]
  backend/app/main.py → backend/app/enums.py
- `kill_switch()` --uses--> `BotStatus`  [INFERRED]
  backend/app/main.py → backend/app/enums.py
- `promote_live()` --uses--> `BotStatus`  [INFERRED]
  backend/app/main.py → backend/app/enums.py
- `start_demo()` --uses--> `BotStatus`  [INFERRED]
  backend/app/main.py → backend/app/enums.py

## Import Cycles
- None detected.

## Communities (30 total, 3 thin omitted)

### Community 0 - "pipeline.py"
Cohesion: 0.08
Nodes (77): System prompt — decision constitution. No MCP. No WAIT. OANDA numbers only., _card(), ensure_vision(), PipelineInput, PipelineOutput, _plan(), publish(), Any (+69 more)

### Community 1 - "app/main.py"
Cohesion: 0.07
Nodes (87): AliasIn, BotCreateIn, ChatIn, ExecuteIn, InstrumentOut, KillSwitchIn, LoginIn, PromoteLiveIn (+79 more)

### Community 2 - "App.tsx"
Cohesion: 0.08
Nodes (42): App(), Guard(), KLineChartPro(), Modals(), Overlay(), RecCard(), more, primary (+34 more)

### Community 3 - "OandaClient"
Cohesion: 0.06
Nodes (32): get_settings(), Settings, AssetClass, FeedStatus, MetaApiClient, OrderRequest, OrderResult, MetaApi execution. SL always attached. Idempotent. Never used for analysis… (+24 more)

### Community 4 - "models.py"
Cohesion: 0.07
Nodes (37): async_sessionmaker, current_operator(), AsyncSession, AgentRun, BacktestRun, Base, BotRationale, BotVersion (+29 more)

### Community 5 - "dependencies"
Cohesion: 0.05
Nodes (36): @capacitor/android, @capacitor/core, @copilotkit/react-core, @copilotkit/react-ui, dependencies, @capacitor/android, @capacitor/core, @copilotkit/react-core (+28 more)

### Community 6 - "devDependencies"
Cohesion: 0.07
Nodes (27): autoprefixer, @capacitor/cli, devDependencies, autoprefixer, @capacitor/cli, jsdom, postcss, tailwindcss (+19 more)

### Community 7 - "handle_telegram_update"
Cohesion: 0.10
Nodes (14): Any, Do not send deprecated temperature/top_p on models that reject them., Native agent tools (NOT MCP). Read/analysis only., Invoke Claude Agent SDK. Graceful degradation when the key is missing., run_claude(), sampling_kwargs(), tool_specs(), handle_telegram_update() (+6 more)

### Community 8 - "compilerOptions"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 9 - "tools.py"
Cohesion: 0.17
Nodes (17): compute_atr(), compute_structure(), compute_zones(), get_candles(), get_exposure_tool(), get_news(), get_price(), Any (+9 more)

### Community 10 - "run_backtest"
Cohesion: 0.30
Nodes (12): apply_costs(), BacktestResult, CostModel, max_drawdown(), profit_factor(), Mandatory cost model. Sample floor → 'Insufficient data'. Never fabricate %., Simple level-touch simulator. Indicators NEVER come from Twelve Data., run_backtest() (+4 more)

### Community 11 - "check_bot_safety"
Cohesion: 0.41
Nodes (9): check_bot_safety(), Bot safety gates (16.9). Kill switch overrides everything. Mind may VETO, never…, SafetyContext, SafetyVerdict, _ok(), test_kill_switch_overrides_everything(), test_missing_rationale_no_order(), test_unmapped_alias_blocks_bot_order() (+1 more)

### Community 12 - "resolve_alias"
Cohesion: 0.32
Nodes (8): AliasResolution, canonical_id → execution_symbol. Unmapped = analyze OK, execute NEVER., resolve_alias(), validate_alias_payload(), test_mapped_and_tested_can_execute(), test_mapped_but_untested_cannot_execute(), test_payload_validation(), test_unmapped_analyze_ok_execute_never()

### Community 13 - "MainActivity.java"
Cohesion: 0.47
Nodes (4): android.os.Bundle, com.getcapacitor.BridgeActivity, MainActivity, Override

### Community 14 - "logging_conf.py"
Cohesion: 0.40
Nodes (4): JsonFormatter, Structured JSON logging. Never log secrets., setup_logging(), LogRecord

## Knowledge Gaps
- **61 isolated node(s):** `ModalName`, `State`, `*.json`, `more`, `primary` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OandaClient` connect `OandaClient` to `pipeline.py`, `tools.py`, `models.py`, `app/main.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `handle_telegram_update()` connect `handle_telegram_update` to `pipeline.py`, `app/main.py`, `OandaClient`, `models.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `Direction` connect `pipeline.py` to `app/main.py`, `OandaClient`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `Operator` (e.g. with `current_operator()` and `accounts()`) actually correct?**
  _`Operator` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `analyze()` (e.g. with `PipelineInput` and `SimilarCases`) actually correct?**
  _`analyze()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ModalName`, `State`, `*.json` to the rest of the system?**
  _61 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07502799552071669 - nodes in this community are weakly interconnected._