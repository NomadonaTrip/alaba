# Wave 1: Auth + Multi-Device — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship phone-OTP auth for viewers, email+password auth for producers and admins, and the N=2 multi-device capacity with 90-day deactivation cooldown — end-to-end across backend, web portals, and Android.

**Architecture:** Backend adds a new `admins` table, security primitives (JWT + bcrypt + OTP), services (OTP, auth, device), 11 new endpoints, and a `get_current_principal` dependency. Web adds middleware-gated `(producer)` and `(admin)` route groups with login/register/dashboard/admin pages. Android adds auth interceptors, an `AuthEventBus`, repository layer, and 6 screens (PhoneEntry, OtpEntry, DeviceCapReached, DeviceDeactivated, Settings, Devices). The novel piece is a verify-ticket pattern: when a device-cap-reached 409 comes back, the client retries with a short-lived ticket (not the original OTP code) and a chosen `deactivate_device_id`.

**Tech Stack:** Backend Python 3.12 / FastAPI / SQLAlchemy 2.0 async / Alembic / `python-jose` (JWT) / `passlib[bcrypt]` (passwords) / `pytest` + `pytest-asyncio` / `httpx.AsyncClient`. Web Next.js 15.x / TypeScript / Tailwind v4 / shadcn/ui / `jose` (JWT verify) / `react-hook-form` + `zod` / Server Actions. Android Kotlin / Jetpack Compose / Hilt / Retrofit + OkHttp + Moshi / EncryptedSharedPreferences / `kotlinx.coroutines.flow.SharedFlow`.

**Reference:** `docs/superpowers/specs/2026-05-20-wave-1-auth-multidevice-design.md` (the spec). `consolidated-brief.md` (the product brief). Builds on Wave 0 (`git tag: wave-0-complete`).

---

## Prerequisites

Before starting:

- Stack must be running: `make up` (postgres, redis, minio, tusd, mailhog, backend-api, backend-worker, web). Verify with `docker ps` showing 8 alaba- services up.
- Working tree clean: `git status` shows only `consolidated-brief.md` untracked.
- On `master` branch at or past commit `e83c827` (the Wave 1 spec commit). Run `git log --oneline | head -3` to confirm.
- Tests baseline green: `make test` shows 17 passing.
- The `alaba_test` database exists in Postgres (created in Wave 0 Task 5).
- The dev Paystack/OTP keys can stay as their dummy values from `infra/.env`; this wave doesn't exercise either.

If any of the above isn't true, stop and resolve before starting Task 1.

---

## File Structure

After all 17 tasks, the new and modified files are:

```
backend/alaba/
├── config.py                              # MODIFIED: small additions if needed (none anticipated; see Task 2)
├── security.py                            # NEW (Task 2)
├── deps.py                                # NEW (Task 3)
├── models/
│   ├── admin.py                           # NEW (Task 1)
│   └── __init__.py                        # MODIFIED (Task 1)
├── schemas/                               # NEW directory (Tasks 2-6)
│   ├── __init__.py
│   ├── auth.py
│   ├── device.py
│   └── user.py
├── services/                              # NEW directory (Tasks 4-6)
│   ├── __init__.py
│   ├── otp_service.py
│   ├── auth_service.py
│   ├── device_service.py
│   └── principal.py
├── api/
│   ├── auth.py                            # NEW (Tasks 4, 6)
│   ├── devices.py                         # NEW (Task 5)
│   ├── admin_users.py                     # NEW (Task 5)
│   ├── me.py                              # NEW (Task 6)
│   └── __init__.py                        # MODIFIED: register new routers (Tasks 4, 5, 6)
└── main.py                                # MODIFIED: include the new routers (Tasks 4, 5, 6)
backend/alembic/versions/
└── 0002_add_admins.py                     # GENERATED (Task 1)
backend/tests/
├── conftest.py                            # MODIFIED: shared fixtures for db cleanup, fake_otp_provider (Task 4)
├── factories.py                           # NEW (Task 4): light data factories (User, Producer, Admin, UserDevice, OtpCode)
├── test_admin_model.py                    # NEW (Task 1)
├── test_security.py                       # NEW (Task 2)
├── test_deps.py                           # NEW (Task 3)
├── test_otp_service.py                    # NEW (Task 4)
├── test_device_service.py                 # NEW (Task 5)
├── test_auth_service.py                   # NEW (Task 6)
└── integration/                           # NEW directory
    ├── __init__.py
    ├── test_auth_otp.py                   # (Task 4)
    ├── test_devices.py                    # (Task 5)
    ├── test_admin_devices.py              # (Task 5)
    ├── test_auth_producer.py              # (Task 6)
    ├── test_auth_admin.py                 # (Task 6)
    └── test_me.py                         # (Task 6)
infra/scripts/
└── make_admin.py                          # NEW (Task 7)
Makefile                                   # MODIFIED: rewire make-admin target (Task 7)

web/src/
├── middleware.ts                          # NEW (Task 8)
├── lib/
│   ├── api-client.ts                      # NEW (Task 8)
│   ├── auth.ts                            # NEW (Task 8)
│   ├── jwt.ts                             # NEW (Task 8)
│   ├── validators.ts                      # NEW (Task 8)
│   └── datetime.ts                        # NEW (Task 10)
├── app/
│   ├── (auth)/
│   │   ├── producer/login/page.tsx        # NEW (Task 8)
│   │   ├── producer/register/page.tsx     # NEW (Task 8)
│   │   └── admin/login/page.tsx           # NEW (Task 8)
│   ├── (producer)/producer/
│   │   ├── layout.tsx                     # NEW (Task 9)
│   │   └── dashboard/page.tsx             # NEW (Task 9)
│   ├── (admin)/admin/
│   │   ├── layout.tsx                     # NEW (Task 10)
│   │   ├── dashboard/page.tsx             # NEW (Task 10)
│   │   ├── users/page.tsx                 # NEW (Task 10)
│   │   └── users/[user_id]/devices/page.tsx  # NEW (Task 10)
│   └── api/auth/logout/route.ts           # NEW (Task 9)
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx                  # NEW (Task 8)
│   │   └── RegisterForm.tsx               # NEW (Task 8)
│   └── admin/
│       ├── DeviceTable.tsx                # NEW (Task 10)
│       └── ForceDeactivateDialog.tsx      # NEW (Task 10)
└── package.json                           # MODIFIED: add `jose` dependency (Task 8)

android/app/src/main/java/com/orbanforest/alaba/
├── AlabaApplication.kt                    # (unchanged)
├── MainActivity.kt                        # MODIFIED (Task 16)
├── di/
│   ├── NetworkModule.kt                   # MODIFIED (Task 11)
│   └── AuthModule.kt                      # NEW (Task 11)
├── data/
│   ├── api/
│   │   ├── HealthApi.kt                   # (unchanged)
│   │   ├── AuthApi.kt                     # NEW (Task 12)
│   │   ├── DevicesApi.kt                  # NEW (Task 12)
│   │   ├── MeApi.kt                       # NEW (Task 12)
│   │   └── dto/                           # NEW (Task 12)
│   │       ├── OtpRequestBody.kt
│   │       ├── OtpVerifyBody.kt
│   │       ├── OtpVerifyResponse.kt
│   │       ├── OtpVerify409Body.kt
│   │       ├── DeviceDto.kt
│   │       ├── DeviceListResponse.kt
│   │       ├── MeViewerDto.kt
│   │       └── ErrorResponse.kt
│   ├── auth/
│   │   ├── TokenStore.kt                  # NEW (Task 11)
│   │   ├── DeviceIdStore.kt               # NEW (Task 11)
│   │   ├── AuthInterceptor.kt             # NEW (Task 11)
│   │   ├── AuthErrorInterceptor.kt        # NEW (Task 11)
│   │   ├── AuthEventBus.kt                # NEW (Task 11)
│   │   ├── AlabaError.kt                  # NEW (Task 12)
│   │   └── AuthRepository.kt              # NEW (Task 12)
│   └── device/
│       └── DevicesRepository.kt           # NEW (Task 12)
├── ui/
│   ├── nav/
│   │   ├── AlabaNavHost.kt                # NEW (Task 16)
│   │   ├── AuthGraph.kt                   # NEW (Task 13 builds it; Tasks 14-15 extend)
│   │   └── MainGraph.kt                   # NEW (Task 15)
│   ├── theme/
│   │   ├── Color.kt                       # NEW (Task 13)
│   │   ├── Theme.kt                       # NEW (Task 13)
│   │   └── Type.kt                        # NEW (Task 13)
│   ├── auth/
│   │   ├── PhoneEntryScreen.kt            # NEW (Task 13)
│   │   ├── PhoneEntryViewModel.kt         # NEW (Task 13)
│   │   ├── OtpEntryScreen.kt              # NEW (Task 13)
│   │   ├── OtpEntryViewModel.kt           # NEW (Task 13)
│   │   ├── DeviceCapReachedScreen.kt      # NEW (Task 14)
│   │   ├── DeviceCapReachedViewModel.kt   # NEW (Task 14)
│   │   └── DeviceDeactivatedScreen.kt     # NEW (Task 14)
│   ├── home/
│   │   ├── SignedInPlaceholderScreen.kt   # NEW (Task 15)
│   │   └── SignedInPlaceholderViewModel.kt # NEW (Task 15)
│   ├── settings/
│   │   ├── SettingsScreen.kt              # NEW (Task 15)
│   │   ├── DevicesScreen.kt               # NEW (Task 15)
│   │   └── DevicesViewModel.kt            # NEW (Task 15)
│   └── components/
│       ├── OtpCodeInput.kt                # NEW (Task 13)
│       ├── DeviceCard.kt                  # NEW (Task 14)
│       ├── ThisDevicePill.kt              # NEW (Task 15)
│       └── ConfirmBottomSheet.kt          # NEW (Task 15)
└── BuildConfig.kt                         # (Gradle-generated)
android/app/src/test/java/com/orbanforest/alaba/  # NEW directory (Tasks 11-15)
android/app/build.gradle.kts                # MODIFIED: add test deps (Task 11)

docs/test-checklist.md                     # NEW (Task 17)
```

---

## Task 1: Admin model + Alembic migration 0002

**Files:**
- Create: `backend/alaba/models/admin.py`
- Modify: `backend/alaba/models/__init__.py`
- Create: `backend/tests/test_admin_model.py`
- Generated: `backend/alembic/versions/0002_add_admins.py`

- [ ] **Step 1.1: Write the failing test**

Create `backend/tests/test_admin_model.py`:

```python
"""Admin model — import + table shape."""

from alaba.models import Admin


def test_admin_imports():
    assert Admin.__tablename__ == "admins"


def test_admin_columns():
    cols = {c.name for c in Admin.__table__.columns}
    expected = {"id", "email", "password_hash", "created_at", "suspended"}
    assert expected == cols


def test_admin_email_unique():
    col = Admin.__table__.columns["email"]
    assert col.unique is True


def test_admin_in_metadata():
    from alaba.models import Base
    assert "admins" in Base.metadata.tables
```

- [ ] **Step 1.2: Run the test — confirm RED**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/test_admin_model.py -v
```

Expected: FAIL with `ImportError: cannot import name 'Admin' from 'alaba.models'`.

- [ ] **Step 1.3: Create `backend/alaba/models/admin.py`**

```python
"""Admin model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

- [ ] **Step 1.4: Update `backend/alaba/models/__init__.py`**

Replace the contents with:

```python
"""All SQLAlchemy models. Importing this module registers them with Base.metadata."""

from alaba.models.admin import Admin
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
    "Admin",
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
```

- [ ] **Step 1.5: Run tests — confirm GREEN**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/test_admin_model.py -v
```

Expected: 4 passing.

- [ ] **Step 1.6: Generate the Alembic migration**

The backend-api container has `alembic` on path. From the project root:

```bash
docker exec alaba-backend-api alembic revision --autogenerate -m "add_admins"
```

Expected: a new file under `backend/alembic/versions/` named something like `<hash>_add_admins.py`. It will contain `op.create_table('admins', ...)` and matching downgrade.

- [ ] **Step 1.7: Rename and clean the generated migration**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend/alembic/versions
ls -1 *_add_admins.py | grep -v 0002 | head -n 1 | xargs -I {} mv {} 0002_add_admins.py
```

Open `backend/alembic/versions/0002_add_admins.py` and:

1. Change the `revision:` line to `revision: str = "0002"`.
2. Confirm `down_revision: Union[str, None] = "0001"` (Alembic should set this automatically). If it's something else, change it to `"0001"`.

- [ ] **Step 1.8: Apply the migration**

```bash
docker exec alaba-backend-api alembic upgrade head
```

Expected: `Running upgrade 0001 -> 0002, add_admins`.

- [ ] **Step 1.9: Verify the table exists**

```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "\d admins"
```

Expected output includes:
- `id` (uuid, primary key)
- `email` (varchar(255), not null, unique)
- `password_hash` (varchar(255), not null)
- `created_at` (timestamp with time zone, not null)
- `suspended` (boolean, not null)

Also verify it's in the Alembic version table:

```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "SELECT version_num FROM alembic_version;"
```

Expected: `0002`.

- [ ] **Step 1.10: Run the full backend test suite**

```bash
docker exec alaba-backend-api pytest -v
```

Expected: 21 passing (17 from Wave 0 + 4 new admin model tests). No regressions.

- [ ] **Step 1.11: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add backend/alaba/models/admin.py backend/alaba/models/__init__.py backend/alembic/versions/0002_add_admins.py backend/tests/test_admin_model.py
git commit -m "feat(backend): Admin model + Alembic migration 0002"
```

---

## Task 2: security.py — JWT + bcrypt + OTP code generation (TDD)

**Files:**
- Create: `backend/alaba/security.py`
- Create: `backend/tests/test_security.py`

This task ships three concerns in one module: JWT encode/decode (access + verify-ticket), bcrypt password and OTP-code hashing, and OTP code generation. They share dependencies and live together to keep imports tight.

- [ ] **Step 2.1: Write the failing tests**

Create `backend/tests/test_security.py`:

```python
"""Tests for security primitives: JWT, bcrypt, OTP code generation."""

import re
import time

import pytest

from alaba.security import (
    decode_access_jwt,
    decode_verify_ticket,
    generate_otp_code,
    hash_password,
    hash_secret,
    mint_access_jwt,
    mint_verify_ticket,
    verify_password,
    verify_secret,
)


def test_generate_otp_code_is_six_digits():
    for _ in range(20):
        code = generate_otp_code()
        assert re.fullmatch(r"\d{6}", code), f"got {code!r}"


def test_generate_otp_code_is_random():
    codes = {generate_otp_code() for _ in range(50)}
    # Probability of all 50 colliding to <5 unique is astronomical
    assert len(codes) > 25


def test_hash_password_then_verify_password():
    h = hash_password("supersecret123")
    assert h != "supersecret123"
    assert verify_password("supersecret123", h) is True
    assert verify_password("wrong", h) is False


def test_hash_secret_handles_short_inputs():
    """hash_secret is for short secrets like OTP codes. bcrypt has a 72-byte
    limit, so OTP codes work fine."""
    h = hash_secret("482917")
    assert verify_secret("482917", h) is True
    assert verify_secret("482918", h) is False


def test_mint_access_jwt_viewer_round_trip():
    token = mint_access_jwt(
        sub="11111111-1111-1111-1111-111111111111",
        role="viewer",
        extras={"user_device_id": "22222222-2222-2222-2222-222222222222"},
    )
    payload = decode_access_jwt(token)
    assert payload["sub"] == "11111111-1111-1111-1111-111111111111"
    assert payload["role"] == "viewer"
    assert payload["user_device_id"] == "22222222-2222-2222-2222-222222222222"
    assert payload["kind"] == "access"


def test_mint_access_jwt_producer_round_trip():
    token = mint_access_jwt(
        sub="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="producer"
    )
    payload = decode_access_jwt(token)
    assert payload["sub"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert payload["role"] == "producer"


def test_decode_access_jwt_rejects_tampered():
    token = mint_access_jwt(sub="a", role="admin")
    bad = token[:-4] + "ZZZZ"
    with pytest.raises(Exception):
        decode_access_jwt(bad)


def test_decode_access_jwt_rejects_expired(monkeypatch):
    monkeypatch.setenv("JWT_EXPIRY_HOURS", "0")
    # Reload the settings cached singleton
    import alaba.config
    alaba.config._settings = None
    token = mint_access_jwt(sub="a", role="admin")
    time.sleep(1)
    with pytest.raises(Exception):
        decode_access_jwt(token)
    # Restore for other tests
    alaba.config._settings = None


def test_decode_access_jwt_rejects_verify_ticket():
    """An access decode must NOT accept a verify-ticket — different kinds."""
    ticket = mint_verify_ticket(
        phone="+2348031234567",
        user_id="11111111-1111-1111-1111-111111111111",
    )
    with pytest.raises(Exception):
        decode_access_jwt(ticket)


def test_mint_verify_ticket_round_trip():
    ticket = mint_verify_ticket(
        phone="+2348031234567",
        user_id="11111111-1111-1111-1111-111111111111",
    )
    payload = decode_verify_ticket(ticket)
    assert payload["phone"] == "+2348031234567"
    assert payload["user_id"] == "11111111-1111-1111-1111-111111111111"
    assert payload["kind"] == "device_cap_remediation"


def test_decode_verify_ticket_rejects_access_token():
    """A verify-ticket decode must NOT accept an access token."""
    access = mint_access_jwt(sub="a", role="viewer", extras={"user_device_id": "b"})
    with pytest.raises(Exception):
        decode_verify_ticket(access)
```

- [ ] **Step 2.2: Run tests — confirm RED**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/test_security.py -v
```

Expected: collection error or ImportError — `alaba.security` doesn't exist.

- [ ] **Step 2.3: Implement `backend/alaba/security.py`**

```python
"""Security primitives: JWT, bcrypt, OTP code generation."""

import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from alaba.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# ---------------------------------------------------------------------------
# Passwords and short secrets (bcrypt)
# ---------------------------------------------------------------------------

def hash_password(plaintext: str) -> str:
    """Hash a producer/admin password. Use only on inputs <= 72 bytes."""
    return _pwd_context.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    return _pwd_context.verify(plaintext, hashed)


def hash_secret(plaintext: str) -> str:
    """Hash a short secret like an OTP code. Same backend as passwords."""
    return _pwd_context.hash(plaintext)


def verify_secret(plaintext: str, hashed: str) -> bool:
    return _pwd_context.verify(plaintext, hashed)


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
```

- [ ] **Step 2.4: Run tests — confirm GREEN**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/test_security.py -v
```

Expected: 11 passing.

- [ ] **Step 2.5: Run the full suite**

```bash
docker exec alaba-backend-api pytest -v
```

Expected: 32 passing (21 + 11). No regressions.

- [ ] **Step 2.6: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add backend/alaba/security.py backend/tests/test_security.py
git commit -m "feat(backend): security primitives (JWT access + verify-ticket, bcrypt, OTP gen)"
```

---

## Task 3: deps.py — get_current_principal + role-specific helpers (TDD)

**Files:**
- Create: `backend/alaba/services/principal.py`
- Create: `backend/alaba/deps.py`
- Create: `backend/tests/test_deps.py`
- Create: `backend/alaba/services/__init__.py`

The `Principal` type is a tagged union returned from the dependency. Role-specific helpers (`get_current_viewer`, etc.) call `get_current_principal` and raise 403 if the role doesn't match.

- [ ] **Step 3.1: Create `backend/alaba/services/__init__.py`**

Empty file (just a package marker):

```python
"""Service layer — framework-free business logic."""
```

- [ ] **Step 3.2: Write the failing tests**

Create `backend/tests/test_deps.py`:

```python
"""Tests for deps.py — get_current_principal and role-specific helpers."""

import uuid

import pytest
from fastapi import HTTPException

from alaba.deps import (
    _extract_token,
    get_current_admin,
    get_current_principal,
    get_current_producer,
    get_current_viewer,
)
from alaba.models import Admin, Producer, User, UserDevice
from alaba.security import hash_password, mint_access_jwt


class FakeRequest:
    def __init__(self, headers: dict | None = None, cookies: dict | None = None):
        self.headers = headers or {}
        self.cookies = cookies or {}


def test_extract_token_from_authorization_header():
    req = FakeRequest(headers={"Authorization": "Bearer abc123"})
    assert _extract_token(req) == "abc123"


def test_extract_token_from_cookie_fallback():
    req = FakeRequest(cookies={"auth_token": "xyz789"})
    assert _extract_token(req) == "xyz789"


def test_extract_token_header_takes_precedence():
    req = FakeRequest(
        headers={"Authorization": "Bearer header_token"},
        cookies={"auth_token": "cookie_token"},
    )
    assert _extract_token(req) == "header_token"


def test_extract_token_none_when_neither_set():
    req = FakeRequest()
    assert _extract_token(req) is None


def test_extract_token_ignores_non_bearer_authorization():
    req = FakeRequest(headers={"Authorization": "Basic abc123"})
    assert _extract_token(req) is None


async def test_get_current_principal_missing_token_raises_401(db_session):
    req = FakeRequest()
    with pytest.raises(HTTPException) as exc:
        await get_current_principal(req, db=db_session)
    assert exc.value.status_code == 401


async def test_get_current_principal_invalid_token_raises_401(db_session):
    req = FakeRequest(headers={"Authorization": "Bearer not.a.jwt"})
    with pytest.raises(HTTPException) as exc:
        await get_current_principal(req, db=db_session)
    assert exc.value.status_code == 401


async def test_get_current_principal_viewer_happy(db_session):
    user = User(phone="+2348031234567", phone_verified=True)
    db_session.add(user); await db_session.flush()
    device = UserDevice(user_id=user.id, device_id="dev-1", platform="android")
    db_session.add(device); await db_session.flush()
    token = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    principal = await get_current_principal(req, db=db_session)
    assert principal.role == "viewer"
    assert principal.user.id == user.id
    assert principal.user_device.id == device.id


async def test_get_current_principal_viewer_deactivated_device_403(db_session):
    from datetime import UTC, datetime
    user = User(phone="+2348031234568", phone_verified=True)
    db_session.add(user); await db_session.flush()
    device = UserDevice(
        user_id=user.id, device_id="dev-2", platform="android",
        deactivated_at=datetime.now(UTC),
    )
    db_session.add(device); await db_session.flush()
    token = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    with pytest.raises(HTTPException) as exc:
        await get_current_principal(req, db=db_session)
    assert exc.value.status_code == 403
    assert exc.value.detail == {"reason": "device_deactivated"}


async def test_get_current_principal_producer_happy(db_session):
    producer = Producer(
        email="p@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(producer); await db_session.flush()
    token = mint_access_jwt(sub=str(producer.id), role="producer")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    principal = await get_current_principal(req, db=db_session)
    assert principal.role == "producer"
    assert principal.producer.id == producer.id


async def test_get_current_principal_admin_happy(db_session):
    admin = Admin(
        email="a@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(admin); await db_session.flush()
    token = mint_access_jwt(sub=str(admin.id), role="admin")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    principal = await get_current_principal(req, db=db_session)
    assert principal.role == "admin"
    assert principal.admin.id == admin.id


async def test_get_current_viewer_rejects_producer(db_session):
    producer = Producer(
        email="p2@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(producer); await db_session.flush()
    token = mint_access_jwt(sub=str(producer.id), role="producer")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    p = await get_current_principal(req, db=db_session)
    with pytest.raises(HTTPException) as exc:
        await get_current_viewer(p)
    assert exc.value.status_code == 403


async def test_get_current_producer_rejects_admin(db_session):
    admin = Admin(
        email="a2@test.com", password_hash=hash_password("ten_chars!"),
    )
    db_session.add(admin); await db_session.flush()
    token = mint_access_jwt(sub=str(admin.id), role="admin")
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    p = await get_current_principal(req, db=db_session)
    with pytest.raises(HTTPException) as exc:
        await get_current_producer(p)
    assert exc.value.status_code == 403


async def test_get_current_admin_rejects_viewer(db_session):
    user = User(phone="+2348031234569", phone_verified=True)
    db_session.add(user); await db_session.flush()
    device = UserDevice(user_id=user.id, device_id="dev-3", platform="android")
    db_session.add(device); await db_session.flush()
    token = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    req = FakeRequest(headers={"Authorization": f"Bearer {token}"})
    p = await get_current_principal(req, db=db_session)
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(p)
    assert exc.value.status_code == 403
```

This test file expects a `db_session` async fixture. We add it to `conftest.py` in the next step.

- [ ] **Step 3.3: Add the `db_session` fixture to conftest**

Append to `backend/tests/conftest.py`:

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Yields a transactional session that rolls back after each test."""
    from alaba.db import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
