"""Appendix C — Settings overlay. Secrets never round-trip in full."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.deps import current_operator
from app.db.models import EncryptedSecret, Operator, SettingsAudit
from app.db.session import get_db
from app.main import app
from app.runtime_config import (
    apply_overlay,
    clear_overlay,
    get_setting,
    last4,
    setting_source,
)

SECRET = "sk-ant-SUPERSECRET-xyz9876ABCD"
OANDA_SECRET = "oanda-live-token-NEVER-LEAK-9999"


class _Scalar:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class OverlaySession:
    def __init__(self):
        self.secrets: dict[str, EncryptedSecret] = {}
        self.audit: list[SettingsAudit] = []

    async def get(self, model, key):
        if model is EncryptedSecret:
            return self.secrets.get(key)
        return None

    def add(self, obj):
        if isinstance(obj, EncryptedSecret):
            self.secrets[obj.name] = obj
        elif isinstance(obj, SettingsAudit):
            self.audit.append(obj)

    async def delete(self, obj):
        if isinstance(obj, EncryptedSecret):
            self.secrets.pop(obj.name, None)

    async def scalars(self, stmt):
        text = str(stmt).lower()
        if "settings_audit" in text:
            return _Scalar(list(self.audit))
        return _Scalar(list(self.secrets.values()))

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def execute(self, *_a, **_k):
        return SimpleNamespace(all=lambda: [])


@pytest.fixture
def operator_client():
    store = OverlaySession()
    op = Operator(id="op-1", email="op@local", password_hash="x", language="en")

    async def _db():
        yield store

    async def _op():
        return op

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[current_operator] = _op
    clear_overlay()
    client = TestClient(app)
    yield client, store, op
    app.dependency_overrides.clear()
    clear_overlay()


def test_overlay_overrides_env(monkeypatch):
    clear_overlay()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key-FROMENV")
    assert get_setting("ANTHROPIC_API_KEY") == "env-key-FROMENV"
    apply_overlay({"ANTHROPIC_API_KEY": "settings-key-OVER"})
    assert get_setting("ANTHROPIC_API_KEY") == "settings-key-OVER"
    assert setting_source("ANTHROPIC_API_KEY") == "settings"


def test_empty_overlay_falls_back_to_env(monkeypatch):
    clear_overlay()
    monkeypatch.setenv("OANDA_API_KEY", "env-oanda-AAA1")
    apply_overlay({"OANDA_API_TOKEN": "desk-oanda-BBB2"})
    assert get_setting("OANDA_API_TOKEN") == "desk-oanda-BBB2"
    apply_overlay({"OANDA_API_TOKEN": ""})
    assert get_setting("OANDA_API_TOKEN") == "env-oanda-AAA1"
    assert setting_source("OANDA_API_TOKEN") == "env"


def test_get_providers_never_returns_full_secret(operator_client):
    client, _store, _op = operator_client
    r = client.put("/api/settings/providers", json={"ANTHROPIC_API_KEY": SECRET})
    assert r.status_code == 200
    got = client.get("/api/settings/providers")
    assert got.status_code == 200
    blob = got.text
    assert SECRET not in blob
    assert "SUPERSECRET" not in blob
    body = got.json()
    assert "mcp" not in body
    assert "mcp" not in body.get("providers", {})
    field = body["providers"]["anthropic"]["fields"]["ANTHROPIC_API_KEY"]
    assert field["status"] == "configured"
    assert field["last4"] == last4(SECRET)
    assert field["last4"] == SECRET[-4:]


def test_anthropic_key_settable_via_api(operator_client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client, store, _op = operator_client
    r = client.put("/api/settings/providers", json={"ANTHROPIC_API_KEY": SECRET})
    assert r.status_code == 200
    assert get_setting("ANTHROPIC_API_KEY") == SECRET
    assert "ANTHROPIC_API_KEY" in store.secrets
    assert SECRET not in (store.secrets["ANTHROPIC_API_KEY"].ciphertext or "")


def test_put_rejects_mcp_and_env_only(operator_client):
    client, _store, _op = operator_client
    r = client.put("/api/settings/providers", json={"MCP_TOKEN": "nope"})
    assert r.status_code == 400
    r2 = client.put("/api/settings/providers", json={"DATABASE_URL": "postgres://x"})
    assert r2.status_code == 400
    r3 = client.put("/api/settings/providers", json={"REDIS_URL": "redis://x"})
    assert r3.status_code == 400


def test_audit_records_key_name_not_value(operator_client):
    client, store, _op = operator_client
    client.put("/api/settings/providers", json={"OANDA_API_TOKEN": OANDA_SECRET})
    keys = [a.key_name for a in store.audit]
    assert "OANDA_API_TOKEN" in keys
    for row in store.audit:
        assert OANDA_SECRET not in (row.key_name or "")
        assert OANDA_SECRET not in (row.action or "")
    body = client.get("/api/settings/providers").json()
    audit_blob = str(body.get("audit"))
    assert "OANDA_API_TOKEN" in audit_blob
    assert OANDA_SECRET not in audit_blob


def test_oanda_client_reads_overlay_immediately(monkeypatch):
    from app.feeds.oanda import OandaClient

    clear_overlay()
    monkeypatch.setenv("OANDA_API_KEY", "old-env-token")
    monkeypatch.setenv("OANDA_ACCOUNT_ID", "acct-env")
    c = OandaClient()
    assert c.api_token == "old-env-token"
    apply_overlay({"OANDA_API_TOKEN": "new-settings-token"})
    assert c.api_token == "new-settings-token"


class _Resp:
    def __init__(self, status_code=200, payload=None, text="ok"):
        self.status_code = status_code
        self._payload = payload or {"instruments": [{"name": "EUR_USD"}]}
        self.text = text
        self.headers = {"content-type": "application/json"}

    def json(self):
        return self._payload


class _FakeClient:
    last: dict | None = None

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return None

    async def get(self, url, **kwargs):
        _FakeClient.last = {"url": url, **kwargs}
        if "api.anthropic.com" in url:
            return _Resp(200, {"data": [{"id": "claude-sonnet-5"}]})
        if "calendar/economic" in url:
            return _Resp(200, {"economicCalendar": []})
        if "twelvedata" in url or "/quote" in url:
            return _Resp(200, {"symbol": "EUR/USD"})
        if "api.telegram.org" in url:
            return _Resp(200, {"ok": True, "result": {"username": "zorro"}})
        if "agiliumtrade" in url:
            return _Resp(200, {"id": "acc"})
        return _Resp(200, {"instruments": [{"name": "EUR_USD"}]})


def test_test_endpoint_uses_unsaved_form_value(operator_client, monkeypatch):
    client, _store, _op = operator_client
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    _FakeClient.last = None
    unsaved = "unsaved-oanda-token-FORMVALUE"
    r = client.post(
        "/api/settings/providers/oanda/test",
        json={"OANDA_API_TOKEN": unsaved, "OANDA_ACCOUNT_ID": "001-001", "OANDA_ENV": "practice"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert _FakeClient.last is not None
    assert _FakeClient.last["headers"]["Authorization"] == f"Bearer {unsaved}"
    assert unsaved not in client.get("/api/settings/providers").text


def test_test_endpoint_fails_honestly_when_missing(operator_client, monkeypatch):
    client, _store, _op = operator_client
    monkeypatch.delenv("OANDA_API_KEY", raising=False)
    monkeypatch.delenv("OANDA_API_TOKEN", raising=False)
    monkeypatch.delenv("OANDA_ACCOUNT_ID", raising=False)
    clear_overlay()

    def boom(*_a, **_k):
        raise AssertionError("must not network when key is missing")

    monkeypatch.setattr(httpx, "AsyncClient", boom)
    r = client.post("/api/settings/providers/oanda/test", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert "not configured" in body["detail"].lower() or "yapılandır" in body["detail"].lower()


def test_anthropic_test_uses_unsaved_key(operator_client, monkeypatch):
    client, _store, _op = operator_client
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    r = client.post("/api/settings/providers/anthropic/test", json={"ANTHROPIC_API_KEY": "sk-unsaved-ANTH"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert _FakeClient.last["headers"]["x-api-key"] == "sk-unsaved-ANTH"


def test_clients_resolve_via_get_setting_not_os_environ_only():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    files = [
        root / "feeds" / "oanda.py",
        root / "feeds" / "twelve.py",
        root / "feeds" / "finnhub.py",
        root / "execution" / "metaapi.py",
        root / "agent" / "runtime.py",
        root / "telegram" / "bot.py",
    ]
    for path in files:
        text = path.read_text()
        assert "get_setting(" in text, path.name
        assert "get_settings()" not in text or path.name == "runtime.py"
        # Trading API keys must not be read with os.getenv / os.environ in these modules
        # (base URLs for Twelve/Finnhub hosts are allowed).
        for line in text.splitlines():
            if "OANDA_API" in line or "ANTHROPIC_API_KEY" in line or "FINNHUB_API_KEY" in line:
                if "os.getenv" in line or "os.environ.get(\"OANDA" in line or "os.environ.get('OANDA" in line:
                    raise AssertionError(f"{path.name}: trading key read from os.environ: {line}")
            if "METAAPI_TOKEN" in line and ("os.getenv" in line or "os.environ.get" in line):
                raise AssertionError(f"{path.name}: METAAPI_TOKEN from os.environ: {line}")
            if "TELEGRAM_BOT_TOKEN" in line and ("os.getenv" in line or "os.environ.get" in line):
                raise AssertionError(f"{path.name}: TELEGRAM_BOT from os.environ: {line}")
            if "TWELVE_DATA_API_KEY" in line and ("os.getenv" in line or "os.environ.get" in line):
                raise AssertionError(f"{path.name}: TWELVE key from os.environ: {line}")


def test_no_mcp_in_overlay_catalog():
    from app.runtime_config import OVERLAY_KEYS

    assert not any("MCP" in k for k in OVERLAY_KEYS)
