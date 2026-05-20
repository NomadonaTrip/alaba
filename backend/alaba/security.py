"""Security primitives: JWT, bcrypt, OTP code generation."""

import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from alaba.config import get_settings

_BCRYPT_ROUNDS = 12

# ---------------------------------------------------------------------------
# Passwords and short secrets (bcrypt)
# ---------------------------------------------------------------------------

def hash_password(plaintext: str) -> str:
    """Hash a producer/admin password. Use only on inputs <= 72 bytes."""
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))


def hash_secret(plaintext: str) -> str:
    """Hash a short secret like an OTP code. Same backend as passwords."""
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_secret(plaintext: str, hashed: str) -> bool:
    return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# OTP code generation
# ---------------------------------------------------------------------------

def generate_otp_code() -> str:
    """6-digit numeric OTP code, cryptographically random."""
    s = get_settings()
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(s.otp_length))


# ---------------------------------------------------------------------------
# JWT (access tokens and verify tickets)
# ---------------------------------------------------------------------------

ACCESS_KIND = "access"
VERIFY_TICKET_KIND = "device_cap_remediation"
_VERIFY_TICKET_TTL_SECONDS = 120


def mint_access_jwt(
    *,
    sub: str,
    role: str,
    extras: dict | None = None,
) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "role": role,
        "kind": ACCESS_KIND,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=s.jwt_expiry_hours)).timestamp()),
    }
    if extras:
        payload.update(extras)
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_access_jwt(token: str) -> dict:
    s = get_settings()
    payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    if payload.get("kind") != ACCESS_KIND:
        raise JWTError(f"Wrong kind: {payload.get('kind')}")
    return payload


def mint_verify_ticket(*, phone: str, user_id: str) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    payload = {
        "phone": phone,
        "user_id": user_id,
        "kind": VERIFY_TICKET_KIND,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=_VERIFY_TICKET_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_verify_ticket(token: str) -> dict:
    s = get_settings()
    payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    if payload.get("kind") != VERIFY_TICKET_KIND:
        raise JWTError(f"Wrong kind: {payload.get('kind')}")
    return payload
