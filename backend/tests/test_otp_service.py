"""Unit tests for OtpService."""

from datetime import UTC, datetime, timedelta

import pytest

from alaba.models import OtpCode
from alaba.security import hash_secret
from alaba.services.otp_service import (
    OtpAttemptsExhausted,
    OtpExpired,
    OtpInvalid,
    OtpRateLimited,
    OtpService,
)


async def test_issue_creates_otp_row(db_session):
    svc = OtpService(db_session)
    code = await svc.issue("+2348031234567")
    assert len(code) == 6
    rows = (await db_session.execute(
        OtpCode.__table__.select().where(OtpCode.__table__.c.phone == "+2348031234567")
    )).all()
    assert len(rows) == 1


async def test_issue_rate_limits_after_5_per_15min(db_session):
    svc = OtpService(db_session)
    for _ in range(5):
        await svc.issue("+2348031234567")
    with pytest.raises(OtpRateLimited):
        await svc.issue("+2348031234567")


async def test_issue_does_not_count_old_rows(db_session):
    """Rows older than 15 minutes don't count toward the limit."""
    old_row = OtpCode(
        phone="+2348031234567",
        code_hash=hash_secret("000000"),
        expires_at=datetime.now(UTC) - timedelta(minutes=20),
        attempts=0,
    )
    db_session.add(old_row); await db_session.flush()
    svc = OtpService(db_session)
    code = await svc.issue("+2348031234567")
    assert len(code) == 6


async def test_verify_happy_consumes_row(db_session):
    svc = OtpService(db_session)
    raw_code = await svc.issue("+2348031234567")
    row = await svc.verify("+2348031234567", raw_code)
    assert row.consumed_at is not None


async def test_verify_wrong_code_increments_attempts(db_session):
    svc = OtpService(db_session)
    await svc.issue("+2348031234567")
    with pytest.raises(OtpInvalid) as exc:
        await svc.verify("+2348031234567", "wrong1")
    assert exc.value.attempts_remaining == 4


async def test_verify_attempts_exhausted_after_5(db_session):
    svc = OtpService(db_session)
    await svc.issue("+2348031234567")
    for _ in range(5):
        with pytest.raises(OtpInvalid):
            await svc.verify("+2348031234567", "wrong1")
    with pytest.raises(OtpAttemptsExhausted):
        await svc.verify("+2348031234567", "wrong1")


async def test_verify_expired_raises(db_session):
    svc = OtpService(db_session)
    row = OtpCode(
        phone="+2348031234567",
        code_hash=hash_secret("123456"),
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
        attempts=0,
    )
    db_session.add(row); await db_session.flush()
    with pytest.raises(OtpExpired):
        await svc.verify("+2348031234567", "123456")


async def test_verify_no_row_raises_invalid(db_session):
    svc = OtpService(db_session)
    with pytest.raises(OtpInvalid):
        await svc.verify("+2348031234567", "123456")


async def test_verify_already_consumed_raises_invalid(db_session):
    svc = OtpService(db_session)
    raw = await svc.issue("+2348031234567")
    await svc.verify("+2348031234567", raw)
    with pytest.raises(OtpInvalid):
        await svc.verify("+2348031234567", raw)
