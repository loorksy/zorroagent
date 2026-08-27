# Bots runbook (CODE + MIND)

1. Create via library / convert saved recommendation (lock exact levels) / draw-describe.
2. Every code change is a **new version**. Live keeps current until explicit activate.
3. **Mandatory demo** on a demo MetaApi account.
4. Promote-to-live: demo success + modal + typed canonical symbol or PIN.
5. Bind the bot to **exactly one** broker account.
6. Before **every** order:
   - Kill switch? stop.
   - 16 safety checks (`app/bots/safety.py`).
   - Bot Rationale Writer (Deep default model) writes rationale. Failure or VETO → **NO ORDER**.
   - Mind never flips direction and never invents strategy.
7. `/stopall` (Telegram) and Kill Switch (web) override everything.
8. Performance UI: sample size, max DD, profit factor. Never monthly return %.