```

- [ ] **Step 3.4: Create `backend/alaba/services/principal.py`**

```python
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
```

- [ ] **Step 3.5: Create `backend/alaba/deps.py`**

```python
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
```

- [ ] **Step 3.6: Run tests — confirm GREEN**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/test_deps.py -v
```

Expected: 14 passing.

- [ ] **Step 3.7: Run the full suite**

```bash
docker exec alaba-backend-api pytest -v
```

Expected: 46 passing (32 + 14).

- [ ] **Step 3.8: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add backend/alaba/services/__init__.py backend/alaba/services/principal.py backend/alaba/deps.py backend/tests/conftest.py backend/tests/test_deps.py
git commit -m "feat(backend): get_current_principal dep + role-specific helpers"
```

---

## Task 4: OTP service + /auth/otp endpoints (Mode A only) + integration tests

This task ships the unit-tested `OtpService` plus the `/auth/otp/request` endpoint and the OTP-code path of `/auth/otp/verify` (Mode A from the spec — without device-cap remediation yet; Task 5 adds Mode B). Device resolution lives in Task 5; this task wires up to a stub that creates devices unconditionally until Task 5 replaces it.

Wait — that produces test churn. Better: include enough of `device_service` here so `/auth/otp/verify` works for a fresh user with no existing devices (the happy single-device case). Task 5 then layers cap enforcement, deactivation, and the verify-ticket path on top.

**Files:**
- Create: `backend/alaba/services/otp_service.py`
- Create: `backend/alaba/services/device_service.py` (skeleton — `resolve_or_create_device` only; cap logic in Task 5)
- Create: `backend/alaba/schemas/__init__.py`
- Create: `backend/alaba/schemas/auth.py`
- Create: `backend/alaba/api/auth.py`
- Modify: `backend/alaba/main.py` to include the auth router
- Create: `backend/tests/test_otp_service.py`
- Create: `backend/tests/integration/__init__.py`
- Create: `backend/tests/integration/test_auth_otp.py`
- Create: `backend/tests/factories.py`

- [ ] **Step 4.1: Create the factories helper**

Create `backend/tests/factories.py`:

```python
"""Light data factories for tests. No Faker dependency; deterministic values."""

import uuid
from datetime import UTC, datetime

from alaba.models import Admin, Producer, User, UserDevice
from alaba.security import hash_password


def make_user(phone: str = "+2348031234567", phone_verified: bool = True) -> User:
    return User(phone=phone, phone_verified=phone_verified)


def make_user_device(
    user_id: uuid.UUID,
    device_id: str = "device-abc",
    display_name: str = "TECNO Camon 18",
    deactivated: bool = False,
) -> UserDevice:
    return UserDevice(
        user_id=user_id,
        device_id=device_id,
        display_name=display_name,
        model="Camon 18",
        platform="android",
        last_seen_at=datetime.now(UTC),
        deactivated_at=datetime.now(UTC) if deactivated else None,
    )


def make_producer(
    email: str = "producer@test.com",
    password: str = "ten_chars!",
    company_name: str = "Orban Forest Films",
    verified: bool = False,
) -> Producer:
    return Producer(
        email=email,
        password_hash=hash_password(password),
        company_name=company_name,
        verified=verified,
    )


def make_admin(
    email: str = "admin@test.com",
    password: str = "ten_chars!",
) -> Admin:
    return Admin(email=email, password_hash=hash_password(password))
```

- [ ] **Step 4.2: Write the OTP service tests**

Create `backend/tests/test_otp_service.py`:

```python
"""Unit tests for OtpService."""

from datetime import UTC, datetime, timedelta

import pytest

from alaba.models import OtpCode
from alaba.security import hash_secret
from alaba.services.otp_service import (
    OtpAttemptsExhausted,
    OtpExpired,
    OtpInvalid,
    OtpRateLimited,
    OtpService,
)


async def test_issue_creates_otp_row(db_session):
    svc = OtpService(db_session)
    code = await svc.issue("+2348031234567")
    assert len(code) == 6
    rows = (await db_session.execute(
        OtpCode.__table__.select().where(OtpCode.__table__.c.phone == "+2348031234567")
    )).all()
    assert len(rows) == 1


async def test_issue_rate_limits_after_5_per_15min(db_session):
    svc = OtpService(db_session)
    for _ in range(5):
        await svc.issue("+2348031234567")
    with pytest.raises(OtpRateLimited):
        await svc.issue("+2348031234567")


async def test_issue_does_not_count_old_rows(db_session):
    """Rows older than 15 minutes don't count toward the limit."""
    old_row = OtpCode(
        phone="+2348031234567",
        code_hash=hash_secret("000000"),
        expires_at=datetime.now(UTC) - timedelta(minutes=20),
        attempts=0,
    )
    db_session.add(old_row); await db_session.flush()
    svc = OtpService(db_session)
    code = await svc.issue("+2348031234567")
    assert len(code) == 6


async def test_verify_happy_consumes_row(db_session):
    svc = OtpService(db_session)
    raw_code = await svc.issue("+2348031234567")
    row = await svc.verify("+2348031234567", raw_code)
    assert row.consumed_at is not None


async def test_verify_wrong_code_increments_attempts(db_session):
    svc = OtpService(db_session)
    await svc.issue("+2348031234567")
    with pytest.raises(OtpInvalid) as exc:
        await svc.verify("+2348031234567", "wrong1")
    assert exc.value.attempts_remaining == 4


async def test_verify_attempts_exhausted_after_5(db_session):
    svc = OtpService(db_session)
    await svc.issue("+2348031234567")
    for _ in range(5):
        with pytest.raises(OtpInvalid):
            await svc.verify("+2348031234567", "wrong1")
    with pytest.raises(OtpAttemptsExhausted):
        await svc.verify("+2348031234567", "wrong1")


async def test_verify_expired_raises(db_session):
    svc = OtpService(db_session)
    row = OtpCode(
        phone="+2348031234567",
        code_hash=hash_secret("123456"),
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
        attempts=0,
    )
    db_session.add(row); await db_session.flush()
    with pytest.raises(OtpExpired):
        await svc.verify("+2348031234567", "123456")


async def test_verify_no_row_raises_invalid(db_session):
    svc = OtpService(db_session)
    with pytest.raises(OtpInvalid):
        await svc.verify("+2348031234567", "123456")


async def test_verify_already_consumed_raises_invalid(db_session):
    svc = OtpService(db_session)
    raw = await svc.issue("+2348031234567")
    await svc.verify("+2348031234567", raw)
    with pytest.raises(OtpInvalid):
        await svc.verify("+2348031234567", raw)
```

- [ ] **Step 4.3: Implement `backend/alaba/services/otp_service.py`**

```python
"""OTP issuance, verification, attempt tracking."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.models import OtpCode
from alaba.security import generate_otp_code, hash_secret, verify_secret


class OtpRateLimited(Exception):
    """Too many OTP-request calls for this phone."""


class OtpInvalid(Exception):
    """The supplied code is wrong, missing, or already consumed."""
    def __init__(self, attempts_remaining: int = 0):
        super().__init__("invalid_code")
        self.attempts_remaining = attempts_remaining


class OtpExpired(Exception):
    """The OTP row exists but is past its expires_at."""


class OtpAttemptsExhausted(Exception):
    """The OTP row exists but has been tried >= max_attempts times."""


@dataclass
class OtpService:
    db: AsyncSession

    async def issue(self, phone: str) -> str:
        """Generate, persist, and return the raw OTP code for `phone`."""
        s = get_settings()
        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=15)

        result = await self.db.execute(
            select(OtpCode).where(
                OtpCode.phone == phone,
                OtpCode.created_at >= cutoff,
            )
        )
        recent_rows = result.scalars().all()
        if len(recent_rows) >= 5:
            raise OtpRateLimited()

        raw = generate_otp_code()
        row = OtpCode(
            phone=phone,
            code_hash=hash_secret(raw),
            expires_at=now + timedelta(minutes=s.otp_expiry_minutes),
            attempts=0,
        )
        self.db.add(row)
        await self.db.flush()
        return raw

    async def verify(self, phone: str, code: str) -> OtpCode:
        """Look up the latest unconsumed OTP for `phone` and verify `code`.
        On success, marks consumed_at and returns the row.
        Raises OtpInvalid, OtpExpired, or OtpAttemptsExhausted on failure paths."""
        s = get_settings()
        now = datetime.now(UTC)

        result = await self.db.execute(
            select(OtpCode)
            .where(
                OtpCode.phone == phone,
                OtpCode.consumed_at.is_(None),
            )
            .order_by(OtpCode.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise OtpInvalid(attempts_remaining=0)

        if row.expires_at <= now:
            raise OtpExpired()

        if row.attempts >= s.otp_max_attempts:
            raise OtpAttemptsExhausted()

        if not verify_secret(code, row.code_hash):
            row.attempts += 1
            await self.db.flush()
            remaining = max(0, s.otp_max_attempts - row.attempts)
            raise OtpInvalid(attempts_remaining=remaining)

        row.consumed_at = now
        await self.db.flush()
        return row
```

- [ ] **Step 4.4: Run OTP service tests — confirm GREEN**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/test_otp_service.py -v
```

Expected: 9 passing.

- [ ] **Step 4.5: Implement the skeleton device service (`resolve_or_create_device` only)**

Create `backend/alaba/services/device_service.py`:

```python
"""Device resolution and lifecycle. Cap enforcement layered in Task 5."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.models import User, UserDevice


@dataclass
class DeviceService:
    db: AsyncSession

    async def find_or_create_user(self, phone: str) -> User:
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(phone=phone, phone_verified=True)
            self.db.add(user)
            await self.db.flush()
        else:
            if not user.phone_verified:
                user.phone_verified = True
                await self.db.flush()
        return user

    async def resolve_or_create_device(
        self,
        *,
        user: User,
        device_id: str,
        display_name: str | None,
        model: str | None,
        platform: str = "android",
    ) -> UserDevice:
        """Task-4 simplified: create a new device row OR update last_seen on existing
        active. Cap + cooldown + reactivation logic arrives in Task 5."""
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user.id,
                UserDevice.device_id == device_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None and existing.deactivated_at is None:
            existing.last_seen_at = now
            await self.db.flush()
            return existing

        device = UserDevice(
            user_id=user.id,
            device_id=device_id,
            display_name=display_name,
            model=model,
            platform=platform,
            last_seen_at=now,
        )
        self.db.add(device)
        await self.db.flush()
        return device
```

- [ ] **Step 4.6: Create the auth schemas**

Create `backend/alaba/schemas/__init__.py`:

```python
"""Pydantic request/response schemas."""
```

Create `backend/alaba/schemas/auth.py`:

```python
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
```

- [ ] **Step 4.7: Create the OTP provider integration (mock)**

Create `backend/alaba/integrations/__init__.py`:

```python
"""External integrations: OTP, payments, storage."""
```

Create `backend/alaba/integrations/otp.py`:

```python
"""OTP provider protocol + MockOTPProvider."""

import logging
from typing import Protocol

from alaba.config import get_settings


class OTPProvider(Protocol):
    async def send(self, phone: str, code: str) -> None: ...


class MockOTPProvider:
    """Logs the OTP code at INFO level. Production refuses to boot with this."""

    def __init__(self):
        s = get_settings()
        if s.environment == "production":
            raise ValueError(
                "MockOTPProvider is forbidden in production. "
                "Set OTP_PROVIDER=termii (or another real provider)."
            )
        self._logger = logging.getLogger("alaba.otp.mock")

    async def send(self, phone: str, code: str) -> None:
        self._logger.info("[OTP] %s → %s", phone, code)


def get_otp_provider() -> OTPProvider:
    """Factory keyed on settings.otp_provider."""
    s = get_settings()
    if s.otp_provider == "mock":
        return MockOTPProvider()
    raise NotImplementedError(f"OTP provider not implemented: {s.otp_provider}")
```

- [ ] **Step 4.8: Implement `backend/alaba/api/auth.py` (request + verify Mode A only)**

```python
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
```

- [ ] **Step 4.9: Register the router in `main.py`**

Open `backend/alaba/main.py`. Replace:

```python
from alaba.api import health
```

with:

```python
from alaba.api import auth, health
```

And replace:

```python
    app.include_router(health.router)
```

with:

```python
    app.include_router(health.router)
    app.include_router(auth.router)
```

- [ ] **Step 4.10: Write the integration tests**

Create `backend/tests/integration/__init__.py`:

```python
```

Create `backend/tests/integration/test_auth_otp.py`:

```python
"""Integration tests for /auth/otp/request and /auth/otp/verify (Mode A)."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_request_otp_happy(caplog):
    import logging
    caplog.set_level(logging.INFO, logger="alaba.otp.mock")
    async with await _client() as c:
        r = await c.post("/auth/otp/request", json={"phone": "+2348031234500"})
    assert r.status_code == 200
    assert r.json() == {"sent": True}
    # Code was logged
    assert any("+2348031234500" in m for m in caplog.messages)


async def test_request_otp_rate_limit(caplog):
    import logging
    caplog.set_level(logging.INFO, logger="alaba.otp.mock")
    phone = "+2348031234501"
    async with await _client() as c:
        for _ in range(5):
            r = await c.post("/auth/otp/request", json={"phone": phone})
            assert r.status_code == 200
        r = await c.post("/auth/otp/request", json={"phone": phone})
    assert r.status_code == 429
    assert r.json()["detail"]["error"] == "too_many_otp_requests"


async def test_verify_otp_happy_new_user_new_device(caplog):
    import logging
    caplog.set_level(logging.INFO, logger="alaba.otp.mock")
    phone = "+2348031234502"
    async with await _client() as c:
        await c.post("/auth/otp/request", json={"phone": phone})
        # Extract code from log
        code = None
        for m in caplog.messages:
            if phone in m and "→" in m:
                code = m.split("→")[-1].strip()
        assert code, "OTP code not logged"
        r = await c.post(
            "/auth/otp/verify",
            json={
                "phone": phone,
                "code": code,
                "device_id": "test-dev-1",
                "display_name": "Test Device",
                "model": "Test",
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "jwt" in body
    assert "user_device_id" in body
    assert "expires_at" in body


async def test_verify_otp_wrong_code(caplog):
    import logging
    caplog.set_level(logging.INFO, logger="alaba.otp.mock")
    phone = "+2348031234503"
    async with await _client() as c:
        await c.post("/auth/otp/request", json={"phone": phone})
        r = await c.post(
            "/auth/otp/verify",
            json={"phone": phone, "code": "000000", "device_id": "test-dev-2"},
        )
    assert r.status_code == 401
    detail = r.json()["detail"]
    assert detail["error"] == "invalid_code"
    assert detail["attempts_remaining"] == 4


async def test_verify_otp_missing_both_code_and_ticket():
    async with await _client() as c:
        r = await c.post(
            "/auth/otp/verify",
            json={"phone": "+2348031234504", "device_id": "x"},
        )
    assert r.status_code == 422


async def test_verify_otp_both_code_and_ticket():
    async with await _client() as c:
        r = await c.post(
            "/auth/otp/verify",
            json={
                "phone": "+2348031234505",
                "code": "123456",
                "verify_ticket": "ticket",
                "device_id": "x",
            },
        )
    assert r.status_code == 422
```

- [ ] **Step 4.11: Run integration tests — confirm GREEN**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/integration/test_auth_otp.py -v
```

Expected: 6 passing.

- [ ] **Step 4.12: Run the full suite**

```bash
docker exec alaba-backend-api pytest -v
```

Expected: 70 passing (46 + 9 service + 6 integration + 9 already counted? — actual count: 46 prior + 9 + 6 = 61 — adjust expectations). The exact total depends on whether some old tests interact with new code; if any fail, investigate.

Acceptable result: all prior 46 still pass, plus the 9 service and 6 integration tests added in this task = 61 total. If higher, that's fine.

- [ ] **Step 4.13: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add backend/alaba/services/otp_service.py backend/alaba/services/device_service.py backend/alaba/schemas/__init__.py backend/alaba/schemas/auth.py backend/alaba/integrations/__init__.py backend/alaba/integrations/otp.py backend/alaba/api/auth.py backend/alaba/main.py backend/tests/factories.py backend/tests/test_otp_service.py backend/tests/integration/__init__.py backend/tests/integration/test_auth_otp.py
git commit -m "feat(backend): OtpService + /auth/otp/request + /auth/otp/verify Mode A"
```

---

## Task 5: Device service (cap + cooldown + Mode B) + /devices + admin device endpoints

This task layers cap enforcement, cooldown handling, and the verify-ticket Mode B flow on top of Task 4's skeleton. It also adds the viewer-facing `/devices` endpoints and the admin-facing `/admin/users/*/devices` endpoints.

**Files:**
- Modify: `backend/alaba/services/device_service.py` (add cap enforcement, deactivate, cooldown calc)
- Modify: `backend/alaba/api/auth.py` (wire up Mode B verify-ticket path)
- Create: `backend/alaba/schemas/device.py`
- Create: `backend/alaba/api/devices.py`
- Create: `backend/alaba/api/admin_users.py`
- Modify: `backend/alaba/main.py` (register new routers)
- Create: `backend/tests/test_device_service.py`
- Create: `backend/tests/integration/test_devices.py`
- Create: `backend/tests/integration/test_admin_devices.py`
- Modify: `backend/tests/integration/test_auth_otp.py` (add Mode B tests)

- [ ] **Step 5.1: Write device service tests**

Create `backend/tests/test_device_service.py`:

```python
"""Unit tests for DeviceService cap + cooldown + Mode B logic."""

from datetime import UTC, datetime, timedelta

import pytest

from alaba.config import get_settings
from alaba.models import User, UserDevice
from alaba.services.device_service import (
    DeviceCapReached,
    DeviceCooldownActive,
    DeviceNotFound,
    DeviceService,
)
from tests.factories import make_user, make_user_device


async def test_register_new_device_under_cap(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    svc = DeviceService(db_session)
    device = await svc.register_or_resolve_device(
        user=user, device_id="dev-1", display_name="phone", model="X",
    )
    assert device.user_id == user.id
    assert device.device_id == "dev-1"
    assert device.deactivated_at is None


async def test_register_at_cap_raises_cap_reached(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A")
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceCapReached) as exc:
        await svc.register_or_resolve_device(
            user=user, device_id="dev-NEW", display_name="phone3", model="Z",
        )
    assert len(exc.value.active_devices) == 2


async def test_existing_active_device_updates_last_seen(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A")
    d1.last_seen_at = datetime.now(UTC) - timedelta(days=7)
    db_session.add(d1); await db_session.flush()
    svc = DeviceService(db_session)
    device = await svc.register_or_resolve_device(
        user=user, device_id="dev-A", display_name="phone", model="X",
    )
    assert device.id == d1.id
    assert (datetime.now(UTC) - device.last_seen_at).total_seconds() < 5


async def test_existing_deactivated_within_cooldown_raises(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    deactivated = make_user_device(user.id, "dev-A", deactivated=True)
    deactivated.deactivated_at = datetime.now(UTC) - timedelta(days=30)
    db_session.add(deactivated); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceCooldownActive):
        await svc.register_or_resolve_device(
            user=user, device_id="dev-A", display_name="phone", model="X",
        )


async def test_existing_deactivated_past_cooldown_reactivates(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    deactivated = make_user_device(user.id, "dev-A", deactivated=True)
    deactivated.deactivated_at = datetime.now(UTC) - timedelta(days=100)
    db_session.add(deactivated); await db_session.flush()
    svc = DeviceService(db_session)
    device = await svc.register_or_resolve_device(
        user=user, device_id="dev-A", display_name="phone", model="X",
    )
    assert device.deactivated_at is None


async def test_deactivate_device_happy(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d = make_user_device(user.id, "dev-A")
    db_session.add(d); await db_session.flush()
    svc = DeviceService(db_session)
    await svc.deactivate(user, d.id)
    await db_session.refresh(d)
    assert d.deactivated_at is not None


async def test_deactivate_blocked_by_cooldown(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A", deactivated=True)
    d1.deactivated_at = datetime.now(UTC) - timedelta(days=30)
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceCooldownActive):
        await svc.deactivate(user, d2.id)


async def test_deactivate_device_belonging_to_other_user_raises(db_session):
    u1 = make_user("+2348031234001")
    u2 = make_user("+2348031234002")
    db_session.add_all([u1, u2]); await db_session.flush()
    d = make_user_device(u2.id, "dev-foreign")
    db_session.add(d); await db_session.flush()
    svc = DeviceService(db_session)
    with pytest.raises(DeviceNotFound):
        await svc.deactivate(u1, d.id)


async def test_deactivate_idempotent_on_already_deactivated(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d = make_user_device(user.id, "dev-A", deactivated=True)
    d.deactivated_at = datetime.now(UTC) - timedelta(days=200)  # past cooldown
    db_session.add(d); await db_session.flush()
    svc = DeviceService(db_session)
    # Should not raise
    await svc.deactivate(user, d.id)


async def test_admin_force_deactivate_bypasses_cooldown(db_session):
    user = make_user()
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A", deactivated=True)
    d1.deactivated_at = datetime.now(UTC) - timedelta(days=30)
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    svc = DeviceService(db_session)
    await svc.admin_force_deactivate(
        user_id=user.id, device_id=d2.id,
        admin_email="admin@test.com", reason="lost phone",
    )
    await db_session.refresh(d2)
    assert d2.deactivated_at is not None
    # AdminAction row exists
    from alaba.models import AdminAction
    from sqlalchemy import select
    result = await db_session.execute(select(AdminAction))
    actions = result.scalars().all()
    assert any(a.action == "force_deactivate_device" for a in actions)
```

- [ ] **Step 5.2: Replace `backend/alaba/services/device_service.py` with the full version**

```python
"""Device resolution + cap enforcement + cooldown + Mode B path."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.models import AdminAction, User, UserDevice


class DeviceCapReached(Exception):
    def __init__(self, active_devices: list[UserDevice], user_id: UUID):
        self.active_devices = active_devices
        self.user_id = user_id


class DeviceCooldownActive(Exception):
    def __init__(self, unlock_at: datetime):
        self.unlock_at = unlock_at


class DeviceNotFound(Exception):
    pass


