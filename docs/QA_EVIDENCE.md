# QA evidence pack — Appendix B + Appendix C

Repo: `loorksy/zorroagent`  
Branch: `cursor/ai-trading-assistant-47d6`  
PR: https://github.com/loorksy/zorroagent/pull/1  
Preferred base: `main`

**Git SHA (this pack):** `6ee18bd` (overlay implementation) + this docs commit.

Method: audit-as-untrusted. No live OANDA / Anthropic / MetaApi / Telegram secrets in this environment (no `.env`; `.env.example` only). Live labs that need those keys are **BLOCKED**, not faked. Live Test Connection is reported as **fail** when keys are missing — never a fake pass.

**B15 sentence is not used.** B0.3 is false (live OANDA Deep Analysis). **B0.11 is TRUE** (Settings overlay).

---

## B0 stop-conditions

| # | Condition | Status |
|---|---|---|
| 1 | Every route loads 1280 / 768 / 390 + RTL Arabic without crash | **TRUE** — Playwright smoke 64/64 `#main` present, 0 `pageerror` after `asList` fail-closed fix. Pack in `docs/qa-screenshots/`. |
| 2 | Automated tests for gates, fill-rule, alias, backtest, bot loop, kill, divergence | **TRUE** — `pytest -q` **101 passed**; `npm test` **16 passed**. |
| 3 | Live Deep Analysis XAU_USD + FX with real OANDA chart images | **FALSE / BLOCKED** — `OANDA_API_KEY` unset. No fabricated candles or BUY/SELL. |
| 4 | Bot CODE → MIND → DEMO fill; promote blocked without demo+PIN | **PARTIAL** — unit paths pass (`test_bot_loop.py`, `test_bot_safety.py`). Live demo fill **BLOCKED** (no MetaApi). Promote without demo/PIN returns 403. |
| 5 | Kill switch web + Telegram `/stopall` share one function | **TRUE** (code + tests). Live Telegram `/stopall` **BLOCKED** (no bot token). |
| 6 | Analysis works with MetaApi disconnected | **TRUE** — indicators import graph has no MetaApi; `test_feeds.py`. |
| 7 | Divergence beyond threshold blocks recs + banner | **TRUE** — `check_divergence` + UI `data-testid=price-banner` + screenshots. |
| 8 | UI matches AiChart desk family | **TRUE with gaps** — rail, tokens, bottom composer, one liquid-metal Send, no execute on thread card. Chart empty without OANDA. See B2. |
| 9 | EN / TR / AR complete; Arabic RTL | **TRUE** after skip-link overflow fix. Recaptured pack: AR-dark-390-ask-rec.png = 43870 bytes (was 2737 black). |
| 10 | This evidence file | **TRUE** (this document). |
| 11 | Settings overlay for all C2 keys works, tested, masked, and documented | **TRUE** — `GET/PUT /api/settings/providers` + Test per provider; secrets last-4 only; i18n EN/TR/AR; screenshots `docs/qa-screenshots/settings-providers.png` (dark) and `settings-providers-light.png`. See Appendix C below. |

Remaining **false** B0 items: **3** (live OANDA). **4** live demo fill is blocked (unit coverage exists). **B0.11 is true.**

---

## Commands run

