"""Admin endpoints for user device management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.db import get_db
from alaba.deps import get_current_admin
from alaba.models import User
from alaba.schemas.device import (
    AdminForceDeactivateIn,
    DeviceListOut,
    DeviceOut,
    UserLookupOut,
)
from alaba.services.device_service import DeviceNotFound, DeviceService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/lookup", response_model=UserLookupOut)
async def lookup_user(
    phone: str = Query(...),
    principal=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "user_not_found"},
        )
    return UserLookupOut(user_id=user.id, phone=user.phone)


@router.get("/users/{user_id}/devices", response_model=DeviceListOut)
async def list_user_devices_for_admin(
    user_id: UUID,
    principal=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from alaba.config import get_settings
    s = get_settings()
    svc = DeviceService(db)
    devices = await svc.list_user_devices(user_id)
    active = [d for d in devices if d.deactivated_at is None]
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
                is_current=False,
            )
            for d in devices
        ],
        cap=s.max_active_devices_per_user,
        active_count=len(active),
        deactivation_cooldown_unlock_at=None,
    )


@router.post(
    "/users/{user_id}/devices/{device_id}/deactivate",
    status_code=204,
)
async def admin_force_deactivate(
    user_id: UUID,
    device_id: UUID,
    body: AdminForceDeactivateIn,
    principal=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = DeviceService(db)
    try:
        await svc.admin_force_deactivate(
            user_id=user_id,
            device_id=device_id,
            admin_email=principal.admin.email,
            reason=body.reason,
        )
    except DeviceNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "device_not_found"},
        )
    await db.commit()