@dataclass
class DeviceService:
    db: AsyncSession

    async def find_or_create_user(self, phone: str) -> User:
        result = await self.db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(phone=phone, phone_verified=True)
            self.db.add(user)
            await self.db.flush()
        elif not user.phone_verified:
            user.phone_verified = True
            await self.db.flush()
        return user

    async def _list_active_for_user(self, user_id: UUID) -> list[UserDevice]:
        result = await self.db.execute(
            select(UserDevice)
            .where(UserDevice.user_id == user_id, UserDevice.deactivated_at.is_(None))
            .order_by(UserDevice.activated_at.asc())
        )
        return list(result.scalars().all())

    async def _check_cooldown(self, user_id: UUID) -> None:
        s = get_settings()
        cutoff = datetime.now(UTC) - timedelta(days=s.device_deactivation_cooldown_days)
        result = await self.db.execute(
            select(UserDevice)
            .where(
                UserDevice.user_id == user_id,
                UserDevice.deactivated_at.is_not(None),
                UserDevice.deactivated_at > cutoff,
            )
            .order_by(UserDevice.deactivated_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            unlock_at = row.deactivated_at + timedelta(days=s.device_deactivation_cooldown_days)
            raise DeviceCooldownActive(unlock_at=unlock_at)

    async def register_or_resolve_device(
        self,
        *,
        user: User,
        device_id: str,
        display_name: str | None,
        model: str | None,
        platform: str = "android",
    ) -> UserDevice:
        s = get_settings()
        now = datetime.now(UTC)

        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.user_id == user.id,
                UserDevice.device_id == device_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None and existing.deactivated_at is None:
            existing.last_seen_at = now
            await self.db.flush()
            return existing
        if existing is not None:
            # Deactivated row — check cooldown for reactivation
            cooldown_cutoff = now - timedelta(days=s.device_deactivation_cooldown_days)
            if existing.deactivated_at > cooldown_cutoff:
                raise DeviceCooldownActive(
                    unlock_at=existing.deactivated_at + timedelta(days=s.device_deactivation_cooldown_days),
                )
            existing.deactivated_at = None
            existing.last_seen_at = now
            await self.db.flush()
            return existing

        # New device
        active = await self._list_active_for_user(user.id)
        if len(active) >= s.max_active_devices_per_user:
            raise DeviceCapReached(active_devices=active, user_id=user.id)

        device = UserDevice(
            user_id=user.id,
            device_id=device_id,
            display_name=display_name,
            model=model,
            platform=platform,
            last_seen_at=now,
        )
        self.db.add(device)
        await self.db.flush()
        return device

    async def deactivate_with_cap_remediation(
        self,
        *,
        user: User,
        new_device_id: str,
        new_display_name: str | None,
        new_model: str | None,
        new_platform: str,
        deactivate_device_id: UUID,
    ) -> UserDevice:
        """Mode B: simultaneously deactivate one device and register another."""
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.id == deactivate_device_id,
                UserDevice.user_id == user.id,
            )
        )
        to_deactivate = result.scalar_one_or_none()
        if to_deactivate is None or to_deactivate.deactivated_at is not None:
            raise DeviceNotFound()

        await self._check_cooldown(user.id)

        now = datetime.now(UTC)
        to_deactivate.deactivated_at = now

        device = UserDevice(
            user_id=user.id,
            device_id=new_device_id,
            display_name=new_display_name,
            model=new_model,
            platform=new_platform,
            last_seen_at=now,
        )
        self.db.add(device)
        await self.db.flush()
        return device

    async def list_user_devices(self, user_id: UUID) -> list[UserDevice]:
        """Active first, then deactivated, both sorted by recency."""
        result = await self.db.execute(
            select(UserDevice)
            .where(UserDevice.user_id == user_id)
            .order_by(
                UserDevice.deactivated_at.is_not(None).asc(),
                UserDevice.activated_at.desc(),
            )
        )
        return list(result.scalars().all())

    async def deactivate(self, user: User, device_id: UUID) -> None:
        """Self-deactivate. Enforces cooldown."""
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.id == device_id,
                UserDevice.user_id == user.id,
            )
        )
        device = result.scalar_one_or_none()
        if device is None:
            raise DeviceNotFound()
        if device.deactivated_at is not None:
            return  # idempotent
        await self._check_cooldown(user.id)
        device.deactivated_at = datetime.now(UTC)
        await self.db.flush()

    async def admin_force_deactivate(
        self,
        *,
        user_id: UUID,
        device_id: UUID,
        admin_email: str,
        reason: str,
    ) -> None:
        """Admin force-deactivate: bypasses cooldown. Logs to admin_actions."""
        result = await self.db.execute(
            select(UserDevice).where(
                UserDevice.id == device_id,
                UserDevice.user_id == user_id,
            )
        )
        device = result.scalar_one_or_none()
        if device is None:
            raise DeviceNotFound()
        if device.deactivated_at is None:
            device.deactivated_at = datetime.now(UTC)
        action = AdminAction(
            admin_email=admin_email,
            action="force_deactivate_device",
            target_type="user_device",
            target_id=device.id,
            reason=reason,
        )
        self.db.add(action)
        await self.db.flush()
```

- [ ] **Step 5.3: Run device service tests — confirm GREEN**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/backend
uv run pytest tests/test_device_service.py -v
```

Expected: 10 passing.

- [ ] **Step 5.4: Update `/auth/otp/verify` to handle device-cap and Mode B**

Open `backend/alaba/api/auth.py`. Replace the `verify_otp` function with this version (the imports section adds `mint_verify_ticket`, `decode_verify_ticket`, and the device-service exceptions):

```python
from jose import JWTError

from alaba.schemas.auth import ActiveDeviceSummary, OtpVerify409Body
from alaba.security import decode_verify_ticket, mint_access_jwt, mint_verify_ticket
from alaba.services.device_service import (
    DeviceCapReached,
    DeviceCooldownActive,
    DeviceNotFound,
    DeviceService,
)
```

Replace the existing `verify_otp` function with:

```python
@router.post("/otp/verify", response_model=OtpVerifyOut)
async def verify_otp(
    body: OtpVerifyIn,
    db: AsyncSession = Depends(get_db),
):
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

    dev_svc = DeviceService(db)

    if body.verify_ticket is not None:
        # Mode B
        if body.deactivate_device_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "deactivate_device_id_required_with_ticket"},
            )
        try:
            payload = decode_verify_ticket(body.verify_ticket)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        if payload.get("phone") != body.phone:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        from uuid import UUID
        try:
            user_id = UUID(payload["user_id"])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        user = await db.get(__import__('alaba.models', fromlist=['User']).User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_verify_ticket"},
            )
        try:
            device = await dev_svc.deactivate_with_cap_remediation(
                user=user,
                new_device_id=body.device_id,
                new_display_name=body.display_name,
                new_model=body.model,
                new_platform=body.platform,
                deactivate_device_id=body.deactivate_device_id,
            )
        except DeviceCooldownActive as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "cooldown_active", "unlock_at": e.unlock_at.isoformat()},
            )
        except DeviceNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "device_not_found_or_already_inactive"},
            )
        await db.commit()
        jwt_token = mint_access_jwt(
            sub=str(user.id),
            role="viewer",
            extras={"user_device_id": str(device.id)},
        )
        s = get_settings()
        expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
        return OtpVerifyOut(
            jwt=jwt_token,
            user_device_id=device.id,
            expires_at=expires_at,
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

    user = await dev_svc.find_or_create_user(body.phone)
    try:
        device = await dev_svc.register_or_resolve_device(
            user=user,
            device_id=body.device_id,
            display_name=body.display_name,
            model=body.model,
            platform=body.platform,
        )
    except DeviceCapReached as e:
        ticket = mint_verify_ticket(phone=body.phone, user_id=str(e.user_id))
        active_summaries = [
            ActiveDeviceSummary(
                id=d.id,
                display_name=d.display_name,
                model=d.model,
                platform=d.platform,
                activated_at=d.activated_at,
                last_seen_at=d.last_seen_at,
            )
            for d in e.active_devices
        ]
        await db.commit()  # commit OTP consume + user creation
        body_dict = OtpVerify409Body(
            active_devices=active_summaries, verify_ticket=ticket
        ).model_dump(mode="json")
        raise HTTPException(status_code=409, detail=body_dict)
    except DeviceCooldownActive as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "cooldown_active", "unlock_at": e.unlock_at.isoformat()},
        )

    await db.commit()
    jwt_token = mint_access_jwt(
        sub=str(user.id),
        role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    s = get_settings()
    expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
    return OtpVerifyOut(
        jwt=jwt_token,
        user_device_id=device.id,
        expires_at=expires_at,
    )
```

- [ ] **Step 5.5: Create device schemas**

Create `backend/alaba/schemas/device.py`:

```python
"""Schemas for /devices/* and /admin/users/*/devices/*."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceOut(BaseModel):
    id: UUID
    display_name: str | None
    model: str | None
    platform: str
    activated_at: datetime
    deactivated_at: datetime | None
    last_seen_at: datetime | None
    is_current: bool = False


class DeviceListOut(BaseModel):
    devices: list[DeviceOut]
    cap: int
    active_count: int
    deactivation_cooldown_unlock_at: datetime | None


class AdminForceDeactivateIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class UserLookupOut(BaseModel):
    user_id: UUID
    phone: str
```

- [ ] **Step 5.6: Create `backend/alaba/api/devices.py`**

```python
"""Viewer-facing device endpoints."""

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.config import get_settings
from alaba.db import get_db
from alaba.deps import get_current_viewer
from alaba.schemas.device import DeviceListOut, DeviceOut
from alaba.services.device_service import (
    DeviceCooldownActive,
    DeviceNotFound,
    DeviceService,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=DeviceListOut)
async def list_my_devices(
    principal=Depends(get_current_viewer),
    db: AsyncSession = Depends(get_db),
):
    s = get_settings()
    svc = DeviceService(db)
    devices = await svc.list_user_devices(principal.user.id)
    active = [d for d in devices if d.deactivated_at is None]

    # Compute cooldown unlock if applicable
    cooldown_unlock = None
    cutoff_delta = timedelta(days=s.device_deactivation_cooldown_days)
    deactivated = [d for d in devices if d.deactivated_at is not None]
    if deactivated:
        latest = max(deactivated, key=lambda d: d.deactivated_at)
        from datetime import datetime, UTC
        cooldown_end = latest.deactivated_at + cutoff_delta
        if cooldown_end > datetime.now(UTC):
            cooldown_unlock = cooldown_end

    return DeviceListOut(
        devices=[
            DeviceOut(
                id=d.id,
                display_name=d.display_name,
                model=d.model,
                platform=d.platform,
                activated_at=d.activated_at,
                deactivated_at=d.deactivated_at,
                last_seen_at=d.last_seen_at,
                is_current=(d.id == principal.user_device.id),
            )
            for d in devices
        ],
        cap=s.max_active_devices_per_user,
        active_count=len(active),
        deactivation_cooldown_unlock_at=cooldown_unlock,
    )


@router.post("/{device_id}/deactivate", status_code=204)
async def deactivate_my_device(
    device_id: UUID,
    principal=Depends(get_current_viewer),
    db: AsyncSession = Depends(get_db),
):
    svc = DeviceService(db)
    try:
        await svc.deactivate(principal.user, device_id)
    except DeviceNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "device_not_found"},
        )
    except DeviceCooldownActive as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "cooldown_active", "unlock_at": e.unlock_at.isoformat()},
        )
    await db.commit()
```

- [ ] **Step 5.7: Create `backend/alaba/api/admin_users.py`**

```python
"""Admin endpoints for user device management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.db import get_db
from alaba.deps import get_current_admin
from alaba.models import User
from alaba.schemas.device import (
    AdminForceDeactivateIn,
    DeviceListOut,
    DeviceOut,
    UserLookupOut,
)
from alaba.services.device_service import DeviceNotFound, DeviceService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users/lookup", response_model=UserLookupOut)
async def lookup_user(
    phone: str = Query(...),
    principal=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "user_not_found"},
        )
    return UserLookupOut(user_id=user.id, phone=user.phone)


@router.get("/users/{user_id}/devices", response_model=DeviceListOut)
async def list_user_devices_for_admin(
    user_id: UUID,
    principal=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from alaba.config import get_settings
    s = get_settings()
    svc = DeviceService(db)
    devices = await svc.list_user_devices(user_id)
    active = [d for d in devices if d.deactivated_at is None]
    return DeviceListOut(
        devices=[
            DeviceOut(
                id=d.id,
                display_name=d.display_name,
                model=d.model,
                platform=d.platform,
                activated_at=d.activated_at,
                deactivated_at=d.deactivated_at,
                last_seen_at=d.last_seen_at,
                is_current=False,
            )
            for d in devices
        ],
        cap=s.max_active_devices_per_user,
        active_count=len(active),
        deactivation_cooldown_unlock_at=None,
    )


@router.post(
    "/users/{user_id}/devices/{device_id}/deactivate",
    status_code=204,
)
async def admin_force_deactivate(
    user_id: UUID,
    device_id: UUID,
    body: AdminForceDeactivateIn,
    principal=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = DeviceService(db)
    try:
        await svc.admin_force_deactivate(
            user_id=user_id,
            device_id=device_id,
            admin_email=principal.admin.email,
            reason=body.reason,
        )
    except DeviceNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "device_not_found"},
        )
    await db.commit()
```

- [ ] **Step 5.8: Register the new routers in `main.py`**

Open `backend/alaba/main.py`. Update the imports:

```python
from alaba.api import admin_users, auth, devices, health
```

And update the router includes inside `create_app`:

```python
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(devices.router)
    app.include_router(admin_users.router)
```

- [ ] **Step 5.9: Write the integration tests for /devices**

Create `backend/tests/integration/test_devices.py`:

```python
"""Integration tests for /devices/* viewer endpoints."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from alaba.security import mint_access_jwt
from tests.factories import make_user, make_user_device


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _auth_headers(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


async def test_list_my_devices_empty_after_login(db_session):
    """Setup: user with one device → list returns one device, marked is_current."""
    user = make_user("+2348031234600")
    db_session.add(user); await db_session.flush()
    device = make_user_device(user.id, "dev-1")
    db_session.add(device); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    async with await _client() as c:
        r = await c.get("/devices", headers=_auth_headers(jwt))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cap"] == 2
    assert body["active_count"] == 1
    assert len(body["devices"]) == 1
    assert body["devices"][0]["is_current"] is True
    assert body["deactivation_cooldown_unlock_at"] is None


async def test_deactivate_my_device(db_session):
    user = make_user("+2348031234601")
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "dev-A")
    d2 = make_user_device(user.id, "dev-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(d1.id)},
    )
    async with await _client() as c:
        r = await c.post(f"/devices/{d2.id}/deactivate", headers=_auth_headers(jwt))
    assert r.status_code == 204


async def test_cannot_deactivate_other_users_device(db_session):
    u1 = make_user("+2348031234602")
    u2 = make_user("+2348031234603")
    db_session.add_all([u1, u2]); await db_session.flush()
    d1 = make_user_device(u1.id, "u1-dev")
    d2 = make_user_device(u2.id, "u2-dev")
    db_session.add_all([d1, d2]); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(u1.id), role="viewer",
        extras={"user_device_id": str(d1.id)},
    )
    async with await _client() as c:
        r = await c.post(f"/devices/{d2.id}/deactivate", headers=_auth_headers(jwt))
    assert r.status_code == 404


async def test_no_auth_returns_401():
    async with await _client() as c:
        r = await c.get("/devices")
    assert r.status_code == 401
```

- [ ] **Step 5.10: Write the integration tests for admin /admin/users/...**

Create `backend/tests/integration/test_admin_devices.py`:

```python
"""Integration tests for admin user-devices endpoints."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from alaba.models import AdminAction
from alaba.security import mint_access_jwt
from sqlalchemy import select
from tests.factories import make_admin, make_user, make_user_device


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _auth_headers(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


async def test_lookup_user_by_phone_happy(db_session):
    admin = make_admin("a1@test.com")
    user = make_user("+2348031234700")
    db_session.add_all([admin, user]); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.get(
            "/admin/users/lookup",
            params={"phone": "+2348031234700"},
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user_id"] == str(user.id)
    assert body["phone"] == "+2348031234700"


async def test_lookup_user_404(db_session):
    admin = make_admin("a2@test.com")
    db_session.add(admin); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.get(
            "/admin/users/lookup",
            params={"phone": "+2348039999999"},
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 404


async def test_list_user_devices_for_admin(db_session):
    admin = make_admin("a3@test.com")
    user = make_user("+2348031234701")
    db_session.add_all([admin, user]); await db_session.flush()
    d = make_user_device(user.id, "ud-1")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.get(
            f"/admin/users/{user.id}/devices",
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 200
    body = r.json()
    assert body["active_count"] == 1


async def test_force_deactivate_writes_admin_action(db_session):
    admin = make_admin("a4@test.com")
    user = make_user("+2348031234702")
    db_session.add_all([admin, user]); await db_session.flush()
    d = make_user_device(user.id, "ud-2")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.post(
            f"/admin/users/{user.id}/devices/{d.id}/deactivate",
            json={"reason": "user reported phone lost"},
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 204
    result = await db_session.execute(select(AdminAction))
    actions = result.scalars().all()
    assert any(
        a.action == "force_deactivate_device" and a.admin_email == "a4@test.com"
        for a in actions
    )


async def test_admin_endpoint_rejects_viewer_jwt(db_session):
    user = make_user("+2348031234703")
    db_session.add(user); await db_session.flush()
    d = make_user_device(user.id, "ud-3")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(d.id)},
    )
    async with await _client() as c:
        r = await c.get("/admin/users/lookup", params={"phone": "x"}, headers=_auth_headers(jwt))
    assert r.status_code == 403


async def test_force_deactivate_validates_reason_length(db_session):
    admin = make_admin("a5@test.com")
    user = make_user("+2348031234704")
    db_session.add_all([admin, user]); await db_session.flush()
    d = make_user_device(user.id, "ud-4")
    db_session.add(d); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(admin.id), role="admin")
    async with await _client() as c:
        r = await c.post(
            f"/admin/users/{user.id}/devices/{d.id}/deactivate",
            json={"reason": "x"},  # < 5 chars
            headers=_auth_headers(jwt),
        )
    assert r.status_code == 422
```

- [ ] **Step 5.11: Add Mode B tests to existing test_auth_otp.py**

Append to `backend/tests/integration/test_auth_otp.py`:

```python
async def test_verify_otp_mode_b_device_cap_reached_returns_409_with_ticket(caplog, db_session):
    """User has 2 active devices; 3rd verify attempt returns 409 with verify_ticket."""
    import logging
    caplog.set_level(logging.INFO, logger="alaba.otp.mock")
    phone = "+2348031234800"
    # Pre-seed: 2 devices for this phone's user
    from tests.factories import make_user, make_user_device
    user = make_user(phone)
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "preexist-1")
    d2 = make_user_device(user.id, "preexist-2")
    db_session.add_all([d1, d2]); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        await c.post("/auth/otp/request", json={"phone": phone})
        code = None
        for m in caplog.messages:
            if phone in m and "→" in m:
                code = m.split("→")[-1].strip()
        r = await c.post(
            "/auth/otp/verify",
            json={"phone": phone, "code": code, "device_id": "third-dev"},
        )
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert detail["error"] == "device_cap_reached"
    assert len(detail["active_devices"]) == 2
    assert "verify_ticket" in detail


async def test_verify_otp_mode_b_completes_with_valid_ticket(caplog, db_session):
    """After 409, retrying with verify_ticket + deactivate_device_id succeeds."""
    import logging
    caplog.set_level(logging.INFO, logger="alaba.otp.mock")
    phone = "+2348031234801"
    from tests.factories import make_user, make_user_device
    user = make_user(phone)
    db_session.add(user); await db_session.flush()
    d1 = make_user_device(user.id, "preexist-A")
    d2 = make_user_device(user.id, "preexist-B")
    db_session.add_all([d1, d2]); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        await c.post("/auth/otp/request", json={"phone": phone})
        code = None
        for m in caplog.messages:
            if phone in m and "→" in m:
                code = m.split("→")[-1].strip()
        r1 = await c.post(
            "/auth/otp/verify",
            json={"phone": phone, "code": code, "device_id": "third-dev"},
        )
        ticket = r1.json()["detail"]["verify_ticket"]
        r2 = await c.post(
            "/auth/otp/verify",
            json={
                "phone": phone,
                "verify_ticket": ticket,
                "device_id": "third-dev",
                "deactivate_device_id": str(d1.id),
            },
        )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert "jwt" in body


async def test_verify_ticket_with_wrong_phone_rejected(caplog, db_session):
    import logging
    caplog.set_level(logging.INFO, logger="alaba.otp.mock")
    from alaba.security import mint_verify_ticket
    import uuid
    bad_ticket = mint_verify_ticket(
        phone="+2348031234999", user_id=str(uuid.uuid4()),
    )
    async with await _client() as c:
        r = await c.post(
            "/auth/otp/verify",
            json={
                "phone": "+2348031234802",
                "verify_ticket": bad_ticket,
                "device_id": "x",
                "deactivate_device_id": str(uuid.uuid4()),
            },
        )
    assert r.status_code == 401
```

- [ ] **Step 5.12: Run all backend tests — confirm GREEN**

```bash
docker exec alaba-backend-api pytest -v
```

Expected: ~80+ passing (every prior test plus the new ones in this task). No regressions. If any prior test fails because of the new code, investigate before continuing.

- [ ] **Step 5.13: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add backend/alaba/services/device_service.py backend/alaba/schemas/device.py backend/alaba/api/auth.py backend/alaba/api/devices.py backend/alaba/api/admin_users.py backend/alaba/main.py backend/tests/test_device_service.py backend/tests/integration/test_devices.py backend/tests/integration/test_admin_devices.py backend/tests/integration/test_auth_otp.py
git commit -m "feat(backend): DeviceService cap+cooldown, Mode B verify-ticket, /devices, /admin/users endpoints"
```

---

## Task 6: Producer + admin auth endpoints + /me + integration tests

**Files:**
- Create: `backend/alaba/services/auth_service.py`
- Create: `backend/alaba/schemas/user.py`
- Modify: `backend/alaba/schemas/auth.py` (add LoginIn, RegisterIn, AuthJwtOut)
- Modify: `backend/alaba/api/auth.py` (add producer/admin endpoints)
- Create: `backend/alaba/api/me.py`
- Modify: `backend/alaba/main.py` (include me router)
- Create: `backend/tests/test_auth_service.py`
- Create: `backend/tests/integration/test_auth_producer.py`
- Create: `backend/tests/integration/test_auth_admin.py`
- Create: `backend/tests/integration/test_me.py`

- [ ] **Step 6.1: Write auth_service tests**

Create `backend/tests/test_auth_service.py`:

```python
"""Unit tests for AuthService (password-based login)."""

import pytest

from alaba.services.auth_service import (
    EmailInUse,
    InvalidCredentials,
    PasswordTooShort,
    AuthService,
)
from tests.factories import make_admin, make_producer


async def test_register_producer_happy(db_session):
    svc = AuthService(db_session)
    producer = await svc.register_producer(
        email="new@test.com", password="ten_chars!", company_name="X",
    )
    assert producer.email == "new@test.com"
    assert producer.verified is False


async def test_register_producer_duplicate_email(db_session):
    existing = make_producer("dup@test.com")
    db_session.add(existing); await db_session.flush()
    svc = AuthService(db_session)
    with pytest.raises(EmailInUse):
        await svc.register_producer(
            email="dup@test.com", password="ten_chars!", company_name=None,
        )


async def test_register_producer_short_password(db_session):
    svc = AuthService(db_session)
    with pytest.raises(PasswordTooShort):
        await svc.register_producer(
            email="short@test.com", password="short", company_name=None,
        )


