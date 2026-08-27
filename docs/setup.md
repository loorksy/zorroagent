# Setup

## Requirements

- Python 3.12, Node 22, Docker (optional)
- API keys in `.env` (see `.env.example`). Missing keys degrade gracefully:
  health reports `disconnected`; tests use fixtures; live numbers are never faked.

## Local

```bash
cp .env.example .env
docker compose up -d postgres redis
cd backend && pip install -e ".[dev]"
alembic upgrade head   # or rely on create_all on API boot
uvicorn app.main:app --reload --port 8000

cd ../frontend && npm install && npm run dev
```

Worker:

```bash
cd backend && arq app.workers.main.WorkerSettings
```

## Tests

```bash
cd backend && pytest -q
cd frontend && npm test
```

## Android

```bash
cd frontend && npm run build && npx cap sync android
# Open android/ in Android Studio. Unsigned APK only in this repo/environment.
```

## Telegram

Set `TELEGRAM_BOT_TOKEN` and point the webhook at `/api/telegram/webhook`.
Same brain as web. `/stopall` is the kill switch.
