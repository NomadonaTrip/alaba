"""Unit tests for DeviceService cap + cooldown + Mode B logic."""

from datetime import UTC, datetime, timedelta

import pytest

from alaba.config import get_settings
from alaba.models import User, UserDevice
from alaba.services.device_service import (
    DeviceCapReached,
    DeviceCooldownActive,
    DeviceNotFound,
    DeviceService,
)
from tests.factories import make_user, make_user_device


async def test_register_new_device_under_cap(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    svc = DeviceService(db_session)
    device = await svc.register_or_resolve_device(
        user=user, device_id="dev-1", display_name="phone", model="X",
    )
    assert device.user_id == user.id
    assert device.device_id == "dev-1"
    assert device.deactivated_at is None


async def test_register_at_cap_raises_cap_reached(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A")
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceCapReached) as exc:
        await svc.register_or_resolve_device(
            user=user, device_id="dev-NEW", display_name="phone3", model="Z",
        )
    assert len(exc.value.active_devices) == 2


async def test_existing_active_device_updates_last_seen(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A")
    d1.last_seen_at = datetime.now(UTC) - timedelta(days=7)
    db_session.add(d1); await db_session.flush()
    svc = DeviceService(db_session)
    device = await svc.register_or_resolve_device(
        user=user, device_id="dev-A", display_name="phone", model="X",
    )
    assert device.id == d1.id
    assert (datetime.now(UTC) - device.last_seen_at).total_seconds() < 5


async def test_existing_deactivated_within_cooldown_raises(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    deactivated = make_user_device(user.id, "dev-A", deactivated=True)
    deactivated.deactivated_at = datetime.now(UTC) - timedelta(days=30)
    db_session.add(deactivated); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceCooldownActive):
        await svc.register_or_resolve_device(
            user=user, device_id="dev-A", display_name="phone", model="X",
        )


async def test_existing_deactivated_past_cooldown_reactivates(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    deactivated = make_user_device(user.id, "dev-A", deactivated=True)
    deactivated.deactivated_at = datetime.now(UTC) - timedelta(days=100)
    db_session.add(deactivated); await db_session.flush()
    svc = DeviceService(db_session)
    device = await svc.register_or_resolve_device(
        user=user, device_id="dev-A", display_name="phone", model="X",
    )
    assert device.deactivated_at is None


async def test_deactivate_device_happy(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d = make_user_device(user.id, "dev-A")
    db_session.add(d); await db_session.flush()
    svc = DeviceService(db_session)
    await svc.deactivate(user, d.id)
    await db_session.refresh(d)
    assert d.deactivated_at is not None


async def test_deactivate_blocked_by_cooldown(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A", deactivated=True)
    d1.deactivated_at = datetime.now(UTC) - timedelta(days=30)
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceCooldownActive):
        await svc.deactivate(user, d2.id)


async def test_deactivate_device_belonging_to_other_user_raises(db_session):
    u1 = make_user("+2348031234001")
    u2 = make_user("+2348031234002")
    db_session.add_all([u1, u2]); await db_session.flush()
    d = make_user_device(u2.id, "dev-foreign")
    db_session.add(d); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceNotFound):
        await svc.deactivate(u1, d.id)


async def test_deactivate_idempotent_on_already_deactivated(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d = make_user_device(user.id, "dev-A", deactivated=True)
    d.deactivated_at = datetime.now(UTC) - timedelta(days=200)  # past cooldown
    db_session.add(d); await db_session.flush()
    svc = DeviceService(db_session)
    # Should not raise
    await svc.deactivate(user, d.id)


async def test_admin_force_deactivate_bypasses_cooldown(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A", deactivated=True)
    d1.deactivated_at = datetime.now(UTC) - timedelta(days=30)
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    svc = DeviceService(db_session)
    await svc.admin_force_deactivate(
        user_id=user.id, device_id=d2.id,
        admin_email="admin@test.com", reason="lost phone",
    )
    await db_session.refresh(d2)
    assert d2.deactivated_at is not None
    # AdminAction row exists
    from alaba.models import AdminAction
    from sqlalchemy import select
    result = await db_session.execute(select(AdminAction))
    actions = result.scalars().all()
    assert any(a.action == "force_deactivate_device" for a in actions)