async def test_login_producer_happy(db_session):
    producer = make_producer("login@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    svc = AuthService(db_session)
    result = await svc.login_producer("login@test.com", "ten_chars!")
    assert result.id == producer.id


async def test_login_producer_wrong_password(db_session):
    producer = make_producer("wp@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.login_producer("wp@test.com", "wrong_pass!")


async def test_login_producer_unknown_email(db_session):
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.login_producer("nobody@test.com", "ten_chars!")


async def test_login_admin_happy(db_session):
    admin = make_admin("alogin@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    svc = AuthService(db_session)
    result = await svc.login_admin("alogin@test.com", "ten_chars!")
    assert result.id == admin.id


async def test_login_admin_wrong_password(db_session):
    admin = make_admin("awp@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    svc = AuthService(db_session)
    with pytest.raises(InvalidCredentials):
        await svc.login_admin("awp@test.com", "wrong_pass!")
```

- [ ] **Step 6.2: Implement `backend/alaba/services/auth_service.py`**

```python
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
```

- [ ] **Step 6.3: Extend `backend/alaba/schemas/auth.py`**

Append at the bottom:

```python
class RegisterIn(BaseModel):
    email: str = Field(min_length=4, max_length=255)
    password: str = Field(min_length=1, max_length=1000)  # service validates min length
    company_name: str | None = None


class LoginIn(BaseModel):
    email: str = Field(min_length=4, max_length=255)
    password: str = Field(min_length=1, max_length=1000)


class AuthJwtOut(BaseModel):
    jwt: str
    expires_at: datetime
    role: str
    subject_id: UUID
```

- [ ] **Step 6.4: Create `backend/alaba/schemas/user.py`**

```python
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
```

- [ ] **Step 6.5: Add producer/admin endpoints to `backend/alaba/api/auth.py`**

Add these imports near the top of the file:

```python
from alaba.schemas.auth import AuthJwtOut, LoginIn, RegisterIn
from alaba.services.auth_service import (
    AuthService,
    EmailInUse,
    InvalidCredentials,
    PasswordTooShort,
)
```

Add these endpoints at the end of the file:

```python
@router.post("/producer/register", response_model=AuthJwtOut)
async def register_producer(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        producer = await svc.register_producer(
            email=body.email, password=body.password, company_name=body.company_name,
        )
    except EmailInUse:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "email_in_use"},
        )
    except PasswordTooShort:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "password_too_short", "min_length": 10},
        )
    await db.commit()
    s = get_settings()
    token = mint_access_jwt(sub=str(producer.id), role="producer")
    expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
    return AuthJwtOut(
        jwt=token, expires_at=expires_at, role="producer", subject_id=producer.id,
    )


@router.post("/producer/login", response_model=AuthJwtOut)
async def login_producer(body: LoginIn, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        producer = await svc.login_producer(body.email, body.password)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials"},
        )
    s = get_settings()
    token = mint_access_jwt(sub=str(producer.id), role="producer")
    expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
    return AuthJwtOut(
        jwt=token, expires_at=expires_at, role="producer", subject_id=producer.id,
    )


@router.post("/admin/login", response_model=AuthJwtOut)
async def login_admin(body: LoginIn, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        admin = await svc.login_admin(body.email, body.password)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials"},
        )
    s = get_settings()
    token = mint_access_jwt(sub=str(admin.id), role="admin")
    expires_at = datetime.now(UTC) + timedelta(hours=s.jwt_expiry_hours)
    return AuthJwtOut(
        jwt=token, expires_at=expires_at, role="admin", subject_id=admin.id,
    )
```

- [ ] **Step 6.6: Create `backend/alaba/api/me.py`**

```python
"""/me endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from alaba.deps import get_current_principal
from alaba.schemas.user import MeAdminOut, MeProducerOut, MeViewerOut
from alaba.services.principal import Principal

router = APIRouter(tags=["me"])


@router.get("/me")
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
```

- [ ] **Step 6.7: Register /me router in main.py**

Update the imports:

```python
from alaba.api import admin_users, auth, devices, health, me
```

And the includes:

```python
    app.include_router(me.router)
```

- [ ] **Step 6.8: Write the producer auth integration tests**

Create `backend/tests/integration/test_auth_producer.py`:

```python
"""Integration tests for /auth/producer/* endpoints."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from tests.factories import make_producer


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_register_happy():
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/register",
            json={
                "email": "newprod@test.com",
                "password": "ten_chars!",
                "company_name": "Orban Forest",
            },
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "producer"
    assert "jwt" in body


async def test_register_short_password():
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/register",
            json={"email": "short@test.com", "password": "short"},
        )
    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "password_too_short"


async def test_register_duplicate_email(db_session):
    existing = make_producer("dup@test.com")
    db_session.add(existing); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/register",
            json={"email": "dup@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 409


async def test_login_happy(db_session):
    producer = make_producer("loginok@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/login",
            json={"email": "loginok@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 200
    assert r.json()["role"] == "producer"


async def test_login_wrong_password(db_session):
    producer = make_producer("loginwp@test.com", "ten_chars!")
    db_session.add(producer); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/login",
            json={"email": "loginwp@test.com", "password": "wrong_pass!"},
        )
    assert r.status_code == 401


async def test_login_unknown_email():
    async with await _client() as c:
        r = await c.post(
            "/auth/producer/login",
            json={"email": "nobody@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 401
```

- [ ] **Step 6.9: Write the admin auth integration tests**

Create `backend/tests/integration/test_auth_admin.py`:

```python
"""Integration tests for /auth/admin/login."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from tests.factories import make_admin


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_admin_login_happy(db_session):
    admin = make_admin("aint@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/admin/login",
            json={"email": "aint@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


async def test_admin_login_wrong_password(db_session):
    admin = make_admin("aiwp@test.com", "ten_chars!")
    db_session.add(admin); await db_session.flush()
    await db_session.commit()
    async with await _client() as c:
        r = await c.post(
            "/auth/admin/login",
            json={"email": "aiwp@test.com", "password": "wrong_pass!"},
        )
    assert r.status_code == 401


async def test_admin_login_unknown():
    async with await _client() as c:
        r = await c.post(
            "/auth/admin/login",
            json={"email": "noadmin@test.com", "password": "ten_chars!"},
        )
    assert r.status_code == 401
```

- [ ] **Step 6.10: Write the /me integration tests**

Create `backend/tests/integration/test_me.py`:

```python
"""Integration tests for /me endpoint."""

from datetime import UTC, datetime

from httpx import ASGITransport, AsyncClient

from alaba.main import app
from alaba.security import mint_access_jwt
from tests.factories import make_admin, make_producer, make_user, make_user_device


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _hdr(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


async def test_me_viewer(db_session):
    user = make_user("+2348031234900")
    db_session.add(user); await db_session.flush()
    device = make_user_device(user.id, "me-1")
    db_session.add(device); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "viewer"
    assert body["phone"] == "+2348031234900"


async def test_me_producer(db_session):
    p = make_producer("mep@test.com")
    db_session.add(p); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(p.id), role="producer")
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "producer"
    assert body["verified"] is False


async def test_me_admin(db_session):
    a = make_admin("mea@test.com")
    db_session.add(a); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(sub=str(a.id), role="admin")
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


async def test_me_viewer_with_deactivated_device_returns_403(db_session):
    user = make_user("+2348031234901")
    db_session.add(user); await db_session.flush()
    device = make_user_device(user.id, "me-deact", deactivated=True)
    device.deactivated_at = datetime.now(UTC)
    db_session.add(device); await db_session.flush()
    await db_session.commit()
    jwt = mint_access_jwt(
        sub=str(user.id), role="viewer",
        extras={"user_device_id": str(device.id)},
    )
    async with await _client() as c:
        r = await c.get("/me", headers=_hdr(jwt))
    assert r.status_code == 403
    assert r.json()["detail"]["reason"] == "device_deactivated"


async def test_me_no_auth():
    async with await _client() as c:
        r = await c.get("/me")
    assert r.status_code == 401
```

- [ ] **Step 6.11: Run all backend tests**

```bash
docker exec alaba-backend-api pytest -v
```

Expected: ~110+ passing. No regressions.

- [ ] **Step 6.12: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add backend/alaba/services/auth_service.py backend/alaba/schemas/auth.py backend/alaba/schemas/user.py backend/alaba/api/auth.py backend/alaba/api/me.py backend/alaba/main.py backend/tests/test_auth_service.py backend/tests/integration/test_auth_producer.py backend/tests/integration/test_auth_admin.py backend/tests/integration/test_me.py
git commit -m "feat(backend): producer/admin auth endpoints + /me"
```

---

## Task 7: make_admin script + wire Makefile target

**Files:**
- Create: `infra/scripts/make_admin.py`
- Modify: `Makefile`

- [ ] **Step 7.1: Create `infra/scripts/make_admin.py`**

```python
"""Bootstrap an admin user.

Run from inside the backend-api container so that env vars and the
alaba package are on PYTHONPATH:

    docker exec -it alaba-backend-api python /app/scripts/make_admin.py --email x

For host-side convenience, the Makefile wraps this with `make make-admin email=...`."""

import argparse
import asyncio
import getpass
import os
import sys

# Allow running this file from inside the container at /app/scripts/make_admin.py
sys.path.insert(0, "/app")

from sqlalchemy import select  # noqa: E402

from alaba.db import AsyncSessionLocal  # noqa: E402
from alaba.models import Admin  # noqa: E402
from alaba.security import hash_password  # noqa: E402


async def create_admin(email: str, password: str) -> None:
    if len(password) < 10:
        print("ERROR: password must be at least 10 characters.", file=sys.stderr)
        sys.exit(1)
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Admin).where(Admin.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"ERROR: admin {email!r} already exists.", file=sys.stderr)
            sys.exit(1)
        admin = Admin(email=email, password_hash=hash_password(password))
        db.add(admin)
        await db.commit()
        print(f"Admin created: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an Alaba admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--password",
        default=None,
        help="Password (if omitted, prompts interactively).",
    )
    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("Password (>= 10 chars): ")
        confirm = getpass.getpass("Confirm: ")
        if password != confirm:
            print("ERROR: passwords don't match.", file=sys.stderr)
            sys.exit(1)

    asyncio.run(create_admin(args.email, password))


if __name__ == "__main__":
    main()
```

- [ ] **Step 7.2: Make the script reachable inside the backend container**

The compose file mounts `../backend/alaba` and `../backend/alembic` into the container. Scripts under `infra/scripts/` are NOT mounted by default. Add a mount.

Open `infra/docker-compose.yml`, find the `backend-api` service's `volumes:` block:

```yaml
    volumes:
      - ../backend/alaba:/app/alaba
      - ../backend/alembic:/app/alembic
```

Replace with:

```yaml
    volumes:
      - ../backend/alaba:/app/alaba
      - ../backend/alembic:/app/alembic
      - ./scripts:/app/scripts:ro
```

Restart the backend container so the mount takes effect:

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --force-recreate backend-api
```

Wait for healthy:

```bash
sleep 8
docker inspect -f '{{.State.Health.Status}}' alaba-backend-api
```

Expected: `healthy`.

- [ ] **Step 7.3: Rewire the Makefile target**

Open `/mnt/e/TOOLMAKER/PYTHON/alaba/Makefile`. Find the `make-admin:` block:

```makefile
make-admin: ## Bootstrap an admin user (script arrives in Wave 1)
	@echo "make make-admin is not yet wired. The script (infra/scripts/make_admin.py) is created in Wave 1."
	@exit 1
```

Replace with:

```makefile
make-admin: ## Bootstrap an admin user. Usage: make make-admin email=admin@alaba.test
	@if [ -z "$(email)" ]; then echo "Usage: make make-admin email=admin@alaba.test"; exit 1; fi
	docker exec -it alaba-backend-api python /app/scripts/make_admin.py --email "$(email)"
```

- [ ] **Step 7.4: Test the script with a real admin**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
make make-admin email=admin@alaba.test
# Enter password "ten_chars_admin" twice when prompted
```

Expected: `Admin created: admin@alaba.test`.

Verify in DB:

```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "SELECT email, suspended FROM admins;"
```

Expected: shows the new admin row.

- [ ] **Step 7.5: Verify the admin can actually log in**

```bash
curl -s -X POST http://localhost:8000/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@alaba.test", "password": "ten_chars_admin"}' | python3 -m json.tool
```

Expected: JSON with `role: "admin"` and a `jwt` token.

- [ ] **Step 7.6: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add infra/scripts/make_admin.py infra/docker-compose.yml Makefile
git commit -m "feat(infra): make_admin script + Makefile target"
```

---

## Task 8: Web — middleware + lib + login/register pages

**Files:**
- Modify: `web/package.json` (add `jose`)
- Create: `web/src/middleware.ts`
- Create: `web/src/lib/jwt.ts`
- Create: `web/src/lib/api-client.ts`
- Create: `web/src/lib/auth.ts`
- Create: `web/src/lib/validators.ts`
- Create: `web/src/app/(auth)/producer/login/page.tsx`
- Create: `web/src/app/(auth)/producer/register/page.tsx`
- Create: `web/src/app/(auth)/admin/login/page.tsx`
- Create: `web/src/components/auth/LoginForm.tsx`
- Create: `web/src/components/auth/RegisterForm.tsx`
- Modify: `web/src/app/page.tsx` (add login/register entry links)

- [ ] **Step 8.1: Install `jose` and `react-hook-form` + `@hookform/resolvers` + `zod` + shadcn form components**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/web
npm install jose react-hook-form @hookform/resolvers zod
```

Then add shadcn form-related components:

```bash
npx shadcn@latest add input label form alert --yes
```

Verify these now exist:
- `web/src/components/ui/input.tsx`
- `web/src/components/ui/label.tsx`
- `web/src/components/ui/form.tsx`
- `web/src/components/ui/alert.tsx`

- [ ] **Step 8.2: Create `web/src/lib/jwt.ts`**

```typescript
import { jwtVerify, type JWTPayload } from "jose";

export interface AlabaJwtClaims extends JWTPayload {
  sub: string;
  role: "viewer" | "producer" | "admin";
  kind: "access";
  user_device_id?: string;
}

const secret = new TextEncoder().encode(process.env.JWT_SECRET || "");

export async function verifyJwt(token: string): Promise<AlabaJwtClaims> {
  if (!process.env.JWT_SECRET) {
    throw new Error("JWT_SECRET env var is not set");
  }
  const { payload } = await jwtVerify(token, secret, { algorithms: ["HS256"] });
  if (payload.kind !== "access") {
    throw new Error(`Wrong kind: ${payload.kind}`);
  }
  return payload as AlabaJwtClaims;
}
```

- [ ] **Step 8.3: Create `web/src/lib/validators.ts`**

```typescript
import { z } from "zod";

export const LoginInput = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password required"),
});
export type LoginInput = z.infer<typeof LoginInput>;

export const RegisterInput = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(10, "Password must be at least 10 characters"),
  company_name: z.string().optional(),
});
export type RegisterInput = z.infer<typeof RegisterInput>;

export const ForceDeactivateInput = z.object({
  reason: z.string().min(5, "Reason is required (5+ chars)"),
});
export type ForceDeactivateInput = z.infer<typeof ForceDeactivateInput>;
```

- [ ] **Step 8.4: Create `web/src/lib/api-client.ts`**

```typescript
import { cookies } from "next/headers";

const BACKEND = process.env.BACKEND_INTERNAL_URL || "http://backend-api:8000";

interface FetchOptions extends RequestInit {
  authenticated?: boolean;
}

export async function apiFetch(path: string, opts: FetchOptions = {}): Promise<Response> {
  const headers = new Headers(opts.headers);
  headers.set("Content-Type", "application/json");

  if (opts.authenticated !== false) {
    const cookieStore = await cookies();
    const jwt = cookieStore.get("auth_token")?.value;
    if (jwt) {
      headers.set("Authorization", `Bearer ${jwt}`);
    }
  }

  return fetch(`${BACKEND}${path}`, { ...opts, headers, cache: "no-store" });
}

export async function apiJson<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const r = await apiFetch(path, opts);
  if (!r.ok) {
    const text = await r.text();
    throw new ApiError(r.status, text);
  }
  return (await r.json()) as T;
}

export class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`API ${status}: ${body}`);
  }
  json(): unknown {
    try { return JSON.parse(this.body); } catch { return null; }
  }
}
```

- [ ] **Step 8.5: Create `web/src/lib/auth.ts`**

```typescript
import { cookies } from "next/headers";
import { verifyJwt, type AlabaJwtClaims } from "@/lib/jwt";

const COOKIE_NAME = "auth_token";
const TWENTY_FOUR_HOURS = 60 * 60 * 24;

export async function setAuthCookie(jwt: string): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(COOKIE_NAME, jwt, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: TWENTY_FOUR_HOURS,
  });
}

export async function clearAuthCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NAME);
}

export async function getServerPrincipal(): Promise<AlabaJwtClaims | null> {
  const cookieStore = await cookies();
  const jwt = cookieStore.get(COOKIE_NAME)?.value;
  if (!jwt) return null;
  try {
    return await verifyJwt(jwt);
  } catch {
    return null;
  }
}
```

- [ ] **Step 8.6: Create `web/src/middleware.ts`**

```typescript
import { NextRequest, NextResponse } from "next/server";
import { verifyJwt } from "@/lib/jwt";

export const config = {
  matcher: ["/producer/((?!login|register).*)", "/admin/((?!login).*)"],
};

export async function middleware(req: NextRequest) {
  const isProducerRoute = req.nextUrl.pathname.startsWith("/producer");
  const loginUrl = isProducerRoute ? "/producer/login" : "/admin/login";
  const token = req.cookies.get("auth_token")?.value;

  if (!token) {
    return NextResponse.redirect(new URL(loginUrl, req.url));
  }

  try {
    const payload = await verifyJwt(token);
    if (isProducerRoute && payload.role !== "producer") {
      return NextResponse.redirect(new URL("/producer/login", req.url));
    }
    if (req.nextUrl.pathname.startsWith("/admin") && payload.role !== "admin") {
      return NextResponse.redirect(new URL("/admin/login", req.url));
    }
    return NextResponse.next();
  } catch {
    const res = NextResponse.redirect(new URL(loginUrl, req.url));
    res.cookies.delete("auth_token");
    return res;
  }
}
```

- [ ] **Step 8.7: Create `web/src/components/auth/LoginForm.tsx`**

```tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { LoginInput } from "@/lib/validators";

interface LoginFormProps {
  role: "producer" | "admin";
  action: (input: LoginInput) => Promise<{ ok: true } | { ok: false; error: string }>;
}

export default function LoginForm({ role, action }: LoginFormProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<LoginInput>({ resolver: zodResolver(LoginInput) });

  const onSubmit = handleSubmit(async (data) => {
    setError(null);
    const result = await action(data);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    router.push(role === "producer" ? "/producer/dashboard" : "/admin/dashboard");
  });

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <div className="space-y-1">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && (
          <p className="text-xs text-red-600">{errors.email.message}</p>
        )}
      </div>
      <div className="space-y-1">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          {...register("password")}
        />
        {errors.password && (
          <p className="text-xs text-red-600">{errors.password.message}</p>
        )}
      </div>
      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Signing in..." : "Log in"}
      </Button>
    </form>
  );
}
```

- [ ] **Step 8.8: Create `web/src/components/auth/RegisterForm.tsx`**

```tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RegisterInput } from "@/lib/validators";

interface RegisterFormProps {
  action: (
    input: RegisterInput
  ) => Promise<{ ok: true } | { ok: false; error: string }>;
}

export default function RegisterForm({ action }: RegisterFormProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<RegisterInput>({ resolver: zodResolver(RegisterInput) });

  const onSubmit = handleSubmit(async (data) => {
    setError(null);
    const result = await action(data);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    router.push("/producer/dashboard");
  });

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <div className="space-y-1">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && (
          <p className="text-xs text-red-600">{errors.email.message}</p>
        )}
      </div>
      <div className="space-y-1">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          placeholder="At least 10 characters"
          {...register("password")}
        />
        {errors.password && (
          <p className="text-xs text-red-600">{errors.password.message}</p>
        )}
      </div>
      <div className="space-y-1">
        <Label htmlFor="company_name">
          Company name <span className="text-muted-foreground">(optional)</span>
        </Label>
        <Input id="company_name" {...register("company_name")} />
      </div>
      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </Button>
      <p className="text-xs text-muted-foreground text-center">
        After registration you'll need to accept the Distribution Agreement and wait
        for admin verification before uploading.
      </p>
    </form>
  );
}
```

- [ ] **Step 8.9: Create `web/src/app/(auth)/producer/login/page.tsx`**

```tsx
import Link from "next/link";
import { redirect } from "next/navigation";

import LoginForm from "@/components/auth/LoginForm";
import { setAuthCookie, getServerPrincipal } from "@/lib/auth";
import { apiFetch } from "@/lib/api-client";
import { LoginInput } from "@/lib/validators";

async function loginAction(
  input: LoginInput
): Promise<{ ok: true } | { ok: false; error: string }> {
  "use server";
  const r = await apiFetch("/auth/producer/login", {
    method: "POST",
    body: JSON.stringify(input),
    authenticated: false,
  });
  if (!r.ok) {
    if (r.status === 401) return { ok: false, error: "Wrong email or password." };
    return { ok: false, error: `Server error (${r.status})` };
  }
  const body = (await r.json()) as { jwt: string };
  await setAuthCookie(body.jwt);
  return { ok: true };
}

export default async function ProducerLoginPage() {
  const principal = await getServerPrincipal();
  if (principal?.role === "producer") redirect("/producer/dashboard");

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Alaba</h1>
          <p className="text-sm text-muted-foreground mt-1">For producers</p>
        </div>
        <div className="bg-card border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-1">Welcome back</h2>
          <p className="text-sm text-muted-foreground mb-6">
            New here?{" "}
            <Link href="/producer/register" className="underline text-foreground">
              Register
            </Link>
          </p>
          <LoginForm role="producer" action={loginAction} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 8.10: Create `web/src/app/(auth)/producer/register/page.tsx`**

```tsx
import Link from "next/link";
import { redirect } from "next/navigation";

import RegisterForm from "@/components/auth/RegisterForm";
import { setAuthCookie, getServerPrincipal } from "@/lib/auth";
import { apiFetch } from "@/lib/api-client";
import { RegisterInput } from "@/lib/validators";

async function registerAction(
  input: RegisterInput
): Promise<{ ok: true } | { ok: false; error: string }> {
  "use server";
  const r = await apiFetch("/auth/producer/register", {
    method: "POST",
    body: JSON.stringify(input),
    authenticated: false,
  });
  if (!r.ok) {
    if (r.status === 409) return { ok: false, error: "That email is already registered." };
    if (r.status === 422) return { ok: false, error: "Password must be at least 10 characters." };
    return { ok: false, error: `Server error (${r.status})` };
  }
  const body = (await r.json()) as { jwt: string };
  await setAuthCookie(body.jwt);
  return { ok: true };
}

export default async function ProducerRegisterPage() {
  const principal = await getServerPrincipal();
  if (principal?.role === "producer") redirect("/producer/dashboard");

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Alaba</h1>
          <p className="text-sm text-muted-foreground mt-1">For producers</p>
        </div>
        <div className="bg-card border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-1">Create your account</h2>
          <p className="text-sm text-muted-foreground mb-6">
            Already have one?{" "}
            <Link href="/producer/login" className="underline text-foreground">
              Log in
            </Link>
          </p>
          <RegisterForm action={registerAction} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 8.11: Create `web/src/app/(auth)/admin/login/page.tsx`**

```tsx
import Link from "next/link";
import { redirect } from "next/navigation";

import LoginForm from "@/components/auth/LoginForm";
import { setAuthCookie, getServerPrincipal } from "@/lib/auth";
import { apiFetch } from "@/lib/api-client";
import { LoginInput } from "@/lib/validators";

async function adminLoginAction(
  input: LoginInput
): Promise<{ ok: true } | { ok: false; error: string }> {
  "use server";
  const r = await apiFetch("/auth/admin/login", {
    method: "POST",
    body: JSON.stringify(input),
    authenticated: false,
  });
  if (!r.ok) {
    if (r.status === 401) return { ok: false, error: "Wrong email or password." };
    return { ok: false, error: `Server error (${r.status})` };
  }
  const body = (await r.json()) as { jwt: string };
  await setAuthCookie(body.jwt);
  return { ok: true };
}

export default async function AdminLoginPage() {
  const principal = await getServerPrincipal();
  if (principal?.role === "admin") redirect("/admin/dashboard");

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Alaba</h1>
          <p className="text-sm text-muted-foreground mt-1">Admin console</p>
        </div>
        <div className="bg-card border rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-6">Log in</h2>
          <LoginForm role="admin" action={adminLoginAction} />
          <p className="text-xs text-muted-foreground text-center mt-4">
            Producer accounts: use{" "}
            <Link href="/producer/login" className="underline">
              /producer/login
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 8.12: Update `web/src/app/page.tsx` to add entry links**

Replace contents:

```tsx
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="max-w-xl text-center space-y-6 px-6">
        <h1 className="text-4xl font-bold tracking-tight">Alaba</h1>
        <p className="text-lg text-muted-foreground">
          Nollywood films. ₦500. Download and watch offline, anytime.
        </p>
        <div className="flex gap-4 justify-center pt-4 text-sm">
          <Link
            href="/producer/login"
            className="underline text-foreground hover:opacity-70"
          >
            Producer log in
          </Link>
          <span className="text-muted-foreground">·</span>
          <Link
            href="/admin/login"
            className="underline text-muted-foreground hover:text-foreground"
          >
            Admin
          </Link>
        </div>
        <p className="text-sm text-muted-foreground pt-8">
          The Android app will be available on Google Play soon.
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 8.13: Update `web/Dockerfile` so the new dependencies install correctly**

The current Dockerfile copies `package.json` and `package-lock.json` then runs `npm ci`. Because we just modified `package.json`, the next compose build needs to repeat `npm ci`. No Dockerfile change needed but we DO need to rebuild.

- [ ] **Step 8.14: Set JWT_SECRET in web container's env**

Open `infra/docker-compose.yml`. Find the `web:` service's `environment:` block:

```yaml
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
      BACKEND_INTERNAL_URL: ${BACKEND_INTERNAL_URL}
```

Replace with:

```yaml
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
      BACKEND_INTERNAL_URL: ${BACKEND_INTERNAL_URL}
      JWT_SECRET: ${JWT_SECRET}
      NODE_ENV: development
```

- [ ] **Step 8.15: Rebuild the web container**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --build --force-recreate web
sleep 8
docker inspect -f '{{.State.Status}}' alaba-web
```

Expected: `running`. Check logs if it's not.

- [ ] **Step 8.16: Manual verify auth pages render**

```bash
curl -sL http://localhost:3000/producer/login | grep -c "Welcome back"
curl -sL http://localhost:3000/producer/register | grep -c "Create your account"
curl -sL http://localhost:3000/admin/login | grep -c "Log in"
```

Expected: each returns at least 1.

- [ ] **Step 8.17: Manually test register → cookie set → can fetch /producer/dashboard (will 404 until Task 9 but should reach middleware)**

```bash
# Register and capture the redirect / cookie
curl -sL -c /tmp/alaba-cookies.txt -X POST http://localhost:3000/producer/register \
  -H "Content-Type: application/json" \
  -d '{"email": "manual@test.com", "password": "ten_chars_test", "company_name": "Test"}' -o /dev/null -w "%{http_code}\n"
```

Expected: a 200 from the Server Action. Actually since this is a Server Action via form post, plain curl won't trigger it the same way. The real verification: open <http://localhost:3000/producer/register> in a browser, fill the form, submit.

For automated verification, defer to Task 9's Playwright test in Step 9.13.

- [ ] **Step 8.18: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add web/package.json web/package-lock.json web/components.json web/src/middleware.ts web/src/lib web/src/components/auth web/src/components/ui web/src/app/page.tsx web/src/app/\(auth\) infra/docker-compose.yml
git commit -m "feat(web): JWT middleware, login + register pages for producer + admin"
```

---

## Task 9: Web — producer dashboard banner states + sidebar shell + logout

**Files:**
- Create: `web/src/app/(producer)/producer/layout.tsx`
- Create: `web/src/app/(producer)/producer/dashboard/page.tsx`
- Create: `web/src/app/api/auth/logout/route.ts`
- Create: `web/src/lib/datetime.ts`
- Create: `web/src/components/producer/Sidebar.tsx`
- Optional Playwright test: `web/e2e/producer-register-login.spec.ts` (if Playwright is set up; otherwise documented as manual test in Task 17)

- [ ] **Step 9.1: Create `web/src/lib/datetime.ts`**

```typescript
export function formatWAT(d: Date | string): string {
  const date = typeof d === "string" ? new Date(d) : d;
  return new Intl.DateTimeFormat("en-NG", {
    timeZone: "Africa/Lagos",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date) + " WAT";
}

export function formatWATDate(d: Date | string): string {
  const date = typeof d === "string" ? new Date(d) : d;
  return new Intl.DateTimeFormat("en-NG", {
    timeZone: "Africa/Lagos",
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(date);
}
```

- [ ] **Step 9.2: Create `web/src/components/producer/Sidebar.tsx`**

```tsx
import Link from "next/link";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/producer/dashboard", enabled: true, wave: null },
  { label: "Films", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Upload", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Payouts", href: "#", enabled: false, wave: "Wave 8" },
  { label: "Settings", href: "#", enabled: false, wave: "Wave 9" },
];

interface SidebarProps {
  email: string;
  role: "producer" | "admin";
}

export default function Sidebar({ email, role }: SidebarProps) {
  return (
    <aside className="w-56 border-r bg-card p-4 flex flex-col h-screen sticky top-0">
      <div className="text-lg font-bold mb-1">Alaba {role === "admin" ? "Admin" : ""}</div>
      <div className="text-xs text-muted-foreground mb-6 truncate">{email}</div>
      <nav className="space-y-1 flex-1">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`block px-2 py-1.5 rounded text-sm ${
              item.enabled
                ? "bg-muted/50 font-medium"
                : "text-muted-foreground pointer-events-none"
            }`}
          >
            {item.label}
            {item.wave && (
              <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                {item.wave}
              </span>
            )}
          </Link>
        ))}
      </nav>
      <form action="/api/auth/logout" method="POST">
        <button
          type="submit"
          className="w-full text-left text-xs text-muted-foreground py-2 hover:text-foreground"
        >
          Log out
        </button>
      </form>
    </aside>
  );
}
```

- [ ] **Step 9.3: Create `web/src/app/(producer)/producer/layout.tsx`**

```tsx
import { redirect } from "next/navigation";

import Sidebar from "@/components/producer/Sidebar";
import { getServerPrincipal } from "@/lib/auth";
import { apiJson } from "@/lib/api-client";

interface MeProducerOut {
  role: "producer";
  producer_id: string;
  email: string;
  company_name: string | null;
  verified: boolean;
  agreement_accepted_at: string | null;
}

export default async function ProducerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const principal = await getServerPrincipal();
  if (!principal || principal.role !== "producer") redirect("/producer/login");

  // Fetch /me for the email display in sidebar
  let email = "";
  try {
    const me = await apiJson<MeProducerOut>("/me");
    email = me.email;
  } catch {
    redirect("/producer/login");
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar email={email} role="producer" />
      <main className="flex-1 p-8 max-w-5xl">{children}</main>
    </div>
  );
}
```

- [ ] **Step 9.4: Create `web/src/app/(producer)/producer/dashboard/page.tsx`**

```tsx
import { apiJson } from "@/lib/api-client";

interface MeProducerOut {
  role: "producer";
  producer_id: string;
  email: string;
  company_name: string | null;
  verified: boolean;
  agreement_accepted_at: string | null;
}

export default async function ProducerDashboard() {
  const me = await apiJson<MeProducerOut>("/me");

  let banner: { color: string; icon: string; title: string; body: string } | null = null;
  if (!me.verified) {
    banner = {
      color: "yellow",
      icon: "⏳",
      title: "Your account is awaiting verification",
      body: "An admin needs to verify your identity before you can accept the Distribution Agreement and upload films. You'll see a notification here when it's done.",
    };
  } else if (!me.agreement_accepted_at) {
    banner = {
      color: "blue",
      icon: "📄",
      title: "Distribution Agreement coming soon",
      body: "You've been verified. Agreement signing arrives in Wave 2.",
    };
  } else {
    banner = {
      color: "green",
      icon: "✓",
      title: "Account ready",
      body: "Upload, films, and payouts open up in upcoming releases.",
    };
  }

  const colorClasses: Record<string, { bg: string; border: string; titleC: string; bodyC: string }> = {
    yellow: { bg: "bg-yellow-50", border: "border-yellow-300", titleC: "text-yellow-900", bodyC: "text-yellow-800" },
    blue: { bg: "bg-blue-50", border: "border-blue-300", titleC: "text-blue-900", bodyC: "text-blue-800" },
    green: { bg: "bg-green-50", border: "border-green-300", titleC: "text-green-900", bodyC: "text-green-800" },
  };
  const c = colorClasses[banner.color];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Welcome{me.company_name ? `, ${me.company_name}` : ""}.
      </p>

      <div
        className={`rounded-lg p-4 mb-8 border ${c.bg} ${c.border}`}
        role="status"
      >
        <div className="flex gap-3">
          <div className="text-2xl">{banner.icon}</div>
          <div>
            <div className={`font-semibold mb-1 ${c.titleC}`}>{banner.title}</div>
            <p className={`text-sm ${c.bodyC}`}>{banner.body}</p>
          </div>
        </div>
      </div>

      <div className="border border-dashed rounded-lg p-12 text-center text-muted-foreground">
        <p className="text-sm mb-1">Films, licenses, revenue, geo breakdown</p>
        <p className="text-xs">Full dashboard arrives in Wave 8.</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 9.5: Create `web/src/app/api/auth/logout/route.ts`**

```typescript
import { NextResponse } from "next/server";

export async function POST() {
  const res = NextResponse.redirect(
    new URL("/", process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3000"),
    { status: 303 }
  );
  res.cookies.delete("auth_token");
  return res;
}
```

- [ ] **Step 9.6: Manually verify the producer flow**

In a browser (Windows host, hitting <http://localhost:3000>):

1. Visit <http://localhost:3000/producer/register>.
2. Register with email `dashtest@test.com`, password `ten_chars_test`, company `Dash Test`. Submit.
3. You should be redirected to `/producer/dashboard` showing the yellow "Awaiting verification" banner.
4. Click "Log out" — you should be redirected to `/`.
5. Visit <http://localhost:3000/producer/dashboard> again — you should be bounced to `/producer/login`.

If any step fails, check `docker logs alaba-web` and `docker logs alaba-backend-api`.

- [ ] **Step 9.7: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add web/src/lib/datetime.ts web/src/components/producer web/src/app/\(producer\) web/src/app/api/auth/logout
git commit -m "feat(web): producer dashboard banner states + sidebar + logout"
```

---

## Task 10: Web — admin pages (lookup, device panel, force-deactivate dialog)

**Files:**
- Create: `web/src/app/(admin)/admin/layout.tsx`
- Create: `web/src/app/(admin)/admin/dashboard/page.tsx`
- Create: `web/src/app/(admin)/admin/users/page.tsx`
- Create: `web/src/app/(admin)/admin/users/[user_id]/devices/page.tsx`
- Create: `web/src/components/admin/Sidebar.tsx`
- Create: `web/src/components/admin/DeviceTable.tsx`
- Create: `web/src/components/admin/ForceDeactivateDialog.tsx`

The admin sidebar shares structure with producer's but with different nav items. Worth a small refactor: parameterize the Sidebar component on the items list rather than duplicate.

- [ ] **Step 10.1: Add shadcn dialog component**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/web
npx shadcn@latest add dialog textarea badge --yes
```

- [ ] **Step 10.2: Refactor `Sidebar` to be reusable**

Replace `web/src/components/producer/Sidebar.tsx` with a thin wrapper, and move the generic shell into a new component.

Create `web/src/components/SidebarShell.tsx`:

```tsx
import Link from "next/link";

export interface NavItem {
  label: string;
  href: string;
  enabled: boolean;
  wave: string | null;
}

interface SidebarShellProps {
  email: string;
  title: string;
  navItems: NavItem[];
}

export default function SidebarShell({ email, title, navItems }: SidebarShellProps) {
  return (
    <aside className="w-56 border-r bg-card p-4 flex flex-col h-screen sticky top-0">
      <div className="text-lg font-bold mb-1">{title}</div>
      <div className="text-xs text-muted-foreground mb-6 truncate">{email}</div>
      <nav className="space-y-1 flex-1">
        {navItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`block px-2 py-1.5 rounded text-sm ${
              item.enabled
                ? "bg-muted/50 font-medium"
                : "text-muted-foreground pointer-events-none"
            }`}
          >
            {item.label}
            {item.wave && (
              <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                {item.wave}
              </span>
            )}
          </Link>
        ))}
      </nav>
      <form action="/api/auth/logout" method="POST">
        <button
          type="submit"
          className="w-full text-left text-xs text-muted-foreground py-2 hover:text-foreground"
        >
          Log out
        </button>
      </form>
    </aside>
  );
}
```

Replace `web/src/components/producer/Sidebar.tsx`:

```tsx
import SidebarShell, { type NavItem } from "@/components/SidebarShell";

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/producer/dashboard", enabled: true, wave: null },
  { label: "Films", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Upload", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Payouts", href: "#", enabled: false, wave: "Wave 8" },
  { label: "Settings", href: "#", enabled: false, wave: "Wave 9" },
];

export default function Sidebar({ email }: { email: string }) {
  return <SidebarShell title="Alaba" email={email} navItems={NAV_ITEMS} />;
}
```

Update `web/src/app/(producer)/producer/layout.tsx`:

Replace `import Sidebar from "@/components/producer/Sidebar";` line stays the same; only update the JSX:

```tsx
<Sidebar email={email} />
```

(remove the `role="producer"` prop since refactored Sidebar no longer takes it).

- [ ] **Step 10.3: Create `web/src/components/admin/Sidebar.tsx`**

```tsx
import SidebarShell, { type NavItem } from "@/components/SidebarShell";

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/admin/dashboard", enabled: true, wave: null },
  { label: "Review", href: "#", enabled: false, wave: "Wave 3" },
  { label: "Producers", href: "#", enabled: false, wave: "Wave 2" },
  { label: "Users", href: "/admin/users", enabled: true, wave: null },
];

export default function AdminSidebar({ email }: { email: string }) {
  return <SidebarShell title="Alaba Admin" email={email} navItems={NAV_ITEMS} />;
}
```

- [ ] **Step 10.4: Create `web/src/app/(admin)/admin/layout.tsx`**

```tsx
import { redirect } from "next/navigation";

import AdminSidebar from "@/components/admin/Sidebar";
import { getServerPrincipal } from "@/lib/auth";
import { apiJson } from "@/lib/api-client";

interface MeAdminOut {
  role: "admin";
  admin_id: string;
  email: string;
}

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const principal = await getServerPrincipal();
  if (!principal || principal.role !== "admin") redirect("/admin/login");

  let email = "";
  try {
    const me = await apiJson<MeAdminOut>("/me");
    email = me.email;
  } catch {
    redirect("/admin/login");
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <AdminSidebar email={email} />
      <main className="flex-1 p-8 max-w-5xl">{children}</main>
    </div>
  );
}
```

- [ ] **Step 10.5: Create `web/src/app/(admin)/admin/dashboard/page.tsx`**

```tsx
export default function AdminDashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Welcome to the admin console.
      </p>
      <div className="border border-dashed rounded-lg p-12 text-center text-muted-foreground">
        <p className="text-sm mb-1">Platform metrics, top films, top producers</p>
        <p className="text-xs">Full dashboard arrives in Wave 8.</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 10.6: Create `web/src/app/(admin)/admin/users/page.tsx`**

```tsx
import { redirect } from "next/navigation";

import { apiFetch } from "@/lib/api-client";

interface UserLookupOut {
  user_id: string;
  phone: string;
}

async function lookupAction(formData: FormData): Promise<void> {
  "use server";
  const phone = (formData.get("phone") as string | null)?.trim();
  if (!phone) return;
  const r = await apiFetch(`/admin/users/lookup?phone=${encodeURIComponent(phone)}`);
  if (!r.ok) {
    redirect(`/admin/users?error=not_found&q=${encodeURIComponent(phone)}`);
  }
  const body = (await r.json()) as UserLookupOut;
  redirect(`/admin/users/${body.user_id}/devices`);
}

export default async function AdminUsersPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; q?: string }>;
}) {
  const params = await searchParams;
  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold mb-1">Users</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Look up a viewer by phone to manage their authorized devices.
      </p>
      <form action={lookupAction} className="space-y-3">
        <div>
          <label htmlFor="phone" className="block text-sm font-medium mb-1">
            Phone number
          </label>
          <input
            id="phone"
            name="phone"
            type="tel"
            placeholder="+2348031234567"
            defaultValue={params.q || ""}
            className="w-full px-3 py-2 border rounded-md text-sm"
            required
          />
        </div>
        <button
          type="submit"
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium"
        >
          Search
        </button>
        {params.error === "not_found" && (
          <p className="text-sm text-red-600">
            No user found with phone {params.q}.
          </p>
        )}
      </form>
    </div>
  );
}
```

- [ ] **Step 10.7: Create `web/src/components/admin/ForceDeactivateDialog.tsx`**

```tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ForceDeactivateInput } from "@/lib/validators";

interface ForceDeactivateDialogProps {
  userId: string;
  deviceId: string;
  deviceLabel: string;
  action: (
    userId: string,
    deviceId: string,
    input: ForceDeactivateInput
  ) => Promise<{ ok: boolean; error?: string }>;
}

export default function ForceDeactivateDialog({
  userId,
  deviceId,
  deviceLabel,
  action,
}: ForceDeactivateDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [serverErr, setServerErr] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<ForceDeactivateInput>({
    resolver: zodResolver(ForceDeactivateInput),
  });

  const onSubmit = handleSubmit(async (data) => {
    setServerErr(null);
    const result = await action(userId, deviceId, data);
    if (!result.ok) {
      setServerErr(result.error ?? "Server error");
      return;
    }
    setOpen(false);
    router.refresh();
  });

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        Force deactivate
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Force-deactivate device?</DialogTitle>
            <DialogDescription>
              <strong>{deviceLabel}</strong> will be deactivated immediately,
              bypassing the user's 90-day cooldown. Downloaded films on this device
              will continue to play until the device is reset, but the user cannot
              re-authenticate on it.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-3">
            <div className="space-y-1">
              <Label htmlFor="reason">
                Reason for the audit log <span className="text-red-600">*</span>
              </Label>
              <Textarea
                id="reason"
                placeholder="e.g. User reported phone stolen via support ticket #234"
                rows={3}
                {...register("reason")}
              />
              {errors.reason && (
                <p className="text-xs text-red-600">{errors.reason.message}</p>
              )}
              {serverErr && <p className="text-xs text-red-600">{serverErr}</p>}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="destructive" disabled={isSubmitting}>
                {isSubmitting ? "Deactivating..." : "Force deactivate"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

- [ ] **Step 10.8: Create `web/src/components/admin/DeviceTable.tsx`**

```tsx
import { Badge } from "@/components/ui/badge";

import ForceDeactivateDialog from "@/components/admin/ForceDeactivateDialog";
import { formatWAT } from "@/lib/datetime";
import { ForceDeactivateInput } from "@/lib/validators";

export interface DeviceRow {
  id: string;
  display_name: string | null;
  model: string | null;
  platform: string;
  activated_at: string;
  last_seen_at: string | null;
  deactivated_at: string | null;
}

interface DeviceTableProps {
  userId: string;
  devices: DeviceRow[];
  action: (
    userId: string,
    deviceId: string,
    input: ForceDeactivateInput
  ) => Promise<{ ok: boolean; error?: string }>;
}

export default function DeviceTable({ userId, devices, action }: DeviceTableProps) {
  return (
    <table className="w-full border-collapse bg-card border rounded-lg overflow-hidden">
      <thead>
        <tr className="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
          <th className="text-left p-3">Device</th>
          <th className="text-left p-3">Status</th>
          <th className="text-left p-3">Activated</th>
          <th className="text-left p-3">Last seen</th>
          <th className="text-right p-3"></th>
        </tr>
      </thead>
      <tbody className="text-sm">
        {devices.map((d) => {
          const isActive = d.deactivated_at === null;
          return (
            <tr key={d.id} className="border-t">
              <td className="p-3">
                <div className="font-medium">
                  {d.display_name ?? d.model ?? "Unknown device"}
                </div>
                <div className="text-xs text-muted-foreground font-mono">
                  {d.platform} · {d.id.slice(0, 8)}
                </div>
              </td>
              <td className="p-3">
                {isActive ? (
                  <Badge variant="default">Active</Badge>
                ) : (
                  <Badge variant="secondary">
                    Deactivated {d.deactivated_at && formatWAT(d.deactivated_at)}
                  </Badge>
                )}
              </td>
              <td className="p-3 text-muted-foreground">
                {formatWAT(d.activated_at)}
              </td>
              <td className="p-3 text-muted-foreground">
                {d.last_seen_at ? formatWAT(d.last_seen_at) : "—"}
              </td>
              <td className="p-3 text-right">
                {isActive ? (
                  <ForceDeactivateDialog
                    userId={userId}
                    deviceId={d.id}
                    deviceLabel={d.display_name ?? d.model ?? "this device"}
                    action={action}
                  />
                ) : (
                  <span className="text-xs text-muted-foreground">—</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 10.9: Create `web/src/app/(admin)/admin/users/[user_id]/devices/page.tsx`**

```tsx
import Link from "next/link";

import DeviceTable, { type DeviceRow } from "@/components/admin/DeviceTable";
import { apiFetch, apiJson } from "@/lib/api-client";
import { ForceDeactivateInput } from "@/lib/validators";

interface DeviceListOut {
  devices: DeviceRow[];
  cap: number;
  active_count: number;
  deactivation_cooldown_unlock_at: string | null;
}

async function forceDeactivateAction(
  userId: string,
  deviceId: string,
  input: ForceDeactivateInput
): Promise<{ ok: boolean; error?: string }> {
  "use server";
  const r = await apiFetch(
    `/admin/users/${userId}/devices/${deviceId}/deactivate`,
    { method: "POST", body: JSON.stringify(input) }
  );
  if (!r.ok) {
    return { ok: false, error: `Server error (${r.status})` };
  }
  return { ok: true };
}

export default async function AdminUserDevicesPage({
  params,
}: {
  params: Promise<{ user_id: string }>;
}) {
  const { user_id } = await params;
  const data = await apiJson<DeviceListOut>(`/admin/users/${user_id}/devices`);

  return (
    <div>
      <div className="text-xs text-muted-foreground mb-2">
        <Link href="/admin/users" className="hover:text-foreground">
          ← Users
        </Link>
      </div>
      <h1 className="text-2xl font-bold mb-1">Devices for user {user_id.slice(0, 8)}…</h1>
      <p className="text-sm text-muted-foreground mb-6">
        {data.active_count} of {data.cap} device slots in use.
      </p>
      <DeviceTable
        userId={user_id}
        devices={data.devices}
        action={forceDeactivateAction}
      />
      <p className="text-xs text-muted-foreground mt-4">
        Force-deactivating bypasses the 90-day user cooldown. Action is logged to{" "}
        <code>admin_actions</code> with the reason you provide.
      </p>
    </div>
  );
}
```

- [ ] **Step 10.10: Manually verify the admin flow end-to-end**

1. Log in at <http://localhost:3000/admin/login> with `admin@alaba.test` / `ten_chars_admin` (created in Task 7).
2. Should land on `/admin/dashboard`.
3. Navigate to `/admin/users`.
4. To test the lookup, create a viewer via the OTP flow. Easiest way: a manual curl:
   ```bash
   curl -X POST http://localhost:8000/auth/otp/request -H "Content-Type: application/json" -d '{"phone": "+2348031234555"}'
   # watch the OTP in: docker logs alaba-backend-api 2>&1 | grep OTP | tail -1
   # extract code, then:
   curl -X POST http://localhost:8000/auth/otp/verify -H "Content-Type: application/json" \
     -d '{"phone": "+2348031234555", "code": "<the_code>", "device_id": "manual-test-1", "display_name": "Manual Test Phone"}'
   ```
5. Back in the browser at `/admin/users`, enter `+2348031234555`. Submit. Should land on the devices page.
6. Click "Force deactivate" on the active device row. Enter a reason. Submit. Page refreshes; row now shows "Deactivated" badge.
7. Verify in psql: `docker exec alaba-postgres psql -U alaba -d alaba -c "SELECT action, reason FROM admin_actions ORDER BY created_at DESC LIMIT 5;"` — should show the force_deactivate_device entry.

- [ ] **Step 10.11: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add web/src/components/SidebarShell.tsx web/src/components/producer/Sidebar.tsx web/src/components/admin web/src/app/\(admin\) web/src/app/\(producer\)/producer/layout.tsx web/src/components/ui
git commit -m "feat(web): admin pages — dashboard, user lookup, device panel with force-deactivate"
```

---

## Task 11: Android — TokenStore, DeviceIdStore, interceptors, AuthEventBus

**Files:**
- Modify: `android/app/build.gradle.kts` (add `androidx.security:security-crypto`, test deps)
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/auth/TokenStore.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/auth/DeviceIdStore.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/auth/AuthInterceptor.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/auth/AuthErrorInterceptor.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/auth/AuthEventBus.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/di/AuthModule.kt`
- Modify: `android/app/src/main/java/com/orbanforest/alaba/di/NetworkModule.kt`
- Create: `android/app/src/test/java/com/orbanforest/alaba/data/auth/AuthInterceptorTest.kt`

- [ ] **Step 11.1: Update `android/app/build.gradle.kts` dependencies**

Add inside the `dependencies { ... }` block (after existing entries):

```kotlin
    // EncryptedSharedPreferences
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // Coroutines for tests
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
    testImplementation("io.mockk:mockk:1.13.13")
    testImplementation("app.cash.turbine:turbine:1.2.0")
```

- [ ] **Step 11.2: Create `TokenStore.kt`**

```kotlin
package com.orbanforest.alaba.data.auth

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TokenStore @Inject constructor(@ApplicationContext context: Context) {
    private val prefs by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context, "alaba_auth", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun saveJwt(jwt: String, userDeviceId: String) {
        prefs.edit()
            .putString(KEY_JWT, jwt)
            .putString(KEY_USER_DEVICE_ID, userDeviceId)
            .apply()
    }

    fun readJwt(): String? = prefs.getString(KEY_JWT, null)
    fun readUserDeviceId(): String? = prefs.getString(KEY_USER_DEVICE_ID, null)
    fun hasJwt(): Boolean = readJwt() != null

    fun clear() {
        prefs.edit().remove(KEY_JWT).remove(KEY_USER_DEVICE_ID).apply()
    }

    private companion object {
        const val KEY_JWT = "jwt"
        const val KEY_USER_DEVICE_ID = "user_device_id"
    }
}
```

- [ ] **Step 11.3: Create `DeviceIdStore.kt`**

```kotlin
package com.orbanforest.alaba.data.auth

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeviceIdStore @Inject constructor(@ApplicationContext context: Context) {
    private val prefs by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context, "alaba_device", masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun getOrCreate(): String {
        val existing = prefs.getString(KEY, null)
        if (existing != null) return existing
        val fresh = UUID.randomUUID().toString()
        prefs.edit().putString(KEY, fresh).apply()
        return fresh
    }

    private companion object {
        const val KEY = "device_id"
    }
}
```

- [ ] **Step 11.4: Create `AuthEventBus.kt`**

```kotlin
package com.orbanforest.alaba.data.auth

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import javax.inject.Inject
import javax.inject.Singleton

sealed class AuthEvent {
    data object DeviceDeactivated : AuthEvent()
    data object TokenExpired : AuthEvent()
}

@Singleton
class AuthEventBus @Inject constructor() {
    private val _events = MutableSharedFlow<AuthEvent>(extraBufferCapacity = 1)
    val events: SharedFlow<AuthEvent> = _events

    fun emit(event: AuthEvent) {
        _events.tryEmit(event)
    }
}
```

- [ ] **Step 11.5: Create `AuthInterceptor.kt`**

```kotlin
package com.orbanforest.alaba.data.auth

import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthInterceptor @Inject constructor(
    private val tokenStore: TokenStore,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val token = tokenStore.readJwt()
        val finalRequest = if (token != null) {
            request.newBuilder().addHeader("Authorization", "Bearer $token").build()
        } else {
            request
        }
        return chain.proceed(finalRequest)
    }
}
```

- [ ] **Step 11.6: Create `AuthErrorInterceptor.kt`**

```kotlin
package com.orbanforest.alaba.data.auth

import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthErrorInterceptor @Inject constructor(
    private val authEventBus: AuthEventBus,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val response = chain.proceed(chain.request())
        when (response.code) {
            401 -> authEventBus.emit(AuthEvent.TokenExpired)
            403 -> {
                val body = response.peekBody(4096L).string()
                if (body.contains("\"device_deactivated\"")) {
                    authEventBus.emit(AuthEvent.DeviceDeactivated)
                }
            }
        }
        return response
    }
}
```

- [ ] **Step 11.7: Create `AuthModule.kt`**

```kotlin
package com.orbanforest.alaba.di

import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@Module
@InstallIn(SingletonComponent::class)
object AuthModule {
    // TokenStore, DeviceIdStore, AuthEventBus, AuthInterceptor, AuthErrorInterceptor
    // are all @Singleton with @Inject constructors — Hilt provides them automatically.
    // This module exists for future bindings if needed.
}
```

- [ ] **Step 11.8: Update `NetworkModule.kt` to register interceptors**

Replace `android/app/src/main/java/com/orbanforest/alaba/di/NetworkModule.kt` with:

```kotlin
package com.orbanforest.alaba.di

import com.orbanforest.alaba.BuildConfig
import com.orbanforest.alaba.data.api.HealthApi
import com.orbanforest.alaba.data.auth.AuthErrorInterceptor
import com.orbanforest.alaba.data.auth.AuthInterceptor
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideMoshi(): Moshi =
        Moshi.Builder().add(KotlinJsonAdapterFactory()).build()

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        authErrorInterceptor: AuthErrorInterceptor,
    ): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        return OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(authErrorInterceptor)
            .addInterceptor(logging)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(client: OkHttpClient, moshi: Moshi): Retrofit =
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()

    @Provides
    @Singleton
    fun provideHealthApi(retrofit: Retrofit): HealthApi =
        retrofit.create(HealthApi::class.java)
}
```

- [ ] **Step 11.9: Create the AuthInterceptor unit test**

Create `android/app/src/test/java/com/orbanforest/alaba/data/auth/AuthInterceptorTest.kt`:

```kotlin
package com.orbanforest.alaba.data.auth

import io.mockk.every
import io.mockk.mockk
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class AuthInterceptorTest {
    @Test
    fun `attaches Authorization header when token present`() {
        val server = MockWebServer().apply { start(); enqueue(MockResponse().setBody("ok")) }
        val tokenStore = mockk<TokenStore>()
        every { tokenStore.readJwt() } returns "my-jwt-123"
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenStore))
            .build()
        val request = Request.Builder().url(server.url("/")).build()
        client.newCall(request).execute().use { /* drop body */ }
        val sent = server.takeRequest()
        assertEquals("Bearer my-jwt-123", sent.getHeader("Authorization"))
        server.shutdown()
    }

    @Test
    fun `no header when token null`() {
        val server = MockWebServer().apply { start(); enqueue(MockResponse().setBody("ok")) }
        val tokenStore = mockk<TokenStore>()
        every { tokenStore.readJwt() } returns null
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenStore))
            .build()
        val request = Request.Builder().url(server.url("/")).build()
        client.newCall(request).execute().use { }
        val sent = server.takeRequest()
        assertNull(sent.getHeader("Authorization"))
        server.shutdown()
    }
}
```

Note: this requires `mockwebserver`. Add to `android/app/build.gradle.kts` under dependencies:

```kotlin
    testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
