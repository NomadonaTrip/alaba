"""Light data factories for tests. No Faker dependency; deterministic values."""

import uuid
from datetime import UTC, datetime

from alaba.models import Admin, Producer, User, UserDevice
from alaba.security import hash_password


def make_user(phone: str = "+2348031234567", phone_verified: bool = True) -> User:
    return User(phone=phone, phone_verified=phone_verified)


def make_user_device(
    user_id: uuid.UUID,
    device_id: str = "device-abc",
    display_name: str = "TECNO Camon 18",
    deactivated: bool = False,
) -> UserDevice:
    return UserDevice(
        user_id=user_id,
        device_id=device_id,
        display_name=display_name,
        model="Camon 18",
        platform="android",
        last_seen_at=datetime.now(UTC),
        deactivated_at=datetime.now(UTC) if deactivated else None,
    )


def make_producer(
    email: str = "producer@test.com",
    password: str = "ten_chars!",
    company_name: str = "Orban Forest Films",
    verified: bool = False,
) -> Producer:
    return Producer(
        email=email,
        password_hash=hash_password(password),
        company_name=company_name,
        verified=verified,
    )


def make_admin(
    email: str = "admin@test.com",
    password: str = "ten_chars!",
) -> Admin:
    return Admin(email=email, password_hash=hash_password(password))
