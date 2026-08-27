"""Settings-owned environment REST. Secrets never leave the server in full."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_operator
from app.db.models import Operator
from app.db.session import get_db
from app.provider_pings import PINGERS
from app.runtime_config import (
    apply_overlay,
    generate_link_code,
    load_audit_from_db,
    load_overlay_from_db,
    persist_overlay,
    providers_payload,
    record_audit,
    validate_updates,
)

router = APIRouter()


class ProvidersIn(BaseModel):
    model_config = {"extra": "allow"}


class ProviderTestIn(BaseModel):
    model_config = {"extra": "allow"}


class TelegramLinkIn(BaseModel):
    action: str  # generate | revoke


async def _system_health() -> dict[str, str]:
    db_status = "disconnected"
    redis_status = "disconnected"
    try:
        from sqlalchemy import text

        from app.db.session import get_engine

        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    try:
        import redis.asyncio as redis

        from app.config import get_settings

        r = redis.from_url(get_settings().redis_url)
        await r.ping()
        redis_status = "connected"
        await r.aclose()
    except Exception:
        redis_status = "disconnected"
    return {"postgres": db_status, "redis": redis_status}


@router.get("/api/settings/providers")
async def get_providers(op: Operator = Depends(current_operator), db: AsyncSession = Depends(get_db)):
    await load_overlay_from_db(db)
    await load_audit_from_db(db)
    body = providers_payload(await _system_health())
    return body


@router.put("/api/settings/providers")
async def put_providers(
    body: ProvidersIn,
    op: Operator = Depends(current_operator),
    db: AsyncSession = Depends(get_db),
):
    raw = body.model_dump(exclude_unset=False)
    # Drop pydantic internals if any
    raw.pop("model_config", None)
    try:
        updates = validate_updates(raw)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not updates:
        return {"ok": True, "changed": [], **providers_payload(await _system_health())}
    apply_overlay(updates)
    await persist_overlay(db, updates, operator_id=op.id)
    if updates.get("QUICK_MODEL"):
        op.quick_model = updates["QUICK_MODEL"]
    if updates.get("DEEP_MODEL"):
        op.deep_model = updates["DEEP_MODEL"]
    try:
        await db.commit()
    except Exception:
        pass
    return {
        "ok": True,
        "changed": list(updates),
        "hot_reload": True,
        **providers_payload(await _system_health()),
    }


@router.post("/api/settings/providers/{provider}/test")
async def test_provider(
    provider: str,
    body: ProviderTestIn | None = None,
    op: Operator = Depends(current_operator),
):
    ping = PINGERS.get(provider)
    if ping is None:
        raise HTTPException(404, "Unknown provider")
    draft = {k: str(v) for k, v in (body.model_dump() if body else {}).items() if v is not None}
    lang = op.language if op.language in {"en", "tr", "ar"} else "en"
    result = await ping(draft, lang)
    return result


@router.post("/api/settings/telegram/link")
async def telegram_link(
    body: TelegramLinkIn,
    op: Operator = Depends(current_operator),
    db: AsyncSession = Depends(get_db),
):
    if body.action == "generate":
        code = generate_link_code()
        apply_overlay({"TELEGRAM_LINK_CODE": code})
        await persist_overlay(db, {"TELEGRAM_LINK_CODE": code}, operator_id=op.id)
        record_audit("TELEGRAM_LINK_CODE", "generate", op.id)
        return {
            "ok": True,
            "action": "generate",
            "code": code,  # shown once; later GET only last-4
            "last4": code[-4:],
        }
    if body.action == "revoke":
        apply_overlay({"TELEGRAM_LINK_CODE": ""})
        await persist_overlay(db, {"TELEGRAM_LINK_CODE": ""}, operator_id=op.id)
        record_audit("TELEGRAM_LINK_CODE", "revoke", op.id)
        return {"ok": True, "action": "revoke"}
    raise HTTPException(400, "action must be generate or revoke")
