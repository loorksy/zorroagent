"""Provider Test Connection pings. Always use the supplied (possibly unsaved) values."""

from __future__ import annotations

import httpx

from app.runtime_config import get_setting, oanda_base_url

PING_TIMEOUT = 12.0

MESSAGES = {
    "en": {
        "missing": "{label} is not configured.",
        "pass": "{label} ping passed.",
        "fail": "{label} ping failed: {detail}",
        "http": "HTTP {code}",
    },
    "tr": {
        "missing": "{label} yapılandırılmamış.",
        "pass": "{label} bağlantı testi geçti.",
        "fail": "{label} bağlantı testi başarısız: {detail}",
        "http": "HTTP {code}",
    },
    "ar": {
        "missing": "{label} غير مُعدّ.",
        "pass": "نجح اختبار {label}.",
        "fail": "فشل اختبار {label}: {detail}",
        "http": "HTTP {code}",
    },
}

LABELS = {
    "en": {
        "oanda": "OANDA",
        "twelve": "Twelve Data",
        "finnhub": "Finnhub",
        "metaapi": "MetaApi",
        "anthropic": "Anthropic",
        "telegram": "Telegram",
    },
    "tr": {
        "oanda": "OANDA",
        "twelve": "Twelve Data",
        "finnhub": "Finnhub",
        "metaapi": "MetaApi",
        "anthropic": "Anthropic",
        "telegram": "Telegram",
    },
    "ar": {
        "oanda": "OANDA",
        "twelve": "Twelve Data",
        "finnhub": "Finnhub",
        "metaapi": "MetaApi",
        "anthropic": "Anthropic",
        "telegram": "Telegram",
    },
}


def localize(lang: str, key: str, **kwargs: str) -> str:
    pack = MESSAGES.get(lang) or MESSAGES["en"]
    return pack[key].format(**kwargs)


def _label(lang: str, provider: str) -> str:
    return (LABELS.get(lang) or LABELS["en"]).get(provider, provider)


def _pick(draft: dict[str, str] | None, key: str) -> str:
    if draft and key in draft and draft[key] != "":
        return draft[key]
    return get_setting(key)


async def ping_oanda(draft: dict[str, str] | None, lang: str) -> dict:
    label = _label(lang, "oanda")
    token = _pick(draft, "OANDA_API_TOKEN")
    account = _pick(draft, "OANDA_ACCOUNT_ID")
    env = _pick(draft, "OANDA_ENV") or "practice"
    if not token or not account:
        return {"ok": False, "provider": "oanda", "detail": localize(lang, "missing", label=label)}
    url = f"{oanda_base_url(env)}/v3/accounts/{account}/instruments"
    try:
        async with httpx.AsyncClient(timeout=PING_TIMEOUT) as client:
            r = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}", "Accept-Datetime-Format": "RFC3339"},
            )
        if r.status_code == 200:
            return {"ok": True, "provider": "oanda", "detail": localize(lang, "pass", label=label)}
        return {
            "ok": False,
            "provider": "oanda",
            "detail": localize(lang, "fail", label=label, detail=localize(lang, "http", code=str(r.status_code))),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "provider": "oanda", "detail": localize(lang, "fail", label=label, detail=str(exc))}


async def ping_twelve(draft: dict[str, str] | None, lang: str) -> dict:
    label = _label(lang, "twelve")
    key = _pick(draft, "TWELVE_DATA_API_KEY")
    if not key:
        return {"ok": False, "provider": "twelve", "detail": localize(lang, "missing", label=label)}
    base = os_twelve_base()
    try:
        async with httpx.AsyncClient(timeout=PING_TIMEOUT) as client:
            r = await client.get(f"{base}/quote", params={"symbol": "EUR/USD", "apikey": key})
        if r.status_code == 200:
            return {"ok": True, "provider": "twelve", "detail": localize(lang, "pass", label=label)}
        return {
            "ok": False,
            "provider": "twelve",
            "detail": localize(lang, "fail", label=label, detail=localize(lang, "http", code=str(r.status_code))),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "provider": "twelve", "detail": localize(lang, "fail", label=label, detail=str(exc))}