```
cd /workspace/backend && python3 -m pytest -q
# exit 0 — 101 passed, 1 warning (passlib crypt deprecation)
# Appendix C: test_settings_overlay.py (GET last-4, overlay vs .env, unsaved Test, audit, no MCP)

cd /workspace/frontend && npm test
# exit 0 — 16 passed / 5 files (vitest) including settings.test.tsx

python3 /workspace/scripts/qa_settings_providers.py
# exit 0 — docs/qa-screenshots/settings-providers.png + settings-providers-light.png

python3 /workspace/scripts/qa_screenshots.py
# exit 0 — 180 PNGs, MIN_BYTES 8000 enforced
# Method: Playwright + /usr/local/bin/google-chrome --headless=new against Vite :5173 with /api mocked.

cd /workspace/frontend && npm run build
# exit 0 — vite build (tsc -b not used; vitest globals in tsconfig)

cd /workspace/frontend && mkdir -p www && cp -a dist/. www/ && npx cap sync android
# FAIL then FIX: first run "Could not find the web assets directory: ./www"
# After capacitor.config.json + valid capacitor.config.ts export + dist→www copy:
#   ✔ Copying web assets from dist to android/app/src/main/assets/public
#   Sync finished in 0.071s
# Unsigned APK: ANDROID_HOME unset; no sdkmanager/gradle wrapper execution. Lab 13 BLOCKED on SDK.

Playwright route smoke (object API payloads, asList fix):
# 16 routes × {1280-en, 768-en, 390-en, 390-ar} = 64 OK, 0 pageerror
```

### Failing then fixed (do not delete tests)

1. **Arabic 390/768 screenshots all 2737 bytes / solid black.** Cause: `.skip-link { left: -999px }` expanded RTL `scrollWidth`; Playwright captured the empty origin. Fix: clip/`clip-path` skip-link + `overflow-x: clip`. Test: `skip-link css does not use left:-999px`. Recapture sizes AR-dark-390-ask-rec **43870**.
2. **TR/AR leftover English** (`Insufficient data`, `Price data unreliable`, Account/Bots/Strategies raw strings). Fix: keys in en/tr/ar.json; i18n test already required key parity.
3. **`convs.map is not a function`** when `/api/conversations` returned `{}`. Same for recs/bots/accounts. Fix: `asList()` in `frontend/src/lib/api.ts`. Test: `asList fail-closes on object payloads`.
4. **Duplicate `useDesk` import** in Modals after a merge edit → Vite 500, empty `#root`. Removed duplicate. Route smoke 64/64.
5. **Capacitor CLI defaulted `webDir` to `www`** because `capacitor.config.ts` was a JSON blob, not an exported module. Fix: proper `export default` + `capacitor.config.json` + `cap:sync` copies `dist` → `www`.
6. Prior commit: execute on thread RecCard (forbidden) — already `surface="thread"` with no execute; test `execute absent on thread rec card`.

Never deleted a failing test to go green. Health assertion is `"mcp" not in body` (B3.10).

---

## Screenshot index (B2.5)

Method: `scripts/qa_screenshots.py` — real DOM, not mockups. Google Chrome headless. Vite mocked OANDA catalog + rec card seed.

Pattern: `docs/qa-screenshots/{en\|tr\|ar}-{light\|dark}-{390\|768\|1280}-{scene}.png`  
Scenes: `ask-empty`, `ask-rec`, `banner`, `today`, `chart`, `bots`, `confirm-rec`, `execute`, `settings`, `kill`  
Count: **180 files**.

| Scene | What it proves |
|---|---|
| ask-empty | Chat-first desk, bottom composer, collapsed Agent Log |
| ask-rec | Compact BUY card, `claude-fable-5`, no Execute on thread, TP2 present |
| banner | Red `Price data unreliable` / TR `Fiyat verisi güvenilir değil` / AR `بيانات السعر غير موثوقة` |
| today | Scan Today secondary list |
| chart | KLineChart Pro surface, Clear drawings, TF row 1m–1D |
| bots | Bots dashboard |
| confirm-rec | Recommendation confirmation modal + saved RecCard (execute after save) |
| execute | Execute modal after save (lots once) |
| settings | Model picker visible (Quick/Deep defaults, five Claude ids) |
| kill | Kill-switch modal; web path `POST /api/kill-switch` |

Note: `ask-empty` and `banner` are often identical at capture time because Shell sets `banner=unreliable` whenever OANDA health ≠ connected (correct product behavior with keys missing). Chart grid is empty: mock candles `[]` and live OANDA BLOCKED.

