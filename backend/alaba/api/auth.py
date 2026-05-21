"""Authentication endpoints. Mode B of /auth/otp/verify added in Task 5."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.db import get_db
from alaba.integrations.otp import get_otp_provider
from alaba.schemas.auth import (
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    OtpVerifyOut,
)
from alaba.security import mint_access_jwt
from alaba.services.device_service import DeviceService
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
    """Mode A: code provided. Mode B (verify_ticket + deactivate_device_id) arrives in Task 5."""
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
    if body.verify_ticket is not None:
        # Implemented in Task 5
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"error": "verify_ticket_path_not_yet_implemented"},
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

    dev_svc = DeviceService(db)
    user = await dev_svc.find_or_create_user(body.phone)
    device = await dev_svc.resolve_or_create_device(
        user=user,
        device_id=body.device_id,
        display_name=body.display_name,
        model=body.model,
        platform=body.platform,
    )
    await db.commit()

    s = get_settings()
    jwt_token = mint_access_jwt(
        sub=str(user.id),
        role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
    return OtpVerifyOut(
        jwt=jwt_token,
        user_device_id=device.id,
        expires_at=expires_at,
    )
