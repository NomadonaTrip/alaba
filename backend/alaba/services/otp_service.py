"""OTP issuance, verification, attempt tracking."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.models import OtpCode
from alaba.security import generate_otp_code, hash_secret, verify_secret


class OtpRateLimited(Exception):
    """Too many OTP-request calls for this phone."""


class OtpInvalid(Exception):
    """The supplied code is wrong, missing, or already consumed."""
    def __init__(self, attempts_remaining: int = 0):
        super().__init__("invalid_code")
        self.attempts_remaining = attempts_remaining


class OtpExpired(Exception):
    """The OTP row exists but is past its expires_at."""


class OtpAttemptsExhausted(Exception):
    """The OTP row exists but has been tried >= max_attempts times."""


@dataclass
class OtpService:
    db: AsyncSession

    async def issue(self, phone: str) -> str:
        """Generate, persist, and return the raw OTP code for `phone`."""
        s = get_settings()
        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=15)

        result = await self.db.execute(
            select(OtpCode).where(
                OtpCode.phone == phone,
                OtpCode.created_at >= cutoff,
            )
        )
        recent_rows = result.scalars().all()
        if len(recent_rows) >= 5:
            raise OtpRateLimited()

        raw = generate_otp_code()
        row = OtpCode(
            phone=phone,
            code_hash=hash_secret(raw),
            expires_at=now + timedelta(minutes=s.otp_expiry_minutes),
            attempts=0,
        )
        self.db.add(row)
        await self.db.flush()
        return raw

    async def verify(self, phone: str, code: str) -> OtpCode:
        """Look up the latest unconsumed OTP for `phone` and verify `code`.
        On success, marks consumed_at and returns the row.
        Raises OtpInvalid, OtpExpired, or OtpAttemptsExhausted on failure paths."""
        s = get_settings()
        now = datetime.now(UTC)

        result = await self.db.execute(
            select(OtpCode)
            .where(
                OtpCode.phone == phone,
                OtpCode.consumed_at.is_(None),
            )
            .order_by(OtpCode.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise OtpInvalid(attempts_remaining=0)

        if row.expires_at <= now:
            raise OtpExpired()

        if row.attempts >= s.otp_max_attempts:
            raise OtpAttemptsExhausted()

        if not verify_secret(code, row.code_hash):
            row.attempts += 1
            await self.db.flush()
            remaining = max(0, s.otp_max_attempts - row.attempts)
            raise OtpInvalid(attempts_remaining=remaining)

        row.consumed_at = now
        await self.db.flush()
        return row
