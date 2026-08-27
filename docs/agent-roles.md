# Agent roles — adapted from TradingAgents and crewAI

**Runtime is Claude Agent SDK only.** TradingAgents' LangGraph and crewAI's
Crew runtime are **not** embedded.

| Zorro role | Pattern source | Adaptation |
|---|---|---|
| Technical Analyst | TradingAgents `market_analyst` | OANDA candles + Deep vision images. Evidence, not side. |
| Risk Manager | TradingAgents `conservative_debator` / risk_mgmt | R terms, ATR buffer, never lots. |
| News/Sentiment | TradingAgents `news_analyst` | Finnhub ranked by impact → gate G1 fact. |
| Bull Researcher | TradingAgents `bull_researcher` | Argues BUY from tools. Does not publish. |
| Bear Researcher | TradingAgents `bear_researcher` | Argues SELL from tools. Does not publish. |
| Debate Moderator / Synthesizer | TradingAgents `research_manager` + crewAI sequential process | **Must** pick BUY or SELL. WAIT forbidden. |
| Trader | TradingAgents `trader` | Binds levels + fill_rule. **No execution tool.** |
| Bot Rationale Writer | crewAI specialist task before action | Must write rationale before every bot fill. May VETO. Never flips direction. Never invents strategy. |

Quick Scan runs a short chain (technical, news, synthesizer, trader) and stays **non-tradeable**.
Deep runs the full debate and **requires vision** before gates.
