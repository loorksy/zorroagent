# Graph Report - workspace  (2026-08-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 782 nodes · 1928 edges · 49 communities (38 shown, 11 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 260 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ea16d5e5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app/main.py
- App.tsx
- test_gates_paths.py
- OandaClient
- pipeline.py
- analyze
- Direction
- dependencies
- run_backtest
- MetaApiClient
- bot.py
- devDependencies
- compilerOptions
- Decision Constitution (ported from AiChart EXTRACTED doctrine)
- Design System Master File
- test_security.py
- Zorro AI Trading Assistant - UI Screenshots
- qa_screenshots.py
- MainActivity.java
- logging_conf.py
- Three daily modes (gstack Designer + UI/UX Pro Max)
- test_i18n_keys.py
- OANDA catalog + alias mapping + feed reconciliation
- Architecture
- Route map (auth, REST/WS, native agent tools). No MCP.
- test_api_auth.py
- ask.md
- build.md
- today.md
- agent-roles.md
- backtest.md
- bots-runbook.md
- graphify-aichart.md
- schema.md
- vite-env.d.ts
- zorro-backend

## God Nodes (most connected - your core abstractions)
1. `Operator` - 43 edges
2. `Direction` - 41 edges
3. `Base` - 29 edges
4. `analyze()` - 29 edges
5. `PlanType` - 26 edges
6. `useDesk` - 26 edges
7. `FillRule` - 25 edges
8. `OandaClient` - 24 edges
9. `EntryPlan` - 23 edges
10. `get_settings()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `test_wait_is_not_a_direction()` --uses--> `Direction`  [INFERRED]
  backend/tests/test_gates.py → backend/app/enums.py
- `analyze()` --uses--> `SimilarCases`  [INFERRED]
  backend/app/main.py → backend/app/agent/pipeline.py
- `PipelineInput` --uses--> `ActivationRule`  [INFERRED]
  backend/app/agent/pipeline.py → backend/app/domain/fill_rules.py
- `PipelineInput` --uses--> `Direction`  [INFERRED]
  backend/app/agent/pipeline.py → backend/app/enums.py
- `PipelineInput` --uses--> `FillRule`  [INFERRED]
  backend/app/agent/pipeline.py → backend/app/enums.py

## Import Cycles
- None detected.

## Communities (49 total, 11 thin omitted)

### Community 0 - "app/main.py"
Cohesion: 0.06
Nodes (107): AliasIn, AnalyzeIn, BotCreateIn, ChatIn, ExecuteIn, InstrumentOut, KillSwitchIn, LoginIn (+99 more)

### Community 1 - "App.tsx"
Cohesion: 0.08
Nodes (44): App(), Guard(), KLineChartPro(), Modals(), Overlay(), cardKind, RecCard(), more (+36 more)

### Community 2 - "test_gates_paths.py"
Cohesion: 0.10
Nodes (60): ActivationRule, CoherenceProblem, EntryPlan, Fill-rule coherence. Ported from AiChart EXTRACTED doctrine…, Machine-checkable activation. Must agree with activation_condition text., resolve_invalidation_mode(), reward_to_risk(), _same_level() (+52 more)

### Community 3 - "OandaClient"
Cohesion: 0.06
Nodes (40): async_sessionmaker, current_operator(), AsyncSession, get_settings(), Settings, Instrument, create_all(), get_db() (+32 more)

### Community 4 - "pipeline.py"
Cohesion: 0.12
Nodes (36): System prompt — decision constitution. No MCP. No WAIT. OANDA numbers only., _card(), ensure_vision(), PipelineInput, PipelineOutput, _plan(), publish(), Any (+28 more)

### Community 5 - "analyze"
Cohesion: 0.08
Nodes (33): compute_atr(), compute_structure(), compute_zones(), get_candles(), get_exposure_tool(), get_news(), get_price(), Any (+25 more)

### Community 6 - "Direction"
Cohesion: 0.14
Nodes (36): kill_blocks_orders(), Single kill-switch implementation used by the web API AND Telegram /stopall. Do…, Unit-level predicate: an engaged switch forbids every order path., CodeCandidate, execution_table_for(), MindResult, CODE → MIND rationale → order. Mind may VETO; it never flips direction., One bot tick. Tables stay separate: demo_executions vs executions. (+28 more)

### Community 7 - "dependencies"
Cohesion: 0.05
Nodes (36): @capacitor/android, @capacitor/core, @copilotkit/react-core, @copilotkit/react-ui, dependencies, @capacitor/android, @capacitor/core, @copilotkit/react-core (+28 more)

### Community 8 - "run_backtest"
Cohesion: 0.13
Nodes (28): apply_costs(), BacktestResult, CostModel, CostModelRequired, incremental_backtest(), IncrementState, max_drawdown(), oos_fragility_tag() (+20 more)

### Community 9 - "MetaApiClient"
Cohesion: 0.11
Nodes (21): MetaApiClient, OrderRequest, OrderResult, MetaApi execution. SL always attached. Idempotent. Never used for analysis…, AliasResolution, apply_broker_suffix(), canonical_id → execution_symbol. Unmapped = analyze OK, execute NEVER., EUR_USD → EURUSD. XAU_USD → XAUUSD. (+13 more)

### Community 10 - "bot.py"
Cohesion: 0.08
Nodes (19): Any, Do not send deprecated temperature/top_p on models that reject them., Native agent tools (NOT MCP). Read/analysis only., Invoke Claude Agent SDK. Graceful degradation when the key is missing., run_claude(), sampling_kwargs(), tool_specs(), apply_kill_switch() (+11 more)

### Community 11 - "devDependencies"
Cohesion: 0.07
Nodes (27): autoprefixer, @capacitor/cli, devDependencies, autoprefixer, @capacitor/cli, jsdom, postcss, tailwindcss (+19 more)

### Community 12 - "compilerOptions"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 13 - "Decision Constitution (ported from AiChart EXTRACTED doctrine)"
Cohesion: 0.10
Nodes (18): Card discipline, Decision authority, Decision Constitution (ported from AiChart EXTRACTED doctrine), Gate chain (in order, never flip direction), Identity, Vision loop, What was NOT copied, Android (+10 more)

### Community 14 - "Design System Master File"
Cohesion: 0.11
Nodes (17): Additional Forbidden Patterns, Anti-Patterns (Do NOT Use), Buttons, Cards, Color Palette, Component Specs, Design System Master File, Global Rules (+9 more)

### Community 15 - "test_security.py"
Cohesion: 0.20
Nodes (7): compose_with_news(), news_cannot_override_constitution(), Prompt-injection defense for untrusted news/calendar text. External copy cannot…, True when the constitution still governs the composed prompt., wrap_untrusted(), B3.9 auth, rate limit, prompt injection, no MetaApi token in browser JSON., test_prompt_injection_in_news_cannot_change_system_rules()

### Community 16 - "Zorro AI Trading Assistant - UI Screenshots"
Cohesion: 0.25
Nodes (7): Capture Environment, Desktop Views (~1280x800), Features Demonstrated, Mobile Views (~400x924), Screenshots, Technical Notes, Zorro AI Trading Assistant - UI Screenshots

### Community 17 - "qa_screenshots.py"
Cohesion: 0.48
Nodes (6): apply_state(), mock(), open_desk(), Playwright visual pack: EN/TR/AR × light/dark × 390/768/1280. Method: Google…, run(), shot()

### Community 18 - "MainActivity.java"
Cohesion: 0.47
Nodes (4): android.os.Bundle, com.getcapacitor.BridgeActivity, MainActivity, Override

### Community 19 - "logging_conf.py"
Cohesion: 0.40
Nodes (4): JsonFormatter, Structured JSON logging. Never log secrets., setup_logging(), LogRecord

### Community 20 - "Three daily modes (gstack Designer + UI/UX Pro Max)"
Cohesion: 0.33
Nodes (5): Mode 1 — Ask (`/`), Mode 2 — Scan Today (`/today`), Mode 3 — Build (`/build`), Secondary nav, Three daily modes (gstack Designer + UI/UX Pro Max)

### Community 21 - "test_i18n_keys.py"
Cohesion: 0.50
Nodes (3): leaves(), Fail if EN/TR/AR JSON keys diverge., test_i18n_keys_match()

### Community 22 - "OANDA catalog + alias mapping + feed reconciliation"
Cohesion: 0.40
Nodes (4): Alias map, Catalog, OANDA catalog + alias mapping + feed reconciliation, Reconciliation

### Community 24 - "Architecture"
Cohesion: 0.50
Nodes (3): Architecture, Daily UI, Layers

### Community 25 - "Route map (auth, REST/WS, native agent tools). No MCP."
Cohesion: 0.50
Nodes (3): Primary, Route map (auth, REST/WS, native agent tools). No MCP., Secondary

## Knowledge Gaps
- **112 isolated node(s):** `zorro-backend`, `name`, `private`, `version`, `type` (+107 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Direction` connect `Direction` to `app/main.py`, `test_gates_paths.py`, `pipeline.py`, `run_backtest`, `MetaApiClient`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `handle_telegram_update()` connect `bot.py` to `app/main.py`, `OandaClient`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `OandaClient` connect `OandaClient` to `app/main.py`, `pipeline.py`, `analyze`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `Operator` (e.g. with `current_operator()` and `accounts()`) actually correct?**
  _`Operator` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `Direction` (e.g. with `PipelineInput` and `AnalyzeIn`) actually correct?**
  _`Direction` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `analyze()` (e.g. with `PipelineInput` and `SimilarCases`) actually correct?**
  _`analyze()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `zorro-backend`, `name`, `private` to the rest of the system?**
  _112 weakly-connected nodes found - possible documentation gaps or missing edges._