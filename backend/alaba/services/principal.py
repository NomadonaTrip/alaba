"""Principal — tagged union returned by get_current_principal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from alaba.models import Admin, Producer, User, UserDevice


@dataclass
class Principal:
    role: Literal["viewer", "producer", "admin"]
    user: User | None = None
    user_device: UserDevice | None = None
    producer: Producer | None = None
    admin: Admin | None = None
