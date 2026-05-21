"""Schemas for /me."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class MeViewerOut(BaseModel):
    role: Literal["viewer"] = "viewer"
    user_id: UUID
    phone: str
    user_device_id: UUID
    user_device_display_name: str | None
    user_device_model: str | None
    user_device_last_seen_at: datetime | None


class MeProducerOut(BaseModel):
    role: Literal["producer"] = "producer"
    producer_id: UUID
    email: str
    company_name: str | None
    verified: bool
    agreement_accepted_at: datetime | None


class MeAdminOut(BaseModel):
    role: Literal["admin"] = "admin"
    admin_id: UUID
    email: str
