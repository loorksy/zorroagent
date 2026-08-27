"""Claude Agent SDK runtime. Roles are PATTERNS from TradingAgents/crewAI — not a second runtime.

READ/ANALYSIS tools only. Execution is never an agent tool.
"""

from __future__ import annotations

from typing import Any

from app.agent.constitution import CONSTITUTION, ROLE_PROMPTS
from app.enums import AnalysisTier, ClaudeModel, DEFAULT_DEEP, DEFAULT_QUICK, NO_SAMPLING_PARAMS


ALLOWED_MODELS = {m.value for m in ClaudeModel}


def resolve_model(model_id: str | None, tier: AnalysisTier, defaults: dict[str, str] | None = None) -> str:
    defaults = defaults or {}
    if model_id and model_id in ALLOWED_MODELS:
        return model_id
    if tier == AnalysisTier.DEEP:
        return defaults.get("deep_model") or DEFAULT_DEEP.value
    return defaults.get("quick_model") or DEFAULT_QUICK.value


def sampling_kwargs(model_id: str) -> dict[str, Any]:
    """Do not send deprecated temperature/top_p on models that reject them."""
    if model_id in {m.value for m in NO_SAMPLING_PARAMS} or model_id in ALLOWED_MODELS:
        return {}
    return {}


def system_prompt(tier: AnalysisTier, language: str) -> str:
    extra = {
        "en": "Reply in English.",
        "tr": "Türkçe yanıt ver.",
        "ar": "أجب بالعربية.",
    }.get(language, "Reply in the operator's language.")
    tier_line = (
        "This run is DEEP ANALYSIS. Vision is mandatory. Tradeable only if vision succeeds and gates pass."
        if tier == AnalysisTier.DEEP
        else "This run is QUICK SCAN. Numbers only. Label the result NON-TRADEABLE. Never silently upgrade to Deep."
    )
    return CONSTITUTION + "\n\n" + extra + "\n" + tier_line


ANALYSIS_TOOL_NAMES = [
    "list_instruments",
    "get_candles",
    "get_price",
    "get_spread",
    "get_news",
    "get_similar_cases",
    "get_lessons",
    "get_exposure",
    "capture_chart_images",
    "compute_atr",
    "compute_structure",
    "compute_zones",
]


def tool_specs() -> list[dict[str, Any]]:
    """Native agent tools (NOT MCP). Read/analysis only."""
    return [
        {"name": n, "kind": "read"} for n in ANALYSIS_TOOL_NAMES
    ]


async def run_claude(model_id: str, prompt: str, images: list[dict[str, Any]] | None = None) -> str:
    """Invoke Claude Agent SDK. Graceful degradation when the key is missing."""
    import os

    from app.runtime_config import get_setting

    api_key = get_setting("ANTHROPIC_API_KEY")
    if not api_key:
        return (
            "[agent disconnected] ANTHROPIC_API_KEY is not configured. "
            "Set it in Settings → Models. Analysis tools and gates still run; the model turn is skipped."
        )
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
    except ImportError:
        return "[agent disconnected] claude-agent-sdk is not installed."

    options = ClaudeAgentOptions(
        model=model_id,
        system_prompt=CONSTITUTION,
        **sampling_kwargs(model_id),
    )
    chunks: list[str] = []
    previous = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = api_key
    try:
        async for message in query(prompt=prompt, options=options):
            text = getattr(message, "text", None) or getattr(message, "content", None)
            if isinstance(text, str):
                chunks.append(text)
    finally:
        if previous is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = previous
    return "".join(chunks) or ""


def role_order(tier: AnalysisTier) -> list[str]:
    if tier == AnalysisTier.QUICK:
        return ["technical_analyst", "news_sentiment", "debate_moderator", "trader"]
    return [
        "technical_analyst",
        "risk_manager",
        "news_sentiment",
        "bull_researcher",
        "bear_researcher",
        "debate_moderator",
        "trader",
    ]


def render_role_prompt(role: str) -> str:
    return ROLE_PROMPTS[role]