RTL: `ar-dark-1280-ask-rec.png` — rail on inline-start (right), composer Send on inline-start, ActiveMarker start-edge. `dir=rtl` via `applyDir("ar")`.

Compared to cloned AiChart console (not the marketing site): same family — white/black paper, muted `#f2f2f2`, radius ~0.625rem, left/start rail, chat-first, quiet chrome. Not copied: gold-only, MCP card, billing, TradingView.

---

## Labs 1–13

| Lab | Result |
|---|---|
| 1 Ask/Deep XAU_USD + FX live | **BLOCKED** — no `OANDA_API_KEY` / Anthropic. UI path exists; Deep without vision refuses `"Chart vision unavailable"` (`test_deep_without_vision_refuses`). Seeded card screenshots only. |
| 2 Fill rule close vs touch | **PASS (unit)** — `test_close_touch_same_level_refused`. Live force-close **BLOCKED**. |
| 3 Scan Today | **PASS (UI)** whale-free. Live Finnhub/OANDA catalog **BLOCKED**. |
| 4 Chart drawings / TF / layout persist | **PASS (UI)** Clear drawings + TF buttons; `zorro.chart.layout` in localStorage. Live overlays **BLOCKED** (no candles). |
| 5 Build bot CODE→MIND→demo | **PASS (unit)** `run_code_mind_tick`. Live demo **BLOCKED** (no MetaApi). |
| 6 Alias map live activate | **PASS (unit)** suffixes `m`, `pro`, `.m`, `.pro`, `#`; `EUR_USD`→`EURUSDm`; unmapped live bot cannot order. Live MetaApi map **BLOCKED**. |
| 7 Kill web + Telegram `/stopall` | **PASS (unit + UI)** shared `apply_kill_switch`. Live `/stopall` **BLOCKED** (no `TELEGRAM_BOT_TOKEN`). |
| 8 MetaApi invalid, Deep still OANDA | **PASS (unit)** indicators never import MetaApi. Live Deep **BLOCKED** (no OANDA). |
| 9 Divergence banner + block | **PASS (unit + UI)**. Live Twelve≠OANDA **BLOCKED**. |
| 10 Five models; Quick cannot save tradeable | **PASS (unit)** `test_quick_scan_is_non_tradeable`; picker only the five Claude ids. Live vision Deep **BLOCKED**. |
| 11 i18n + RTL | **PASS** key parity test; AR RTL screenshots; TR banner/insufficient translated. |
| 12 Responsive 390/768/1280 | **PASS** after header compact + skip-link fix; 390 composer usable; rail drawer via hamburger. |
| 13 APK | **PARTIAL** — `npm run build` OK; `npx cap sync android` OK after www workaround. `assembleDebug` **BLOCKED** (`ANDROID_HOME` unset). Push path compiled into Capacitor Android project only. |

---

## B5 product checklist

