"""/me endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from alaba.deps import get_current_principal
from alaba.schemas.user import MeAdminOut, MeProducerOut, MeViewerOut
from alaba.services.principal import Principal

router = APIRouter(tags=["me"])


@router.get("/me", response_model=None)
async def me(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> MeViewerOut | MeProducerOut | MeAdminOut:
    if principal.role == "viewer":
        return MeViewerOut(
            user_id=principal.user.id,
            phone=principal.user.phone,
            user_device_id=principal.user_device.id,
            user_device_display_name=principal.user_device.display_name,
            user_device_model=principal.user_device.model,
            user_device_last_seen_at=principal.user_device.last_seen_at,
        )
    if principal.role == "producer":
        return MeProducerOut(
            producer_id=principal.producer.id,
            email=principal.producer.email,
            company_name=principal.producer.company_name,
            verified=principal.producer.verified,
            agreement_accepted_at=principal.producer.agreement_accepted_at,
        )
    return MeAdminOut(admin_id=principal.admin.id, email=principal.admin.email)
