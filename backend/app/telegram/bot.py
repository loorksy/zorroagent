"""Telegram shares the SAME brain as the web app. /stopall is the kill switch."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots.kill import apply_kill_switch
from app.runtime_config import apply_overlay, get_setting, persist_overlay
from app.db.models import Bot, Recommendation


HELP = (
    "Zorro — same brain as the web app.\n"
    "/ask <text> — chat\n"
    "/today — scan today\n"
    "/rec <id> — recommendation card\n"
    "/bots — list bots\n"
    "/stopall — KILL SWITCH (overrides everything)\n"
    "/killoff — disengage kill switch\n"
    "Personal analysis, not fund management. Risk of loss."
)


async def handle_telegram_update(payload: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
    message = (payload.get("message") or {})
    chat_id = str((message.get("chat") or {}).get("id") or "")
    text = (message.get("text") or "").strip()
    allowed = get_setting("TELEGRAM_ALLOWED_CHAT_ID")
    if allowed and chat_id and chat_id != allowed:
        return {"ok": False, "error": "unauthorized chat"}
    if not text:
        return {"ok": True, "reply": HELP}

    cmd, _, rest = text.partition(" ")
    cmd = cmd.lower()
    if cmd in {"/start", "/help"}:
        return {"ok": True, "reply": HELP}
    if cmd == "/stopall":
        await apply_kill_switch(db, engaged=True, reason="telegram:/stopall")
        return {"ok": True, "reply": "Kill switch ENGAGED. All bots stopped. Overrides everything."}
    if cmd == "/killoff":
        await apply_kill_switch(db, engaged=False, reason="telegram:/killoff")
        return {"ok": True, "reply": "Kill switch disengaged."}
    if cmd == "/link":
        provided = rest.strip()
        stored = get_setting("TELEGRAM_LINK_CODE")
        if provided and stored and provided == stored:
            apply_overlay({"TELEGRAM_ALLOWED_CHAT_ID": chat_id})
            try:
                await persist_overlay(db, {"TELEGRAM_ALLOWED_CHAT_ID": chat_id})
            except Exception:
                pass
            return {"ok": True, "reply": "Telegram linked. Same brain as the web desk."}
        if not provided:
            return {
                "ok": True,
                "reply": "Generate a linking code in Settings → Telegram, then send /link <code>.",
            }
        return {"ok": True, "reply": "Linking code did not match. Generate a new one in Settings."}
    if cmd == "/today":
        recs = (await db.scalars(select(Recommendation).order_by(Recommendation.created_at.desc()).limit(10))).all()
        lines = [f"{r.direction} {r.canonical_id} {r.plan_type} ({r.execution_status})" for r in recs] or ["No cards today."]
        return {"ok": True, "reply": "Scan Today\n" + "\n".join(lines)}
    if cmd == "/bots":
        bots = (await db.scalars(select(Bot))).all()
        lines = [f"{b.name} {b.status}" for b in bots] or ["No bots."]
        return {"ok": True, "reply": "\n".join(lines)}
    if cmd == "/rec":
        rec = await db.get(Recommendation, rest.strip())
        if not rec:
            return {"ok": True, "reply": "Named recommendation not found."}
        return {
            "ok": True,
            "reply": (
                f"{rec.direction} {rec.canonical_id}\n"
                f"bias={rec.analytical_bias} plan={rec.plan_type} status={rec.execution_status}\n"
                f"entry {rec.preferred_entry} sl {rec.stop_loss} tp {rec.take_profits}\n"
                f"fill={rec.fill_rule} next={rec.next_action}\n"
                f"similar={rec.similar_past_cases}\n"
                f"model={rec.model_id}"
            ),
            "card": {
                "direction": rec.direction,
                "canonical_id": rec.canonical_id,
                "analytical_bias": rec.analytical_bias,
                "plan_type": rec.plan_type,
                "execution_status": rec.execution_status,
                "preferred_entry": rec.preferred_entry,
                "stop_loss": rec.stop_loss,
                "take_profits": rec.take_profits,
                "fill_rule": rec.fill_rule,
                "next_action": rec.next_action,
                "similar_past_cases": rec.similar_past_cases,
                "model_id": rec.model_id,
            },
        }
    if cmd == "/ask":
        from app.agent.runtime import run_claude

        reply = await run_claude(get_setting("DEEP_MODEL"), rest or "Scan the book.")
        return {"ok": True, "reply": reply}
    return {"ok": True, "reply": HELP}
