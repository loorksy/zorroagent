# Zorro — AI Trading Assistant

Single-operator, chat-first analyst desk. Analysis on **OANDA**. Execution on **MetaApi**.
Claude Agent SDK only. No MCP. No billing. No WAIT as an analytical outcome.

## Daily modes

- **Ask** `/` — chat + chart + one recommendation card
- **Scan Today** `/today`
- **Build** `/build` — library / convert rec / draw idea

## Quick start

See [docs/setup.md](docs/setup.md). Copy `.env.example` → `.env`.

```bash
docker compose up -d postgres redis
cd backend && pip install -e ".[dev]" && pytest -q
uvicorn app.main:app --reload --port 8000
cd ../frontend && npm install && npm run dev
```

## Decision constitution

Ported (not copied) from AiChart via Graphify deep EXTRACTED edges.
See [docs/decision-constitution.md](docs/decision-constitution.md).

## Disclaimer

Personal analysis, not fund management. Trading involves risk of loss.
This platform does not display or promise monthly return percentages.
