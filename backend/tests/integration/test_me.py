"""Integration tests for /me endpoint."""

from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from alaba.security import mint_access_jwt
from tests.factories import make_admin, make_producer, make_user, make_user_device


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _hdr(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


async def test_me_viewer(db_session):
    user = make_user("+2348031234900")
    db_session.add(user); await db_session.flush()
    device = make_user_device(user.id, "me-1")
    db_session.add(device); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "viewer"
    assert body["phone"] == "+2348031234900"


async def test_me_producer(db_session):
    p = make_producer("mep@test.com")
    db_session.add(p); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(p.id), role="producer")
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "producer"
    assert body["verified"] is False


async def test_me_admin(db_session):
    a = make_admin("mea@test.com")
    db_session.add(a); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(a.id), role="admin")
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


async def test_me_viewer_with_deactivated_device_returns_403(db_session):
    user = make_user("+2348031234901")
    db_session.add(user); await db_session.flush()
    device = make_user_device(user.id, "me-deact", deactivated=True)
    device.deactivated_at = datetime.now(UTC)
    db_session.add(device); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 403
    assert r.json()["detail"]["reason"] == "device_deactivated"


async def test_me_no_auth():
    async with await _client() as c:
        r = await c.get("/me")
    assert r.status_code == 401