| Item | Verdict | Evidence |
|---|---|---|
| Single operator only | PASS | `operators` table; no multi-tenant user directory |
| Three daily modes Ask / Scan Today / Build | PASS | Shell primary nav; screenshots |
| All other pages secondary | PASS | `more` rail links |
| No MCP server/settings/deps | PASS | B6 grep; `/healthz` has no mcp key; `/api/routes` documents `"mcp": false` as exclusion |
| Zustand not Redux; Arq not Celery | PASS | `frontend` zustand; `arq app.workers.main.WorkerSettings` |
| Finnhub calendar; Twelve fallback only | PASS | feeds modules; Twelve never in indicators |
| OANDA sole analysis prices | PASS | `test_oanda_candles_compute_atr`; constitution |
| Full OANDA instrument picker | PASS | searchable modal `data-testid=symbol-filter` |
| Broker suffix alias map | PASS | `test_alias_suffix.py` |
| No free-text analysis ticker | PASS | Ask uses picker; Account canonical from picker |
| BUY/SELL only; WAIT invalid | PASS | schema + enum tests |
| Three layers on every rec | PASS | pipeline EntryPlan fields |
| Fill-rule coherence | PASS | close+touch rejected |
| ATR buffer on stop | PASS | `test_stop_on_raw_level_without_atr_buffer_rejected` |
| ≥2 take profits | PASS | missing TP2 rejected |
| Chart vision mandatory on Deep | PASS | `test_deep_without_vision_refuses` |
| Similar cases on the card | PASS | RecCard + insufficient label |
| Confidence: real stats or Insufficient data | PASS | `SimilarCases.card_payload` |
| Risk in R; lots only in execute modal | PASS | execute modal lots; thread card has no lots |
| Gates 1–6 + never flip | PASS | `test_gates.py` / `test_gates_paths.py` |
| Session / weekend handling | PASS | gate session_blocked |
| Bots = code + mind before fill | PASS | `test_bot_loop.py` |
| Demo mandatory before live | PASS | promote 403 |
| PIN or typed symbol to promote | PASS | `test_promote_without_pin_or_symbol_is_403` |
| Version + rollback | PASS | `test_versioning.py` |
| Kill switch web + Telegram | PASS | shared function |
| Execution log ≠ recommendation log | PASS | `executions` / `demo_executions` / `recommendations` |
| Performance in R not blended P&L | PASS | review/demo notes; never monthly return % |
| Exposure view + correlation warning | PASS | `test_exposure_correlation_warning` |
| Weekly/monthly review job | PASS | `lessons_job` in worker |
| Five Anthropic multimodal models only | PASS | picker grep test |
| Telegram same brain / card / rationale | PASS | `/rec` card fields; `/stopall` shared kill |
| Disclaimer visible; no monthly return % | PASS | footer + i18n; B6 |
| ui-ux-pro-max applied; gstack QA role run | PASS | skip-link, 44px targets, focus rings, one primary CTA, dialog aria-modal; this pack is the QA role. **No git tag** (Release Manager). |
| Graphify this repo + AiChart doctrine | PASS | `graphify-out/GRAPH_REPORT.md` — 782 nodes; god nodes Operator/Direction/analyze()/OandaClient not TODO |
| Provider credentials configurable in Settings | **PASS** | Settings groups Market/News/Execution/Models/Telegram/System; `PUT /api/settings/providers`; `test_anthropic_key_settable_via_api` |
| Secrets masked; last-4 only on read | **PASS** | GET never returns full secret (`test_get_providers_never_returns_full_secret`); UI `type=password` + last-4; copy forbidden |
| Test Connection per provider | **PASS (mocked + honest fail)** | `POST /api/settings/providers/{provider}/test` uses unsaved form body (`test_test_endpoint_uses_unsaved_form_value`). Live keys missing → fail, not a fake pass (see C Test results). |
| Settings overrides .env; empty falls back to .env | **PASS** | `test_overlay_overrides_env`; `test_empty_overlay_falls_back_to_env`; OandaClient re-reads overlay without restart |

---

## B6 grep (app code)

Searched `backend/app` and `frontend/src` (not lockfiles, not this brief).

| Token | Result |
|---|---|
| mcp / @modelcontextprotocol / mcp.true-north | Only exclusion comments + `"mcp": False` on `/api/routes`. `/healthz` has **no** mcp key. `test_b6_static.py` |
| WAIT as recommendation direction | Not in Direction enum. Mentions are "WAIT is forbidden" |
| openai, gpt-4, gemini, grok in picker | Absent from Shell + Settings |
| celery, redux | Absent from app code |
| monthly return / guaranteed | Disclaimer "does not promise" / i18n "No monthly return is promised" |
| whale, polymarket, okx, bitget, bingx | No hits in app code |
| raw ticker `<input>` in analysis | Ask/analysis use picker; symbol modal is `type=search` filter |
| executeRecommendation in chat artifact | Execute is not an agent tool (`test_execute_not_an_agent_tool`) |
| MetaApi in OHLC/indicator modules | `test_indicators_do_not_use_metaapi` |

