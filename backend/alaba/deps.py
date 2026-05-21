"""FastAPI dependencies: principal resolution + role-specific helpers."""

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.db import get_db
from alaba.models import Admin, Producer, User, UserDevice
from alaba.security import decode_access_jwt
from alaba.services.principal import Principal


def _extract_token(request) -> str | None:
    """Authorization: Bearer header first, then auth_token cookie."""
    auth = (request.headers or {}).get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):].strip() or None
    return (request.cookies or {}).get("auth_token")


async def get_current_principal(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Principal:
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_token"},
        )
    try:
        payload = decode_access_jwt(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token"},
        )
    role = payload.get("role")
    try:
        sub = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token"},
        )

    if role == "viewer":
        device_id_str = payload.get("user_device_id")
        if not device_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_token"},
            )
        device = await db.get(UserDevice, UUID(device_id_str))
        if device is None or device.deactivated_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"reason": "device_deactivated"},
            )
        user = await db.get(User, sub)
        if user is None or user.suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"reason": "account_suspended"},
            )
        return Principal(role="viewer", user=user, user_device=device)

    if role == "producer":
        producer = await db.get(Producer, sub)
        if producer is None or producer.suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"reason": "account_suspended"},
            )
        return Principal(role="producer", producer=producer)

    if role == "admin":
        admin = await db.get(Admin, sub)
        if admin is None or admin.suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"reason": "account_suspended"},
            )
        return Principal(role="admin", admin=admin)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "unknown_role"},
    )


async def get_current_viewer(
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    if principal.role != "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"reason": "viewer_required"},
        )
    return principal


async def get_current_producer(
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    if principal.role != "producer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"reason": "producer_required"},
        )
    return principal


async def get_current_admin(
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    if principal.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"reason": "admin_required"},
        )
    return principal
