"""All SQLAlchemy models. Importing this module registers them with Base.metadata."""

from alaba.models.admin_action import AdminAction
from alaba.models.base import Base
from alaba.models.film import Film
from alaba.models.license import License
from alaba.models.otp_code import OtpCode
from alaba.models.payout import Payout
from alaba.models.producer import Producer
from alaba.models.rating import Rating
from alaba.models.user import User
from alaba.models.user_device import UserDevice

__all__ = [
    "AdminAction",
    "Base",
    "Film",
    "License",
    "OtpCode",
    "Payout",
    "Producer",
    "Rating",
    "User",
    "UserDevice",
]