```

- [ ] **Step 11.10: Build the project and run the unit test**

The engineer should open Android Studio. After Gradle sync:

1. Build → Make Project (verifies everything compiles).
2. Run the unit test: right-click `AuthInterceptorTest` → "Run 'AuthInterceptorTest'". Both tests should pass.

Alternatively from the command line (if gradle wrapper is available):

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/android
./gradlew :app:testDebugUnitTest --tests "com.orbanforest.alaba.data.auth.AuthInterceptorTest"
```

Expected: 2 tests pass.

- [ ] **Step 11.11: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add android/app/build.gradle.kts android/app/src/main/java/com/orbanforest/alaba/di/NetworkModule.kt android/app/src/main/java/com/orbanforest/alaba/di/AuthModule.kt android/app/src/main/java/com/orbanforest/alaba/data/auth android/app/src/test
git commit -m "feat(android): TokenStore, DeviceIdStore, interceptors, AuthEventBus"
```

---

## Task 12: Android — AuthRepository + DevicesRepository + DTOs + AlabaError

**Files:**
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/api/AuthApi.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/api/DevicesApi.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/api/MeApi.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/api/dto/*.kt` (multiple)
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/auth/AlabaError.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/auth/AuthRepository.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/device/DevicesRepository.kt`
- Update Hilt providers in `NetworkModule.kt` to provide new APIs

- [ ] **Step 12.1: Create the DTO files**

Create `android/app/src/main/java/com/orbanforest/alaba/data/api/dto/OtpRequestBody.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class OtpRequestBody(val phone: String)
```

Create `OtpRequestResponse.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class OtpRequestResponse(val sent: Boolean)
```

Create `OtpVerifyBody.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class OtpVerifyBody(
    val phone: String,
    val code: String? = null,
    @field:com.squareup.moshi.Json(name = "verify_ticket") val verifyTicket: String? = null,
    @field:com.squareup.moshi.Json(name = "device_id") val deviceId: String,
    @field:com.squareup.moshi.Json(name = "display_name") val displayName: String? = null,
    val model: String? = null,
    val platform: String = "android",
    @field:com.squareup.moshi.Json(name = "deactivate_device_id") val deactivateDeviceId: String? = null,
)
```

Create `OtpVerifyResponse.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class OtpVerifyResponse(
    val jwt: String,
    @field:com.squareup.moshi.Json(name = "user_device_id") val userDeviceId: String,
    @field:com.squareup.moshi.Json(name = "expires_at") val expiresAt: String,
)
```

Create `OtpVerify409Body.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ActiveDeviceSummary(
    val id: String,
    @field:com.squareup.moshi.Json(name = "display_name") val displayName: String?,
    val model: String?,
    val platform: String,
    @field:com.squareup.moshi.Json(name = "activated_at") val activatedAt: String,
    @field:com.squareup.moshi.Json(name = "last_seen_at") val lastSeenAt: String?,
)

