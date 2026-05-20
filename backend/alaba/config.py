"""Application settings, loaded from environment variables."""

from typing import Any, Literal, get_origin

from pydantic import model_validator
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


class _CommaListEnvSource(EnvSettingsSource):
    """Custom env source that parses comma-separated strings into list[str] fields."""

    def prepare_field_value(self, field_name: str, field: Any, value: Any, value_is_complex: bool) -> Any:
        if value is not None and isinstance(value, str):
            if get_origin(field.annotation) is list:
                return [s.strip() for s in value.split(",") if s.strip()]
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    """All application configuration, sourced from env."""

    model_config = SettingsConfigDict(
        env_file=None,  # env is injected by Docker/compose; no .env loading at runtime
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["dev", "test", "staging", "production"] = "dev"

    # Database
    database_url: str
    redis_url: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Multi-device
    max_active_devices_per_user: int = 2
    device_deactivation_cooldown_days: int = 90

    # OTP
    otp_provider: Literal["mock", "termii"] = "mock"
    otp_length: int = 6
    otp_expiry_minutes: int = 10
    otp_max_attempts: int = 5

    # Payments
    payment_provider: Literal["paystack"] = "paystack"
    paystack_base_url: str
    paystack_secret_key: str
    paystack_public_key: str
    paystack_webhook_secret: str = ""

    # Payouts
    payout_provider: Literal["noop", "paystack_transfers"] = "noop"

    # CORS
    cors_origins: list[str] = []

    # Storage
    s3_public_endpoint: str
    s3_internal_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str = "us-east-1"
    minio_bucket_source: str = "alaba-source"
    minio_bucket_transcoded: str = "alaba-transcoded"
    minio_bucket_previews: str = "alaba-previews"

    @classmethod
    def settings_customise_sources(cls, settings_cls, env_settings, **kwargs):  # type: ignore[override]
        return (_CommaListEnvSource(settings_cls),)

    @model_validator(mode="after")
    def _refuse_unsafe_combos(self):
        if self.environment == "production" and self.otp_provider == "mock":
            raise ValueError(
                "MockOTPProvider is forbidden in production. "
                "Set OTP_PROVIDER=termii (or another real provider)."
            )
        return self


def get_settings() -> Settings:
    """Lazily-constructed singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


_settings: Settings | None = None
