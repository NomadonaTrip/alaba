"""Schemas for /auth/* endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OtpRequestIn(BaseModel):
    phone: str = Field(min_length=4, max_length=20)


class OtpRequestOut(BaseModel):
    sent: bool


class OtpVerifyIn(BaseModel):
    phone: str = Field(min_length=4, max_length=20)
    code: str | None = None
    verify_ticket: str | None = None
    device_id: str = Field(min_length=1, max_length=255)
    display_name: str | None = None
    model: str | None = None
    platform: str = "android"
    deactivate_device_id: UUID | None = None


class OtpVerifyOut(BaseModel):
    jwt: str
    user_device_id: UUID
    expires_at: datetime


class ActiveDeviceSummary(BaseModel):
    id: UUID
    display_name: str | None
    model: str | None
    platform: str
    activated_at: datetime
    last_seen_at: datetime | None


class OtpVerify409Body(BaseModel):
    error: str = "device_cap_reached"
    active_devices: list[ActiveDeviceSummary]
    verify_ticket: str
