"""FastAPI application. Single operator. No MCP. No billing."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.agent.pipeline import PipelineInput, SimilarCases, publish
from app.agent.runtime import ALLOWED_MODELS, resolve_model
from app.agent.vision import capture_pngs
from app.api.deps import current_operator
from app.api.schemas import (
    AliasIn,
    AnalyzeIn,
    BotCreateIn,
    ChatIn,
    ExecuteIn,
    KillSwitchIn,
    LoginIn,
    PromoteLiveIn,
    SettingsIn,
    WatchlistIn,
)
from app.backtest.engine import CostModel, run_backtest
from app.bots.safety import SafetyContext, check_bot_safety
from app.config import get_settings
from app.db.models import (
    AgentRun,
    AliasMap,
    BacktestRun,
    Bot,
    BotRationale,
    BotVersion,
    BrokerAccount,
    Conversation,
    EncryptedSecret,
    Execution,
    FeedHealth,
    Instrument,
    KillSwitch,
    Lesson,
    MemoryCase,
    Message,
    Operator,
    Recommendation,
    RecommendationGate,
    Strategy,
    StrategyVersion,
    WatchlistItem,
)
from app.db.session import create_all, get_db
from app.domain.fill_rules import ActivationRule
from app.enums import (
    AnalysisTier,
    MODEL_CATALOG,
    BotStatus,
    Direction,
    ExecutionStatus,
    FillRule,
    PlanType,
)
from app.execution.metaapi import MetaApiClient, OrderRequest
from app.exposure import OpenRisk, aggregate_exposure
from app.feeds.divergence import check_divergence, mid_from_oanda
from app.feeds.finnhub import FinnhubClient
from app.feeds.oanda import OandaClient
from app.feeds.twelve import TwelveDataClient
from app.security import create_token, decrypt_secret, encrypt_secret, hash_password, verify_password
from app.symbols.alias import resolve_alias, validate_alias_payload
from app.logging_conf import setup_logging
from app.telegram.bot import handle_telegram_update

setup_logging()
settings = get_settings()
_rate: dict[str, deque[float]] = defaultdict(deque)


def _rate_ok(key: str, limit: int) -> bool:
    now = time.time()
    q = _rate[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_all()
    except Exception:
        # DB may be down in unit tests / first boot without compose
        pass
    yield


app = FastAPI(title="Zorro AI Trading Assistant", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCLAIMER = (
    "Personal analysis, not fund management. Trading involves risk of loss. "
    "This platform does not promise monthly returns."
)


@app.middleware("http")
async def disclaimer_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Zorro-Disclaimer"] = DISCLAIMER
    return response


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    oanda = OandaClient()
    twelve = TwelveDataClient()
    finn = FinnhubClient()
    meta = MetaApiClient()
    o_s, o_d = await oanda.health()
    t_s, t_d = await twelve.health()
    f_s, f_d = await finn.health()
    m_s, m_d = await meta.health()
    db_status = "disconnected"
    redis_status = "disconnected"
    try:
        from sqlalchemy import text

        from app.db.session import get_engine

        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:  # noqa: BLE001
        db_status = f"disconnected:{exc.__class__.__name__}"
    try:
        import redis.asyncio as redis

        r = redis.from_url(settings.redis_url)
        await r.ping()
        redis_status = "connected"
        await r.aclose()
    except Exception as exc:  # noqa: BLE001
        redis_status = f"disconnected:{exc.__class__.__name__}"
    return {
        "ok": True,
        "disclaimer": DISCLAIMER,
        "feeds": {
            "postgres": db_status,
            "redis": redis_status,
            "oanda": {"status": o_s.value, "detail": o_d},
            "twelve_data": {"status": t_s.value, "detail": t_d},
            "finnhub": {"status": f_s.value, "detail": f_d},
            "metaapi": {"status": m_s.value, "detail": m_d},
            "anthropic": "connected" if settings.anthropic_api_key else "disconnected",
        },
        "mcp": False,
    }


@app.get("/api/models")
async def models():
    return {
        "models": [
            {"id": k.value, **v} for k, v in MODEL_CATALOG.items()
        ],
        "defaults": {"quick": settings.quick_model, "deep": settings.deep_model},
    }


# ---------------------------------------------------------------------------
# Auth (single operator)
# ---------------------------------------------------------------------------
@app.post("/api/auth/login")
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    op = await db.scalar(select(Operator).where(Operator.email == body.email))
    if op is None:
        op = Operator(
            email=body.email,
            password_hash=hash_password(body.password),
            language=settings.default_language,
        )
        db.add(op)
        await db.commit()
        await db.refresh(op)
    elif not verify_password(body.password, op.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(op.id), "token_type": "bearer", "operator_id": op.id}


@app.get("/api/me")
async def me(op: Operator = Depends(current_operator)):
    return {
        "id": op.id,
        "email": op.email,
        "language": op.language,
        "theme": op.theme,
        "quick_model": op.quick_model,
        "deep_model": op.deep_model,
        "exposure_cap_r": op.exposure_cap_r,
        "disclaimer": DISCLAIMER,
    }


@app.put("/api/settings")
async def update_settings(body: SettingsIn, op: Operator = Depends(current_operator), db: AsyncSession = Depends(get_db)):
    if body.language:
        op.language = body.language
    if body.theme:
        op.theme = body.theme
    if body.quick_model:
        if body.quick_model not in ALLOWED_MODELS:
            raise HTTPException(400, "Model not in the Anthropic multimodal catalog")
        op.quick_model = body.quick_model
    if body.deep_model:
        if body.deep_model not in ALLOWED_MODELS:
            raise HTTPException(400, "Model not in the Anthropic multimodal catalog")
        op.deep_model = body.deep_model
    if body.exposure_cap_r is not None:
        op.exposure_cap_r = body.exposure_cap_r
    if body.pin:
        op.pin_hash = hash_password(body.pin)
    await db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Instruments (OANDA catalog — no free-text symbols)
# ---------------------------------------------------------------------------
@app.get("/api/instruments")
async def instruments(q: str | None = None, db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(Instrument))).all()
    if not rows:
        fetched = await OandaClient().fetch_instruments()
        for item in fetched:
            db.add(
                Instrument(
                    canonical_id=item.canonical_id,
                    display_symbol=item.display_symbol,
                    asset_class=item.asset_class.value,
                    tradable=item.tradable,
                    pip_location=item.pip_location,
                    display_precision=item.display_precision,
                    extra=item.extra or {},
                )
            )
        await db.commit()
        rows = (await db.scalars(select(Instrument))).all()
    out = [
        {
            "canonical_id": r.canonical_id,
            "display_symbol": r.display_symbol,
            "asset_class": r.asset_class,
            "tradable": r.tradable,
        }
        for r in rows
    ]
    if q:
        ql = q.lower()
        out = [i for i in out if ql in i["canonical_id"].lower() or ql in i["display_symbol"].lower()]
    return {"instruments": out, "source": "OANDA"}


@app.get("/api/candles/{canonical_id}")
async def candles(canonical_id: str, timeframe: str = "15m", count: int = 200):
    from app.agent.tools import get_candles

    return await get_candles(canonical_id, timeframe, count)


@app.get("/api/price/{canonical_id}")
async def price(canonical_id: str):
    oanda = await OandaClient().price(canonical_id)
    twelve = await TwelveDataClient().quote(canonical_id)
    mid = mid_from_oanda(oanda)
    t = None
    if twelve:
        try:
            t = float(twelve.get("close") or twelve.get("price") or 0) or None
        except (TypeError, ValueError):
            t = None
    div = check_divergence(mid, t, settings.price_divergence_bps)
    return {
        "oanda": oanda if oanda else "Not available",
        "twelve_crosscheck": t,
        "diverged": div.diverged,
        "banner": div.banner,
        "source_of_truth": "OANDA",
    }


# ---------------------------------------------------------------------------
# Conversations / Ask
# ---------------------------------------------------------------------------
@app.get("/api/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(Conversation).order_by(Conversation.updated_at.desc()))).all()
    return [{"id": r.id, "title": r.title, "model_id": r.model_id, "symbol": r.symbol} for r in rows]


@app.post("/api/conversations")
async def create_conversation(db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    c = Conversation(model_id=op.quick_model, language=op.language)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {"id": c.id, "model_id": c.model_id}


@app.post("/api/chat")
async def chat(body: ChatIn, request: Request, db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    if not _rate_ok("chat", settings.rate_limit_chat_per_minute):
        raise HTTPException(429, "Rate limit")
    conv = None
    if body.conversation_id:
        conv = await db.get(Conversation, body.conversation_id)
    if conv is None:
        conv = Conversation(language=body.language or op.language, model_id=body.model_id or op.quick_model)
        db.add(conv)
        await db.flush()
    if body.model_id:
        if body.model_id not in ALLOWED_MODELS:
            raise HTTPException(400, "Model not allowed")
        conv.model_id = body.model_id
    if body.canonical_id:
        conv.symbol = body.canonical_id
    conv.timeframe = body.timeframe
    db.add(Message(conversation_id=conv.id, role="user", content=body.message))
    await db.commit()

    async def gen():
        yield {"event": "status", "data": "thinking"}
        from app.agent.runtime import run_claude

        text = await run_claude(conv.model_id, body.message)
        db.add(Message(conversation_id=conv.id, role="assistant", content=text))
        await db.commit()
        yield {"event": "token", "data": text}
        yield {"event": "done", "data": conv.id}

    if request.headers.get("accept") == "text/event-stream":
        return EventSourceResponse(gen())
    from app.agent.runtime import run_claude

    text = await run_claude(conv.model_id, body.message)
    db.add(Message(conversation_id=conv.id, role="assistant", content=text))
    await db.commit()
    return {
        "conversation_id": conv.id,
        "model_id": conv.model_id,
        "reply": text,
        "recommendation": None,
        "note": "Execution is never started from chat. Name a saved recommendation to execute.",
        "disclaimer": DISCLAIMER,
    }


@app.websocket("/ws/ticks/{canonical_id}")
async def ticks(ws: WebSocket, canonical_id: str):
    await ws.accept()
    try:
        while True:
            p = await OandaClient().price(canonical_id)
            await ws.send_json({"canonical_id": canonical_id, "price": p or "Not available", "source": "OANDA"})
            import asyncio

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


# ---------------------------------------------------------------------------
# Analysis / recommendations
# ---------------------------------------------------------------------------
@app.post("/api/analyze")
async def analyze(body: AnalyzeIn, db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    if not _rate_ok("analyze", settings.rate_limit_analysis_per_minute):
        raise HTTPException(429, "Rate limit")
    inst = await db.get(Instrument, body.canonical_id)
    if inst is None and (await db.scalar(select(Instrument))) is not None:
        raise HTTPException(400, "Symbol must be chosen from the OANDA catalog")

    oanda_px = await OandaClient().price(body.canonical_id)
    twelve_q = await TwelveDataClient().quote(body.canonical_id)
    mid = mid_from_oanda(oanda_px)
    tpx = None
    if twelve_q:
        try:
            tpx = float(twelve_q.get("close") or twelve_q.get("price") or 0) or None
        except (TypeError, ValueError):
            tpx = None
    div = check_divergence(mid, tpx, settings.price_divergence_bps)

    from app.agent.tools import compute_atr, compute_structure, compute_zones, get_candles

    candle_payload = await get_candles(body.canonical_id, body.timeframe, 200)
    candles = candle_payload.get("candles") or []
    atr = compute_atr(candles) or 1.0
    structure = compute_structure(candles)
    zones = compute_zones(candles)
    finn = FinnhubClient()
    news_events = await finn.calendar() if finn.configured else None
    blocking = finn.blocking_event(news_events or [], datetime.now(timezone.utc)) if news_events is not None else None

    vision_ok = False
    vision_tfs: list[str] = []
    if body.tier == AnalysisTier.DEEP:
        cap = await capture_pngs(body.canonical_id, ["15m", "1h", "4h", body.timeframe])
        vision_ok = cap.ok
        vision_tfs = cap.timeframes

    cases = (await db.scalars(select(MemoryCase).where(MemoryCase.canonical_id == body.canonical_id))).all()
    similar = SimilarCases(
        count=len(cases),
        sample_floor=settings.sample_floor,
        items=[{"outcome": c.outcome} for c in cases],
    )
    rule = None
    if body.activation_rule:
        rule = ActivationRule(
            kind=body.activation_rule.get("kind", "price_touch"),
            level=body.activation_rule.get("level"),
            timeframe=body.activation_rule.get("timeframe"),
            zone_low=body.activation_rule.get("zone_low"),
            zone_high=body.activation_rule.get("zone_high"),
        )
    spread = None
    typical = None
    if oanda_px:
        try:
            bids = oanda_px.get("bids") or []
            asks = oanda_px.get("asks") or []
            if bids and asks:
                spread = float(asks[0]["price"]) - float(bids[0]["price"])
                typical = spread
        except (KeyError, TypeError, ValueError):
            spread = None

    inp = PipelineInput(
        canonical_id=body.canonical_id,
        timeframe=body.timeframe,
        tier=body.tier,
        model_id=body.model_id,
        language=body.language,
        direction=body.direction,
        fill_rule=body.fill_rule,
        preferred_entry=body.preferred_entry,
        entry_zone_low=body.entry_zone_low,
        entry_zone_high=body.entry_zone_high,
        stop_loss=body.stop_loss,
        take_profits=body.take_profits,
        plan_type=body.plan_type,
        invalidation_rule=body.invalidation_rule,
        activation_condition=body.activation_condition,
        activation_rule=rule,
        validity_candles=body.validity_candles,
        reasons=body.reasons,
        next_action=body.next_action,
        atr=atr,
        now_ts=time.time(),
        news_provider_configured=finn.configured,
        news={"risk": "high" if blocking else "low", "blocking_event": blocking} if finn.configured else None,
        liquidity={"illiquid": False, "sweeps": 0},
        supply_demand=zones,
        structure=structure,
        session={"blocked": False, "name": "london_ny"},
        live_price=mid,
        oanda_price=mid,
        twelve_price=tpx,
        spread=spread,
        typical_spread=typical,
        divergence_bps=div.bps or 0,
        divergence_limit_bps=settings.price_divergence_bps,
        vision_timeframes=vision_tfs,
        vision_ok=vision_ok,
        cost_model={"spread": spread or 0, "slippage": (spread or 0) * 0.5},
        similar=similar,
        feed_unreliable=div.diverged,
        operator_defaults={"quick_model": op.quick_model, "deep_model": op.deep_model},
    )
    out = publish(inp)
    run = AgentRun(id=out.agent_run_id, model_id=out.model_id, tier=body.tier.value, roles={"order": ["technical_analyst", "debate_moderator", "trader"]})
    db.add(run)
    if not out.published:
        rec = Recommendation(
            name=f"REFUSED {body.canonical_id}",
            canonical_id=body.canonical_id,
            timeframe=body.timeframe,
            direction=body.direction.value,
            analytical_bias=body.direction.value,
            plan_type=body.plan_type.value,
            execution_status=ExecutionStatus.BLOCKED.value,
            fill_rule=body.fill_rule.value,
            entry_zone_low=body.entry_zone_low,
            entry_zone_high=body.entry_zone_high,
            preferred_entry=body.preferred_entry,
            stop_loss=body.stop_loss,
            take_profits=body.take_profits,
            invalidation_rule=body.invalidation_rule,
            model_id=out.model_id,
            tier=body.tier.value,
            tradeable=False,
            refused=True,
            refused_gate=out.refused_gate,
            refused_reason=out.refused_reason,
            lifecycle="refused",
            outcome="refused",
            agent_run_id=out.agent_run_id,
        )
        db.add(rec)
        await db.flush()
        for g in out.gates:
            db.add(RecommendationGate(recommendation_id=rec.id, gate_id=g.gate_id, name=g.name, status=g.status.value, reason=g.reason, evidence=g.evidence))
        await db.commit()
        return {
            "published": False,
            "refused_gate": out.refused_gate,
            "refused_reason": out.refused_reason,
            "gates": [g.__dict__ for g in out.gates],
            "model_id": out.model_id,
            "note": "Platform refusal — not WAIT. Direction was not flipped.",
        }
    rec_d = out.recommendation or {}
    rec = Recommendation(
        id=rec_d["id"],
        name=rec_d["name"],
        canonical_id=body.canonical_id,
        timeframe=body.timeframe,
        direction=rec_d["direction"],
        analytical_bias=rec_d["analytical_bias"],
        plan_type=rec_d["plan_type"],
        execution_status=rec_d["execution_status"],
        fill_rule=rec_d["fill_rule"],
        entry_zone_low=body.entry_zone_low,
        entry_zone_high=body.entry_zone_high,
        preferred_entry=body.preferred_entry,
        stop_loss=body.stop_loss,
        take_profits=body.take_profits,
        invalidation_rule=body.invalidation_rule,
        activation_condition=body.activation_condition,
        activation_rule=body.activation_rule,
        validity_candles=body.validity_candles,
        similar_past_cases=rec_d.get("similar_past_cases") or {},
        reasons=body.reasons,
        next_action=body.next_action,
        model_id=out.model_id,
        tier=body.tier.value,
        tradeable=out.tradeable,
        vision_ok=vision_ok,
        vision_timeframes=vision_tfs,
        agent_run_id=out.agent_run_id,
    )
    db.add(rec)
    await db.flush()
    for g in out.gates:
        db.add(RecommendationGate(recommendation_id=rec.id, gate_id=g.gate_id, name=g.name, status=g.status.value, reason=g.reason, evidence=g.evidence))
    await db.commit()
    return {"published": True, "recommendation": rec_d, "gates": [g.__dict__ for g in out.gates], "model_id": out.model_id}


@app.get("/api/recommendations")
async def list_recs(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(Recommendation).order_by(Recommendation.created_at.desc()))).all()
    return [_rec_out(r) for r in rows]


@app.get("/api/recommendations/{rec_id}")
async def get_rec(rec_id: str, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    r = await db.get(Recommendation, rec_id)
    if not r:
        raise HTTPException(404, "Not found")
    gates = (await db.scalars(select(RecommendationGate).where(RecommendationGate.recommendation_id == rec_id))).all()
    payload = _rec_out(r)
    payload["gates"] = [{"gate_id": g.gate_id, "name": g.name, "status": g.status, "reason": g.reason, "evidence": g.evidence} for g in gates]
    return payload


def _rec_out(r: Recommendation) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "canonical_id": r.canonical_id,
        "timeframe": r.timeframe,
        "direction": r.direction,
        "analytical_bias": r.analytical_bias,
        "plan_type": r.plan_type,
        "execution_status": r.execution_status,
        "fill_rule": r.fill_rule,
        "entry_zone": {"low": r.entry_zone_low, "high": r.entry_zone_high},
        "preferred_entry": r.preferred_entry,
        "stop_loss": r.stop_loss,
        "take_profits": r.take_profits,
        "invalidation_rule": r.invalidation_rule,
        "activation_condition": r.activation_condition,
        "activation_rule": r.activation_rule,
        "validity_candles": r.validity_candles,
        "similar_past_cases": r.similar_past_cases,
        "reasons": r.reasons,
        "next_action": r.next_action,
        "model_id": r.model_id,
        "tier": r.tier,
        "tradeable": r.tradeable,
        "refused": r.refused,
        "refused_gate": r.refused_gate,
        "refused_reason": r.refused_reason,
        "lifecycle": r.lifecycle,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# ---------------------------------------------------------------------------
# Execute — NEVER from analyze. Named rec/bot + lot once.
# ---------------------------------------------------------------------------
def _lots_from_r(balance: float, risk_r: float, entry: float, stop: float, pip: float = 0.0001) -> float:
    """Lot conversion happens EXACTLY once, here, for the Execute Trade modal."""
    risk_cash = balance * risk_r
    stop_dist = abs(entry - stop)
    if stop_dist <= 0:
        return 0.0
    # Standard FX: 1 lot ≈ $10 / pip on XXXUSD; simplified:
    per_lot = stop_dist / pip * 10
    if per_lot <= 0:
        return 0.0
    return round(risk_cash / per_lot, 2)


@app.post("/api/execute/preview")
async def execute_preview(body: ExecuteIn, db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    rec = await db.get(Recommendation, body.source_id) if body.source == "recommendation" else None
    if body.source == "recommendation" and rec is None:
        raise HTTPException(404, "Named recommendation not found")
    return {
        "lots": body.lots,
        "note": "Lot size is asked once. SL always attached. Recommendation record is not updated with the fill.",
        "disclaimer": DISCLAIMER,
    }


@app.post("/api/execute")
async def execute(body: ExecuteIn, db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    ks = await db.get(KillSwitch, 1)
    if ks and ks.engaged:
        raise HTTPException(423, "Kill switch engaged")
    account = await db.get(BrokerAccount, body.account_id)
    if not account:
        raise HTTPException(400, "Unknown account")
    if body.source == "recommendation":
        rec = await db.get(Recommendation, body.source_id)
        if not rec or rec.name != body.source_name and rec.id != body.source_id:
            raise HTTPException(400, "Must name an existing saved recommendation")
        canonical = rec.canonical_id
        direction = Direction(rec.direction)
        sl = rec.stop_loss
        tps = rec.take_profits or []
    else:
        bot = await db.get(Bot, body.source_id)
        if not bot:
            raise HTTPException(400, "Must name an existing bot")
        canonical = bot.canonical_id
        direction = Direction.BUY
        sl = 0.0
        tps = []
        raise HTTPException(400, "Bot-originated orders go through the worker after rationale")
    pin_ok = bool(op.pin_hash and verify_password(body.confirmation, op.pin_hash))
    if body.confirmation != canonical and not pin_ok:
        raise HTTPException(400, "Type the canonical symbol or PIN to confirm")
    aliases = {a.canonical_id: a.execution_symbol for a in (await db.scalars(select(AliasMap).where(AliasMap.account_id == account.id))).all()}
    tested = {a.canonical_id for a in (await db.scalars(select(AliasMap).where(AliasMap.account_id == account.id, AliasMap.last_test_ok.is_(True)))).all()}
    alias = resolve_alias(canonical, aliases, tested)
    if not alias.can_execute:
        raise HTTPException(400, alias.error or "Unmapped: execute NEVER")
    token = decrypt_secret(account.encrypted_token)
    client = MetaApiClient()
    result = await client.place(
        account.metaapi_account_id,
        token,
        alias,
        OrderRequest(
            idempotency_key=str(uuid.uuid4()),
            execution_symbol=alias.execution_symbol or "",
            direction=direction,
            lots=body.lots,
            stop_loss=sl,
            take_profit=tps[0] if tps else None,
            comment=body.source_name[:30],
        ),
    )
    ex = Execution(
        idempotency_key=str(uuid.uuid4()),
        source=body.source,
        source_id=body.source_id,
        source_name=body.source_name,
        account_id=account.id,
        canonical_id=canonical,
        execution_symbol=alias.execution_symbol or "",
        direction=direction.value,
        lots=body.lots,
        sl=sl,
        status="filled" if result.ok else "rejected",
        broker_order_id=result.broker_order_id,
        fill_price=result.fill_price,
        error=result.error,
    )
    db.add(ex)
    await db.commit()
    return {"ok": result.ok, "execution_id": ex.id, "error": result.error, "note": "Fill is stored in executions, never on the recommendation."}


# ---------------------------------------------------------------------------
# Watchlist / exposure / account
# ---------------------------------------------------------------------------
@app.get("/api/watchlist")
async def watchlist(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(WatchlistItem))).all()
    return [{"id": r.id, "canonical_id": r.canonical_id, "notes": r.notes} for r in rows]


@app.post("/api/watchlist")
async def add_watch(body: WatchlistIn, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    item = WatchlistItem(canonical_id=body.canonical_id, notes=body.notes)
    db.add(item)
    await db.commit()
    return {"id": item.id}


@app.delete("/api/watchlist/{item_id}")
async def del_watch(item_id: str, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    row = await db.get(WatchlistItem, item_id)
    if row:
        await db.delete(row)
        await db.commit()
    return {"ok": True}


@app.get("/api/exposure")
async def exposure(db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    execs = (await db.scalars(select(Execution).where(Execution.status == "filled"))).all()
    positions = [OpenRisk(e.canonical_id, e.direction, 1.0, "forex") for e in execs]
    report = aggregate_exposure(positions, op.exposure_cap_r)
    return report.__dict__ | {"disclaimer": DISCLAIMER}


@app.get("/api/accounts")
async def accounts(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(BrokerAccount))).all()
    return [{"id": r.id, "name": r.name, "is_demo": r.is_demo, "metaapi_account_id": r.metaapi_account_id} for r in rows]


@app.post("/api/accounts")
async def add_account(payload: dict[str, Any], db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    acc = BrokerAccount(
        name=payload.get("name") or "account",
        metaapi_account_id=payload.get("metaapi_account_id") or "",
        encrypted_token=encrypt_secret(payload.get("token") or settings.metaapi_token or "unset"),
        is_demo=bool(payload.get("is_demo", True)),
        region=payload.get("region") or settings.metaapi_region,
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    return {"id": acc.id}


@app.get("/api/accounts/{account_id}/aliases")
async def list_aliases(account_id: str, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(AliasMap).where(AliasMap.account_id == account_id))).all()
    return [r.__dict__ | {"_sa_instance_state": None} if False else {
        "id": r.id, "canonical_id": r.canonical_id, "execution_symbol": r.execution_symbol,
        "last_test_ok": r.last_test_ok, "last_test_error": r.last_test_error,
    } for r in rows]


@app.post("/api/accounts/{account_id}/aliases")
async def save_alias(account_id: str, body: AliasIn, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    err = validate_alias_payload(body.canonical_id, body.execution_symbol)
    if err:
        raise HTTPException(400, err)
    acc = await db.get(BrokerAccount, account_id)
    if not acc:
        raise HTTPException(404, "Unknown account")
    token = decrypt_secret(acc.encrypted_token)
    ok, detail = await MetaApiClient().test_symbol(acc.metaapi_account_id, token, body.execution_symbol)
    row = AliasMap(
        account_id=account_id,
        canonical_id=body.canonical_id,
        execution_symbol=body.execution_symbol,
        resolved=ok,
        last_test_ok=ok,
        last_test_error=None if ok else detail,
    )
    db.add(row)
    await db.commit()
    if not ok:
        raise HTTPException(400, f"Test-resolve failed: {detail}")
    return {"ok": True, "id": row.id}


# ---------------------------------------------------------------------------
# Strategies / bots
# ---------------------------------------------------------------------------
LIBRARY = {
    "session_breakout": "# Zorro strategy — session breakout\ndef signal(candles, params):\n    return {'action': 'none'}\n",
    "zone_retest": "# Zorro strategy — zone retest\ndef signal(candles, params):\n    return {'action': 'none'}\n",
    "structure_continuation": "# Zorro strategy — structure continuation\ndef signal(candles, params):\n    return {'action': 'none'}\n",
}


@app.get("/api/strategies")
async def list_strategies(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(Strategy))).all()
    return [{"id": r.id, "name": r.name, "origin": r.origin, "description": r.description} for r in rows]


@app.get("/api/strategies/library")
async def strategy_library():
    return {"templates": list(LIBRARY)}


@app.post("/api/strategies")
async def create_strategy(payload: dict[str, Any], db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    s = Strategy(
        name=payload["name"],
        description=payload.get("description") or "",
        origin=payload.get("origin") or "library",
        locked_levels=payload.get("locked_levels"),
    )
    db.add(s)
    await db.flush()
    code = payload.get("code") or LIBRARY.get(payload.get("template") or "", LIBRARY["session_breakout"])
    db.add(StrategyVersion(strategy_id=s.id, version=1, code=code, changelog="initial"))
    await db.commit()
    return {"id": s.id}


@app.get("/api/strategies/{sid}/versions")
async def strategy_versions(sid: str, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(StrategyVersion).where(StrategyVersion.strategy_id == sid))).all()
    return [{"id": r.id, "version": r.version, "changelog": r.changelog} for r in rows]


@app.post("/api/strategies/{sid}/optimize")
async def optimize(sid: str, payload: dict[str, Any], db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    candles = payload.get("candles") or []
    result = run_backtest(
        candles,
        payload.get("direction") or "BUY",
        float(payload.get("entry") or 0),
        float(payload.get("stop") or 0),
        payload.get("targets") or [0, 0],
        CostModel(spread=float(payload.get("spread") or 0), slippage=float(payload.get("slippage") or 0)),
        settings.sample_floor,
    )
    run = BacktestRun(
        strategy_id=sid,
        canonical_id=payload.get("canonical_id") or "",
        sample_size=result.sample_size,
        max_dd=result.max_dd,
        profit_factor=result.profit_factor,
        insufficient_data=result.insufficient_data,
        equity_curve=result.equity_curve,
        trades=[t.__dict__ for t in result.trades],
        cost_model={"spread": payload.get("spread"), "slippage": payload.get("slippage")},
        fragility_warning=result.fragility_warning,
    )
    db.add(run)
    await db.commit()
    return {
        "sample_size": result.sample_size,
        "max_dd": result.max_dd,
        "profit_factor": result.profit_factor,
        "label": result.label,
        "insufficient_data": result.insufficient_data,
        "fragility_warning": result.fragility_warning,
        "equity_curve": result.equity_curve,
        "note": "Never displayed as monthly return %.",
    }


@app.get("/api/bots")
async def list_bots(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    rows = (await db.scalars(select(Bot))).all()
    return [{"id": r.id, "name": r.name, "status": r.status, "mode": r.mode, "canonical_id": r.canonical_id} for r in rows]


@app.post("/api/bots")
async def create_bot(body: BotCreateIn, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    locked = None
    if body.origin == "recommendation":
        rec = await db.get(Recommendation, body.recommendation_id or "")
        if not rec:
            raise HTTPException(400, "Convert path requires a saved recommendation")
        locked = {
            "direction": rec.direction,
            "entry_zone": [rec.entry_zone_low, rec.entry_zone_high],
            "preferred_entry": rec.preferred_entry,
            "stop_loss": rec.stop_loss,
            "take_profits": rec.take_profits,
            "fill_rule": rec.fill_rule,
            "note": "Exact levels locked — no new rules.",
        }
    strat = Strategy(name=f"bot-{body.name}", origin=body.origin, locked_levels=locked)
    db.add(strat)
    await db.flush()
    db.add(StrategyVersion(strategy_id=strat.id, version=1, code=body.code, changelog="bot initial"))
    bot = Bot(name=body.name, strategy_id=strat.id, canonical_id=body.canonical_id, account_id=body.account_id, status=BotStatus.DRAFT.value)
    db.add(bot)
    await db.flush()
    ver = BotVersion(bot_id=bot.id, version=1, code=body.code)
    db.add(ver)
    await db.commit()
    return {"id": bot.id, "locked_levels": locked}


@app.get("/api/bots/{bid}")
async def get_bot(bid: str, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    b = await db.get(Bot, bid)
    if not b:
        raise HTTPException(404)
    versions = (await db.scalars(select(BotVersion).where(BotVersion.bot_id == bid))).all()
    return {
        "id": b.id,
        "name": b.name,
        "status": b.status,
        "mode": b.mode,
        "demo_success": b.demo_success,
        "kill_switched": b.kill_switched,
        "canonical_id": b.canonical_id,
        "versions": [{"id": v.id, "version": v.version} for v in versions],
        "performance_note": "Sample size, max DD, profit factor only. Never monthly return %.",
    }


@app.post("/api/bots/{bid}/demo")
async def start_demo(bid: str, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    b = await db.get(Bot, bid)
    if not b:
        raise HTTPException(404)
    b.status = BotStatus.DEMO_RUNNING.value
    b.mode = "demo"
    await db.commit()
    return {"ok": True, "status": b.status}


@app.post("/api/bots/{bid}/live")
async def promote_live(bid: str, body: PromoteLiveIn, db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    b = await db.get(Bot, bid)
    if not b:
        raise HTTPException(404)
    if not b.demo_success:
        raise HTTPException(400, "Mandatory demo success before live")
    pin_ok = bool(op.pin_hash and verify_password(body.confirmation, op.pin_hash))
    if body.confirmation != b.canonical_id and not pin_ok:
        raise HTTPException(400, "Type the canonical symbol or PIN")
    b.account_id = body.account_id
    b.mode = "live"
    b.status = BotStatus.LIVE_STOPPED.value
    await db.commit()
    return {"ok": True, "status": b.status}


@app.post("/api/bots/{bid}/rollback")
async def rollback(bid: str, payload: dict[str, Any], db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    b = await db.get(Bot, bid)
    if not b:
        raise HTTPException(404)
    b.active_version_id = payload.get("version_id")
    await db.commit()
    return {"ok": True, "active_version_id": b.active_version_id}


@app.post("/api/bots/{bid}/rationale")
async def bot_rationale(bid: str, payload: dict[str, Any], db: AsyncSession = Depends(get_db), op: Operator = Depends(current_operator)):
    b = await db.get(Bot, bid)
    if not b:
        raise HTTPException(404)
    model_id = payload.get("model_id") or op.deep_model
    text = payload.get("text") or ""
    veto = bool(payload.get("veto"))
    if not text.strip():
        raise HTTPException(400, "Rationale required before any order. If rationale fails, NO ORDER.")
    row = BotRationale(bot_id=bid, model_id=model_id, direction=payload.get("direction") or "BUY", veto=veto, text=text)
    db.add(row)
    await db.commit()
    return {"ok": True, "veto": veto, "model_id": model_id}


@app.post("/api/kill-switch")
async def kill_switch(body: KillSwitchIn, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    row = await db.get(KillSwitch, 1)
    if row is None:
        row = KillSwitch(id=1)
        db.add(row)
        await db.flush()
    row.engaged = body.engaged
    row.reason = body.reason
    row.engaged_at = datetime.now(timezone.utc) if body.engaged else None
    if body.engaged:
        bots = (await db.scalars(select(Bot))).all()
        for b in bots:
            b.kill_switched = True
            b.status = BotStatus.KILLED.value
    await db.commit()
    return {"engaged": row.engaged, "reason": row.reason}


@app.get("/api/kill-switch")
async def get_kill(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    row = await db.get(KillSwitch, 1)
    return {"engaged": bool(row and row.engaged), "reason": row.reason if row else ""}


# ---------------------------------------------------------------------------
# Memory / review / history / demo
# ---------------------------------------------------------------------------
@app.get("/api/memory")
async def memory(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    cases = (await db.scalars(select(MemoryCase))).all()
    lessons = (await db.scalars(select(Lesson))).all()
    return {
        "cases": [{"id": c.id, "canonical_id": c.canonical_id, "direction": c.direction, "summary": c.summary} for c in cases],
        "lessons": [{"id": l.id, "body": l.body} for l in lessons],
        "note": "Memory never flips direction or bypasses gates.",
    }


@app.get("/api/review")
async def review(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    recs = (await db.scalars(select(Recommendation))).all()
    sample = len([r for r in recs if r.outcome != "pending"])
    return {
        "sample_size": sample,
        "label": "Insufficient data" if sample < settings.sample_floor else "ok",
        "note": "Informational only. Never a monthly return %. Platform skill = recommendation vs candles.",
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/history")
async def history(db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    recs = (await db.scalars(select(Recommendation).order_by(Recommendation.created_at.desc()))).all()
    execs = (await db.scalars(select(Execution).order_by(Execution.created_at.desc()))).all()
    return {
        "recommendations": [_rec_out(r) for r in recs],
        "executions": [{"id": e.id, "source": e.source, "status": e.status, "lots": e.lots} for e in execs],
        "note": "Executions are a separate table.",
    }


@app.get("/api/agent-runs/{run_id}")
async def agent_run(run_id: str, db: AsyncSession = Depends(get_db), _: Operator = Depends(current_operator)):
    row = await db.get(AgentRun, run_id)
    if not row:
        raise HTTPException(404)
    return {"id": row.id, "model_id": row.model_id, "tier": row.tier, "transcript": row.transcript, "roles": row.roles}


@app.get("/api/demo")
async def demo():
    return {
        "title": "Demo desk",
        "modes": ["Ask", "Scan Today", "Build"],
        "disclaimer": DISCLAIMER,
        "note": "Demo bots must succeed before promote-to-live.",
    }


@app.get("/api/routes")
async def routes_doc():
    return {
        "primary": {
            "/": {"auth": True, "api": ["/api/chat", "/api/conversations", "/api/models"], "tools": "native agent tools, no MCP"},
            "/today": {"auth": True, "api": ["/api/recommendations", "/api/price/{id}", "/health"]},
            "/build": {"auth": True, "api": ["/api/strategies", "/api/bots"]},
        },
        "secondary": {
            "/chart/:symbol?": {"api": ["/api/candles/{id}", "/ws/ticks/{id}"]},
            "/recommendations": {"api": ["/api/recommendations"]},
            "/recommendations/:id": {"api": ["/api/recommendations/{id}"]},
            "/watchlist": {"api": ["/api/watchlist"]},
            "/exposure": {"api": ["/api/exposure"]},
            "/account": {"api": ["/api/accounts", "/api/accounts/{id}/aliases"]},
            "/strategies": {"api": ["/api/strategies"]},
            "/strategies/new": {"api": ["POST /api/strategies"]},
            "/strategies/:id/optimize": {"api": ["POST /api/strategies/{id}/optimize"]},
            "/strategies/:id/versions": {"api": ["/api/strategies/{id}/versions"]},
            "/demo": {"api": ["/api/demo"]},
            "/bots": {"api": ["/api/bots"]},
            "/bots/:id": {"api": ["/api/bots/{id}"]},
            "/bots/:id/live": {"api": ["POST /api/bots/{id}/live"]},
            "/memory": {"api": ["/api/memory"]},
            "/review": {"api": ["/api/review"]},
            "/settings": {"api": ["/api/settings", "/api/models"]},
            "/history": {"api": ["/api/history"]},
            "/login": {"api": ["POST /api/auth/login"], "auth": False},
        },
        "mcp": False,
    }


@app.post("/api/telegram/webhook")
async def telegram_webhook(payload: dict[str, Any], db: AsyncSession = Depends(get_db)):
    return await handle_telegram_update(payload, db)
