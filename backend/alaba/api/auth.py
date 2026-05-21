"""Authentication endpoints. Mode B of /auth/otp/verify added in Task 5."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.db import get_db
from alaba.integrations.otp import get_otp_provider
from alaba.schemas.auth import (
    ActiveDeviceSummary,
    OtpRequestIn,
    OtpRequestOut,
    OtpVerify409Body,
    OtpVerifyIn,
    OtpVerifyOut,
)
from alaba.security import decode_verify_ticket, mint_access_jwt, mint_verify_ticket
from alaba.services.device_service import (
    DeviceCapReached,
    DeviceCooldownActive,
    DeviceNotFound,
    DeviceService,
)
from alaba.services.otp_service import (
    OtpAttemptsExhausted,
    OtpExpired,
    OtpInvalid,
    OtpRateLimited,
    OtpService,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request", response_model=OtpRequestOut)
async def request_otp(
    body: OtpRequestIn,
    db: AsyncSession = Depends(get_db),
):
    svc = OtpService(db)
    try:
        code = await svc.issue(body.phone)
    except OtpRateLimited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "too_many_otp_requests"},
        )
    provider = get_otp_provider()
    await provider.send(body.phone, code)
    await db.commit()
    return OtpRequestOut(sent=True)


@router.post("/otp/verify", response_model=OtpVerifyOut)
async def verify_otp(
    body: OtpVerifyIn,
    db: AsyncSession = Depends(get_db),
):
    if body.code is None and body.verify_ticket is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "code_or_verify_ticket_required"},
        )
    if body.code is not None and body.verify_ticket is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "specify_one_of_code_or_verify_ticket"},
        )

    dev_svc = DeviceService(db)

    if body.verify_ticket is not None:
        # Mode B
        if body.deactivate_device_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "deactivate_device_id_required_with_ticket"},
            )
        try:
            payload = decode_verify_ticket(body.verify_ticket)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        if payload.get("phone") != body.phone:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        from uuid import UUID
        try:
            user_id = UUID(payload["user_id"])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        from alaba.models import User
        user = await db.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        try:
            device = await dev_svc.deactivate_with_cap_remediation(
                user=user,
                new_device_id=body.device_id,
                new_display_name=body.display_name,
                new_model=body.model,
                new_platform=body.platform,
                deactivate_device_id=body.deactivate_device_id,
            )
        except DeviceCooldownActive as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "cooldown_active", "unlock_at": e.unlock_at.isoformat()},
            )
        except DeviceNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "device_not_found_or_already_inactive"},
            )
        await db.commit()
        jwt_token = mint_access_jwt(
            sub=str(user.id),
            role="viewer",
            extras={"user_device_id": str(device.id)},
        )
        s = get_settings()
        expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
        return OtpVerifyOut(
            jwt=jwt_token,
            user_device_id=device.id,
            expires_at=expires_at,
        )

    # Mode A
    otp_svc = OtpService(db)
    try:
        await otp_svc.verify(body.phone, body.code)
    except OtpInvalid as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_code", "attempts_remaining": e.attempts_remaining},
        )
    except OtpExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "code_expired"},
        )
    except OtpAttemptsExhausted:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "attempts_exhausted"},
        )

    user = await dev_svc.find_or_create_user(body.phone)
    try:
        device = await dev_svc.register_or_resolve_device(
            user=user,
            device_id=body.device_id,
            display_name=body.display_name,
            model=body.model,
            platform=body.platform,
        )
    except DeviceCapReached as e:
        ticket = mint_verify_ticket(phone=body.phone, user_id=str(e.user_id))
        active_summaries = [
            ActiveDeviceSummary(
                id=d.id,
                display_name=d.display_name,
                model=d.model,
                platform=d.platform,
                activated_at=d.activated_at,
                last_seen_at=d.last_seen_at,
            )
            for d in e.active_devices
        ]
        await db.commit()  # commit OTP consume + user creation
        body_dict = OtpVerify409Body(
            active_devices=active_summaries, verify_ticket=ticket
        ).model_dump(mode="json")
        raise HTTPException(status_code=409, detail=body_dict)
    except DeviceCooldownActive as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "cooldown_active", "unlock_at": e.unlock_at.isoformat()},
        )

    await db.commit()
    jwt_token = mint_access_jwt(
        sub=str(user.id),
        role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    s = get_settings()
    expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
    return OtpVerifyOut(
        jwt=jwt_token,
        user_device_id=device.id,
        expires_at=expires_at,
    )