---

## B3 test map

| Area | Files |
|---|---|
| 3.1 Gates | `test_gates.py`, `test_gates_paths.py` |
| 3.2 Schema | `test_schema_card.py`, RecCard exhaustive switch |
| 3.3 Feeds | `test_feeds.py`, `test_divergence.py` |
| 3.4 Aliases | `test_alias.py`, `test_alias_suffix.py` |
| 3.5 Bots | `test_bot_loop.py`, `test_bot_safety.py`, `test_versioning.py` |
| 3.6 Execution | `test_execution.py` |
| 3.7 Backtest | `test_backtest.py`, `test_backtest_extra.py` |
| 3.8 i18n | `test_i18n_keys.py`, desk.test i18n keys |
| 3.9 Auth/security | `test_api_auth.py`, `test_security.py` |
| 3.10 Health | `test_api_health.py` `/healthz` |
| 3.11 Frontend | `desk.test.tsx`, `api.test.ts`, `login.test.tsx`, `build.test.tsx`, `settings.test.tsx` |
| C overlay | `test_settings_overlay.py` |
| B6 static | `test_b6_static.py` |

**Counts:** backend **101 passed** / 0 failed; frontend **16 passed** / 0 failed.

---

## Appendix C — Settings-owned environment

Principle: `.env` is bootstrap only. After first launch the operator configures the desk from Settings. Overlay wins when non-empty; empty falls back to `.env`. Trading clients resolve through `get_setting()` in `app/runtime_config.py`, not raw `os.environ` in client modules.

### C2 keys in Settings (Save / Test / Clear)

| Group | Keys |
|---|---|
| Market data | `OANDA_API_TOKEN`, `OANDA_ACCOUNT_ID`, `OANDA_ENV` (practice\|live), `TWELVE_DATA_API_KEY`, price-divergence bps |
| News | `FINNHUB_API_KEY` |
| Execution | `METAAPI_TOKEN`, `METAAPI_ACCOUNT_ID`, broker/server, account type demo\|live; alias map linked to Account |
| Models | `ANTHROPIC_API_KEY`, default quick/deep; five-model picker remains |
| Telegram | `TELEGRAM_BOT_TOKEN`, generate/revoke linking code |
| Optional | Sentry DSN, public app URL, webhook base URL |
| System (read-only) | Postgres / Redis connected\|disconnected — **no URLs with passwords** |

Env-only (never in the browser): `DATABASE_URL`, `REDIS_URL`, `ENCRYPTION_KEY` / `SETTINGS_SECRET`, bind host/port. PUT of those or any MCP key is **400**.

Encrypted at rest (`encrypted_secrets` + Fernet via `ENCRYPTION_KEY`/`SETTINGS_SECRET`). Audit log stores **key name + action + time**, never the secret (`settings_audit`).

API hot-reload: overlay is in-memory; clients read `get_setting()` per call. Arq workers call `load_overlay_from_db` at the start of each job — **no worker restart for API keys**. Documented in `docs/RUNBOOK.md`.

### Test Connection results (this environment)

Live keys are **not present**. Results below are honest fails, not faked passes.

| Provider | Ping | Result |
|---|---|---|
| OANDA | instruments | **FAIL** `OANDA is not configured.` (no network when missing) |
| Twelve Data | quote | **FAIL** `Twelve Data is not configured.` |
| Finnhub | calendar | **FAIL** `Finnhub is not configured.` |
| MetaApi | account | **FAIL** `MetaApi is not configured.` |
| Anthropic | models.list | **FAIL** `Anthropic is not configured.` |
| Telegram | getMe | **FAIL** `Telegram is not configured.` |

Mocked httpx (unsaved form value): OANDA Test sends `Authorization: Bearer <unsaved>` and returns pass; Anthropic Test sends `x-api-key: sk-unsaved-ANTH`. See `backend/tests/test_settings_overlay.py`.

