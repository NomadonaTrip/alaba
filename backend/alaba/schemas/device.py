"""Schemas for /devices/* and /admin/users/*/devices/*."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceOut(BaseModel):
    id: UUID
    display_name: str | None
    model: str | None
    platform: str
    activated_at: datetime
    deactivated_at: datetime | None
    last_seen_at: datetime | None
    is_current: bool = False


class DeviceListOut(BaseModel):
    devices: list[DeviceOut]
    cap: int
    active_count: int
    deactivation_cooldown_unlock_at: datetime | None


class AdminForceDeactivateIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class UserLookupOut(BaseModel):
    user_id: UUID
    phone: str
