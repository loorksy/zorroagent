# Zorro runbook

Personal desk. One operator. Never commit `.env`.

## Environment

Copy `.env.example` to `.env`. Missing keys degrade health to `disconnected`; the app must not fabricate prices, win rates, or monthly returns.

| Variable | Role |
|---|---|
| `DATABASE_URL` | Postgres (`postgresql+asyncpg://…`) |
| `REDIS_URL` | Redis (Arq + rate limit). If down, `/healthz` redis is red; do not place orders. |
| `JWT_SECRET` / `APP_SECRET_KEY` / `ENCRYPTION_KEY` | Auth + MetaApi token at rest |
| `OPERATOR_EMAIL` / `OPERATOR_PASSWORD` | Bootstrap login |
| `OPERATOR_PIN` / `CONFIRMATION_PIN` | Promote-to-live |
| `ANTHROPIC_API_KEY` | Claude Agent SDK only. Models: `claude-fable-5`, `claude-opus-5`, `claude-opus-4-8`, `claude-sonnet-5`, `claude-opus-4-7` |
| `OANDA_API_KEY` / `OANDA_ACCOUNT_ID` / `OANDA_ENVIRONMENT` | **Sole** analysis/chart/indicator prices |
| `TWELVE_DATA_API_KEY` | Cross-check quotes only. Never indicators. |
| `PRICE_DIVERGENCE_BPS` | Default 15. Beyond this, banner + block new recs |
| `FINNHUB_API_KEY` | News + calendar |
| `METAAPI_TOKEN` / `METAAPI_ACCOUNT_ID` | Execution only. Analysis must run with this unset. |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ALLOWED_CHAT_ID` | Same brain as web. `/stopall` → `apply_kill_switch` |

## Start (local)

```bash
cp .env.example .env
docker compose up -d postgres redis   # if compose is present
cd backend && pip install -e ".[dev]"
alembic upgrade head                  # empty DB: apply migrations
uvicorn app.main:app --reload --port 8000

cd ../frontend && npm install && npm run dev
```

Worker (bot ticks, catalog refresh, incremental nightly backtest):

```bash
cd backend && arq app.workers.main.WorkerSettings
```

Telegram: set token, point webhook at `POST /api/telegram/webhook`. Commands: `/ask`, `/today`, `/rec`, `/bots`, `/stopall`, `/killoff`, `/link`.

## Health

- `GET /healthz` → `{db, redis, oanda, twelve, metaapi}` — **no `mcp` key**
- `GET /health` — same feeds, disclaimer. No `mcp` key.

## Tests

```bash
cd backend && pytest -q
cd frontend && npm test
python3 scripts/qa_screenshots.py   # Vite on :5173, Playwright + Google Chrome
```

## Android

```bash
cd frontend && npm run build && npm run cap:sync
# cap:sync copies dist/ → www/ then `cap sync android`
# Unsigned APK: open android/ in Android Studio, or
#   cd android && ./gradlew assembleDebug
# Requires ANDROID_HOME / Android SDK. This cloud image has neither.
```

Push notifications: Capacitor Android project is present (`MainActivity.java`). Compile path is `assembleDebug` after sync. Not exercised live here.

## Kill switch

One function: `app.bots.kill.apply_kill_switch`. Web `POST /api/kill-switch` and Telegram `/stopall` both call it. Do not add a second implementation.