async def ping_finnhub(draft: dict[str, str] | None, lang: str) -> dict:
    label = _label(lang, "finnhub")
    key = _pick(draft, "FINNHUB_API_KEY")
    if not key:
        return {"ok": False, "provider": "finnhub", "detail": localize(lang, "missing", label=label)}
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = os_finnhub_base()
    try:
        async with httpx.AsyncClient(timeout=PING_TIMEOUT) as client:
            r = await client.get(
                f"{base}/calendar/economic",
                params={"from": today, "to": today, "token": key},
            )
        if r.status_code == 200:
            return {"ok": True, "provider": "finnhub", "detail": localize(lang, "pass", label=label)}
        return {
            "ok": False,
            "provider": "finnhub",
            "detail": localize(lang, "fail", label=label, detail=localize(lang, "http", code=str(r.status_code))),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "provider": "finnhub", "detail": localize(lang, "fail", label=label, detail=str(exc))}


async def ping_metaapi(draft: dict[str, str] | None, lang: str) -> dict:
    label = _label(lang, "metaapi")
    token = _pick(draft, "METAAPI_TOKEN")
    account = _pick(draft, "METAAPI_ACCOUNT_ID")
    region = _pick(draft, "METAAPI_REGION") or "new-york"
    if not token:
        return {"ok": False, "provider": "metaapi", "detail": localize(lang, "missing", label=label)}
    if account:
        url = f"https://mt-client-api-v1.{region}.agiliumtrade.ai/users/current/accounts/{account}"
    else:
        url = f"https://mt-client-api-v1.{region}.agiliumtrade.ai/users/current/accounts"
    try:
        async with httpx.AsyncClient(timeout=PING_TIMEOUT) as client:
            r = await client.get(url, headers={"auth-token": token})
        if r.status_code < 400:
            return {"ok": True, "provider": "metaapi", "detail": localize(lang, "pass", label=label)}
        return {
            "ok": False,
            "provider": "metaapi",
            "detail": localize(lang, "fail", label=label, detail=localize(lang, "http", code=str(r.status_code))),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "provider": "metaapi", "detail": localize(lang, "fail", label=label, detail=str(exc))}


async def ping_anthropic(draft: dict[str, str] | None, lang: str) -> dict:
    label = _label(lang, "anthropic")
    key = _pick(draft, "ANTHROPIC_API_KEY")
    if not key:
        return {"ok": False, "provider": "anthropic", "detail": localize(lang, "missing", label=label)}
    try:
        async with httpx.AsyncClient(timeout=PING_TIMEOUT) as client:
            r = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            )
        if r.status_code == 200:
            return {"ok": True, "provider": "anthropic", "detail": localize(lang, "pass", label=label)}
        return {
            "ok": False,
            "provider": "anthropic",
            "detail": localize(lang, "fail", label=label, detail=localize(lang, "http", code=str(r.status_code))),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "provider": "anthropic", "detail": localize(lang, "fail", label=label, detail=str(exc))}


async def ping_telegram(draft: dict[str, str] | None, lang: str) -> dict:
    label = _label(lang, "telegram")
    token = _pick(draft, "TELEGRAM_BOT_TOKEN")
    if not token:
        return {"ok": False, "provider": "telegram", "detail": localize(lang, "missing", label=label)}
    try:
        async with httpx.AsyncClient(timeout=PING_TIMEOUT) as client:
            r = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code == 200 and data.get("ok"):
            return {"ok": True, "provider": "telegram", "detail": localize(lang, "pass", label=label)}
        detail = str(data.get("description") or localize(lang, "http", code=str(r.status_code)))
        return {"ok": False, "provider": "telegram", "detail": localize(lang, "fail", label=label, detail=detail)}
    except httpx.HTTPError as exc:
        return {"ok": False, "provider": "telegram", "detail": localize(lang, "fail", label=label, detail=str(exc))}


PINGERS = {
    "oanda": ping_oanda,
    "twelve": ping_twelve,
    "finnhub": ping_finnhub,
    "metaapi": ping_metaapi,
    "anthropic": ping_anthropic,
    "telegram": ping_telegram,
}


def os_twelve_base() -> str:
    import os

    return os.environ.get("TWELVE_DATA_BASE_URL") or "https://api.twelvedata.com"


def os_finnhub_base() -> str:
    import os

    return os.environ.get("FINNHUB_BASE_URL") or "https://finnhub.io/api/v1"
