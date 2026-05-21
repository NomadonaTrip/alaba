"""Viewer-facing device endpoints."""

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.db import get_db
from alaba.deps import get_current_viewer
from alaba.schemas.device import DeviceListOut, DeviceOut
from alaba.services.device_service import (
    DeviceCooldownActive,
    DeviceNotFound,
    DeviceService,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=DeviceListOut)
async def list_my_devices(
    principal=Depends(get_current_viewer),
    db: AsyncSession = Depends(get_db),
):
    s = get_settings()
    svc = DeviceService(db)
    devices = await svc.list_user_devices(principal.user.id)
    active = [d for d in devices if d.deactivated_at is None]

    # Compute cooldown unlock if applicable
    cooldown_unlock = None
    cutoff_delta = timedelta(days=s.device_deactivation_cooldown_days)
    deactivated = [d for d in devices if d.deactivated_at is not None]
    if deactivated:
        latest = max(deactivated, key=lambda d: d.deactivated_at)
        from datetime import datetime, UTC
        cooldown_end = latest.deactivated_at + cutoff_delta
        if cooldown_end > datetime.now(UTC):
            cooldown_unlock = cooldown_end

    return DeviceListOut(
        devices=[
            DeviceOut(
                id=d.id,
                display_name=d.display_name,
                model=d.model,
                platform=d.platform,
                activated_at=d.activated_at,
                deactivated_at=d.deactivated_at,
                last_seen_at=d.last_seen_at,
                is_current=(d.id == principal.user_device.id),
            )
            for d in devices
        ],
        cap=s.max_active_devices_per_user,
        active_count=len(active),
        deactivation_cooldown_unlock_at=cooldown_unlock,
    )


@router.post("/{device_id}/deactivate", status_code=204)
async def deactivate_my_device(
    device_id: UUID,
    principal=Depends(get_current_viewer),
    db: AsyncSession = Depends(get_db),
):
    svc = DeviceService(db)
    try:
        await svc.deactivate(principal.user, device_id)
    except DeviceNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "device_not_found"},
        )
    except DeviceCooldownActive as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "cooldown_active", "unlock_at": e.unlock_at.isoformat()},
        )
    await db.commit()
