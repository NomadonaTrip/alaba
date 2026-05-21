"""OTP provider protocol + MockOTPProvider."""

import logging
from typing import Protocol

from alaba.config import get_settings


class OTPProvider(Protocol):
    async def send(self, phone: str, code: str) -> None: ...


class MockOTPProvider:
    """Logs the OTP code at INFO level. Production refuses to boot with this."""

    def __init__(self):
        s = get_settings()
        if s.environment == "production":
            raise ValueError(
                "MockOTPProvider is forbidden in production. "
                "Set OTP_PROVIDER=termii (or another real provider)."
            )
        self._logger = logging.getLogger("alaba.otp.mock")

    async def send(self, phone: str, code: str) -> None:
        self._logger.info("[OTP] %s → %s", phone, code)


def get_otp_provider() -> OTPProvider:
    """Factory keyed on settings.otp_provider."""
    s = get_settings()
    if s.otp_provider == "mock":
        return MockOTPProvider()
    raise NotImplementedError(f"OTP provider not implemented: {s.otp_provider}")
