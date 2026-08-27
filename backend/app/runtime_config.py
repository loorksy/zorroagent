"""Settings overlay: operator Settings DB wins over bootstrap .env.

.env / process environment is first-install only for trading keys.
After save, in-memory overlay is the live config; API clients re-read it
on every call (no process restart). Arq workers reload from Postgres at
the start of each job.

Never put DATABASE_URL, REDIS_URL, ENCRYPTION_KEY, SETTINGS_SECRET, JWT,
or bind host/port in browser JSON.
"""

from __future__ import annotations

import inspect
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Iterable, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EncryptedSecret, SettingsAudit
from app.security import decrypt_secret, encrypt_secret

log = logging.getLogger("zorro.settings")

# ---------------------------------------------------------------------------
# Key catalogs
# ---------------------------------------------------------------------------

SECRET_KEYS: frozenset[str] = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "OANDA_API_TOKEN",
        "OANDA_ACCOUNT_ID",
        "TWELVE_DATA_API_KEY",
        "FINNHUB_API_KEY",
        "METAAPI_TOKEN",
        "METAAPI_ACCOUNT_ID",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_LINK_CODE",
        "TELEGRAM_ALLOWED_CHAT_ID",
        "SENTRY_DSN",
    }
)

PUBLIC_KEYS: frozenset[str] = frozenset(
    {
        "OANDA_ENV",
        "PRICE_DIVERGENCE_BPS",
        "QUICK_MODEL",
        "DEEP_MODEL",
        "METAAPI_BROKER_SERVER",
        "METAAPI_ACCOUNT_TYPE",
        "METAAPI_REGION",
        "PUBLIC_APP_URL",
        "WEBHOOK_BASE_URL",
    }
)

OVERLAY_KEYS: frozenset[str] = SECRET_KEYS | PUBLIC_KEYS

# Host concerns — never accepted from Settings PUT, never shown as values.
ENV_ONLY_KEYS: frozenset[str] = frozenset(
    {
        "DATABASE_URL",
        "REDIS_URL",
        "ENCRYPTION_KEY",
        "SETTINGS_SECRET",
        "JWT_SECRET",
        "JWT_ALGORITHM",
        "APP_SECRET_KEY",
        "API_HOST",
        "API_PORT",
        "OPERATOR_PASSWORD",
        "OPERATOR_PIN",
        "CONFIRMATION_PIN",
    }
)

# Overlay key → env names to read when overlay is empty.
ENV_ALIASES: dict[str, tuple[str, ...]] = {
    "ANTHROPIC_API_KEY": ("ANTHROPIC_API_KEY",),
    "OANDA_API_TOKEN": ("OANDA_API_TOKEN", "OANDA_API_KEY"),
    "OANDA_ACCOUNT_ID": ("OANDA_ACCOUNT_ID",),
    "OANDA_ENV": ("OANDA_ENV", "OANDA_ENVIRONMENT"),
    "TWELVE_DATA_API_KEY": ("TWELVE_DATA_API_KEY",),
    "PRICE_DIVERGENCE_BPS": ("PRICE_DIVERGENCE_BPS",),
    "FINNHUB_API_KEY": ("FINNHUB_API_KEY",),
    "METAAPI_TOKEN": ("METAAPI_TOKEN",),
    "METAAPI_ACCOUNT_ID": ("METAAPI_ACCOUNT_ID",),
    "METAAPI_BROKER_SERVER": ("METAAPI_BROKER_SERVER", "METAAPI_SERVER"),
    "METAAPI_ACCOUNT_TYPE": ("METAAPI_ACCOUNT_TYPE",),
    "METAAPI_REGION": ("METAAPI_REGION",),
    "QUICK_MODEL": ("QUICK_MODEL",),
    "DEEP_MODEL": ("DEEP_MODEL",),
    "TELEGRAM_BOT_TOKEN": ("TELEGRAM_BOT_TOKEN",),
    "TELEGRAM_LINK_CODE": ("TELEGRAM_LINK_CODE",),
    "TELEGRAM_ALLOWED_CHAT_ID": ("TELEGRAM_ALLOWED_CHAT_ID",),
    "SENTRY_DSN": ("SENTRY_DSN",),
    "PUBLIC_APP_URL": ("PUBLIC_APP_URL", "FRONTEND_ORIGIN"),
    "WEBHOOK_BASE_URL": ("WEBHOOK_BASE_URL",),
}

_DEFAULTS: dict[str, str] = {
    "OANDA_ENV": "practice",
    "PRICE_DIVERGENCE_BPS": "15",
    "QUICK_MODEL": "claude-sonnet-5",
    "DEEP_MODEL": "claude-fable-5",
    "METAAPI_ACCOUNT_TYPE": "demo",
    "METAAPI_REGION": "new-york",
}

OANDA_PRACTICE_URL = "https://api-fxpractice.oanda.com"
OANDA_LIVE_URL = "https://api-fxtrade.oanda.com"

