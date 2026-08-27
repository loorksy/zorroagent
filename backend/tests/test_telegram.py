import pytest

from app.telegram.bot import handle_telegram_update


class FakeScalar:
    def __init__(self, rows=None):
        self.rows = rows or []

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self):
        self.ks = None
        self.bots = []

    async def get(self, model, key):
        return self.ks

    async def scalars(self, *_a, **_k):
        return FakeScalar(self.bots)

    def add(self, obj):
        self.ks = obj

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None


@pytest.mark.asyncio
async def test_stopall_engages_kill_switch():
    db = FakeDB()
    out = await handle_telegram_update({"message": {"text": "/stopall", "chat": {"id": 1}}}, db)
    assert "Kill switch ENGAGED" in out["reply"]
    assert db.ks.engaged is True