PUT `ANTHROPIC_API_KEY=sk-ant-SUPERSECRET-xyz9876ABCD` then GET: full secret **absent**; `last4=ABCD`, `source=settings`.

### Grep proof — trading keys are not ONLY `os.environ`

Client modules call `get_setting(...)`. Overlay reads Settings DB then `os.environ` as fallback inside `runtime_config.py` only.

| Module | API key resolution |
|---|---|
| `feeds/oanda.py` | `get_setting("OANDA_API_TOKEN")` |
| `feeds/twelve.py` | `get_setting("TWELVE_DATA_API_KEY")` (base URL may use env) |
| `feeds/finnhub.py` | `get_setting("FINNHUB_API_KEY")` (base URL may use env) |
| `execution/metaapi.py` | `get_setting("METAAPI_TOKEN")` |
| `agent/runtime.py` | `get_setting("ANTHROPIC_API_KEY")` then temporary env inject for the Claude SDK **after** overlay resolve |
| `telegram/bot.py` | `get_setting("TELEGRAM_ALLOWED_CHAT_ID")` / link code |

No MCP providers in overlay catalog (`test_no_mcp_in_overlay_catalog`, B6 grep).

Screenshots: `docs/qa-screenshots/settings-providers.png` (dark 1280), `docs/qa-screenshots/settings-providers-light.png`. Groups, masked secrets, last-4, Test/Save/Clear, no MCP.

---

---

## B7 performance / reliability smoke

- Analyze latency: `logging.getLogger("zorro.latency").info("analyze_latency", extra={tier, elapsed_ms, canonical_id})` in `app/main.py`. Live p95 **not measured** (no Anthropic/OANDA).
- SSE/WebSocket buffer: not load-tested here.
- Redis down: `/healthz` reports redis independently. Live redis-kill **not run** in this pod.
- Postgres: `cd backend && alembic upgrade head` (see RUNBOOK). Empty-DB path documented; not applied against a live empty cluster here (no local Postgres daemon verified).
- Arq: `arq app.workers.main.WorkerSettings` — functions include `bot_tick`, `feed_divergence_job`, `nightly_backtest` (incremental; no full replay). Worker process **not kept running** in this audit.

---

## B8 accessibility + i18n

- Contrast: light `#fff/#000`, dark inverted neutrals; semantic green/red/amber/blue only for trading.
- Buttons: `aria-label` on kill, theme, settings, close, skip link.
- Dialogs: `role=dialog` `aria-modal=true` `aria-labelledby=modal-title`; Escape closes; Tab cycles in overlay.
- Arabic: `document.documentElement.dir = rtl` when AR selected; persists via `zorro.lang` + zustand.
- Skip link: clip technique (not physical negative left).

---

## B9 Telegram parity

- `/rec` returns the same card fields as the web RecCard (direction, entry, SL, TPs, fill_rule, next_action, similar, model_id).
- `/stopall` → `apply_kill_switch(db, engaged=True, reason="telegram:/stopall")` — **not** a second KillSwitch writer.
- `/link` returns a linking code for Settings.
- Live webhook **BLOCKED** (no token).

---

## B10 ui-ux-pro-max

Applied from `/tmp/refs/ui-ux-pro-max-skill` quick-reference during design QA:

- One primary CTA (liquid-metal Send only; other actions muted/foreground)
- Touch 44px mobile / 40px lg
- Visible `:focus-visible` rings
- Empty/error/offline/unreliable/gate-refusal states (banner, chart pick-symbol empty, insufficient data — no dumped JSON)
- Dark via class `.dark` on `<html>`
- Radius token 0.625rem
- Competing `bg-accent` (buy-green chrome) removed from non-trading buttons

Desk remains AiChart-family, not generic admin.

---

## B11 Graphify

`graphify-out/GRAPH_REPORT.md` (commit `ea16d5e` graph, still lists gates/schema/kill/loop/alias/feeds). God nodes: `Operator`, `Direction`, `analyze()`, `OandaClient`, `FillRule` — not TODO/placeholder.

