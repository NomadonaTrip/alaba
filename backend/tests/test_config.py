"""Tests for the Settings class (pydantic-settings)."""

import pytest

from alaba.config import Settings


def test_settings_reads_from_env():
    s = Settings()
    assert s.environment == "dev"
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.jwt_secret == "test_jwt_secret"
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expiry_hours == 24


def test_settings_multi_device_config():
    s = Settings()
    assert s.max_active_devices_per_user == 2
    assert s.device_deactivation_cooldown_days == 90


def test_settings_otp_config():
    s = Settings()
    assert s.otp_provider == "mock"
    assert s.otp_length == 6
    assert s.otp_expiry_minutes == 10
    assert s.otp_max_attempts == 5


def test_settings_payment_config():
    s = Settings()
    assert s.payment_provider == "paystack"
    assert s.paystack_base_url == "https://api.paystack.co"
    assert s.paystack_secret_key == "sk_test_dummy"
    assert s.payout_provider == "noop"


def test_settings_cors_origins_parsed_as_list():
    s = Settings()
    assert s.cors_origins == ["http://localhost:3000"]


def test_settings_storage_config():
    s = Settings()
    assert s.s3_public_endpoint == "http://localhost:9000"
    assert s.s3_internal_endpoint == "http://localhost:9000"
    assert s.s3_access_key == "test_access_key"
    assert s.minio_bucket_source == "alaba-source"


def test_mock_otp_refuses_production(monkeypatch):
    """Production must refuse to boot with mock OTP."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    with pytest.raises(ValueError, match="MockOTPProvider"):
        Settings()
