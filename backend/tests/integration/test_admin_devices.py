"""Integration tests for admin user-devices endpoints."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from alaba.models import AdminAction
from alaba.security import mint_access_jwt
from sqlalchemy import select
from tests.factories import make_admin, make_user, make_user_device


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _auth_headers(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


async def test_lookup_user_by_phone_happy(db_session):
    admin = make_admin("adm1@test.com")
    user = make_user("+2348031234700")
    db_session.add_all([admin, user]); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.get(
            "/admin/users/lookup",
            params={"phone": "+2348031234700"},
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user_id"] == str(user.id)
    assert body["phone"] == "+2348031234700"


async def test_lookup_user_404(db_session):
    admin = make_admin("adm2@test.com")
    db_session.add(admin); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.get(
            "/admin/users/lookup",
            params={"phone": "+2348039999999"},
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 404


async def test_list_user_devices_for_admin(db_session):
    admin = make_admin("adm3@test.com")
    user = make_user("+2348031234701")
    db_session.add_all([admin, user]); await db_session.flush()
    d = make_user_device(user.id, "ud-1")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.get(
            f"/admin/users/{user.id}/devices",
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 200
    body = r.json()
    assert body["active_count"] == 1


async def test_force_deactivate_writes_admin_action(db_session):
    admin = make_admin("adm4@test.com")
    user = make_user("+2348031234702")
    db_session.add_all([admin, user]); await db_session.flush()
    d = make_user_device(user.id, "ud-2")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.post(
            f"/admin/users/{user.id}/devices/{d.id}/deactivate",
            json={"reason": "user reported phone lost"},
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 204
    result = await db_session.execute(select(AdminAction))
    actions = result.scalars().all()
    assert any(
        a.action == "force_deactivate_device" and a.admin_email == "adm4@test.com"
        for a in actions
    )


async def test_admin_endpoint_rejects_viewer_jwt(db_session):
    user = make_user("+2348031234703")
    db_session.add(user); await db_session.flush()
    d = make_user_device(user.id, "ud-3")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(d.id)},
    )
    async with await _client() as c:
        r = await c.get("/admin/users/lookup", params={"phone": "x"}, headers=_auth_headers(jwt))
    assert r.status_code == 403


async def test_force_deactivate_validates_reason_length(db_session):
    admin = make_admin("adm5@test.com")
    user = make_user("+2348031234704")
    db_session.add_all([admin, user]); await db_session.flush()
    d = make_user_device(user.id, "ud-4")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.post(
            f"/admin/users/{user.id}/devices/{d.id}/deactivate",
            json={"reason": "x"},  # < 5 chars
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 422
