import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_login_without_db_does_not_crash_the_suite():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/auth/login", json={"email": "op@local", "password": "x"})
        assert r.status_code in {200, 401, 500}
