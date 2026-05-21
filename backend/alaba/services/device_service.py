"""Device resolution and lifecycle. Cap enforcement layered in Task 5."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.models import User, UserDevice


@dataclass
class DeviceService:
    db: AsyncSession

    async def find_or_create_user(self, phone: str) -> User:
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(phone=phone, phone_verified=True)
            self.db.add(user)
            await self.db.flush()
        else:
            if not user.phone_verified:
                user.phone_verified = True
                await self.db.flush()
        return user

    async def resolve_or_create_device(
        self,
        *,
        user: User,
        device_id: str,
        display_name: str | None,
        model: str | None,
        platform: str = "android",
    ) -> UserDevice:
        """Task-4 simplified: create a new device row OR update last_seen on existing
        active. Cap + cooldown + reactivation logic arrives in Task 5."""
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
