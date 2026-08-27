"""Canonical enums. WAIT is not a valid analytical outcome."""

from __future__ import annotations

from enum import StrEnum


class Direction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class AnalyticalBias(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class PlanType(StrEnum):
    IMMEDIATE = "immediate"
    ANTICIPATORY = "anticipatory"
    CONDITIONAL = "conditional"


class ExecutionStatus(StrEnum):
    ACTIVE_NOW = "active_now"
    AWAITING_ACTIVATION = "awaiting_activation"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    BLOCKED = "blocked"


class FillRule(StrEnum):
    MARKET = "market"
    TOUCH = "touch"
    CONFIRMING_CLOSE = "confirming_close"
    RETURN_TO_ZONE = "return_to_zone"


class InvalidationMode(StrEnum):
    TOUCH = "touch"
    CLOSE = "close"


class AnalysisTier(StrEnum):
    QUICK = "quick"
    DEEP = "deep"


class GateStatus(StrEnum):
    PASS = "pass"
    VETO = "veto"
    UNAVAILABLE = "unavailable"
    CONVERT = "convert"  # cost gate may convert plan_type only


class RecLifecycle(StrEnum):
    PENDING_ENTRY = "pending_entry"
    TRIGGERED = "triggered"
    TP1_HIT = "tp1_hit"
    TP2_HIT = "tp2_hit"
    TP3_HIT = "tp3_hit"
    SL_HIT = "sl_hit"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REFUSED = "refused"


class RecOutcome(StrEnum):
    PENDING = "pending"
    WIN_TP1 = "win_tp1"
    WIN_TP2 = "win_tp2"
    WIN_TP3 = "win_tp3"
    LOSS = "loss"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    INVALIDATED = "invalidated"
    REFUSED = "refused"


class AssetClass(StrEnum):
    FOREX = "forex"
    METAL = "metal"
    INDEX = "index"
    CFD = "cfd"
    CRYPTO = "crypto"
    OTHER = "other"


class BotMode(StrEnum):
    DEMO = "demo"
    LIVE = "live"


class BotStatus(StrEnum):
    DRAFT = "draft"
    DEMO_RUNNING = "demo_running"
    DEMO_STOPPED = "demo_stopped"
    LIVE_RUNNING = "live_running"
    LIVE_STOPPED = "live_stopped"
    KILLED = "killed"


class ClaudeModel(StrEnum):
    FABLE_5 = "claude-fable-5"
    OPUS_5 = "claude-opus-5"
    OPUS_4_8 = "claude-opus-4-8"
    SONNET_5 = "claude-sonnet-5"
    OPUS_4_7 = "claude-opus-4-7"


MODEL_CATALOG: dict[ClaudeModel, dict[str, str]] = {
    ClaudeModel.FABLE_5: {
        "label_en": "Fable 5 — strongest",
        "label_tr": "Fable 5 — en güçlü",
        "label_ar": "Fable 5 — الأقوى",
        "role": "Highest. Default for Deep Analysis.",
    },
    ClaudeModel.OPUS_5: {
        "label_en": "Opus 5 — deep agent",
        "label_tr": "Opus 5 — derin ajan",
        "label_ar": "Opus 5 — وكيل عميق",
        "role": "Strong agentic alternative for Deep.",
    },
    ClaudeModel.OPUS_4_8: {
        "label_en": "Opus 4.8 — previous flagship",
        "label_tr": "Opus 4.8 — الجيل السابق الرائد",
        "label_ar": "Opus 4.8 — الجيل السابق الرائد",
        "role": "Previous-gen flagship.",
    },
    ClaudeModel.SONNET_5: {
        "label_en": "Sonnet 5 — fast (Quick Scan default)",
        "label_tr": "Sonnet 5 — hızlı (Quick Scan varsayılan)",
        "label_ar": "Sonnet 5 — سريع (الافتراضي للمسح السريع)",
        "role": "Default for Quick Scan.",
    },
    ClaudeModel.OPUS_4_7: {
        "label_en": "Opus 4.7 — previous gen",
        "label_tr": "Opus 4.7 — الجيل السابق",
        "label_ar": "Opus 4.7 — الجيل السابق",
        "role": "Previous-gen.",
    },
}

DEFAULT_QUICK = ClaudeModel.SONNET_5
DEFAULT_DEEP = ClaudeModel.FABLE_5

# Models that reject temperature / top_p
NO_SAMPLING_PARAMS = {
    ClaudeModel.FABLE_5,
    ClaudeModel.OPUS_5,
    ClaudeModel.OPUS_4_8,
    ClaudeModel.SONNET_5,
    ClaudeModel.OPUS_4_7,
}


class FeedStatus(StrEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    DIVERGED = "diverged"
