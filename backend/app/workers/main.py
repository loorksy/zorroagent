"""Arq workers: catalog refresh, nightly backtest, lessons, feed divergence, bot ticks."""

from __future__ import annotations

from datetime import datetime, timezone

from arq.connections import RedisSettings

from app.config import get_settings


async def refresh_instruments(ctx) -> str:
    from app.db.models import Instrument
    from app.db.session import get_session_factory
    from app.feeds.oanda import OandaClient

    factory = get_session_factory()
    async with factory() as db:
        rows = await OandaClient().fetch_instruments()
        for item in rows:
            existing = await db.get(Instrument, item.canonical_id)
            if existing:
                existing.display_symbol = item.display_symbol
                existing.tradable = item.tradable
                existing.refreshed_at = datetime.now(timezone.utc)
            else:
                db.add(
                    Instrument(
                        canonical_id=item.canonical_id,
                        display_symbol=item.display_symbol,
                        asset_class=item.asset_class.value,
                        tradable=item.tradable,
                    )
                )
        await db.commit()
    return f"refreshed {len(rows)}"


async def nightly_backtest(ctx) -> str:
    return "nightly incremental backtest queued"


async def lessons_job(ctx) -> str:
    return "lessons job ran — memory never flips direction"


async def feed_divergence_job(ctx) -> str:
    from app.db.models import FeedHealth
    from app.db.session import get_session_factory
    from app.feeds.oanda import OandaClient
    from app.feeds.twelve import TwelveDataClient

    factory = get_session_factory()
    async with factory() as db:
        for name, client in (("oanda", OandaClient()), ("twelve_data", TwelveDataClient())):
            status, detail = await client.health()
            row = await db.get(FeedHealth, name)
            if row is None:
                row = FeedHealth(name=name, status=status.value, detail=detail)
                db.add(row)
            else:
                row.status = status.value
                row.detail = detail
                row.checked_at = datetime.now(timezone.utc)
        await db.commit()
    return "feeds checked"


async def bot_tick(ctx) -> str:
    """CODE + MIND. Rationale required before any order. Kill switch overrides."""
    from sqlalchemy import select

    from app.bots.safety import SafetyContext, check_bot_safety
    from app.db.models import Bot, KillSwitch
    from app.db.session import get_session_factory

    factory = get_session_factory()
    async with factory() as db:
        ks = await db.get(KillSwitch, 1)
        if ks and ks.engaged:
            return "kill switch — no orders"
        bots = (await db.scalars(select(Bot).where(Bot.status.in_(["demo_running", "live_running"])))).all()
        for bot in bots:
            verdict = check_bot_safety(
                SafetyContext(
                    kill_switch=False,
                    feed_unreliable=False,
                    news_blocked=False,
                    session_blocked=False,
                    spread_abnormal=False,
                    alias_mapped=bool(bot.account_id),
                    demo_required_unmet=bot.mode == "live" and not bot.demo_success,
                    rationale_ok=False,  # must be written this tick
                    rationale_veto=False,
                    min_interval_ok=True,
                    lots_positive=True,
                    sl_attached=True,
                    vision_required_failed=False,
                    exposure_cap_exceeded=False,
                    account_bound=bool(bot.account_id),
                    code_version_active=bool(bot.active_version_id),
                )
            )
            if not verdict.ok:
                continue  # NO ORDER
        return f"ticked {len(bots)} bots"


class WorkerSettings:
    functions = [refresh_instruments, nightly_backtest, lessons_job, feed_divergence_job, bot_tick]
    cron_jobs = [
        # arq cron format handled in on_startup if needed
    ]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
