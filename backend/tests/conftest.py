"""Shared pytest fixtures."""

import os

import pytest

# ---------------------------------------------------------------------------
# Set minimum required env vars early (before pytest collects modules) so
# that module-level SQLAlchemy engine creation in db.py succeeds at import
# time.  The per-test `env_setup` fixture below will override these with
# monkeypatch for the duration of each test.
# ---------------------------------------------------------------------------
_EARLY_ENV = {
    "ENVIRONMENT": "dev",
    "DATABASE_URL": "postgresql+asyncpg://alaba:alaba_dev_password@localhost:5433/alaba_test",
    "REDIS_URL": "redis://localhost:6380/1",
    "JWT_SECRET": "test_jwt_secret",
    "JWT_ALGORITHM": "HS256",
    "JWT_EXPIRY_HOURS": "24",
    "MAX_ACTIVE_DEVICES_PER_USER": "2",
    "DEVICE_DEACTIVATION_COOLDOWN_DAYS": "90",
    "OTP_PROVIDER": "mock",
    "OTP_LENGTH": "6",
    "OTP_EXPIRY_MINUTES": "10",
    "OTP_MAX_ATTEMPTS": "5",
    "PAYMENT_PROVIDER": "paystack",
    "PAYSTACK_BASE_URL": "https://api.paystack.co",
    "PAYSTACK_SECRET_KEY": "sk_test_dummy",
    "PAYSTACK_PUBLIC_KEY": "pk_test_dummy",
    "PAYSTACK_WEBHOOK_SECRET": "dummy_webhook_secret",
    "PAYOUT_PROVIDER": "noop",
    "CORS_ORIGINS": "http://localhost:3000",
    "S3_PUBLIC_ENDPOINT": "http://localhost:9000",
    "S3_INTERNAL_ENDPOINT": "http://localhost:9000",
    "S3_ACCESS_KEY": "test_access_key",
    "S3_SECRET_KEY": "test_secret_key",
    "S3_REGION": "us-east-1",
    "MINIO_BUCKET_SOURCE": "alaba-source",
    "MINIO_BUCKET_TRANSCODED": "alaba-transcoded",
    "MINIO_BUCKET_PREVIEWS": "alaba-previews",
}

for _k, _v in _EARLY_ENV.items():
    os.environ.setdefault(_k, _v)


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Force a known-safe environment for every test."""
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://alaba:alaba_dev_password@localhost:5433/alaba_test",
    )
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6380/1")
    monkeypatch.setenv("JWT_SECRET", "test_jwt_secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRY_HOURS", "24")
    monkeypatch.setenv("MAX_ACTIVE_DEVICES_PER_USER", "2")
    monkeypatch.setenv("DEVICE_DEACTIVATION_COOLDOWN_DAYS", "90")
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_LENGTH", "6")
    monkeypatch.setenv("OTP_EXPIRY_MINUTES", "10")
    monkeypatch.setenv("OTP_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("PAYMENT_PROVIDER", "paystack")
    monkeypatch.setenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "sk_test_dummy")
    monkeypatch.setenv("PAYSTACK_PUBLIC_KEY", "pk_test_dummy")
    monkeypatch.setenv("PAYSTACK_WEBHOOK_SECRET", "dummy_webhook_secret")
    monkeypatch.setenv("PAYOUT_PROVIDER", "noop")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("S3_PUBLIC_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("S3_INTERNAL_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("S3_ACCESS_KEY", "test_access_key")
    monkeypatch.setenv("S3_SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("S3_REGION", "us-east-1")
    monkeypatch.setenv("MINIO_BUCKET_SOURCE", "alaba-source")
    monkeypatch.setenv("MINIO_BUCKET_TRANSCODED", "alaba-transcoded")
    monkeypatch.setenv("MINIO_BUCKET_PREVIEWS", "alaba-previews")


import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture(scope="session", autouse=True)
async def truncate_tables():
    """Wipe test data before each pytest session so runs are idempotent."""
    from alaba.db import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE producers, admins, users, user_devices,"
                " otp_codes, admin_actions RESTART IDENTITY CASCADE"
            )
        )
        await session.commit()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Yields a transactional session that rolls back after each test."""
    from alaba.db import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