@JsonClass(generateAdapter = true)
data class OtpVerify409Body(
    val error: String,
    @field:com.squareup.moshi.Json(name = "active_devices") val activeDevices: List<ActiveDeviceSummary>,
    @field:com.squareup.moshi.Json(name = "verify_ticket") val verifyTicket: String,
)
```

Create `DeviceDto.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class DeviceDto(
    val id: String,
    @field:com.squareup.moshi.Json(name = "display_name") val displayName: String?,
    val model: String?,
    val platform: String,
    @field:com.squareup.moshi.Json(name = "activated_at") val activatedAt: String,
    @field:com.squareup.moshi.Json(name = "deactivated_at") val deactivatedAt: String?,
    @field:com.squareup.moshi.Json(name = "last_seen_at") val lastSeenAt: String?,
    @field:com.squareup.moshi.Json(name = "is_current") val isCurrent: Boolean,
)

@JsonClass(generateAdapter = true)
data class DeviceListResponse(
    val devices: List<DeviceDto>,
    val cap: Int,
    @field:com.squareup.moshi.Json(name = "active_count") val activeCount: Int,
    @field:com.squareup.moshi.Json(name = "deactivation_cooldown_unlock_at") val cooldownUnlockAt: String?,
)
```

Create `MeViewerDto.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class MeViewerDto(
    val role: String,
    @field:com.squareup.moshi.Json(name = "user_id") val userId: String,
    val phone: String,
    @field:com.squareup.moshi.Json(name = "user_device_id") val userDeviceId: String,
    @field:com.squareup.moshi.Json(name = "user_device_display_name") val deviceDisplayName: String?,
    @field:com.squareup.moshi.Json(name = "user_device_model") val deviceModel: String?,
    @field:com.squareup.moshi.Json(name = "user_device_last_seen_at") val deviceLastSeenAt: String?,
)
```

Create `ErrorResponse.kt`:

```kotlin
package com.orbanforest.alaba.data.api.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ErrorResponse(val detail: ErrorDetail)

@JsonClass(generateAdapter = true)
data class ErrorDetail(
    val error: String? = null,
    val reason: String? = null,
    @field:com.squareup.moshi.Json(name = "attempts_remaining") val attemptsRemaining: Int? = null,
    @field:com.squareup.moshi.Json(name = "unlock_at") val unlockAt: String? = null,
)
```

- [ ] **Step 12.2: Create the Retrofit API interfaces**

Create `AuthApi.kt`:

```kotlin
package com.orbanforest.alaba.data.api

import com.orbanforest.alaba.data.api.dto.OtpRequestBody
import com.orbanforest.alaba.data.api.dto.OtpRequestResponse
import com.orbanforest.alaba.data.api.dto.OtpVerifyBody
import com.orbanforest.alaba.data.api.dto.OtpVerifyResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApi {
    @POST("/auth/otp/request")
    suspend fun requestOtp(@Body body: OtpRequestBody): Response<OtpRequestResponse>

    @POST("/auth/otp/verify")
    suspend fun verifyOtp(@Body body: OtpVerifyBody): Response<OtpVerifyResponse>
}
```

Create `DevicesApi.kt`:

```kotlin
package com.orbanforest.alaba.data.api

import com.orbanforest.alaba.data.api.dto.DeviceListResponse
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface DevicesApi {
    @GET("/devices")
    suspend fun listDevices(): Response<DeviceListResponse>

    @POST("/devices/{id}/deactivate")
    suspend fun deactivateDevice(@Path("id") deviceId: String): Response<Unit>
}
```

Create `MeApi.kt`:

```kotlin
package com.orbanforest.alaba.data.api

import com.orbanforest.alaba.data.api.dto.MeViewerDto
import retrofit2.Response
import retrofit2.http.GET

interface MeApi {
    @GET("/me")
    suspend fun me(): Response<MeViewerDto>
}
```

- [ ] **Step 12.3: Register the new APIs in NetworkModule**

Add to `NetworkModule.kt` (after the existing `provideHealthApi`):

```kotlin
    @Provides
    @Singleton
    fun provideAuthApi(retrofit: Retrofit): AuthApi = retrofit.create(AuthApi::class.java)

    @Provides
    @Singleton
    fun provideDevicesApi(retrofit: Retrofit): DevicesApi = retrofit.create(DevicesApi::class.java)

    @Provides
    @Singleton
    fun provideMeApi(retrofit: Retrofit): MeApi = retrofit.create(MeApi::class.java)
```

Add the corresponding imports:

```kotlin
import com.orbanforest.alaba.data.api.AuthApi
import com.orbanforest.alaba.data.api.DevicesApi
import com.orbanforest.alaba.data.api.MeApi
```

- [ ] **Step 12.4: Create `AlabaError.kt`**

```kotlin
package com.orbanforest.alaba.data.auth

import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary

sealed class AlabaError(message: String) : Exception(message) {
    data class NetworkError(val cause: Throwable?) : AlabaError("network_error")
    data object InvalidCode : AlabaError("invalid_code")
    data class InvalidCodeWithAttempts(val attemptsRemaining: Int) : AlabaError("invalid_code")
    data object CodeExpired : AlabaError("code_expired")
    data object AttemptsExhausted : AlabaError("attempts_exhausted")
    data object TooManyOtpRequests : AlabaError("too_many_otp_requests")
    data class DeviceCapReached(
        val activeDevices: List<ActiveDeviceSummary>,
        val verifyTicket: String,
    ) : AlabaError("device_cap_reached")
    data class CooldownActive(val unlockAt: String?) : AlabaError("cooldown_active")
    data object InvalidVerifyTicket : AlabaError("invalid_verify_ticket")
    data object DeviceNotFound : AlabaError("device_not_found")
    data object DeviceDeactivated : AlabaError("device_deactivated")
    data class Unknown(val statusCode: Int, val body: String) : AlabaError("unknown")
}
```

- [ ] **Step 12.5: Create `AuthRepository.kt`**

```kotlin
package com.orbanforest.alaba.data.auth

import android.os.Build
import com.orbanforest.alaba.data.api.AuthApi
import com.orbanforest.alaba.data.api.dto.OtpRequestBody
import com.orbanforest.alaba.data.api.dto.OtpVerify409Body
import com.orbanforest.alaba.data.api.dto.OtpVerifyBody
import com.orbanforest.alaba.data.api.dto.OtpVerifyResponse
import com.squareup.moshi.Moshi
import javax.inject.Inject
import javax.inject.Singleton

sealed class AuthResult {
    data class Success(val jwt: String, val userDeviceId: String) : AuthResult()
    data class Failure(val error: AlabaError) : AuthResult()
}

@Singleton
class AuthRepository @Inject constructor(
    private val authApi: AuthApi,
    private val tokenStore: TokenStore,
    private val deviceIdStore: DeviceIdStore,
    private val moshi: Moshi,
) {
    suspend fun requestOtp(phone: String): Result<Unit> = try {
        val r = authApi.requestOtp(OtpRequestBody(phone))
        if (r.isSuccessful) Result.success(Unit)
        else Result.failure(mapError(r.code(), r.errorBody()?.string()))
    } catch (t: Throwable) {
        Result.failure(AlabaError.NetworkError(t))
    }

    suspend fun verifyOtp(phone: String, code: String): AuthResult {
        val body = OtpVerifyBody(
            phone = phone,
            code = code,
            deviceId = deviceIdStore.getOrCreate(),
            displayName = defaultDisplayName(),
            model = Build.MODEL,
        )
        return verifyOtpCommon(body)
    }

    suspend fun verifyOtpWithTicket(
        phone: String,
        verifyTicket: String,
        deactivateDeviceId: String,
    ): AuthResult {
        val body = OtpVerifyBody(
            phone = phone,
            verifyTicket = verifyTicket,
            deviceId = deviceIdStore.getOrCreate(),
            displayName = defaultDisplayName(),
            model = Build.MODEL,
            deactivateDeviceId = deactivateDeviceId,
        )
        return verifyOtpCommon(body)
    }

    private suspend fun verifyOtpCommon(body: OtpVerifyBody): AuthResult = try {
        val r = authApi.verifyOtp(body)
        if (r.isSuccessful) {
            val resp: OtpVerifyResponse = r.body()!!
            tokenStore.saveJwt(resp.jwt, resp.userDeviceId)
            AuthResult.Success(resp.jwt, resp.userDeviceId)
        } else {
            AuthResult.Failure(mapError(r.code(), r.errorBody()?.string()))
        }
    } catch (t: Throwable) {
        AuthResult.Failure(AlabaError.NetworkError(t))
    }

    private fun mapError(code: Int, body: String?): AlabaError {
        val detail = body?.let { parseDetail(it) }
        return when {
            code == 409 && detail?.error == "device_cap_reached" -> {
                val parsed = body?.let { parse409(it) }
                if (parsed != null) {
                    AlabaError.DeviceCapReached(parsed.activeDevices, parsed.verifyTicket)
                } else {
                    AlabaError.Unknown(code, body ?: "")
                }
            }
            code == 429 && detail?.error == "too_many_otp_requests" -> AlabaError.TooManyOtpRequests
            code == 429 && detail?.error == "attempts_exhausted" -> AlabaError.AttemptsExhausted
            code == 429 && detail?.error == "cooldown_active" -> AlabaError.CooldownActive(detail.unlockAt)
            code == 401 && detail?.error == "code_expired" -> AlabaError.CodeExpired
            code == 401 && detail?.error == "invalid_code" -> {
                val attempts = detail.attemptsRemaining
                if (attempts != null) AlabaError.InvalidCodeWithAttempts(attempts)
                else AlabaError.InvalidCode
            }
            code == 401 && detail?.error == "invalid_verify_ticket" -> AlabaError.InvalidVerifyTicket
            code == 404 && detail?.error?.startsWith("device_not_found") == true -> AlabaError.DeviceNotFound
            code == 403 && detail?.reason == "device_deactivated" -> AlabaError.DeviceDeactivated
            else -> AlabaError.Unknown(code, body ?: "")
        }
    }

    private fun parseDetail(body: String): com.orbanforest.alaba.data.api.dto.ErrorDetail? {
        return try {
            val adapter = moshi.adapter(com.orbanforest.alaba.data.api.dto.ErrorResponse::class.java)
            adapter.fromJson(body)?.detail
        } catch (t: Throwable) {
            null
        }
    }

    private fun parse409(body: String): OtpVerify409Body? {
        return try {
            // 409 wraps the same body inside "detail"
            val adapter = moshi.adapter(Map::class.java)
            val outer = adapter.fromJson(body) ?: return null
            val detail = outer["detail"] ?: return null
            val detailJson = moshi.adapter(Any::class.java).toJson(detail)
            val parser = moshi.adapter(OtpVerify409Body::class.java)
            parser.fromJson(detailJson)
        } catch (t: Throwable) {
            null
        }
    }

    private fun defaultDisplayName(): String = "${Build.BRAND} ${Build.MODEL}".trim()
}
```

- [ ] **Step 12.6: Create `DevicesRepository.kt`**

```kotlin
package com.orbanforest.alaba.data.device

import com.orbanforest.alaba.data.api.DevicesApi
import com.orbanforest.alaba.data.api.dto.DeviceListResponse
import com.orbanforest.alaba.data.auth.AlabaError
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DevicesRepository @Inject constructor(
    private val devicesApi: DevicesApi,
) {
    suspend fun list(): Result<DeviceListResponse> = try {
        val r = devicesApi.listDevices()
        if (r.isSuccessful) Result.success(r.body()!!)
        else Result.failure(AlabaError.Unknown(r.code(), r.errorBody()?.string() ?: ""))
    } catch (t: Throwable) {
        Result.failure(AlabaError.NetworkError(t))
    }

    suspend fun deactivate(deviceId: String): Result<Unit> = try {
        val r = devicesApi.deactivateDevice(deviceId)
        when {
            r.isSuccessful -> Result.success(Unit)
            r.code() == 404 -> Result.failure(AlabaError.DeviceNotFound)
            r.code() == 429 -> Result.failure(AlabaError.CooldownActive(unlockAt = null))
            else -> Result.failure(AlabaError.Unknown(r.code(), r.errorBody()?.string() ?: ""))
        }
    } catch (t: Throwable) {
        Result.failure(AlabaError.NetworkError(t))
    }
}
```

- [ ] **Step 12.7: Build the project**

In Android Studio: Build → Make Project. Expected: compiles without error.

- [ ] **Step 12.8: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add android/app/src/main/java/com/orbanforest/alaba/data
git commit -m "feat(android): AuthRepository + DevicesRepository + DTOs + AlabaError"
```

---

## Task 13: Android — PhoneEntry + OtpEntry screens with Compose Navigation

**Files:**
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/theme/Color.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/theme/Theme.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/theme/Type.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/components/OtpCodeInput.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/auth/PhoneEntryViewModel.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/auth/PhoneEntryScreen.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/auth/OtpEntryViewModel.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/auth/OtpEntryScreen.kt`
- Add Compose Navigation dep to `app/build.gradle.kts`
- Create: `android/app/src/test/java/com/orbanforest/alaba/ui/auth/PhoneEntryViewModelTest.kt`
- Create: `android/app/src/test/java/com/orbanforest/alaba/ui/auth/OtpEntryViewModelTest.kt`

- [ ] **Step 13.1: Add Compose Navigation dependency**

Append to `dependencies { ... }` in `android/app/build.gradle.kts`:

```kotlin
    implementation("androidx.navigation:navigation-compose:2.8.5")
```

- [ ] **Step 13.2: Create theme files**

`ui/theme/Color.kt`:

```kotlin
package com.orbanforest.alaba.ui.theme

import androidx.compose.ui.graphics.Color