---

## B12 gstack roles

**Eng Manager — remaining defects by severity**

- **P0 (external):** Live OANDA + Anthropic missing → cannot prove Deep vision BUY/SELL on XAU_USD/FX. Do not ship a "live analysis works" claim until keys exist and Lab 1 is re-run.
- **P1:** Unsigned APK not produced (`ANDROID_HOME` unset). Capacitor sync now works.
- **P1:** Live Telegram `/stopall` and live demo fill unproven.
- **P2:** Chart screenshots show empty grid (no candles). Seed mock should eventually include a short OHLCV fixture so overlays are visible without keys.
- **P2:** `ask-empty` vs `banner` shots duplicate when health is disconnected.
- **P3:** Assistant seed string "Deep Analysis" in screenshots is English even on AR (QA seed, not an i18n key).
- **P3:** Header model picker still `hidden md:block`; Settings page shows all five models (B2.5 satisfied there).

**QA:** Failed visual pack (black AR) reproduced → skip-link fix → test added → pack recaptured. Failed route smoke (`convs.map`) → `asList` → test added → 64/64. Full suite re-run: 89 + 14 green.

**Release Manager:** **No git tag. No release.** PR stays on `cursor/ai-trading-assistant-47d6`.

**Doc Engineer:** `docs/QA_EVIDENCE.md` (this file) + `docs/RUNBOOK.md`.

---

## B13 fix loop log

| Fail | Repro | Fix | Test | Re-run |
|---|---|---|---|---|
| AR screenshots black | PNG 2737 bytes; sliver on 1280 | skip-link clip; overflow-x clip | desk.test skip-link CSS | pack recapture, all AR > 8KB |
| TR/AR English leftovers | grep Account/Bots/Modals | i18n keys | test_i18n_keys | 89 pytest |
| List API crash | `convs.map is not a function` | `asList()` | api.test.ts | 64/64 routes |
| Modals Vite 500 | duplicate import | remove dup | route smoke | 200 on Modals.tsx |
| cap sync www | CLI ignored JSON-as-ts | export default + www copy | `npx cap sync` OK | Lab 13 |

---

## Known remaining risks (honest)

1. Live market data, LLM vision, broker fills, and Telegram are **unproven in this environment**. Health will show disconnected until keys are present.
2. p95 analyze latency, Redis-down order corruption, and empty-DB alembic were **not** executed against real services here.
3. Android APK binary is **not** in the repo (`*.apk` gitignored; SDK missing).
4. ManagePullRequest tool is **not in this agent's catalog**; PR body was not edited via that tool. Suggested Appendix C addition is below. PR URL remains https://github.com/loorksy/zorroagent/pull/1
5. Graphify report SHA may lag the latest commit until `graphify update .` is re-run.
6. Live Test Connection against OANDA/Anthropic/MetaApi/Finnhub/Twelve/Telegram **failed honestly** (keys missing). Mocked httpx tests prove unsaved form values are the ones sent.

---

## Suggested PR body addition

```
## QA (Appendix B)
Evidence: docs/QA_EVIDENCE.md
Runbook: docs/RUNBOOK.md
Screenshots: docs/qa-screenshots/ (180 Playwright Chrome captures + settings-providers.png)

pytest 101 passed · vitest 16 passed

Live OANDA Deep Analysis: BLOCKED (no keys) — B0.3 false.
Do not treat this PR as live-feed certified.

## Appendix C — Settings-owned environment
Trading credentials are editable in Settings (encrypted at rest, last-4 on GET).
Settings overlay overrides .env; empty falls back to .env.
Test Connection per provider; missing keys fail honestly (not faked).
API clients hot-reload; Arq workers re-read overlay at the start of each job.
B0.11 TRUE. No MCP.
```

---

I am **not** done under B0: item 3 is false. This pack is accurate about that.
