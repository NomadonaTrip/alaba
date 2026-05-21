"""Integration tests for /auth/admin/login."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from tests.factories import make_admin


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_admin_login_happy(db_session):
    admin = make_admin("aint@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/admin/login",
            json={"email": "aint@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


async def test_admin_login_wrong_password(db_session):
    admin = make_admin("aiwp@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/admin/login",
            json={"email": "aiwp@test.com", "password": "wrong_pass!"},
        )
    assert r.status_code == 401


async def test_admin_login_unknown():
    async with await _client() as c:
        r = await c.post(
            "/auth/admin/login",
            json={"email": "noadmin@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 401
