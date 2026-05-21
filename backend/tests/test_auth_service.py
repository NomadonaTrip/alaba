"""Unit tests for AuthService (password-based login)."""

import pytest

from alaba.services.auth_service import (
    EmailInUse,
    InvalidCredentials,
    PasswordTooShort,
    AuthService,
)
from tests.factories import make_admin, make_producer


async def test_register_producer_happy(db_session):
    svc = AuthService(db_session)
    producer = await svc.register_producer(
        email="new@test.com", password="ten_chars!", company_name="X",
    )
    assert producer.email == "new@test.com"
    assert producer.verified is False


async def test_register_producer_duplicate_email(db_session):
    existing = make_producer("svc_dup@test.com")
    db_session.add(existing); await db_session.flush()
    svc = AuthService(db_session)
    with pytest.raises(EmailInUse):
        await svc.register_producer(
            email="svc_dup@test.com", password="ten_chars!", company_name=None,
        )


async def test_register_producer_short_password(db_session):
    svc = AuthService(db_session)
    with pytest.raises(PasswordTooShort):
        await svc.register_producer(
            email="short@test.com", password="short", company_name=None,
        )


async def test_login_producer_happy(db_session):
    producer = make_producer("login@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    svc = AuthService(db_session)
    result = await svc.login_producer("login@test.com", "ten_chars!")
    assert result.id == producer.id


async def test_login_producer_wrong_password(db_session):
    producer = make_producer("wp@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.login_producer("wp@test.com", "wrong_pass!")


async def test_login_producer_unknown_email(db_session):
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.login_producer("nobody@test.com", "ten_chars!")


async def test_login_admin_happy(db_session):
    admin = make_admin("alogin@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    svc = AuthService(db_session)
    result = await svc.login_admin("alogin@test.com", "ten_chars!")
    assert result.id == admin.id


async def test_login_admin_wrong_password(db_session):
    admin = make_admin("awp@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.login_admin("awp@test.com", "wrong_pass!")
