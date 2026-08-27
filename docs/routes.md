# Route map (auth, REST/WS, native agent tools). No MCP.

## Primary

| Route | Auth | Backend | Agent tools |
|---|---|---|---|
| `/` Ask | JWT | `/api/chat` SSE, `/api/conversations`, `/api/models` | list_instruments, get_candles, get_price, get_news, capture_chart_images, get_similar_cases, get_lessons, get_exposure, compute_* |
| `/today` | JWT | `/api/recommendations`, `/api/price/{id}`, `/health` | none (desk) |
| `/build` | JWT | `/api/strategies`, `/api/bots` | none |

## Secondary

| Route | Auth | Backend |
|---|---|---|
| `/chart/:symbol?` | JWT | `/api/candles/{id}`, `/ws/ticks/{id}` |
| `/recommendations` `/recommendations/:id` | JWT | `/api/recommendations` |
| `/watchlist` | JWT | `/api/watchlist` |
| `/exposure` | JWT | `/api/exposure` (agent also has read-only get_exposure) |
| `/account` | JWT | `/api/accounts`, `/api/accounts/{id}/aliases` |
| `/strategies` `/new` `/:id/optimize` `/:id/versions` | JWT | `/api/strategies*` |
| `/demo` | JWT | `/api/demo` |
| `/bots` `/bots/:id` `/bots/:id/live` | JWT | `/api/bots*` |
| `/memory` | JWT | `/api/memory` |
| `/review` | JWT | `/api/review` |
| `/settings` | JWT | `/api/settings`, `/api/models` |
| `/history` | JWT | `/api/history` |
| `/login` | public | `POST /api/auth/login` |
| `/download` | public | static `GET /zorro.apk` |

Execution: `POST /api/execute` — never invoked from chat/New Analysis/Generate Recommendation.
Telegram webhook: `POST /api/telegram/webhook` including `/stopall`.
Live runtime: `GET /health`.
MCP: **none**.