val AlabaPrimary = Color(0xFF0F172A)
val AlabaPrimaryContent = Color(0xFFFAFAFA)
val AlabaSurface = Color(0xFFFFFFFF)
val AlabaSurfaceVariant = Color(0xFFF4F4F5)
val AlabaOnSurface = Color(0xFF09090B)
val AlabaMuted = Color(0xFF71717A)
val AlabaBorder = Color(0xFFE4E4E7)
val AlabaError = Color(0xFFDC2626)
```

`ui/theme/Type.kt`:

```kotlin
package com.orbanforest.alaba.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val AlabaTypography = Typography(
    headlineMedium = TextStyle(fontSize = 28.sp, fontWeight = FontWeight.Bold),
    headlineSmall = TextStyle(fontSize = 22.sp, fontWeight = FontWeight.Bold),
    titleLarge = TextStyle(fontSize = 18.sp, fontWeight = FontWeight.SemiBold),
    bodyLarge = TextStyle(fontSize = 15.sp),
    bodyMedium = TextStyle(fontSize = 14.sp),
    bodySmall = TextStyle(fontSize = 12.sp, color = AlabaMuted),
    labelMedium = TextStyle(fontSize = 13.sp, fontWeight = FontWeight.Medium),
    labelSmall = TextStyle(fontSize = 11.sp),
)
```

`ui/theme/Theme.kt`:

```kotlin
package com.orbanforest.alaba.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val AlabaLightColors = lightColorScheme(
    primary = AlabaPrimary,
    onPrimary = AlabaPrimaryContent,
    surface = AlabaSurface,
    surfaceVariant = AlabaSurfaceVariant,
    onSurface = AlabaOnSurface,
    onSurfaceVariant = AlabaMuted,
    outline = AlabaBorder,
    error = AlabaError,
)

@Composable
fun AlabaTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = AlabaLightColors, typography = AlabaTypography, content = content)
}
```

- [ ] **Step 13.3: Create `OtpCodeInput.kt`**

```kotlin
package com.orbanforest.alaba.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun OtpCodeInput(
    value: String,
    onValueChange: (String) -> Unit,
    length: Int = 6,
    modifier: Modifier = Modifier,
) {
    val focusRequester = remember { FocusRequester() }
    LaunchedEffect(Unit) { focusRequester.requestFocus() }

    Box(modifier = modifier) {
        // Invisible TextField captures input
        BasicTextField(
            value = value,
            onValueChange = { new ->
                val digits = new.filter { it.isDigit() }.take(length)
                onValueChange(digits)
            },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
            textStyle = TextStyle(color = Color.Transparent),
            modifier = Modifier.size(0.dp).focusRequester(focusRequester),
            singleLine = true,
        )
        // Visual: 6 boxed digits
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            for (i in 0 until length) {
                val digit = value.getOrNull(i)?.toString() ?: ""
                val borderColor = if (digit.isNotEmpty())
                    MaterialTheme.colorScheme.primary
                else MaterialTheme.colorScheme.outline
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .aspectRatio(1f)
                        .border(width = 1.5.dp, color = borderColor, shape = RoundedCornerShape(8.dp)),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        text = digit,
                        style = MaterialTheme.typography.headlineSmall.copy(
                            fontSize = 20.sp,
                            fontWeight = FontWeight.SemiBold,
                        ),
                    )
                }
            }
        }
    }
}
```

- [ ] **Step 13.4: Create `PhoneEntryViewModel.kt`**

```kotlin
package com.orbanforest.alaba.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class PhoneEntryUiState {
    data class Ready(val phoneInput: String = "", val errorMessage: String? = null) : PhoneEntryUiState()
    data object Submitting : PhoneEntryUiState()
}

sealed class PhoneEntryEvent {
    data class CodeSent(val phone: String) : PhoneEntryEvent()
}

@HiltViewModel
class PhoneEntryViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<PhoneEntryUiState>(PhoneEntryUiState.Ready())
    val state: StateFlow<PhoneEntryUiState> = _state.asStateFlow()

    private val _events = Channel<PhoneEntryEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    fun onPhoneChanged(s: String) {
        _state.value = PhoneEntryUiState.Ready(phoneInput = s.filter { it.isDigit() }.take(11))
    }

    fun submit() {
        val current = (_state.value as? PhoneEntryUiState.Ready) ?: return
        val phone = current.phoneInput
        if (phone.length < 10) {
            _state.value = current.copy(errorMessage = "Enter a valid Nigerian phone number.")
            return
        }
        val fullPhone = "+234" + phone.removePrefix("0")
        _state.value = PhoneEntryUiState.Submitting
        viewModelScope.launch {
            val r = authRepository.requestOtp(fullPhone)
            if (r.isSuccess) {
                _events.send(PhoneEntryEvent.CodeSent(fullPhone))
                _state.value = PhoneEntryUiState.Ready()
            } else {
                val err = r.exceptionOrNull()
                val msg = when (err) {
                    is AlabaError.TooManyOtpRequests -> "Too many requests. Try again in 15 minutes."
                    is AlabaError.NetworkError -> "Network error. Check your connection."
                    else -> "Something went wrong. Try again."
                }
                _state.value = PhoneEntryUiState.Ready(phoneInput = phone, errorMessage = msg)
            }
        }
    }
}
```

- [ ] **Step 13.5: Create `PhoneEntryScreen.kt`**

```kotlin
package com.orbanforest.alaba.ui.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.compose.foundation.text.KeyboardOptions
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun PhoneEntryScreen(
    onCodeSent: (phone: String) -> Unit,
    viewModel: PhoneEntryViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            if (event is PhoneEntryEvent.CodeSent) onCodeSent(event.phone)
        }
    }
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Top,
    ) {
        Spacer(Modifier.height(48.dp))
        Text("Welcome to Alaba", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Enter your Nigerian phone number and we'll text you a 6-digit code.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(40.dp))

        Text("Phone number", style = MaterialTheme.typography.labelMedium)
        Spacer(Modifier.height(6.dp))

        val phoneText = (state as? PhoneEntryUiState.Ready)?.phoneInput ?: ""

        OutlinedTextField(
            value = phoneText,
            onValueChange = viewModel::onPhoneChanged,
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            leadingIcon = { Text("🇳🇬 +234", modifier = Modifier.padding(start = 8.dp)) },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
            placeholder = { Text("803 123 4567") },
            enabled = state is PhoneEntryUiState.Ready,
        )

        val errorMsg = (state as? PhoneEntryUiState.Ready)?.errorMessage
        if (errorMsg != null) {
            Spacer(Modifier.height(6.dp))
            Text(errorMsg, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(24.dp))
        Button(
            onClick = viewModel::submit,
            modifier = Modifier.fillMaxWidth(),
            enabled = state is PhoneEntryUiState.Ready,
        ) {
            Text(if (state is PhoneEntryUiState.Submitting) "Sending..." else "Send code")
        }

        Spacer(Modifier.height(24.dp))
        Text(
            "By continuing you agree to our Terms and Privacy Policy.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
    }
}
```

- [ ] **Step 13.6: Create `OtpEntryViewModel.kt`**

```kotlin
package com.orbanforest.alaba.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthRepository
import com.orbanforest.alaba.data.auth.AuthResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class OtpEntryUiState {
    data class Ready(val codeInput: String = "", val errorMessage: String? = null) : OtpEntryUiState()
    data object Submitting : OtpEntryUiState()
}

sealed class OtpEntryEvent {
    data object VerifiedSignedIn : OtpEntryEvent()
    data class DeviceCapReached(
        val activeDevices: List<ActiveDeviceSummary>,
        val verifyTicket: String,
    ) : OtpEntryEvent()
}

@HiltViewModel
class OtpEntryViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<OtpEntryUiState>(OtpEntryUiState.Ready())
    val state: StateFlow<OtpEntryUiState> = _state.asStateFlow()

    private val _events = Channel<OtpEntryEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    fun onCodeChanged(s: String) {
        _state.value = OtpEntryUiState.Ready(codeInput = s)
        if (s.length == 6) submit("")
    }

    fun submit(phone: String) {
        val current = (_state.value as? OtpEntryUiState.Ready) ?: return
        if (current.codeInput.length != 6) {
            _state.value = current.copy(errorMessage = "Enter all 6 digits.")
            return
        }
        // The phone is held by the screen and passed in to submit when the
        // automatic 6-digit submission fires. Use the screen-provided phone
        // (PhoneEntry sets it via nav args).
        _state.value = OtpEntryUiState.Submitting
        viewModelScope.launch {
            val result = authRepository.verifyOtp(phone, current.codeInput)
            handleResult(result, current.codeInput)
        }
    }

    private suspend fun handleResult(result: AuthResult, code: String) {
        when (result) {
            is AuthResult.Success -> {
                _events.send(OtpEntryEvent.VerifiedSignedIn)
            }
            is AuthResult.Failure -> when (val err = result.error) {
                is AlabaError.DeviceCapReached -> {
                    _events.send(OtpEntryEvent.DeviceCapReached(err.activeDevices, err.verifyTicket))
                }
                is AlabaError.InvalidCodeWithAttempts -> {
                    _state.value = OtpEntryUiState.Ready(
                        codeInput = code,
                        errorMessage = "Wrong code. ${err.attemptsRemaining} attempts left.",
                    )
                }
                AlabaError.CodeExpired -> {
                    _state.value = OtpEntryUiState.Ready(codeInput = code, errorMessage = "Code expired.")
                }
                AlabaError.AttemptsExhausted -> {
                    _state.value = OtpEntryUiState.Ready(codeInput = code, errorMessage = "Too many attempts. Request a new code.")
                }
                else -> {
                    _state.value = OtpEntryUiState.Ready(codeInput = code, errorMessage = "Something went wrong. Try again.")
                }
            }
        }
    }
}
```

- [ ] **Step 13.7: Create `OtpEntryScreen.kt`**

```kotlin
package com.orbanforest.alaba.ui.auth

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.ui.components.OtpCodeInput

@Composable
fun OtpEntryScreen(
    phone: String,
    onSignedIn: () -> Unit,
    onDeviceCapReached: (devices: List<ActiveDeviceSummary>, ticket: String, phone: String) -> Unit,
    onBack: () -> Unit,
    viewModel: OtpEntryViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                OtpEntryEvent.VerifiedSignedIn -> onSignedIn()
                is OtpEntryEvent.DeviceCapReached -> onDeviceCapReached(event.activeDevices, event.verifyTicket, phone)
            }
        }
    }

    // Auto-submit when 6 digits entered.
    LaunchedEffect(state) {
        val codeInput = (state as? OtpEntryUiState.Ready)?.codeInput ?: ""
        if (codeInput.length == 6) viewModel.submit(phone)
    }

    Column(modifier = Modifier.fillMaxSize().padding(24.dp)) {
        Spacer(Modifier.height(8.dp))
        TextButton(onClick = onBack) { Text("← Back") }
        Spacer(Modifier.height(16.dp))
        Text("Check your messages", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(6.dp))
        Text(
            "We texted a 6-digit code to $phone.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(32.dp))

        val codeInput = (state as? OtpEntryUiState.Ready)?.codeInput ?: ""
        OtpCodeInput(
            value = codeInput,
            onValueChange = viewModel::onCodeChanged,
            modifier = Modifier.fillMaxWidth(),
        )

        val errorMsg = (state as? OtpEntryUiState.Ready)?.errorMessage
        if (errorMsg != null) {
            Spacer(Modifier.height(8.dp))
            Text(errorMsg, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(24.dp))
        Button(
            onClick = { viewModel.submit(phone) },
            modifier = Modifier.fillMaxWidth(),
            enabled = state is OtpEntryUiState.Ready,
        ) {
            Text(if (state is OtpEntryUiState.Submitting) "Verifying..." else "Verify")
        }
    }
}
```

- [ ] **Step 13.8: Write the ViewModel unit tests**

`android/app/src/test/java/com/orbanforest/alaba/ui/auth/PhoneEntryViewModelTest.kt`:

```kotlin
package com.orbanforest.alaba.ui.auth

import app.cash.turbine.test
import com.orbanforest.alaba.data.auth.AuthRepository
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class PhoneEntryViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }
    @After fun tearDown() { Dispatchers.resetMain() }

    @Test fun `valid Nigerian phone submits and emits CodeSent`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        coEvery { repo.requestOtp(any()) } returns Result.success(Unit)
        val vm = PhoneEntryViewModel(repo)
        vm.onPhoneChanged("08031234567")
        vm.events.test {
            vm.submit()
            dispatcher.scheduler.advanceUntilIdle()
            val event = awaitItem()
            assertTrue(event is PhoneEntryEvent.CodeSent)
            assertEquals("+2348031234567", (event as PhoneEntryEvent.CodeSent).phone)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test fun `short phone shows validation error`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        val vm = PhoneEntryViewModel(repo)
        vm.onPhoneChanged("123")
        vm.submit()
        val state = vm.state.value
        assertTrue(state is PhoneEntryUiState.Ready)
        assertTrue((state as PhoneEntryUiState.Ready).errorMessage != null)
    }
}
```

`android/app/src/test/java/com/orbanforest/alaba/ui/auth/OtpEntryViewModelTest.kt`:

```kotlin
package com.orbanforest.alaba.ui.auth

