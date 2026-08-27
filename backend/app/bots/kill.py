"""Single kill-switch implementation used by the web API AND Telegram /stopall.

Do not duplicate this logic in telegram/bot.py or the HTTP handler.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bot, KillSwitch
from app.enums import BotStatus


async def apply_kill_switch(
    db: AsyncSession,
    *,
    engaged: bool,
    reason: str,
) -> KillSwitch:
    """Engage or disengage the kill switch and stop running bots + pending executes.

    Shared by POST /api/kill-switch and Telegram /stopall. One implementation.
    """
    row = await db.get(KillSwitch, 1)
    if row is None:
        row = KillSwitch(id=1)
        db.add(row)
        await db.flush()
    row.engaged = engaged
    row.reason = reason
    row.engaged_at = datetime.now(timezone.utc) if engaged else None
    if engaged:
        bots = (await db.scalars(select(Bot))).all()
        for b in bots:
            b.kill_switched = True
            b.status = BotStatus.KILLED.value
    await db.commit()
    await db.refresh(row)
    return row


def kill_blocks_orders(engaged: bool) -> bool:
    """Unit-level predicate: an engaged switch forbids every order path."""
    return bool(engaged)
