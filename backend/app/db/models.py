"""SQLAlchemy models. Executions are a SEPARATE table from recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Operator(Base):
    __tablename__ = "operators"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(8), default="en")
    theme: Mapped[str] = mapped_column(String(8), default="dark")
    quick_model: Mapped[str] = mapped_column(String(64), default="claude-sonnet-5")
    deep_model: Mapped[str] = mapped_column(String(64), default="claude-fable-5")
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exposure_cap_r: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Instrument(Base):
    __tablename__ = "instruments"
    canonical_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_symbol: Mapped[str] = mapped_column(String(64))
    asset_class: Mapped[str] = mapped_column(String(32), default="forex")
    tradable: Mapped[bool] = mapped_column(Boolean, default=True)
    pip_location: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_precision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128))
    metaapi_account_id: Mapped[str] = mapped_column(String(128))
    encrypted_token: Mapped[str] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    region: Mapped[str] = mapped_column(String(64), default="new-york")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    aliases: Mapped[list["AliasMap"]] = relationship(back_populates="account")


class AliasMap(Base):
    __tablename__ = "alias_maps"
    __table_args__ = (UniqueConstraint("account_id", "canonical_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(ForeignKey("broker_accounts.id"))
    canonical_id: Mapped[str] = mapped_column(String(64))
    execution_symbol: Mapped[str] = mapped_column(String(64))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    last_test_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    last_test_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    account: Mapped[BrokerAccount] = relationship(back_populates="aliases")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), default="Ask")
    language: Mapped[str] = mapped_column(String(8), default="en")
    model_id: Mapped[str] = mapped_column(String(64), default="claude-sonnet-5")
    symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timeframe: Mapped[str] = mapped_column(String(16), default="15m")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    artifact: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128))
    canonical_id: Mapped[str] = mapped_column(String(64))
    timeframe: Mapped[str] = mapped_column(String(16))
    direction: Mapped[str] = mapped_column(String(8))
    analytical_bias: Mapped[str] = mapped_column(String(8))
    plan_type: Mapped[str] = mapped_column(String(32))
    execution_status: Mapped[str] = mapped_column(String(32))
    fill_rule: Mapped[str] = mapped_column(String(32))
    entry_zone_low: Mapped[float] = mapped_column(Float)
    entry_zone_high: Mapped[float] = mapped_column(Float)
    preferred_entry: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profits: Mapped[list[Any]] = mapped_column(JSON)
    invalidation_rule: Mapped[str] = mapped_column(Text)
    invalidation_mode: Mapped[str] = mapped_column(String(16), default="close")
    activation_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    activation_rule: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    validity_candles: Mapped[int] = mapped_column(Integer, default=30)
    similar_past_cases: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    reasons: Mapped[list[Any]] = mapped_column(JSON, default=list)
    next_action: Mapped[str] = mapped_column(Text, default="")
    model_id: Mapped[str] = mapped_column(String(64))
    tier: Mapped[str] = mapped_column(String(16))
    tradeable: Mapped[bool] = mapped_column(Boolean, default=False)
    vision_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    vision_timeframes: Mapped[list[Any]] = mapped_column(JSON, default=list)
    refused: Mapped[bool] = mapped_column(Boolean, default=False)
    refused_gate: Mapped[str | None] = mapped_column(String(64), nullable=True)
    refused_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    lifecycle: Mapped[str] = mapped_column(String(32), default="pending_entry")
    outcome: Mapped[str] = mapped_column(String(32), default="pending")
    conversation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gates: Mapped[list["RecommendationGate"]] = relationship(back_populates="recommendation")


class RecommendationGate(Base):
    __tablename__ = "recommendation_gates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("recommendations.id"))
    gate_id: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    recommendation: Mapped[Recommendation] = relationship(back_populates="gates")


class DemoExecution(Base):
    """Demo fills. Separate table from live executions."""

    __tablename__ = "demo_executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    source: Mapped[str] = mapped_column(String(16))
    source_id: Mapped[str] = mapped_column(String(36))
    source_name: Mapped[str] = mapped_column(String(128))
    account_id: Mapped[str] = mapped_column(String(36))
    canonical_id: Mapped[str] = mapped_column(String(64))
    execution_symbol: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(8))
    lots: Mapped[float] = mapped_column(Float)
    sl: Mapped[float] = mapped_column(Float)
    tp: Mapped[float | None] = mapped_column(Float, nullable=True)
    broker_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Execution(Base):
    """Live broker fills. NEVER written into the recommendation record."""

    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    source: Mapped[str] = mapped_column(String(16))
    source_id: Mapped[str] = mapped_column(String(36))
    source_name: Mapped[str] = mapped_column(String(128))
    account_id: Mapped[str] = mapped_column(String(36))
    canonical_id: Mapped[str] = mapped_column(String(64))
    execution_symbol: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(8))
    lots: Mapped[float] = mapped_column(Float)
    sl: Mapped[float] = mapped_column(Float)
    tp: Mapped[float | None] = mapped_column(Float, nullable=True)
    broker_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fill_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Strategy(Base):
    __tablename__ = "strategies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    origin: Mapped[str] = mapped_column(String(32))  # library | recommendation | draw
    locked_levels: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    versions: Mapped[list["StrategyVersion"]] = relationship(back_populates="strategy")


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"))
    version: Mapped[int] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(Text)
    changelog: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    strategy: Mapped[Strategy] = relationship(back_populates="versions")


class Bot(Base):
    __tablename__ = "bots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), unique=True)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"))
    account_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    canonical_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    mode: Mapped[str] = mapped_column(String(16), default="demo")
    active_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    model_id: Mapped[str] = mapped_column(String(64), default="claude-fable-5")
    demo_success: Mapped[bool] = mapped_column(Boolean, default=False)
    kill_switched: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_order_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    versions: Mapped[list["BotVersion"]] = relationship(back_populates="bot")


class BotVersion(Base):
    __tablename__ = "bot_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(ForeignKey("bots.id"))
    version: Mapped[int] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    bot: Mapped[Bot] = relationship(back_populates="versions")


class BotRationale(Base):
    __tablename__ = "bot_rationales"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id: Mapped[str] = mapped_column(ForeignKey("bots.id"))
    version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    model_id: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(8))
    veto: Mapped[bool] = mapped_column(Boolean, default=False)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WatchlistItem(Base):
    __tablename__ = "watchlist"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_id: Mapped[str] = mapped_column(String(64), unique=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MemoryCase(Base):
    __tablename__ = "memory_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_id: Mapped[str] = mapped_column(String(64))
    direction: Mapped[str] = mapped_column(String(8))
    summary: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id: Mapped[str] = mapped_column(String(36))
    canonical_id: Mapped[str] = mapped_column(String(64))
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    max_dd: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    insufficient_data: Mapped[bool] = mapped_column(Boolean, default=True)
    equity_curve: Mapped[list[Any]] = mapped_column(JSON, default=list)
    trades: Mapped[list[Any]] = mapped_column(JSON, default=list)
    cost_model: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    fragility_warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    model_id: Mapped[str] = mapped_column(String(64))
    tier: Mapped[str] = mapped_column(String(16))
    transcript: Mapped[list[Any]] = mapped_column(JSON, default=list)
    roles: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KillSwitch(Base):
    __tablename__ = "kill_switch"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    engaged: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FeedHealth(Base):
    __tablename__ = "feed_health"
    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="disconnected")
    detail: Mapped[str] = mapped_column(Text, default="")
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EncryptedSecret(Base):
    """Operator Settings overlay. Secrets encrypted at rest. Empty/missing = fall back to .env."""

    __tablename__ = "encrypted_secrets"
    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    ciphertext: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SettingsAudit(Base):
    """Which overlay key changed, when. NEVER stores the secret value."""

    __tablename__ = "settings_audit"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_name: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(16))  # set | clear | generate | revoke
    operator_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
