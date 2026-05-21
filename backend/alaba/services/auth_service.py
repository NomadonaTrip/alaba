"""Email+password auth for producers and admins."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.models import Admin, Producer
from alaba.security import hash_password, verify_password

MIN_PASSWORD_LENGTH = 10


class EmailInUse(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class PasswordTooShort(Exception):
    pass


@dataclass
class AuthService:
    db: AsyncSession

    async def register_producer(
        self, *, email: str, password: str, company_name: str | None,
    ) -> Producer:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise PasswordTooShort()
        existing = await self.db.execute(
            select(Producer).where(Producer.email == email)
        )
        if existing.scalar_one_or_none() is not None:
            raise EmailInUse()
        producer = Producer(
            email=email,
            password_hash=hash_password(password),
            company_name=company_name,
        )
        self.db.add(producer)
        await self.db.flush()
        return producer

    async def login_producer(self, email: str, password: str) -> Producer:
        result = await self.db.execute(
            select(Producer).where(Producer.email == email)
        )
        producer = result.scalar_one_or_none()
        if producer is None or not verify_password(password, producer.password_hash):
            raise InvalidCredentials()
        return producer

    async def login_admin(self, email: str, password: str) -> Admin:
        result = await self.db.execute(
            select(Admin).where(Admin.email == email)
        )
        admin = result.scalar_one_or_none()
        if admin is None or not verify_password(password, admin.password_hash):
            raise InvalidCredentials()
        return admin
