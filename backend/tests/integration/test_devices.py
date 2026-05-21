"""Integration tests for /devices/* viewer endpoints."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from alaba.security import mint_access_jwt
from tests.factories import make_user, make_user_device


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _auth_headers(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


async def test_list_my_devices_empty_after_login(db_session):
    """Setup: user with one device → list returns one device, marked is_current."""
    user = make_user("+2348031234600")
    db_session.add(user); await db_session.flush()
    device = make_user_device(user.id, "dev-1")
    db_session.add(device); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    async with await _client() as c:
        r = await c.get("/devices", headers=_auth_headers(jwt))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cap"] == 2
    assert body["active_count"] == 1
    assert len(body["devices"]) == 1
    assert body["devices"][0]["is_current"] is True
    assert body["deactivation_cooldown_unlock_at"] is None


async def test_deactivate_my_device(db_session):
    user = make_user("+2348031234601")
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A")
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(d1.id)},
    )
    async with await _client() as c:
        r = await c.post(f"/devices/{d2.id}/deactivate", headers=_auth_headers(jwt))
    assert r.status_code == 204


async def test_cannot_deactivate_other_users_device(db_session):
    u1 = make_user("+2348031234602")
    u2 = make_user("+2348031234603")
    db_session.add_all([u1, u2]); await db_session.flush()
    d1 = make_user_device(u1.id, "u1-dev")
    d2 = make_user_device(u2.id, "u2-dev")
    db_session.add_all([d1, d2]); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(u1.id), role="viewer",
        extras={"user_device_id": str(d1.id)},
    )
    async with await _client() as c:
        r = await c.post(f"/devices/{d2.id}/deactivate", headers=_auth_headers(jwt))
    assert r.status_code == 404


async def test_no_auth_returns_401():
    async with await _client() as c:
        r = await c.get("/devices")
    assert r.status_code == 401