import app.cash.turbine.test
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthRepository
import com.orbanforest.alaba.data.auth.AuthResult
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class OtpEntryViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }
    @After fun tearDown() { Dispatchers.resetMain() }

    @Test fun `successful verify emits VerifiedSignedIn`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        coEvery { repo.verifyOtp(any(), any()) } returns AuthResult.Success("jwt", "ud-1")
        val vm = OtpEntryViewModel(repo)
        vm.onCodeChanged("123456")
        vm.events.test {
            vm.submit("+2348031234567")
            dispatcher.scheduler.advanceUntilIdle()
            val event = awaitItem()
            assertTrue(event is OtpEntryEvent.VerifiedSignedIn)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test fun `device cap reached emits DeviceCapReached`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        val devices = listOf(ActiveDeviceSummary("d1", "name", "model", "android", "2026-01-01T00:00:00Z", null))
        coEvery { repo.verifyOtp(any(), any()) } returns AuthResult.Failure(
            AlabaError.DeviceCapReached(devices, "ticket-xyz"),
        )
        val vm = OtpEntryViewModel(repo)
        vm.onCodeChanged("123456")
        vm.events.test {
            vm.submit("+2348031234567")
            dispatcher.scheduler.advanceUntilIdle()
            val event = awaitItem()
            assertTrue(event is OtpEntryEvent.DeviceCapReached)
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test fun `wrong code shows attempts remaining`() = runTest(dispatcher) {
        val repo = mockk<AuthRepository>()
        coEvery { repo.verifyOtp(any(), any()) } returns AuthResult.Failure(
            AlabaError.InvalidCodeWithAttempts(attemptsRemaining = 3),
        )
        val vm = OtpEntryViewModel(repo)
        vm.onCodeChanged("123456")
        vm.submit("+2348031234567")
        dispatcher.scheduler.advanceUntilIdle()
        val state = vm.state.value
        assertTrue(state is OtpEntryUiState.Ready)
        assertTrue((state as OtpEntryUiState.Ready).errorMessage!!.contains("3"))
    }
}
```

- [ ] **Step 13.9: Build + run unit tests**

In Android Studio (or via gradlew if available):

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba/android
./gradlew :app:testDebugUnitTest
```

Expected: all auth ViewModel + interceptor tests pass (5 tests total in this task).

- [ ] **Step 13.10: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add android/app/build.gradle.kts android/app/src/main/java/com/orbanforest/alaba/ui/theme android/app/src/main/java/com/orbanforest/alaba/ui/components/OtpCodeInput.kt android/app/src/main/java/com/orbanforest/alaba/ui/auth android/app/src/test/java/com/orbanforest/alaba/ui/auth
git commit -m "feat(android): PhoneEntry + OtpEntry screens + ViewModels + theme + unit tests"
```

---

## Task 14: Android — DeviceCapReached + DeviceDeactivated screens

**Files:**
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/components/DeviceCard.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/auth/DeviceCapReachedViewModel.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/auth/DeviceCapReachedScreen.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/auth/DeviceDeactivatedScreen.kt`

- [ ] **Step 14.1: Create `DeviceCard.kt`**

```kotlin
package com.orbanforest.alaba.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun DeviceCard(
    title: String,
    subtitle: String? = null,
    selected: Boolean = false,
    onClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    val border = if (selected) BorderStroke(2.dp, MaterialTheme.colorScheme.primary)
        else BorderStroke(1.dp, MaterialTheme.colorScheme.outline)
    val bg = if (selected) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface
    androidx.compose.material3.OutlinedCard(
        modifier = modifier.fillMaxWidth().then(
            if (onClick != null) Modifier.clickable { onClick() } else Modifier
        ),
        border = border,
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            if (subtitle != null) {
                Spacer(Modifier.height(4.dp))
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}
```

- [ ] **Step 14.2: Create `DeviceCapReachedViewModel.kt`**

```kotlin
package com.orbanforest.alaba.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthRepository
import com.orbanforest.alaba.data.auth.AuthResult
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DeviceCapState(
    val devices: List<ActiveDeviceSummary>,
    val selectedDeviceId: String? = null,
    val errorMessage: String? = null,
    val submitting: Boolean = false,
)

sealed class DeviceCapEvent {
    data object SignedIn : DeviceCapEvent()
    data object Cancel : DeviceCapEvent()
}

@HiltViewModel
class DeviceCapReachedViewModel @Inject constructor(
    private val authRepository: AuthRepository,
) : ViewModel() {
    private val _state = MutableStateFlow<DeviceCapState?>(null)
    val state: StateFlow<DeviceCapState?> = _state.asStateFlow()

    private val _events = Channel<DeviceCapEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    private var phone: String = ""
    private var ticket: String = ""

    fun initialize(devices: List<ActiveDeviceSummary>, ticket: String, phone: String) {
        this.phone = phone
        this.ticket = ticket
        _state.value = DeviceCapState(devices = devices)
    }

    fun selectDevice(id: String) {
        val current = _state.value ?: return
        _state.value = current.copy(selectedDeviceId = id, errorMessage = null)
    }

    fun confirm() {
        val current = _state.value ?: return
        val deviceId = current.selectedDeviceId ?: return
        _state.value = current.copy(submitting = true)
        viewModelScope.launch {
            val result = authRepository.verifyOtpWithTicket(phone, ticket, deviceId)
            when (result) {
                is AuthResult.Success -> _events.send(DeviceCapEvent.SignedIn)
                is AuthResult.Failure -> {
                    val msg = when (result.error) {
                        is AlabaError.InvalidVerifyTicket -> "Session expired. Request a new code."
                        is AlabaError.CooldownActive -> "You're in a 90-day cooldown. Try again later."
                        is AlabaError.NetworkError -> "Network error. Try again."
                        else -> "Something went wrong. Try again."
                    }
                    _state.value = current.copy(submitting = false, errorMessage = msg)
                }
            }
        }
    }

    fun cancel() {
        viewModelScope.launch { _events.send(DeviceCapEvent.Cancel) }
    }
}
```

- [ ] **Step 14.3: Create `DeviceCapReachedScreen.kt`**

```kotlin
package com.orbanforest.alaba.ui.auth

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.ui.components.DeviceCard

@Composable
fun DeviceCapReachedScreen(
    devices: List<ActiveDeviceSummary>,
    verifyTicket: String,
    phone: String,
    onSignedIn: () -> Unit,
    onCancel: () -> Unit,
    viewModel: DeviceCapReachedViewModel = hiltViewModel(),
) {
    LaunchedEffect(Unit) {
        viewModel.initialize(devices, verifyTicket, phone)
        viewModel.events.collect { event ->
            when (event) {
                DeviceCapEvent.SignedIn -> onSignedIn()
                DeviceCapEvent.Cancel -> onCancel()
            }
        }
    }
    val state by viewModel.state.collectAsStateWithLifecycle()
    val s = state ?: return

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp).verticalScroll(rememberScrollState()),
    ) {
        Spacer(Modifier.height(8.dp))
        TextButton(onClick = onCancel) { Text("← Back") }
        Spacer(Modifier.height(16.dp))
        Text("You're at your 2-device limit", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        Text(
            "Pick a device to deactivate. You'll lose access to downloaded films on it. You can only deactivate one device every 90 days.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(24.dp))

        s.devices.forEach { dev ->
            DeviceCard(
                title = dev.displayName ?: dev.model ?: "Unknown device",
                subtitle = "Activated ${dev.activatedAt.take(10)}",
                selected = (dev.id == s.selectedDeviceId),
                onClick = { viewModel.selectDevice(dev.id) },
                modifier = Modifier.padding(bottom = 8.dp),
            )
        }

        if (s.errorMessage != null) {
            Spacer(Modifier.height(8.dp))
            Text(s.errorMessage, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(20.dp))
        Button(
            onClick = viewModel::confirm,
            modifier = Modifier.fillMaxWidth(),
            enabled = s.selectedDeviceId != null && !s.submitting,
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
        ) {
            Text(if (s.submitting) "Deactivating..." else "Deactivate & continue")
        }
        Spacer(Modifier.height(8.dp))
        TextButton(onClick = viewModel::cancel, modifier = Modifier.fillMaxWidth()) {
            Text("Cancel")
        }
    }
}
```

- [ ] **Step 14.4: Create `DeviceDeactivatedScreen.kt`**

```kotlin
package com.orbanforest.alaba.ui.auth

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

@Composable
fun DeviceDeactivatedScreen(onSignInAgain: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(64.dp))
        Text("🔒", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(16.dp))
        Text("This device is signed out", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(16.dp))
        Text(
            "Someone (probably you, on another device) deactivated this device. Your downloaded films have been removed from this phone.",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(12.dp))
        Text(
            "Sign in again to add this device back — it will use one of your 2 device slots.",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(32.dp))
        Button(onClick = onSignInAgain, modifier = Modifier.fillMaxWidth()) {
            Text("Sign in again")
        }
    }
}
```

- [ ] **Step 14.5: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add android/app/src/main/java/com/orbanforest/alaba/ui/components/DeviceCard.kt android/app/src/main/java/com/orbanforest/alaba/ui/auth/DeviceCapReachedScreen.kt android/app/src/main/java/com/orbanforest/alaba/ui/auth/DeviceCapReachedViewModel.kt android/app/src/main/java/com/orbanforest/alaba/ui/auth/DeviceDeactivatedScreen.kt
git commit -m "feat(android): DeviceCapReached + DeviceDeactivated screens"
```

---

## Task 15: Android — Settings + Devices screens + SignedInPlaceholder

**Files:**
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/components/ThisDevicePill.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/components/ConfirmBottomSheet.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/home/SignedInPlaceholderScreen.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/home/SignedInPlaceholderViewModel.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/settings/SettingsScreen.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/settings/DevicesScreen.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/settings/DevicesViewModel.kt`

- [ ] **Step 15.1: Create `ThisDevicePill.kt`**

```kotlin
package com.orbanforest.alaba.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ThisDevicePill(modifier: Modifier = Modifier) {
    Text(
        text = "THIS DEVICE",
        modifier = modifier
            .clip(RoundedCornerShape(999.dp))
            .background(MaterialTheme.colorScheme.primary)
            .padding(horizontal = 7.dp, vertical = 2.dp),
        color = MaterialTheme.colorScheme.onPrimary,
        fontSize = 9.sp,
        fontWeight = FontWeight.SemiBold,
    )
}
```

- [ ] **Step 15.2: Create `ConfirmBottomSheet.kt`**

```kotlin
package com.orbanforest.alaba.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConfirmBottomSheet(
    title: String,
    body: String,
    confirmLabel: String,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
    destructive: Boolean = false,
) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(modifier = Modifier.fillMaxWidth().padding(24.dp).padding(bottom = 24.dp)) {
            Text(title, style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(8.dp))
            Text(body, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(20.dp))
            Button(
                onClick = onConfirm,
                modifier = Modifier.fillMaxWidth(),
                colors = if (destructive) ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                    else ButtonDefaults.buttonColors(),
            ) { Text(confirmLabel) }
            Spacer(Modifier.height(8.dp))
            TextButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) { Text("Cancel") }
        }
    }
}
```

- [ ] **Step 15.3: Create `SignedInPlaceholderViewModel.kt`**

```kotlin
package com.orbanforest.alaba.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.api.MeApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SignedInState(
    val phone: String? = null,
    val deviceLabel: String? = null,
    val loading: Boolean = true,
)

@HiltViewModel
class SignedInPlaceholderViewModel @Inject constructor(
    private val meApi: MeApi,
) : ViewModel() {
    private val _state = MutableStateFlow(SignedInState())
    val state: StateFlow<SignedInState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            try {
                val r = meApi.me()
                if (r.isSuccessful) {
                    val me = r.body()!!
                    _state.value = SignedInState(
                        phone = me.phone,
                        deviceLabel = me.deviceDisplayName ?: me.deviceModel,
                        loading = false,
                    )
                } else {
                    _state.value = SignedInState(loading = false)
                }
            } catch (t: Throwable) {
                _state.value = SignedInState(loading = false)
            }
        }
    }
}
```

- [ ] **Step 15.4: Create `SignedInPlaceholderScreen.kt`**

```kotlin
package com.orbanforest.alaba.ui.home

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun SignedInPlaceholderScreen(
    onManageDevices: () -> Unit,
    viewModel: SignedInPlaceholderViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(60.dp))
        Text("✅", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(16.dp))
        Text("You're in", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        Text(
            "Catalog, films, and playback arrive in upcoming releases.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(40.dp))
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(8.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .padding(20.dp),
        ) {
            Text("SIGNED IN AS", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(6.dp))
            Text(state.phone ?: "—", style = MaterialTheme.typography.bodyLarge)
            Spacer(Modifier.height(4.dp))
            Text("This device: ${state.deviceLabel ?: "Unknown"}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(Modifier.height(24.dp))
        OutlinedButton(onClick = onManageDevices) { Text("Manage devices") }
    }
}
```

- [ ] **Step 15.5: Create `DevicesViewModel.kt`**

```kotlin
package com.orbanforest.alaba.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.orbanforest.alaba.data.api.dto.DeviceDto
import com.orbanforest.alaba.data.auth.AlabaError
import com.orbanforest.alaba.data.auth.AuthEvent
import com.orbanforest.alaba.data.auth.AuthEventBus
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.data.device.DevicesRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DevicesUiState(
    val devices: List<DeviceDto> = emptyList(),
    val cap: Int = 2,
    val activeCount: Int = 0,
    val cooldownUnlockAt: String? = null,
    val loading: Boolean = true,
    val error: String? = null,
    val confirmDeactivateId: String? = null,
)

@HiltViewModel
class DevicesViewModel @Inject constructor(
    private val devicesRepository: DevicesRepository,
    private val authEventBus: AuthEventBus,
    private val tokenStore: TokenStore,
) : ViewModel() {
    private val _state = MutableStateFlow(DevicesUiState())
    val state: StateFlow<DevicesUiState> = _state.asStateFlow()

    init { load() }

    fun load() {
        viewModelScope.launch {
            val r = devicesRepository.list()
            r.fold(
                onSuccess = { body ->
                    _state.value = DevicesUiState(
                        devices = body.devices,
                        cap = body.cap,
                        activeCount = body.activeCount,
                        cooldownUnlockAt = body.cooldownUnlockAt,
                        loading = false,
                    )
                },
                onFailure = { t ->
                    _state.value = _state.value.copy(loading = false, error = t.message ?: "Error")
                },
            )
        }
    }

    fun askConfirmDeactivate(deviceId: String) {
        _state.value = _state.value.copy(confirmDeactivateId = deviceId)
    }

    fun cancelConfirm() {
        _state.value = _state.value.copy(confirmDeactivateId = null)
    }

    fun confirmDeactivate(currentUserDeviceId: String?) {
        val id = _state.value.confirmDeactivateId ?: return
        viewModelScope.launch {
            val r = devicesRepository.deactivate(id)
            r.fold(
                onSuccess = {
                    if (id == currentUserDeviceId) {
                        // Trigger global "this device signed out" flow
                        tokenStore.clear()
                        authEventBus.emit(AuthEvent.DeviceDeactivated)
                    } else {
                        // Just refresh the list
                        _state.value = _state.value.copy(confirmDeactivateId = null)
                        load()
                    }
                },
                onFailure = { t ->
                    val msg = when (t) {
                        is AlabaError.CooldownActive -> "Cooldown active. Try again later."
                        is AlabaError.DeviceNotFound -> "Device not found."
                        else -> t.message ?: "Error"
                    }
                    _state.value = _state.value.copy(confirmDeactivateId = null, error = msg)
                },
            )
        }
    }
}
```

- [ ] **Step 15.6: Create `DevicesScreen.kt`**

```kotlin
package com.orbanforest.alaba.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.ui.components.ConfirmBottomSheet
import com.orbanforest.alaba.ui.components.ThisDevicePill

@Composable
fun DevicesScreen(
    currentUserDeviceId: String?,
    onBack: () -> Unit,
    viewModel: DevicesViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Column(modifier = Modifier.fillMaxSize().padding(24.dp).verticalScroll(rememberScrollState())) {
        TextButton(onClick = onBack) { Text("← Settings") }
        Spacer(Modifier.height(8.dp))
        Text("Devices", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(6.dp))
        Text(
            "You're using ${state.activeCount} of ${state.cap} device slots.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        if (state.cooldownUnlockAt != null) {
            Spacer(Modifier.height(16.dp))
            Surface(
                color = MaterialTheme.colorScheme.tertiaryContainer.copy(alpha = 0.3f),
                shape = MaterialTheme.shapes.small,
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("Cooldown active", style = MaterialTheme.typography.labelMedium)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "You can deactivate another device after ${state.cooldownUnlockAt!!.take(10)}.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        state.devices.filter { it.deactivatedAt == null }.forEach { d ->
            DeviceRow(
                title = d.displayName ?: d.model ?: "Unknown",
                subtitle = "Added ${d.activatedAt.take(10)}",
                isCurrent = d.isCurrent,
                cooldownActive = state.cooldownUnlockAt != null,
                onDeactivate = { viewModel.askConfirmDeactivate(d.id) },
            )
            Spacer(Modifier.height(8.dp))
        }

        if (state.devices.any { it.deactivatedAt != null }) {
            Spacer(Modifier.height(16.dp))
            Text("DEACTIVATED", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(8.dp))
            state.devices.filter { it.deactivatedAt != null }.forEach { d ->
                DeviceRow(
                    title = d.displayName ?: d.model ?: "Unknown",
                    subtitle = "Deactivated ${d.deactivatedAt?.take(10)}",
                    isCurrent = false,
                    cooldownActive = true,  // can't deactivate an already-deactivated device
                    onDeactivate = null,
                )
                Spacer(Modifier.height(8.dp))
            }
        }

        if (state.error != null) {
            Spacer(Modifier.height(8.dp))
            Text(state.error!!, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
        }
    }

    val confirmId = state.confirmDeactivateId
    if (confirmId != null) {
        val dev = state.devices.find { it.id == confirmId } ?: return
        val isCurrent = dev.id == currentUserDeviceId
        ConfirmBottomSheet(
            title = if (isCurrent) "Deactivate this device?" else "Deactivate ${dev.displayName ?: "device"}?",
            body = if (isCurrent)
                "You'll be signed out and lose access to all downloaded films on this phone. You can re-authorize this device in 90 days."
            else
                "Films downloaded on that device will continue to play offline but it can't connect to Alaba anymore. You can reactivate it in 90 days.",
            confirmLabel = if (isCurrent) "Deactivate and sign out" else "Deactivate",
            destructive = isCurrent,
            onConfirm = { viewModel.confirmDeactivate(currentUserDeviceId) },
            onDismiss = viewModel::cancelConfirm,
        )
    }
}

@Composable
private fun DeviceRow(
    title: String,
    subtitle: String,
    isCurrent: Boolean,
    cooldownActive: Boolean,
    onDeactivate: (() -> Unit)?,
) {
    OutlinedCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.bodyLarge)
                if (isCurrent) {
                    Spacer(Modifier.width(8.dp))
                    ThisDevicePill()
                }
            }
            Spacer(Modifier.height(2.dp))
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            if (onDeactivate != null) {
                Spacer(Modifier.height(12.dp))
                OutlinedButton(
                    onClick = onDeactivate,
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !cooldownActive,
                ) {
                    Text(if (cooldownActive) "Deactivate (locked)" else "Deactivate")
                }
            }
        }
    }
}
```

- [ ] **Step 15.7: Create `SettingsScreen.kt`**

```kotlin
package com.orbanforest.alaba.ui.settings

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.orbanforest.alaba.ui.home.SignedInPlaceholderViewModel

@Composable
fun SettingsScreen(
    onDevices: () -> Unit,
    onLogout: () -> Unit,
    viewModel: SignedInPlaceholderViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Column(modifier = Modifier.fillMaxSize()) {
        Spacer(Modifier.height(16.dp))
        Text("Settings", style = MaterialTheme.typography.headlineSmall, modifier = Modifier.padding(horizontal = 20.dp))
        HorizontalDivider(modifier = Modifier.padding(top = 16.dp))

        Column(modifier = Modifier.padding(horizontal = 20.dp, vertical = 18.dp)) {
            Text("ACCOUNT", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(8.dp))
            Text(state.phone ?: "—", style = MaterialTheme.typography.bodyLarge)
        }
        HorizontalDivider()

        SettingsRow(label = "Devices", subtitle = "Manage authorized devices", onClick = onDevices)
        HorizontalDivider()
        SettingsRow(label = "Terms and Conditions", subtitle = null, onClick = null)
        HorizontalDivider()
        SettingsRow(label = "Privacy Policy", subtitle = null, onClick = null)

        Spacer(Modifier.height(32.dp))
        OutlinedButton(
            onClick = onLogout,
            modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error),
        ) { Text("Log out") }
    }
}

@Composable
private fun SettingsRow(label: String, subtitle: String?, onClick: (() -> Unit)?) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.bodyLarge)
            if (subtitle != null) {
                Spacer(Modifier.height(2.dp))
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        if (onClick != null) Text("›", color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
```

- [ ] **Step 15.8: Build the project**

Open Android Studio → Build → Make Project. Expected: compiles without error.

- [ ] **Step 15.9: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add android/app/src/main/java/com/orbanforest/alaba/ui/components/ThisDevicePill.kt android/app/src/main/java/com/orbanforest/alaba/ui/components/ConfirmBottomSheet.kt android/app/src/main/java/com/orbanforest/alaba/ui/home android/app/src/main/java/com/orbanforest/alaba/ui/settings
git commit -m "feat(android): Settings + Devices + SignedInPlaceholder screens"
```

---

## Task 16: Android — MainActivity nav glue + AuthEventBus wiring

**Files:**
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/nav/AlabaNavHost.kt`
- Modify: `android/app/src/main/java/com/orbanforest/alaba/MainActivity.kt`

- [ ] **Step 16.1: Create `AlabaNavHost.kt`**

```kotlin
package com.orbanforest.alaba.ui.nav

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.orbanforest.alaba.data.api.dto.ActiveDeviceSummary
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.ui.auth.DeviceCapReachedScreen
import com.orbanforest.alaba.ui.auth.DeviceDeactivatedScreen
import com.orbanforest.alaba.ui.auth.OtpEntryScreen
import com.orbanforest.alaba.ui.auth.PhoneEntryScreen
import com.orbanforest.alaba.ui.home.SignedInPlaceholderScreen
import com.orbanforest.alaba.ui.settings.DevicesScreen
import com.orbanforest.alaba.ui.settings.SettingsScreen

// In-memory transient state for the device-cap flow. The 409 payload
// is too large to put into nav args; we hand it off via this holder.
object DeviceCapHandoff {
    var devices: List<ActiveDeviceSummary>? = null
    var verifyTicket: String? = null
    var phone: String? = null

    fun consume(): Triple<List<ActiveDeviceSummary>, String, String>? {
        val d = devices; val t = verifyTicket; val p = phone
        return if (d != null && t != null && p != null) {
            devices = null; verifyTicket = null; phone = null
            Triple(d, t, p)
        } else null
    }
}

@Composable
fun AlabaNavHost(
    navController: NavHostController,
    startDestination: String,
    tokenStore: TokenStore,
) {
    NavHost(navController = navController, startDestination = startDestination) {
        composable("phone_entry") {
            PhoneEntryScreen(
                onCodeSent = { phone ->
                    navController.navigate("otp_entry/${phone.removePrefix("+").trim()}")
                }
            )
        }
        composable(
            "otp_entry/{phoneE164}",
            arguments = listOf(navArgument("phoneE164") { type = NavType.StringType }),
        ) { backStack ->
            val phone = "+" + (backStack.arguments?.getString("phoneE164") ?: "")
            OtpEntryScreen(
                phone = phone,
                onSignedIn = {
                    navController.navigate("signed_in") {
                        popUpTo("phone_entry") { inclusive = true }
                    }
                },
                onDeviceCapReached = { devices, ticket, phoneArg ->
                    DeviceCapHandoff.devices = devices
                    DeviceCapHandoff.verifyTicket = ticket
                    DeviceCapHandoff.phone = phoneArg
                    navController.navigate("device_cap_reached")
                },
                onBack = { navController.popBackStack() },
            )
        }
        composable("device_cap_reached") {
            val handoff = remember { DeviceCapHandoff.consume() }
            if (handoff == null) {
                LaunchedEffect(Unit) { navController.popBackStack() }
            } else {
                val (devices, ticket, phone) = handoff
                DeviceCapReachedScreen(
                    devices = devices,
                    verifyTicket = ticket,
                    phone = phone,
                    onSignedIn = {
                        navController.navigate("signed_in") {
                            popUpTo("phone_entry") { inclusive = true }
                        }
                    },
                    onCancel = { navController.popBackStack("phone_entry", inclusive = false) },
                )
            }
        }
        composable("device_deactivated") {
            DeviceDeactivatedScreen(onSignInAgain = {
                navController.navigate("phone_entry") { popUpTo(0) }
            })
        }
        composable("signed_in") {
            SignedInPlaceholderScreen(onManageDevices = { navController.navigate("settings") })
        }
        composable("settings") {
            SettingsScreen(
                onDevices = { navController.navigate("devices") },
                onLogout = {
                    tokenStore.clear()
                    navController.navigate("phone_entry") { popUpTo(0) }
                },
            )
        }
        composable("devices") {
            DevicesScreen(
                currentUserDeviceId = tokenStore.readUserDeviceId(),
                onBack = { navController.popBackStack() },
            )
        }
    }
}
```

- [ ] **Step 16.2: Replace `MainActivity.kt`**

```kotlin
package com.orbanforest.alaba

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.Surface
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.fillMaxSize
import androidx.navigation.compose.rememberNavController
import com.orbanforest.alaba.data.auth.AuthEvent
import com.orbanforest.alaba.data.auth.AuthEventBus
import com.orbanforest.alaba.data.auth.TokenStore
import com.orbanforest.alaba.ui.nav.AlabaNavHost
import com.orbanforest.alaba.ui.theme.AlabaTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var authEventBus: AuthEventBus
    @Inject lateinit var tokenStore: TokenStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AlabaTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    val navController = rememberNavController()
                    val startDestination = if (tokenStore.hasJwt()) "signed_in" else "phone_entry"

                    LaunchedEffect(Unit) {
                        authEventBus.events.collect { event ->
                            when (event) {
                                AuthEvent.DeviceDeactivated -> {
                                    tokenStore.clear()
                                    navController.navigate("device_deactivated") { popUpTo(0) }
                                }
                                AuthEvent.TokenExpired -> {
                                    tokenStore.clear()
                                    navController.navigate("phone_entry") { popUpTo(0) }
                                }
                            }
                        }
                    }

                    AlabaNavHost(navController, startDestination, tokenStore)
                }
            }
        }
    }
}
```

- [ ] **Step 16.3: Build + run on emulator**

In Android Studio:

1. Build → Make Project. Expected: compiles clean.
2. Start an emulator (API 34+ recommended). Make sure the backend stack is running (`make up`).
3. Click Run → 'app'. The app should launch and display PhoneEntry.
4. Enter `8031234567` (or any 10-digit Nigerian number). Tap "Send code".
5. Watch the logs: `docker logs alaba-backend-api 2>&1 | grep OTP | tail -1`. Extract the 6-digit code.
6. Enter the code in the app. Should auto-submit and navigate to SignedIn.
7. Tap "Manage devices" → reach Devices screen. Should show one device with the THIS DEVICE pill.

- [ ] **Step 16.4: Commit**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add android/app/src/main/java/com/orbanforest/alaba/ui/nav/AlabaNavHost.kt android/app/src/main/java/com/orbanforest/alaba/MainActivity.kt
git commit -m "feat(android): MainActivity nav glue + AlabaNavHost + AuthEventBus wiring"
```

---

## Task 17: Wave 1 smoke test + tag

**Files:**
- Create: `docs/test-checklist.md`

No new code. Just verify the full Wave 1 flow end-to-end. Some steps require Android Studio + an emulator (or two) — those are manual.

- [ ] **Step 17.1: Create `docs/test-checklist.md`**

```markdown
# Alaba — Manual Test Checklist

Run before tagging each wave's completion. Catches things automated tests miss.

## Wave 1

### Backend-only (curl)

- [ ] `POST /auth/otp/request {phone: "+2348031234901"}` returns 200, code logged
- [ ] 6th request within 15min returns 429 `too_many_otp_requests`
- [ ] `POST /auth/otp/verify` with right code returns 200 with JWT
- [ ] `POST /auth/otp/verify` with wrong code returns 401 with `attempts_remaining: 4`
- [ ] After 5 wrong codes, 6th attempt returns 429 `attempts_exhausted`
- [ ] Producer register / login: `POST /auth/producer/{register,login}` work
- [ ] Admin login: `POST /auth/admin/login` works after `make make-admin email=...`
- [ ] `GET /me` returns role-appropriate body for each JWT type
- [ ] `GET /devices` requires viewer JWT, returns the user's devices

### Web (browser, http://localhost:3000)

- [ ] Producer register at `/producer/register` → lands on `/producer/dashboard` with yellow "Awaiting verification" banner
- [ ] Producer login at `/producer/login` with wrong password shows error
- [ ] Logout button clears cookie; visiting `/producer/dashboard` redirects to login
- [ ] Admin login → admin dashboard
- [ ] Admin `/admin/users` lookup with valid phone → device panel
- [ ] Force-deactivate dialog with empty reason → form validation error
- [ ] Force-deactivate with valid reason → device row updates to "Deactivated"; `admin_actions` row in DB

### Android (emulator)

- [ ] App launches at PhoneEntry
- [ ] Enter phone → "Send code" → log shows OTP → enter code → reach SignedIn
- [ ] Settings → Devices shows current device with THIS DEVICE pill
- [ ] Wipe app data (Settings → Apps → Alaba → Clear data) → relaunch → PhoneEntry again

### Multi-device end-to-end (two emulators OR emulator + real device)

- [ ] Device A: sign in with phone X
- [ ] Device B (different `device_id`): sign in with phone X → SignedIn (both devices active)
- [ ] Device C (third device_id): sign in with phone X → DeviceCapReached screen
- [ ] Pick one of A/B to deactivate → Mode B verify-ticket → C signs in successfully
- [ ] The deactivated device's next API call (e.g., open Settings → Devices) returns 403 → bounces to "This device is signed out"

### Cooldown

- [ ] On Device A (active), open Settings → Devices → Deactivate "Device B" → 90-day cooldown begins
- [ ] Immediately try to deactivate "Device C" (if a third exists) or sign in a third device → returns 429 cooldown_active with unlock date

### Admin force-deactivate path

- [ ] On Device A, sign in. Then via web admin, force-deactivate Device A
- [ ] Device A's next request returns 403 → app navigates to "This device is signed out"
- [ ] Verify `admin_actions` row exists in DB with the reason text
```

- [ ] **Step 17.2: Stop and restart everything for a clean state check**

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
make down
make up
make migrate
```

Expected: all 8 services healthy; `alembic upgrade head` either no-op or applies cleanly.

- [ ] **Step 17.3: Backend automated test pass**

```bash
make test
```

Expected: all Wave 0 + Wave 1 backend tests pass (~110+). No regressions.

- [ ] **Step 17.4: Backend curl smoke (the items above in the checklist)**

Run a few quick curl checks:

```bash
# OTP request
curl -sX POST http://localhost:8000/auth/otp/request -H "Content-Type: application/json" -d '{"phone": "+2348031234950"}' | python3 -m json.tool

# Read the logged code
sleep 1
CODE=$(docker logs alaba-backend-api 2>&1 | grep "2348031234950" | tail -1 | awk -F"→" '{print $2}' | tr -d ' ')
echo "OTP code = $CODE"

# Verify
curl -sX POST http://localhost:8000/auth/otp/verify -H "Content-Type: application/json" \
  -d "{\"phone\": \"+2348031234950\", \"code\": \"$CODE\", \"device_id\": \"smoke-test-device-1\", \"display_name\": \"Smoke Test\"}" \
  | python3 -m json.tool

# Make-admin (if not done yet)
make make-admin email=admin@alaba.test  # password: ten_chars_admin

# Admin login
curl -sX POST http://localhost:8000/auth/admin/login -H "Content-Type: application/json" \
  -d '{"email": "admin@alaba.test", "password": "ten_chars_admin"}' | python3 -m json.tool
```

All should return success. Note the JWTs.

- [ ] **Step 17.5: Web flow manual test**

Open browser:

1. <http://localhost:3000/producer/register> — register and verify yellow banner.
2. <http://localhost:3000/admin/login> — log in as admin@alaba.test / ten_chars_admin.
3. <http://localhost:3000/admin/users> — search +2348031234950, reach devices page, force-deactivate (with reason ≥5 chars).

- [ ] **Step 17.6: Android flow manual test**

(See checklist for the full multi-device scenario. Requires real or emulator devices.)

- [ ] **Step 17.7: Tag wave-1-complete**

Only run this after every checklist item passes:

```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git add docs/test-checklist.md
git commit -m "docs: test checklist for Wave 1"
git tag -a wave-1-complete -m "Wave 1 (auth + multi-device) complete: all backend tests pass, multi-device E2E verified"
git log --oneline | head -25
git tag -l
```

Expected: tag listed.

- [ ] **Step 17.8: Push (optional)**

If the remote is configured:

```bash
git push
git push origin wave-1-complete
```

---

## Wave 1 success criteria recap

You should now be able to:

1. `make up && make migrate` brings up the stack with both migrations applied.
2. `make make-admin email=admin@alaba.test` creates the bootstrap admin.
3. <http://localhost:3000/producer/register> registers a producer that immediately lands on the dashboard with the yellow unverified banner.
4. <http://localhost:3000/admin/login> works; admin can reach `/admin/users` to look up users by phone.
5. The Android app boots, requests an OTP, verifies it (code visible in `make logs | grep OTP`), and lands on SignedIn.
6. A second Android device can sign in with the same phone; both appear in Settings → Devices.
7. A third device hits the DeviceCapReached screen; picking one device and confirming completes the verify-ticket flow.
8. An admin force-deactivating a device causes that device's next API call to 403; the app navigates to "This device is signed out."
9. Trying to deactivate a second device within 90 days returns the cooldown error.
10. `make test` shows the full backend test suite green (~110+ tests).

If all ten hold, Wave 1 is done.

---

## Next wave

After Wave 1: brainstorm Wave 2 (producer onboarding + admin verification). It builds on Wave 1's auth: Wave 2 unlocks the agreement-acceptance flow (State 2 of the producer dashboard banner), adds the admin verify-producer action, and surfaces a producer onboarding wizard for bank details.

