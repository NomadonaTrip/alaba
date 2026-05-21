"""Tests for deps.py — get_current_principal and role-specific helpers."""

import uuid

import pytest
from fastapi import HTTPException

from alaba.deps import (
    _extract_token,
    get_current_admin,
    get_current_principal,
    get_current_producer,
    get_current_viewer,
)
from alaba.models import Admin, Producer, User, UserDevice
from alaba.security import hash_password, mint_access_jwt


class FakeRequest:
    def __init__(self, headers: dict | None = None, cookies: dict | None = None):
        self.headers = headers or {}
        self.cookies = cookies or {}


def test_extract_token_from_authorization_header():
    req = FakeRequest(headers={"Authorization": "Bearer abc123"})
    assert _extract_token(req) == "abc123"


def test_extract_token_from_cookie_fallback():
    req = FakeRequest(cookies={"auth_token": "xyz789"})
    assert _extract_token(req) == "xyz789"


def test_extract_token_header_takes_precedence():
    req = FakeRequest(
        headers={"Authorization": "Bearer header_token"},
        cookies={"auth_token": "cookie_token"},
    )
    assert _extract_token(req) == "header_token"


def test_extract_token_none_when_neither_set():
    req = FakeRequest()
    assert _extract_token(req) is None


def test_extract_token_ignores_non_bearer_authorization():
    req = FakeRequest(headers={"Authorization": "Basic abc123"})
    assert _extract_token(req) is None


async def test_get_current_principal_missing_token_raises_401(db_session):
    req = FakeRequest()
    with pytest.raises(HTTPException) as exc:
        await get_current_principal(req, db=db_session)
    assert exc.value.status_code == 401


async def test_get_current_principal_invalid_token_raises_401(db_session):
    req = FakeRequest(headers={"Authorization": "Bearer not.a.jwt"})
    with pytest.raises(HTTPException) as exc:
        await get_current_principal(req, db=db_session)
    assert exc.value.status_code == 401


async def test_get_current_principal_viewer_happy(db_session):
    user = User(phone="+2348031234567", phone_verified=True)
    db_session.add(user); await db_session.flush()
    device = UserDevice(user_id=user.id, device_id="dev-1", platform="android")
    db_session.add(device); await db_session.flush()
    token = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    principal = await get_current_principal(req, db=db_session)
    assert principal.role == "viewer"
    assert principal.user.id == user.id
    assert principal.user_device.id == device.id


async def test_get_current_principal_viewer_deactivated_device_403(db_session):
    from datetime import UTC, datetime
    user = User(phone="+2348031234568", phone_verified=True)
    db_session.add(user); await db_session.flush()
    device = UserDevice(
        user_id=user.id, device_id="dev-2", platform="android",
        deactivated_at=datetime.now(UTC),
    )
    db_session.add(device); await db_session.flush()
    token = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    with pytest.raises(HTTPException) as exc:
        await get_current_principal(req, db=db_session)
    assert exc.value.status_code == 403
    assert exc.value.detail == {"reason": "device_deactivated"}


async def test_get_current_principal_producer_happy(db_session):
    producer = Producer(
        email="p@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(producer); await db_session.flush()
    token = mint_access_jwt(sub=str(producer.id), role="producer")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    principal = await get_current_principal(req, db=db_session)
    assert principal.role == "producer"
    assert principal.producer.id == producer.id


async def test_get_current_principal_admin_happy(db_session):
    admin = Admin(
        email="a@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(admin); await db_session.flush()
    token = mint_access_jwt(sub=str(admin.id), role="admin")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    principal = await get_current_principal(req, db=db_session)
    assert principal.role == "admin"
    assert principal.admin.id == admin.id


async def test_get_current_viewer_rejects_producer(db_session):
    producer = Producer(
        email="p2@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(producer); await db_session.flush()
    token = mint_access_jwt(sub=str(producer.id), role="producer")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    p = await get_current_principal(req, db=db_session)
    with pytest.raises(HTTPException) as exc:
        await get_current_viewer(p)
    assert exc.value.status_code == 403


async def test_get_current_producer_rejects_admin(db_session):
    admin = Admin(
        email="a2@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(admin); await db_session.flush()
    token = mint_access_jwt(sub=str(admin.id), role="admin")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    p = await get_current_principal(req, db=db_session)
    with pytest.raises(HTTPException) as exc:
        await get_current_producer(p)
    assert exc.value.status_code == 403


async def test_get_current_admin_rejects_viewer(db_session):
    user = User(phone="+2348031234569", phone_verified=True)
    db_session.add(user); await db_session.flush()
    device = UserDevice(user_id=user.id, device_id="dev-3", platform="android")
    db_session.add(device); await db_session.flush()
    token = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    p = await get_current_principal(req, db=db_session)
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(p)
    assert exc.value.status_code == 403
