"""Telegram shares the SAME brain as the web app. /stopall is the kill switch."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Bot, KillSwitch, Recommendation
from app.enums import BotStatus


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
    settings = get_settings()
    message = (payload.get("message") or {})
    chat_id = str((message.get("chat") or {}).get("id") or "")
    text = (message.get("text") or "").strip()
    if settings.telegram_allowed_chat_id and chat_id and chat_id != settings.telegram_allowed_chat_id:
        return {"ok": False, "error": "unauthorized chat"}
    if not text:
        return {"ok": True, "reply": HELP}

    cmd, _, rest = text.partition(" ")
    cmd = cmd.lower()
    if cmd in {"/start", "/help"}:
        return {"ok": True, "reply": HELP}
    if cmd == "/stopall":
        row = await db.get(KillSwitch, 1)
        if row is None:
            row = KillSwitch(id=1)
            db.add(row)
            await db.flush()
        row.engaged = True
        row.reason = "telegram:/stopall"
        bots = (await db.scalars(select(Bot))).all()
        for b in bots:
            b.kill_switched = True
            b.status = BotStatus.KILLED.value
        await db.commit()
        return {"ok": True, "reply": "Kill switch ENGAGED. All bots stopped. Overrides everything."}
    if cmd == "/killoff":
        row = await db.get(KillSwitch, 1)
        if row:
            row.engaged = False
            row.reason = ""
        await db.commit()
        return {"ok": True, "reply": "Kill switch disengaged."}
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
                f"plan={rec.plan_type} status={rec.execution_status}\n"
                f"entry {rec.preferred_entry} sl {rec.stop_loss} tp {rec.take_profits}\n"
                f"fill={rec.fill_rule}\n"
                f"model={rec.model_id}"
            ),
        }
    if cmd == "/ask":
        from app.agent.runtime import run_claude

        reply = await run_claude(settings.deep_model, rest or "Scan the book.")
        return {"ok": True, "reply": reply}
    return {"ok": True, "reply": HELP}
