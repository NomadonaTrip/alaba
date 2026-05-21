"""Device resolution + cap enforcement + cooldown + Mode B path."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.models import AdminAction, User, UserDevice


class DeviceCapReached(Exception):
    def __init__(self, active_devices: list[UserDevice], user_id: UUID):
        self.active_devices = active_devices
        self.user_id = user_id


class DeviceCooldownActive(Exception):
    def __init__(self, unlock_at: datetime):
        self.unlock_at = unlock_at


class DeviceNotFound(Exception):
    pass


@dataclass
class DeviceService:
    db: AsyncSession

    async def find_or_create_user(self, phone: str) -> User:
        result = await self.db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(phone=phone, phone_verified=True)
            self.db.add(user)
            await self.db.flush()
        elif not user.phone_verified:
            user.phone_verified = True
            await self.db.flush()
        return user

    async def _list_active_for_user(self, user_id: UUID) -> list[UserDevice]:
        result = await self.db.execute(
            select(UserDevice)
            .where(UserDevice.user_id == user_id, UserDevice.deactivated_at.is_(None))
            .order_by(UserDevice.activated_at.asc())
        )
        return list(result.scalars().all())

    async def _check_cooldown(self, user_id: UUID) -> None:
        s = get_settings()
        cutoff = datetime.now(UTC) - timedelta(days=s.device_deactivation_cooldown_days)
        result = await self.db.execute(
            select(UserDevice)
            .where(
                UserDevice.user_id == user_id,
                UserDevice.deactivated_at.is_not(None),
                UserDevice.deactivated_at > cutoff,
            )
            .order_by(UserDevice.deactivated_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            unlock_at = row.deactivated_at + timedelta(days=s.device_deactivation_cooldown_days)
            raise DeviceCooldownActive(unlock_at=unlock_at)

    async def register_or_resolve_device(
        self,
        *,
        user: User,
        device_id: str,
        display_name: str | None,
        model: str | None,
        platform: str = "android",
    ) -> UserDevice:
        s = get_settings()
        now = datetime.now(UTC)

        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user.id,
                UserDevice.device_id == device_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None and existing.deactivated_at is None:
            existing.last_seen_at = now
            await self.db.flush()
            return existing
        if existing is not None:
            # Deactivated row — check cooldown for reactivation
            cooldown_cutoff = now - timedelta(days=s.device_deactivation_cooldown_days)
            if existing.deactivated_at > cooldown_cutoff:
                raise DeviceCooldownActive(
                    unlock_at=existing.deactivated_at + timedelta(days=s.device_deactivation_cooldown_days),
                )
            existing.deactivated_at = None
            existing.last_seen_at = now
            await self.db.flush()
            return existing

        # New device
        active = await self._list_active_for_user(user.id)
        if len(active) >= s.max_active_devices_per_user:
            raise DeviceCapReached(active_devices=active, user_id=user.id)

        device = UserDevice(
            user_id=user.id,
            device_id=device_id,
            display_name=display_name,
            model=model,
            platform=platform,
            last_seen_at=now,
        )
        self.db.add(device)
        await self.db.flush()
        return device

    async def deactivate_with_cap_remediation(
        self,
        *,
        user: User,
        new_device_id: str,
        new_display_name: str | None,
        new_model: str | None,
        new_platform: str,
        deactivate_device_id: UUID,
    ) -> UserDevice:
        """Mode B: simultaneously deactivate one device and register another."""
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.id == deactivate_device_id,
                UserDevice.user_id == user.id,
            )
        )
        to_deactivate = result.scalar_one_or_none()
        if to_deactivate is None or to_deactivate.deactivated_at is not None:
            raise DeviceNotFound()

        await self._check_cooldown(user.id)

        now = datetime.now(UTC)
        to_deactivate.deactivated_at = now

        device = UserDevice(
            user_id=user.id,
            device_id=new_device_id,
            display_name=new_display_name,
            model=new_model,
            platform=new_platform,
            last_seen_at=now,
        )
        self.db.add(device)
        await self.db.flush()
        return device

    async def list_user_devices(self, user_id: UUID) -> list[UserDevice]:
        """Active first, then deactivated, both sorted by recency."""
        result = await self.db.execute(
            select(UserDevice)
            .where(UserDevice.user_id == user_id)
            .order_by(
                UserDevice.deactivated_at.is_not(None).asc(),
                UserDevice.activated_at.desc(),
            )
        )
        return list(result.scalars().all())

    async def deactivate(self, user: User, device_id: UUID) -> None:
        """Self-deactivate. Enforces cooldown."""
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.id == device_id,
                UserDevice.user_id == user.id,
            )
        )
        device = result.scalar_one_or_none()
        if device is None:
            raise DeviceNotFound()
        if device.deactivated_at is not None:
            return  # idempotent
        await self._check_cooldown(user.id)
        device.deactivated_at = datetime.now(UTC)
        await self.db.flush()

    async def admin_force_deactivate(
        self,
        *,
        user_id: UUID,
        device_id: UUID,
        admin_email: str,
        reason: str,
    ) -> None:
        """Admin force-deactivate: bypasses cooldown. Logs to admin_actions."""
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.id == device_id,
                UserDevice.user_id == user_id,
            )
        )
        device = result.scalar_one_or_none()
        if device is None:
            raise DeviceNotFound()
        if device.deactivated_at is None:
            device.deactivated_at = datetime.now(UTC)
        action = AdminAction(
            admin_email=admin_email,
            action="force_deactivate_device",
            target_type="user_device",
            target_id=device.id,
            reason=reason,
        )
        self.db.add(action)
        await self.db.flush()
