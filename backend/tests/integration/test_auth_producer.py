"""Integration tests for /auth/producer/* endpoints."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from tests.factories import make_producer


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_register_happy():
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/register",
            json={
                "email": "newprod@test.com",
                "password": "ten_chars!",
                "company_name": "Orban Forest",
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "producer"
    assert "jwt" in body


async def test_register_short_password():
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/register",
            json={"email": "short@test.com", "password": "short"},
        )
    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "password_too_short"


async def test_register_duplicate_email(db_session):
    existing = make_producer("dup@test.com")
    db_session.add(existing); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/register",
            json={"email": "dup@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 409


async def test_login_happy(db_session):
    producer = make_producer("loginok@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/login",
            json={"email": "loginok@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 200
    assert r.json()["role"] == "producer"


async def test_login_wrong_password(db_session):
    producer = make_producer("loginwp@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/login",
            json={"email": "loginwp@test.com", "password": "wrong_pass!"},
        )
    assert r.status_code == 401


async def test_login_unknown_email():
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/login",
            json={"email": "nobody@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 401