PROVIDER_FIELDS: dict[str, tuple[str, ...]] = {
    "oanda": ("OANDA_API_TOKEN", "OANDA_ACCOUNT_ID", "OANDA_ENV"),
    "twelve": ("TWELVE_DATA_API_KEY", "PRICE_DIVERGENCE_BPS"),
    "finnhub": ("FINNHUB_API_KEY",),
    "metaapi": (
        "METAAPI_TOKEN",
        "METAAPI_ACCOUNT_ID",
        "METAAPI_BROKER_SERVER",
        "METAAPI_ACCOUNT_TYPE",
        "METAAPI_REGION",
    ),
    "anthropic": ("ANTHROPIC_API_KEY", "QUICK_MODEL", "DEEP_MODEL"),
    "telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_LINK_CODE", "TELEGRAM_ALLOWED_CHAT_ID"),
    "optional": ("SENTRY_DSN", "PUBLIC_APP_URL", "WEBHOOK_BASE_URL"),
}

Source = Literal["settings", "env", "missing"]

_overlay: dict[str, str] = {}
_audit_memory: list[dict[str, Any]] = []
_generation: int = 0


def config_generation() -> int:
    """Increments on every save so callers can detect rotation."""
    return _generation


def last4(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "••••"
    return value[-4:]


def _env_raw(key: str) -> str:
    for name in ENV_ALIASES.get(key, (key,)):
        val = os.environ.get(name)
        if val:
            return val
    return ""


def get_setting(key: str) -> str:
    """Settings DB overlay if non-empty, else process environment, else default."""
    overlay_val = _overlay.get(key)
    if overlay_val:
        return overlay_val
    env_val = _env_raw(key)
    if env_val:
        return env_val
    return _DEFAULTS.get(key, "")


def setting_source(key: str) -> Source:
    if _overlay.get(key):
        return "settings"
    if _env_raw(key):
        return "env"
    if _DEFAULTS.get(key):
        return "env"
    return "missing"


def apply_overlay(updates: dict[str, str]) -> list[str]:
    """Apply in-memory overlay. Empty string clears (fall back to .env). Returns changed keys."""
    global _generation
    changed: list[str] = []
    for key, value in updates.items():
        if key not in OVERLAY_KEYS:
            continue
        if value == "":
            if key in _overlay:
                _overlay.pop(key, None)
                changed.append(key)
            elif key not in changed:
                # Explicit clear even if already empty — still an operator action.
                changed.append(key)
        else:
            if _overlay.get(key) != value:
                _overlay[key] = value
                changed.append(key)
            else:
                changed.append(key)
    if changed:
        _generation += 1
        log.info("settings overlay rotated generation=%s keys=%s", _generation, changed)
    return changed


def clear_overlay() -> None:
    """Test helper — drop in-memory overlay (does not touch Postgres)."""
    global _generation
    _overlay.clear()
    _audit_memory.clear()
    _generation += 1


def overlay_snapshot() -> dict[str, str]:
    return dict(_overlay)


def record_audit(key_name: str, action: str, operator_id: str | None = None) -> dict[str, Any]:
    entry = {
        "key": key_name,
        "action": action,
        "operator_id": operator_id,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    _audit_memory.append(entry)
    log.info("settings audit key=%s action=%s", key_name, action)
    return entry


def recent_audit(limit: int = 20) -> list[dict[str, Any]]:
    return list(reversed(_audit_memory[-limit:]))


def oanda_base_url(environment: str | None = None) -> str:
    env = (environment or get_setting("OANDA_ENV") or "practice").strip().lower()
    if env == "live":
        return OANDA_LIVE_URL
    custom = os.environ.get("OANDA_BASE_URL")
    if custom and env != "live":
        return custom
    return OANDA_PRACTICE_URL


def divergence_bps() -> float:
    raw = get_setting("PRICE_DIVERGENCE_BPS") or "15"
    try:
        return float(raw)
    except ValueError:
        return 15.0


def public_field(key: str) -> dict[str, Any]:
    value = get_setting(key)
    source = setting_source(key)
    configured = bool(value) and source != "missing"
    # Defaults like practice/15 still count as present config, not a secret leak.
    if key in SECRET_KEYS:
        return {
            "status": "configured" if value else "missing",
            "last4": last4(value) if value else "",
            "source": source if value else "missing",
        }
    return {
        "status": "configured" if configured or bool(value) else "missing",
        "value": value,
        "source": source if value else "missing",
    }


def providers_payload(system: dict[str, str] | None = None) -> dict[str, Any]:
    providers: dict[str, Any] = {}
    for name, keys in PROVIDER_FIELDS.items():
        fields = {k: public_field(k) for k in keys}
        secret_keys = [k for k in keys if k in SECRET_KEYS]
        if secret_keys:
            status = "configured" if all(get_setting(k) for k in secret_keys[:1]) else "missing"
        else:
            status = "configured"
        providers[name] = {"status": status, "fields": fields}
    body: dict[str, Any] = {
        "providers": providers,
        "system": system or {},
        "audit": [{"key": a["key"], "action": a["action"], "at": a["at"]} for a in recent_audit()],
        "hot_reload": {
            "api": True,
            "generation": _generation,
            "workers": "reload overlay from Postgres at the start of each job; no restart required for API keys",
        },
    }
    return body


def validate_updates(updates: dict[str, Any]) -> dict[str, str]:
    """Normalize a PUT body. Unknown / env-only keys are rejected. There is no MCP."""
    cleaned: dict[str, str] = {}
    for raw_key, raw_val in updates.items():
        key = str(raw_key)
        upper = key.upper()
        if "MCP" in upper:  # no MCP
            raise ValueError("no MCP: this provider is not supported")
        if upper in ENV_ONLY_KEYS:
            raise ValueError(f"{upper} is host infrastructure and cannot be set from Settings")
        if key not in OVERLAY_KEYS:
            raise ValueError(f"Unknown settings key: {key}")
        if raw_val is None:
            continue
        value = raw_val if isinstance(raw_val, str) else str(raw_val)
        if key == "OANDA_ENV" and value and value not in {"practice", "live"}:
            raise ValueError("OANDA_ENV must be practice or live")
        if key == "METAAPI_ACCOUNT_TYPE" and value and value not in {"demo", "live"}:
            raise ValueError("METAAPI_ACCOUNT_TYPE must be demo or live")
        if key == "PRICE_DIVERGENCE_BPS" and value:
            try:
                num = float(value)
            except ValueError as exc:
                raise ValueError("PRICE_DIVERGENCE_BPS must be a number") from exc
            if num <= 0:
                raise ValueError("PRICE_DIVERGENCE_BPS must be positive")
        if key in {"QUICK_MODEL", "DEEP_MODEL"} and value:
            from app.agent.runtime import ALLOWED_MODELS

            if value not in ALLOWED_MODELS:
                raise ValueError("Model not in the Anthropic multimodal catalog")
        cleaned[key] = value
    return cleaned


def generate_link_code() -> str:
    return "ZORRO-" + secrets.token_urlsafe(6).replace("_", "").replace("-", "")[:8].upper()


def _is_secret_row(row: Any) -> bool:
    return isinstance(row, EncryptedSecret) or getattr(row, "__tablename__", None) == "encrypted_secrets"


async def load_overlay_from_db(db: AsyncSession) -> None:
    """Replace in-memory overlay from Postgres. Missing/empty rows fall back to .env."""
    global _overlay
    try:
        rows = (await db.scalars(select(EncryptedSecret))).all()
    except Exception as exc:  # noqa: BLE001
        log.warning("settings overlay load skipped: %s", exc.__class__.__name__)
        return
    new: dict[str, str] = {}
    for row in rows:
        if not _is_secret_row(row):
            continue
        name = getattr(row, "name", None)
        cipher = getattr(row, "ciphertext", None)
        if not name or name not in OVERLAY_KEYS or not cipher:
            continue
        try:
            plain = decrypt_secret(cipher)
        except ValueError:
            continue
        if plain:
            new[name] = plain
    _overlay = new
    log.info("settings overlay loaded keys=%s", sorted(new))


async def persist_overlay(
    db: AsyncSession,
    updates: dict[str, str],
    operator_id: str | None = None,
) -> list[dict[str, Any]]:
    """Write encrypted rows + audit (key name only). Empty string deletes the row."""
    audit_rows: list[dict[str, Any]] = []
    for key, value in updates.items():
        action = "clear" if value == "" else "set"
        try:
            row = await db.get(EncryptedSecret, key)
        except Exception:
            row = None
        if row is not None and not _is_secret_row(row):
            row = None
        if value == "":
            if row is not None:
                maybe = db.delete(row)
                if inspect.isawaitable(maybe):
                    await maybe
        else:
            cipher = encrypt_secret(value)
            if row is None:
                db.add(EncryptedSecret(name=key, ciphertext=cipher))
            else:
                row.ciphertext = cipher
                row.updated_at = datetime.now(timezone.utc)
        entry = record_audit(key, action, operator_id)
        try:
            db.add(
                SettingsAudit(
                    key_name=key,
                    action=action,
                    operator_id=operator_id,
                )
            )
        except Exception:
            pass
        audit_rows.append(entry)
    try:
        await db.commit()
    except Exception as exc:  # noqa: BLE001
        log.warning("settings persist commit skipped: %s", exc.__class__.__name__)
        try:
            await db.rollback()
        except Exception:
            pass
    return audit_rows


async def load_audit_from_db(db: AsyncSession, limit: int = 20) -> None:
    try:
        rows = (
            await db.scalars(select(SettingsAudit).order_by(SettingsAudit.created_at.desc()).limit(limit))
        ).all()
    except Exception:
        return
    if not rows:
        return
    _audit_memory.clear()
    for row in reversed(list(rows)):
        if getattr(row, "key_name", None):
            _audit_memory.append(
                {
                    "key": row.key_name,
                    "action": row.action,
                    "operator_id": row.operator_id,
                    "at": row.created_at.isoformat() if row.created_at else "",
                }
            )


def assert_no_secrets(blob: Any, secrets: Iterable[str]) -> None:
    text = str(blob)
    for secret in secrets:
        if secret and len(secret) >= 8 and secret in text:
            raise AssertionError("secret leaked in payload")
