# Three daily modes (gstack Designer + UI/UX Pro Max)

Target: **simple professional trading desk — chat + chart + one card.**
No 40-widget wall. No crypto-exchange chrome.

Design system: `design-system/zorro-trading-assistant/MASTER.md`
(Minimalism & Swiss Style, Inter, dark-first with light mode, density 6, subtle motion).

## Mode 1 — Ask (`/`)

Primary surface. Conversation is the product.

Layout (desktop):
- Left: conversation list (collapsed on mobile).
- Center: chat transcript. Compact recommendation card inline when published.
- Right: live KLineChart Pro for the active canonical symbol (hidden until a
  symbol is selected from the searchable OANDA catalog).

Composer:
- Model picker (per conversation, persisted): Fable 5 / Opus 5 / Opus 4.8 /
  Sonnet 5 / Opus 4.7.
- Symbol picker (searchable modal, never free-text).
- Timeframe chips: 1m 5m 15m 1h 4h 1D.
- Tier: Quick Scan (default Sonnet 5, non-tradeable) vs Deep Analysis
  (default Fable 5, requires vision).
- Send. No "place trade" control in the composer.

Agent reasoning is never shown. "Agent Log" is a collapsed disclosure.

## Mode 2 — Scan Today (`/today`)

Operator's morning desk. Lists today's published recommendations, news
blackouts, feed health banner ("Price data unreliable" when OANDA/Twelve Data
diverge), and watchlist snapshots. One-click "Open in Ask" / "Open on Chart".
No auto-execution.

## Mode 3 — Build (`/build`)

Strategy / bot creation. Three paths:

1. **Library** — pick a versioned Python strategy template.
2. **Convert saved recommendation** — lock exact levels, no new rules.
3. **Draw / describe idea** — chart drawings + prose → strategy draft.

Mandatory demo before live. Promote-to-Live is a secondary page (`/bots/:id/live`).

## Secondary nav

Chart, Recommendations, Watchlist, Exposure, Account, Strategies, Demo, Bots,
Memory, Review, Settings, History. Bottom nav on mobile: Ask / Today / Build /
More.
