"""License model — per (user, film), with payment_ref UNIQUE for webhook idempotency."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class License(Base):
    __tablename__ = "licenses"
    __table_args__ = (UniqueConstraint("user_id", "film_id", name="uq_licenses_user_film"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    film_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("films.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    producer_share: Mapped[int] = mapped_column(Integer, default=350, nullable=False)
    platform_share: Mapped[int] = mapped_column(Integer, default=150, nullable=False)
    payment_provider: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_ref: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    credited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    referral_source: Mapped[str | None] = mapped_column(String(255))
    state_geo: Mapped[str | None] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
