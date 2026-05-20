# Wave 0: Foundations — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring up an empty but working full-stack skeleton. `make up` starts the entire Docker Compose stack; backend serves `/health`; Next.js serves a landing page; Android app builds and reaches `/health` from an emulator. All 9 database tables exist via Alembic migration. No business logic yet — just the rails.

**Architecture:** Monorepo with `backend/` (FastAPI + Celery in one Python package), `web/` (Next.js 15 App Router), `android/` (Kotlin + Compose), `infra/` (Docker Compose, scripts, Makefile). Backend uses `uv` for Python package management, SQLAlchemy 2.0 async with asyncpg, Alembic for migrations, pydantic-settings for config. Web uses TypeScript, Tailwind v4, shadcn/ui. Android uses Hilt + Compose + Retrofit + OkHttp + Moshi.

**Tech Stack:** Python 3.12, FastAPI 0.115+, SQLAlchemy 2.0, asyncpg, Alembic, pydantic-settings, uv, pytest, pytest-asyncio. Node 20, Next.js 15, TypeScript 5, Tailwind v4, shadcn/ui. Kotlin 2.x, Android Gradle Plugin 8.x, Compose BOM 2024.12+, Hilt 2.51+, Retrofit 2.11+, OkHttp 4.12+, Moshi 1.15+. Docker + Docker Compose. PostgreSQL 16, Redis 7, MinIO RELEASE.2024-10-13 or later, tusd 2.5+.

**Reference:** `docs/superpowers/specs/2026-05-20-mvp-vertical-slice-design.md` (the spec). `consolidated-brief.md` (the product brief).

---

## File Structure

By the end of Wave 0, the repo contains:

```
alaba/
├── .gitignore
├── README.md
├── Makefile
├── consolidated-brief.md                    (already exists)
├── docs/superpowers/
│   ├── specs/2026-05-20-mvp-vertical-slice-design.md
│   └── plans/2026-05-20-wave-0-foundations.md
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock                              (generated)
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial_schema.py       (generated, edited)
│   ├── alaba/
│   │   ├── __init__.py
│   │   ├── main.py                          (FastAPI app)
│   │   ├── config.py                        (Settings)
│   │   ├── db.py                            (engine, session)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                      (Base, mixins)
│   │   │   ├── user.py
│   │   │   ├── user_device.py
│   │   │   ├── otp_code.py
│   │   │   ├── producer.py
│   │   │   ├── film.py
│   │   │   ├── license.py
│   │   │   ├── rating.py
│   │   │   ├── payout.py
│   │   │   └── admin_action.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── health.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_health.py
├── web/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts                   (or postcss-based for Tailwind v4)
│   ├── postcss.config.mjs
│   ├── components.json                      (shadcn config)
│   ├── Dockerfile
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                     (landing)
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   └── ui/                          (shadcn-generated)
│   │   └── lib/
│   │       └── utils.ts                     (shadcn cn() helper)
│   └── .gitignore
├── android/
│   ├── settings.gradle.kts
│   ├── build.gradle.kts
│   ├── gradle.properties
│   ├── gradle/wrapper/
│   │   └── gradle-wrapper.properties
│   ├── app/
│   │   ├── build.gradle.kts
│   │   ├── proguard-rules.pro
│   │   └── src/main/
│   │       ├── AndroidManifest.xml
│   │       ├── java/com/orbanforest/alaba/
│   │       │   ├── AlabaApplication.kt
│   │       │   ├── MainActivity.kt
│   │       │   ├── di/
│   │       │   │   └── NetworkModule.kt
│   │       │   ├── data/api/
│   │       │   │   └── HealthApi.kt
│   │       │   └── ui/theme/
│   │       │       ├── Color.kt
│   │       │       ├── Theme.kt
│   │       │       └── Type.kt
│   │       └── res/
│   │           ├── values/{strings,colors,themes}.xml
│   │           └── mipmap-*/                  (icons; default for now)
│   └── .gitignore
└── infra/
    ├── docker-compose.yml
    ├── .env.example
    ├── .env                                  (gitignored)
    ├── minio/init.sh                         (creates buckets on startup)
    └── scripts/
        ├── print-android-base-url.sh
        └── wait-for-services.sh
```

---

## Prerequisites the engineer needs installed

Before starting, the engineer must have:

- Docker Desktop or Docker Engine ≥ 24
- Docker Compose v2 (built into Docker Desktop; or `docker compose` plugin)
- Python 3.12 (only needed for IDE; tasks run inside Docker)
- `uv` package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Node.js 20 LTS and npm (or pnpm — examples use npm)
- Android Studio Hedgehog or later (with Android SDK API 24-35)
- JDK 17 (bundled with Android Studio is fine)
- `make` (preinstalled on macOS/Linux; on Windows use WSL2)
- A POSIX shell — examples assume bash

The codebase is being developed on WSL2 Linux (per environment). Backend, web, and infra commands run in WSL2. Android Studio runs on the Windows host and reaches the backend at the WSL2 host IP (printed by `make android-url`).

---

## Task 1: Initialize repo and top-level structure

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `docs/superpowers/specs/.gitkeep` (or the actual spec file is already there)

- [ ] **Step 1.1: Initialize git repo at project root**

Run:
```bash
cd /mnt/e/TOOLMAKER/PYTHON/alaba
git init
git config user.email "you@example.com"
git config user.name "Your Name"
```

Expected: `Initialized empty Git repository in .../alaba/.git/`

- [ ] **Step 1.2: Create root `.gitignore`**

Create `.gitignore`:
```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/

# Node
node_modules/
.next/
out/
.turbo/

# Android
android/.gradle/
android/app/build/
android/.idea/
android/local.properties
*.keystore
*.jks

# IDE
.vscode/
.idea/

# Env
infra/.env
infra/.env.local
.env

# OS
.DS_Store
Thumbs.db

# Docker
postgres_data/
minio_data/
redis_data/
tusd_data/

# Logs
*.log
```

- [ ] **Step 1.3: Create top-level directory skeleton**

Run:
```bash
mkdir -p backend/alaba/{models,api}
mkdir -p backend/tests
mkdir -p backend/alembic/versions
mkdir -p web/src/{app,components,lib}
mkdir -p android/app/src/main/{java/com/orbanforest/alaba,res}
mkdir -p infra/{minio,scripts}
mkdir -p docs/superpowers/{specs,plans}
touch backend/alaba/__init__.py
touch backend/alaba/models/__init__.py
touch backend/alaba/api/__init__.py
touch backend/tests/__init__.py
```

- [ ] **Step 1.4: Create minimal placeholder `README.md`**

Create `README.md`:
```markdown
# Alaba

Nigerian Nollywood film distribution platform. See `consolidated-brief.md` for the product brief and `docs/superpowers/specs/` for the engineering spec.

## Quickstart

(Filled in at end of Wave 0.)
```

- [ ] **Step 1.5: Commit**

Run:
```bash
git add .gitignore README.md backend/ web/ android/ infra/ docs/
git commit -m "chore: initialize monorepo skeleton"
```

Expected: commit succeeds; `git log` shows one commit.

---

## Task 2: Docker Compose foundation services

**Files:**
- Create: `infra/docker-compose.yml`
- Create: `infra/.env.example`
- Create: `infra/minio/init.sh`
- Create: `infra/scripts/wait-for-services.sh`

This task brings up PostgreSQL, Redis, MinIO, tusd, and mailhog. No application services yet — those arrive in Task 6 and Task 9.

- [ ] **Step 2.1: Create `infra/.env.example`**

Create `infra/.env.example`:
```bash
# ============================================================================
# Database
# ============================================================================
POSTGRES_USER=alaba
POSTGRES_PASSWORD=alaba_dev_password
POSTGRES_DB=alaba
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ============================================================================
# Redis
# ============================================================================
REDIS_HOST=redis
REDIS_PORT=6379

# ============================================================================
# MinIO (S3-compatible storage)
# ============================================================================
MINIO_ROOT_USER=alaba_minio_admin
MINIO_ROOT_PASSWORD=alaba_minio_dev_password
MINIO_BUCKET_SOURCE=alaba-source
MINIO_BUCKET_TRANSCODED=alaba-transcoded
MINIO_BUCKET_PREVIEWS=alaba-previews

# Public endpoint reachable from outside the Docker network (host machine + Android)
# Use localhost for browser, 10.0.2.2 for Android emulator (see Makefile android-url)
S3_PUBLIC_ENDPOINT=http://localhost:9000
S3_INTERNAL_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=alaba_minio_admin
S3_SECRET_KEY=alaba_minio_dev_password
S3_REGION=us-east-1

# ============================================================================
# Backend
# ============================================================================
ENVIRONMENT=dev
DATABASE_URL=postgresql+asyncpg://alaba:alaba_dev_password@postgres:5432/alaba
REDIS_URL=redis://redis:6379/0
JWT_SECRET=dev_jwt_secret_change_me_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Multi-device
MAX_ACTIVE_DEVICES_PER_USER=2
DEVICE_DEACTIVATION_COOLDOWN_DAYS=90

# OTP
OTP_PROVIDER=mock
OTP_LENGTH=6
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=5

# Payments
PAYMENT_PROVIDER=paystack
PAYSTACK_BASE_URL=https://api.paystack.co
PAYSTACK_SECRET_KEY=sk_test_PLACEHOLDER_REPLACE_WITH_REAL_TEST_KEY
PAYSTACK_PUBLIC_KEY=pk_test_PLACEHOLDER_REPLACE_WITH_REAL_TEST_KEY
PAYSTACK_WEBHOOK_SECRET=

# Payouts (no-op in slice)
PAYOUT_PROVIDER=noop

# CORS
CORS_ORIGINS=http://localhost:3000

# ============================================================================
# Web (Next.js)
# ============================================================================
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_INTERNAL_URL=http://backend-api:8000

# ============================================================================
# tusd
# ============================================================================
TUSD_PORT=1080
TUSD_HOOKS_HTTP=http://backend-api:8000/internal/tus/hook
```

- [ ] **Step 2.2: Create `infra/.env` (copy of example) for local dev**

Run:
```bash
cp infra/.env.example infra/.env
```

Note: `infra/.env` is gitignored. The engineer can put real Paystack test keys here later.

- [ ] **Step 2.3: Create `infra/minio/init.sh`** (creates buckets on first up)

Create `infra/minio/init.sh`:
```bash
#!/bin/sh
set -e

# Wait for MinIO to be ready
until mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"; do
  echo "Waiting for MinIO..."
  sleep 1
done

# Create buckets (idempotent)
mc mb --ignore-existing local/alaba-source
mc mb --ignore-existing local/alaba-transcoded
mc mb --ignore-existing local/alaba-previews

# Set lifecycle on previews bucket (90-day expiry)
cat > /tmp/lifecycle.json <<EOF
{
  "Rules": [
    {
      "ID": "expire-previews-90d",
      "Status": "Enabled",
      "Expiration": {"Days": 90}
    }
  ]
}
EOF
mc ilm import local/alaba-previews < /tmp/lifecycle.json || true

echo "MinIO buckets ready."
```

Run:
```bash
chmod +x infra/minio/init.sh
```

- [ ] **Step 2.4: Create `infra/docker-compose.yml`**

Create `infra/docker-compose.yml`:
```yaml
name: alaba

services:
  postgres:
    image: postgres:16-alpine
    container_name: alaba-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 2s
      timeout: 5s
      retries: 20

  redis:
    image: redis:7-alpine
    container_name: alaba-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 2s
      timeout: 5s
      retries: 20

  minio:
    image: minio/minio:RELEASE.2024-10-13T13-34-11Z
    container_name: alaba-minio
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 2s
      timeout: 5s
      retries: 20

  minio-init:
    image: minio/mc:RELEASE.2024-10-08T09-37-26Z
    container_name: alaba-minio-init
    depends_on:
      minio:
        condition: service_healthy
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    entrypoint: ["/bin/sh", "/init.sh"]
    volumes:
      - ./minio/init.sh:/init.sh:ro
    restart: "no"

  tusd:
    image: tusproject/tusd:v2.5
    container_name: alaba-tusd
    command:
      - "-hooks-http=${TUSD_HOOKS_HTTP}"
      - "-s3-endpoint=http://minio:9000"
      - "-s3-bucket=${MINIO_BUCKET_SOURCE}"
      - "-s3-region=${S3_REGION}"
      - "-port=1080"
      - "-host=0.0.0.0"
    environment:
      AWS_ACCESS_KEY_ID: ${MINIO_ROOT_USER}
      AWS_SECRET_ACCESS_KEY: ${MINIO_ROOT_PASSWORD}
    ports:
      - "1080:1080"
    depends_on:
      minio-init:
        condition: service_completed_successfully

  mailhog:
    image: mailhog/mailhog:v1.0.1
    container_name: alaba-mailhog
    ports:
      - "1025:1025"
      - "8025:8025"

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

- [ ] **Step 2.5: Create `infra/scripts/wait-for-services.sh`**

Create `infra/scripts/wait-for-services.sh`:
```bash
#!/bin/sh
set -e

cd "$(dirname "$0")/.."

echo "Waiting for foundation services to be healthy..."

# All foundation services must be healthy
for service in postgres redis minio; do
  echo -n "  $service: "
  until [ "$(docker inspect -f '{{.State.Health.Status}}' alaba-$service 2>/dev/null)" = "healthy" ]; do
    echo -n "."
    sleep 2
  done
  echo " healthy"
done

# minio-init must have completed (one-shot)
until [ "$(docker inspect -f '{{.State.Status}}' alaba-minio-init 2>/dev/null)" = "exited" ]; do
  echo "  Waiting for minio-init to complete..."
  sleep 2
done

echo "All foundation services ready."
```

Run:
```bash
chmod +x infra/scripts/wait-for-services.sh
```

- [ ] **Step 2.6: Bring up foundation services and verify**

Run from project root:
```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d
```

Expected: containers start without error. `docker ps` shows alaba-postgres, alaba-redis, alaba-minio, alaba-tusd, alaba-mailhog running.

Run:
```bash
sh infra/scripts/wait-for-services.sh
```

Expected: all services report `healthy`; minio-init completes.

Verify Postgres:
```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "SELECT 1;"
```

Expected: returns `1`.

Verify MinIO buckets:
```bash
docker exec alaba-minio mc alias set local http://localhost:9000 alaba_minio_admin alaba_minio_dev_password
docker exec alaba-minio mc ls local/
```

Expected: shows `alaba-source/`, `alaba-transcoded/`, `alaba-previews/`.

Verify tusd:
```bash
curl -sv http://localhost:1080/files/ 2>&1 | grep "HTTP/1.1"
```

Expected: `HTTP/1.1 405 Method Not Allowed` or similar (POST is required for tus uploads; GET returns 4xx — this confirms tusd is responding).

- [ ] **Step 2.7: Tear down to verify clean shutdown**

Run:
```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml down
```

Expected: containers stop and remove cleanly. Volumes persist (data not deleted).

- [ ] **Step 2.8: Commit**

Run:
```bash
git add infra/
git commit -m "feat(infra): docker-compose foundation services (postgres, redis, minio, tusd, mailhog)"
```

---

## Task 3: Backend Python project skeleton with uv

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/uv.lock` (generated)
- Create: `backend/alaba/__init__.py` (already empty from Task 1)
- Create: `backend/tests/conftest.py`

- [ ] **Step 3.1: Create `backend/pyproject.toml`**

Create `backend/pyproject.toml`:
```toml
[project]
name = "alaba"
version = "0.1.0"
description = "Alaba backend — Nollywood distribution platform"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "celery[redis]>=5.4.0",
    "redis>=5.2.0",
    "httpx>=0.28.0",
    "boto3>=1.35.0",
    "structlog>=24.4.0",
    "python-multipart>=0.0.12",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
```

- [ ] **Step 3.2: Install dependencies with uv**

Run:
```bash
cd backend
uv sync
```

Expected: `uv.lock` is generated, `.venv` directory created, all deps installed without error.

- [ ] **Step 3.3: Create `backend/tests/conftest.py` with basic fixtures**

Create `backend/tests/conftest.py`:
```python
"""Shared pytest fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """Force a known-safe environment for every test."""
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://alaba:alaba_dev_password@localhost:5432/alaba_test",
    )
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("JWT_SECRET", "test_jwt_secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRY_HOURS", "24")
    monkeypatch.setenv("MAX_ACTIVE_DEVICES_PER_USER", "2")
    monkeypatch.setenv("DEVICE_DEACTIVATION_COOLDOWN_DAYS", "90")
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_LENGTH", "6")
    monkeypatch.setenv("OTP_EXPIRY_MINUTES", "10")
    monkeypatch.setenv("OTP_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("PAYMENT_PROVIDER", "paystack")
    monkeypatch.setenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "sk_test_dummy")
    monkeypatch.setenv("PAYSTACK_PUBLIC_KEY", "pk_test_dummy")
    monkeypatch.setenv("PAYSTACK_WEBHOOK_SECRET", "dummy_webhook_secret")
    monkeypatch.setenv("PAYOUT_PROVIDER", "noop")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("S3_PUBLIC_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("S3_INTERNAL_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("S3_ACCESS_KEY", "test_access_key")
    monkeypatch.setenv("S3_SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("S3_REGION", "us-east-1")
    monkeypatch.setenv("MINIO_BUCKET_SOURCE", "alaba-source")
    monkeypatch.setenv("MINIO_BUCKET_TRANSCODED", "alaba-transcoded")
    monkeypatch.setenv("MINIO_BUCKET_PREVIEWS", "alaba-previews")
```

- [ ] **Step 3.4: Verify pytest can discover and run an empty suite**

Run from `backend/`:
```bash
uv run pytest
```

Expected: `no tests ran` (exit code 5 is fine — pytest's signal for "no tests collected"). Or if there's a smoke test from package init, it passes.

- [ ] **Step 3.5: Commit**

Run from project root:
```bash
git add backend/pyproject.toml backend/uv.lock backend/tests/conftest.py
git commit -m "feat(backend): python project skeleton with uv"
```

---

## Task 4: Backend Settings (config.py) — TDD

**Files:**
- Create: `backend/alaba/config.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 4.1: Write the failing test for Settings**

Create `backend/tests/test_config.py`:
```python
"""Tests for the Settings class (pydantic-settings)."""

import pytest

from alaba.config import Settings


def test_settings_reads_from_env():
    s = Settings()
    assert s.environment == "dev"
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.jwt_secret == "test_jwt_secret"
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expiry_hours == 24


def test_settings_multi_device_config():
    s = Settings()
    assert s.max_active_devices_per_user == 2
    assert s.device_deactivation_cooldown_days == 90


def test_settings_otp_config():
    s = Settings()
    assert s.otp_provider == "mock"
    assert s.otp_length == 6
    assert s.otp_expiry_minutes == 10
    assert s.otp_max_attempts == 5


def test_settings_payment_config():
    s = Settings()
    assert s.payment_provider == "paystack"
    assert s.paystack_base_url == "https://api.paystack.co"
    assert s.paystack_secret_key == "sk_test_dummy"
    assert s.payout_provider == "noop"


def test_settings_cors_origins_parsed_as_list():
    s = Settings()
    assert s.cors_origins == ["http://localhost:3000"]


def test_settings_storage_config():
    s = Settings()
    assert s.s3_public_endpoint == "http://localhost:9000"
    assert s.s3_internal_endpoint == "http://localhost:9000"
    assert s.s3_access_key == "test_access_key"
    assert s.minio_bucket_source == "alaba-source"


def test_mock_otp_refuses_production(monkeypatch):
    """Production must refuse to boot with mock OTP."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    with pytest.raises(ValueError, match="MockOTPProvider"):
        Settings()
```

- [ ] **Step 4.2: Run the test to verify it fails**

Run from `backend/`:
```bash
uv run pytest tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'alaba.config'`.

- [ ] **Step 4.3: Implement `backend/alaba/config.py`**

Create `backend/alaba/config.py`:
```python
"""Application settings, loaded from environment variables."""

from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application configuration, sourced from env."""

    model_config = SettingsConfigDict(
        env_file=None,  # env is injected by Docker/compose; no .env loading at runtime
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["dev", "test", "staging", "production"] = "dev"

    # Database
    database_url: str
    redis_url: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Multi-device
    max_active_devices_per_user: int = 2
    device_deactivation_cooldown_days: int = 90

    # OTP
    otp_provider: Literal["mock", "termii"] = "mock"
    otp_length: int = 6
    otp_expiry_minutes: int = 10
    otp_max_attempts: int = 5

    # Payments
    payment_provider: Literal["paystack"] = "paystack"
    paystack_base_url: str
    paystack_secret_key: str
    paystack_public_key: str
    paystack_webhook_secret: str = ""

    # Payouts
    payout_provider: Literal["noop", "paystack_transfers"] = "noop"

    # CORS
    cors_origins: list[str] = []

    # Storage
    s3_public_endpoint: str
    s3_internal_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str = "us-east-1"
    minio_bucket_source: str = "alaba-source"
    minio_bucket_transcoded: str = "alaba-transcoded"
    minio_bucket_previews: str = "alaba-previews"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @model_validator(mode="after")
    def _refuse_unsafe_combos(self):
        if self.environment == "production" and self.otp_provider == "mock":
            raise ValueError(
                "MockOTPProvider is forbidden in production. "
                "Set OTP_PROVIDER=termii (or another real provider)."
            )
        return self


def get_settings() -> Settings:
    """Lazily-constructed singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


_settings: Settings | None = None
```

- [ ] **Step 4.4: Run the tests to verify they pass**

Run from `backend/`:
```bash
uv run pytest tests/test_config.py -v
```

Expected: 7 tests pass.

- [ ] **Step 4.5: Commit**

Run from project root:
```bash
git add backend/alaba/config.py backend/tests/test_config.py
git commit -m "feat(backend): Settings class with multi-device + safety gate against mock OTP in prod"
```

---

## Task 5: Backend database connection (db.py) — TDD

**Files:**
- Create: `backend/alaba/db.py`
- Create: `backend/tests/test_db.py`

This task creates the SQLAlchemy 2.0 async engine and `get_db()` dependency. Tests hit a real Postgres instance — make sure foundation services from Task 2 are running, and a test database exists.

- [ ] **Step 5.1: Create the test database**

Run:
```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d postgres
sh infra/scripts/wait-for-services.sh
docker exec alaba-postgres psql -U alaba -c "CREATE DATABASE alaba_test;" || echo "(already exists)"
```

Expected: database `alaba_test` exists.

- [ ] **Step 5.2: Write the failing test**

Create `backend/tests/test_db.py`:
```python
"""Tests for db.py — engine, session factory, dependency."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.db import async_engine, get_db


async def test_engine_connects():
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


async def test_get_db_yields_session():
    """get_db is an async generator that yields an AsyncSession."""
    gen = get_db()
    session = await anext(gen)
    assert isinstance(session, AsyncSession)
    # cleanup
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass


async def test_get_db_session_is_usable_and_closes():
    """Verify the session yielded by get_db can execute and is cleanly closed."""
    gen = get_db()
    session = await anext(gen)
    result = await session.execute(text("SELECT 42"))
    assert result.scalar() == 42
    # exhaust the generator to trigger cleanup
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass
    # Session should be closed; further use raises
    with pytest.raises(Exception):
        await session.execute(text("SELECT 1"))
```

- [ ] **Step 5.3: Run the test to verify it fails**

Run from `backend/`:
```bash
uv run pytest tests/test_db.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'alaba.db'`.

- [ ] **Step 5.4: Implement `backend/alaba/db.py`**

Create `backend/alaba/db.py`:
```python
"""SQLAlchemy 2.0 async engine, session factory, FastAPI dependency."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from alaba.config import get_settings


def _make_engine():
    s = get_settings()
    return create_async_engine(
        s.database_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )


async_engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. Yields a session that rolls back on uncaught error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 5.5: Run the tests to verify they pass**

Run from `backend/`:
```bash
uv run pytest tests/test_db.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5.6: Commit**

Run:
```bash
git add backend/alaba/db.py backend/tests/test_db.py
git commit -m "feat(backend): SQLAlchemy 2.0 async engine + get_db dependency"
```

---

## Task 6: Backend `/health` endpoint and FastAPI app — TDD

**Files:**
- Create: `backend/alaba/main.py`
- Create: `backend/alaba/api/health.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 6.1: Write the failing test**

Create `backend/tests/test_health.py`:
```python
"""Tests for /health endpoint."""

from httpx import ASGITransport, AsyncClient

from alaba.main import app


async def test_health_returns_200_with_status_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body
    assert body["service"] == "alaba-backend"


async def test_health_reports_db_reachable():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    body = response.json()
    assert body["checks"]["database"] == "ok"
```

- [ ] **Step 6.2: Run the test to verify it fails**

Run from `backend/`:
```bash
uv run pytest tests/test_health.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'alaba.main'`.

- [ ] **Step 6.3: Implement `backend/alaba/api/health.py`**

Create `backend/alaba/api/health.py`:
```python
"""Health-check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from alaba.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    db_status = "ok"
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() != 1:
            db_status = "unexpected_response"
    except Exception as e:  # pragma: no cover
        db_status = f"error: {type(e).__name__}"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "alaba-backend",
        "checks": {"database": db_status},
    }
```

- [ ] **Step 6.4: Implement `backend/alaba/main.py`**

Create `backend/alaba/main.py`:
```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alaba.api import health
from alaba.config import get_settings


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="Alaba API",
        version="0.1.0",
        description="Backend for the Alaba Nollywood distribution platform.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    return app


app = create_app()
```

- [ ] **Step 6.5: Run the tests to verify they pass**

Run from `backend/`:
```bash
uv run pytest tests/test_health.py -v
```

Expected: 2 tests pass.

- [ ] **Step 6.6: Sanity-check via uvicorn**

Run from `backend/`:
```bash
uv run uvicorn alaba.main:app --reload --port 8000 &
sleep 2
curl -s http://localhost:8000/health | python -m json.tool
kill %1 2>/dev/null || true
```

Expected output:
```json
{
    "status": "ok",
    "service": "alaba-backend",
    "checks": {
        "database": "ok"
    }
}
```

- [ ] **Step 6.7: Commit**

Run from project root:
```bash
git add backend/alaba/main.py backend/alaba/api/health.py backend/tests/test_health.py
git commit -m "feat(backend): /health endpoint with DB check"
```

---

## Task 7: SQLAlchemy models — all 9 tables

**Files:**
- Create: `backend/alaba/models/base.py`
- Create: `backend/alaba/models/user.py`
- Create: `backend/alaba/models/user_device.py`
- Create: `backend/alaba/models/otp_code.py`
- Create: `backend/alaba/models/producer.py`
- Create: `backend/alaba/models/film.py`
- Create: `backend/alaba/models/license.py`
- Create: `backend/alaba/models/rating.py`
- Create: `backend/alaba/models/payout.py`
- Create: `backend/alaba/models/admin_action.py`
- Modify: `backend/alaba/models/__init__.py`
- Create: `backend/tests/test_models.py`

Models are declarative-only at this point — no relationships exercised beyond foreign keys, no business methods. Schemas follow the brief's SQL plus the spec's amendments (drop `users.device_id`; add `user_devices` and `otp_codes`).

- [ ] **Step 7.1: Write the failing test (import-only)**

Create `backend/tests/test_models.py`:
```python
"""Models import + table-existence smoke tests."""

from alaba.models import (
    AdminAction,
    Base,
    Film,
    License,
    OtpCode,
    Payout,
    Producer,
    Rating,
    User,
    UserDevice,
)


def test_all_models_import():
    """All 9 models can be imported from alaba.models."""
    assert User.__tablename__ == "users"
    assert UserDevice.__tablename__ == "user_devices"
    assert OtpCode.__tablename__ == "otp_codes"
    assert Producer.__tablename__ == "producers"
    assert Film.__tablename__ == "films"
    assert License.__tablename__ == "licenses"
    assert Rating.__tablename__ == "ratings"
    assert Payout.__tablename__ == "payouts"
    assert AdminAction.__tablename__ == "admin_actions"


def test_metadata_lists_all_tables():
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "users",
        "user_devices",
        "otp_codes",
        "producers",
        "films",
        "licenses",
        "ratings",
        "payouts",
        "admin_actions",
    }
    assert expected == table_names


def test_user_has_no_device_id_column():
    """Spec amendment: users.device_id is dropped in favor of user_devices."""
    cols = {c.name for c in User.__table__.columns}
    assert "device_id" not in cols
    assert "phone" in cols
    assert "phone_verified" in cols
    assert "suspended" in cols


def test_user_device_columns():
    cols = {c.name for c in UserDevice.__table__.columns}
    expected = {
        "id",
        "user_id",
        "device_id",
        "display_name",
        "model",
        "platform",
        "activated_at",
        "deactivated_at",
        "last_seen_at",
    }
    assert expected <= cols


def test_license_has_payment_ref_unique():
    """licenses.payment_ref must be UNIQUE for webhook idempotency."""
    col = License.__table__.columns["payment_ref"]
    assert col.unique is True
```

- [ ] **Step 7.2: Run the test to verify it fails**

Run from `backend/`:
```bash
uv run pytest tests/test_models.py -v
```

Expected: FAIL with `ModuleNotFoundError` or import errors.

- [ ] **Step 7.3: Create `backend/alaba/models/base.py`**

Create `backend/alaba/models/base.py`:
```python
"""SQLAlchemy declarative base + common mixins."""

from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base."""


timestamp = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False),
]
```

- [ ] **Step 7.4: Create `backend/alaba/models/user.py`**

Create `backend/alaba/models/user.py`:
```python
"""User (viewer) model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

- [ ] **Step 7.5: Create `backend/alaba/models/user_device.py`**

Create `backend/alaba/models/user_device.py`:
```python
"""UserDevice model — N=2 per-user device cap."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class UserDevice(Base):
    __tablename__ = "user_devices"
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_user_devices_user_device"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    model: Mapped[str | None] = mapped_column(String(100))
    platform: Mapped[str] = mapped_column(String(20), default="android", nullable=False)
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 7.6: Create `backend/alaba/models/otp_code.py`**

Create `backend/alaba/models/otp_code.py`:
```python
"""OtpCode — slice-specific table for OTP issuance and verification."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class OtpCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 7.7: Create `backend/alaba/models/producer.py`**

Create `backend/alaba/models/producer.py`:
```python
"""Producer model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class Producer(Base):
    __tablename__ = "producers"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    agreement_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bank_name: Mapped[str | None] = mapped_column(String(255))
    bank_account: Mapped[str | None] = mapped_column(String(20))
    bank_code: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

- [ ] **Step 7.8: Create `backend/alaba/models/film.py`**

Create `backend/alaba/models/film.py`:
```python
"""Film model."""

import uuid
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class Film(Base):
    __tablename__ = "films"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    producer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("producers.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer)
    poster_url: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(500))
    encrypted_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    avg_rating: Mapped[float] = mapped_column(DECIMAL(2, 1), default=0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 7.9: Create `backend/alaba/models/license.py`**

Create `backend/alaba/models/license.py`:
```python
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
```

- [ ] **Step 7.10: Create `backend/alaba/models/rating.py`**

Create `backend/alaba/models/rating.py`:
```python
"""Rating model — 1-5 stars, one per (user, film)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "film_id", name="uq_ratings_user_film"),
        CheckConstraint("stars BETWEEN 1 AND 5", name="ck_ratings_stars_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    film_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("films.id"), nullable=False
    )
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 7.11: Create `backend/alaba/models/payout.py`**

Create `backend/alaba/models/payout.py`:
```python
"""Payout model — weekly producer payouts."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    producer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("producers.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    license_count: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    transfer_ref: Mapped[str | None] = mapped_column(String(255))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 7.12: Create `backend/alaba/models/admin_action.py`**

Create `backend/alaba/models/admin_action.py`:
```python
"""AdminAction — audit log for admin operations."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from alaba.models.base import Base


class AdminAction(Base):
    __tablename__ = "admin_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 7.13: Update `backend/alaba/models/__init__.py`**

Replace contents of `backend/alaba/models/__init__.py`:
```python
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
```

- [ ] **Step 7.14: Run the tests to verify they pass**

Run from `backend/`:
```bash
uv run pytest tests/test_models.py -v
```

Expected: 5 tests pass.

- [ ] **Step 7.15: Commit**

Run from project root:
```bash
git add backend/alaba/models/
git add backend/tests/test_models.py
git commit -m "feat(backend): SQLAlchemy models for all 9 tables (user_devices, otp_codes, drop users.device_id)"
```

---

## Task 8: Alembic baseline migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Generated: `backend/alembic/versions/0001_initial_schema.py`

- [ ] **Step 8.1: Create `backend/alembic.ini`**

Create `backend/alembic.ini`:
```ini
[alembic]
script_location = alembic
file_template = %%(rev)s_%%(slug)s
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 8.2: Create `backend/alembic/script.py.mako`** (template for generated migrations)

Create `backend/alembic/script.py.mako`:
```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 8.3: Create `backend/alembic/env.py`**

Create `backend/alembic/env.py`:
```python
"""Alembic environment for async SQLAlchemy."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import models so their tables register on Base.metadata
from alaba import models  # noqa: F401
from alaba.config import get_settings
from alaba.models import Base

config = context.config

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 8.4: Set required env vars for Alembic to use real DB**

The `alembic` command runs outside Docker for Wave 0. It needs the same env as conftest, but pointing at the dev DB (not test). Set them temporarily:

Run from `backend/`:
```bash
export DATABASE_URL="postgresql+asyncpg://alaba:alaba_dev_password@localhost:5432/alaba"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="dev_jwt_secret_change_me_in_production"
export PAYSTACK_BASE_URL="https://api.paystack.co"
export PAYSTACK_SECRET_KEY="sk_test_dummy"
export PAYSTACK_PUBLIC_KEY="pk_test_dummy"
export S3_PUBLIC_ENDPOINT="http://localhost:9000"
export S3_INTERNAL_ENDPOINT="http://localhost:9000"
export S3_ACCESS_KEY="alaba_minio_admin"
export S3_SECRET_KEY="alaba_minio_dev_password"
```

- [ ] **Step 8.5: Generate the initial migration**

Run from `backend/`:
```bash
uv run alembic revision --autogenerate -m "initial_schema"
```

Expected: a file appears under `backend/alembic/versions/` named like `<hash>_initial_schema.py`.

- [ ] **Step 8.6: Rename the generated migration to `0001_initial_schema.py`**

Run:
```bash
cd backend/alembic/versions
ls -1 *.py | head -n 1 | xargs -I {} mv {} 0001_initial_schema.py
```

Edit `backend/alembic/versions/0001_initial_schema.py` and change the `revision:` value at the top of the file to `"0001"` and `down_revision:` to `None`.

(Other lines in the generated file are auto-produced from the models.)

- [ ] **Step 8.7: Apply the migration**

Run from `backend/`:
```bash
uv run alembic upgrade head
```

Expected: completes without error.

- [ ] **Step 8.8: Verify tables exist**

Run:
```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "\dt"
```

Expected output includes (alphabetical):
```
 public | admin_actions     | table | alaba
 public | alembic_version   | table | alaba
 public | films             | table | alaba
 public | licenses          | table | alaba
 public | otp_codes         | table | alaba
 public | payouts           | table | alaba
 public | producers         | table | alaba
 public | ratings           | table | alaba
 public | user_devices      | table | alaba
 public | users             | table | alaba
```

Verify `users` does NOT have `device_id`:
```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "\d users"
```

Expected: no `device_id` column. Columns: `id`, `phone`, `phone_verified`, `created_at`, `suspended`.

- [ ] **Step 8.9: Verify downgrade works (just to make sure it's reversible during dev)**

Run from `backend/`:
```bash
uv run alembic downgrade base
docker exec alaba-postgres psql -U alaba -d alaba -c "\dt" | grep -c "alaba" || echo "no tables"
uv run alembic upgrade head
```

Expected: downgrade succeeds; tables disappear; upgrade re-creates everything.

- [ ] **Step 8.10: Commit**

Run from project root:
```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat(backend): Alembic baseline migration with all 9 tables"
```

---

## Task 9: Backend Dockerfile and Compose integration

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Modify: `infra/docker-compose.yml` (add backend-api and backend-worker services)

- [ ] **Step 9.1: Create `backend/.dockerignore`**

Create `backend/.dockerignore`:
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
tests/
.git/
```

- [ ] **Step 9.2: Create `backend/Dockerfile`**

Create `backend/Dockerfile`:
```dockerfile
# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install deps separately from app code for better caching
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy app source
COPY alaba ./alaba
COPY alembic ./alembic
COPY alembic.ini ./

# Re-run sync now that source is present to install the project itself
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uvicorn", "alaba.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 9.3: Add backend services to `infra/docker-compose.yml`**

Open `infra/docker-compose.yml` and add these two service blocks under `services:` (after `mailhog`):

```yaml
  backend-api:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: alaba-backend-api
    command: ["uvicorn", "alaba.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    environment:
      ENVIRONMENT: ${ENVIRONMENT}
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      JWT_SECRET: ${JWT_SECRET}
      JWT_ALGORITHM: ${JWT_ALGORITHM}
      JWT_EXPIRY_HOURS: ${JWT_EXPIRY_HOURS}
      MAX_ACTIVE_DEVICES_PER_USER: ${MAX_ACTIVE_DEVICES_PER_USER}
      DEVICE_DEACTIVATION_COOLDOWN_DAYS: ${DEVICE_DEACTIVATION_COOLDOWN_DAYS}
      OTP_PROVIDER: ${OTP_PROVIDER}
      OTP_LENGTH: ${OTP_LENGTH}
      OTP_EXPIRY_MINUTES: ${OTP_EXPIRY_MINUTES}
      OTP_MAX_ATTEMPTS: ${OTP_MAX_ATTEMPTS}
      PAYMENT_PROVIDER: ${PAYMENT_PROVIDER}
      PAYSTACK_BASE_URL: ${PAYSTACK_BASE_URL}
      PAYSTACK_SECRET_KEY: ${PAYSTACK_SECRET_KEY}
      PAYSTACK_PUBLIC_KEY: ${PAYSTACK_PUBLIC_KEY}
      PAYSTACK_WEBHOOK_SECRET: ${PAYSTACK_WEBHOOK_SECRET}
      PAYOUT_PROVIDER: ${PAYOUT_PROVIDER}
      CORS_ORIGINS: ${CORS_ORIGINS}
      S3_PUBLIC_ENDPOINT: ${S3_PUBLIC_ENDPOINT}
      S3_INTERNAL_ENDPOINT: ${S3_INTERNAL_ENDPOINT}
      S3_ACCESS_KEY: ${S3_ACCESS_KEY}
      S3_SECRET_KEY: ${S3_SECRET_KEY}
      S3_REGION: ${S3_REGION}
      MINIO_BUCKET_SOURCE: ${MINIO_BUCKET_SOURCE}
      MINIO_BUCKET_TRANSCODED: ${MINIO_BUCKET_TRANSCODED}
      MINIO_BUCKET_PREVIEWS: ${MINIO_BUCKET_PREVIEWS}
    ports:
      - "8000:8000"
    volumes:
      - ../backend/alaba:/app/alaba
      - ../backend/alembic:/app/alembic
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\", timeout=2)'"]
      interval: 5s
      timeout: 5s
      retries: 12
      start_period: 10s

  backend-worker:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: alaba-backend-worker
    command: ["python", "-c", "import time; print('worker placeholder; Celery wiring in Wave 3'); time.sleep(86400)"]
    environment:
      ENVIRONMENT: ${ENVIRONMENT}
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      JWT_SECRET: ${JWT_SECRET}
      PAYSTACK_BASE_URL: ${PAYSTACK_BASE_URL}
      PAYSTACK_SECRET_KEY: ${PAYSTACK_SECRET_KEY}
      PAYSTACK_PUBLIC_KEY: ${PAYSTACK_PUBLIC_KEY}
      S3_PUBLIC_ENDPOINT: ${S3_INTERNAL_ENDPOINT}
      S3_INTERNAL_ENDPOINT: ${S3_INTERNAL_ENDPOINT}
      S3_ACCESS_KEY: ${S3_ACCESS_KEY}
      S3_SECRET_KEY: ${S3_SECRET_KEY}
      MINIO_BUCKET_SOURCE: ${MINIO_BUCKET_SOURCE}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
```

- [ ] **Step 9.4: Build and bring up the full stack**

Run from project root:
```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --build backend-api backend-worker
```

Expected: backend image builds without error; both containers start.

- [ ] **Step 9.5: Apply migrations from inside the backend-api container**

Run:
```bash
docker exec alaba-backend-api alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial_schema` (or "no upgrades" if already applied).

- [ ] **Step 9.6: Verify `/health` over the network**

Run from project root:
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

Expected output:
```json
{
    "status": "ok",
    "service": "alaba-backend",
    "checks": {
        "database": "ok"
    }
}
```

- [ ] **Step 9.7: Verify container healthcheck reports healthy**

Run:
```bash
docker inspect -f '{{.State.Health.Status}}' alaba-backend-api
```

Expected: `healthy`.

- [ ] **Step 9.8: Commit**

Run:
```bash
git add backend/Dockerfile backend/.dockerignore infra/docker-compose.yml
git commit -m "feat(infra): backend-api + backend-worker compose services"
```

---

## Task 10: Next.js web scaffold with Tailwind v4 and shadcn/ui

**Files:**
- Create: `web/package.json`, `web/tsconfig.json`, etc. (via `create-next-app`)
- Modify: created Next.js config files for shadcn

- [ ] **Step 10.1: Run `create-next-app`**

Run from project root:
```bash
npx create-next-app@latest web \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --eslint \
  --turbopack \
  --import-alias "@/*" \
  --no-experimental-app \
  --use-npm
```

If prompted interactively, accept defaults that match the flags above.

Expected: `web/` is populated with a Next.js 15 project.

- [ ] **Step 10.2: Replace `web/src/app/page.tsx` with a minimal landing page**

Replace contents of `web/src/app/page.tsx`:
```tsx
export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="max-w-xl text-center space-y-4 px-6">
        <h1 className="text-4xl font-bold tracking-tight">Alaba</h1>
        <p className="text-lg text-muted-foreground">
          Nollywood films. ₦500. Download and watch offline, anytime.
        </p>
        <p className="text-sm text-muted-foreground">
          The Android app will be available on Google Play soon.
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 10.3: Replace `web/src/app/layout.tsx` to set the right title and lang**

Replace contents of `web/src/app/layout.tsx`:
```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Alaba — Nollywood, licensed",
  description:
    "Nigerian films licensed at ₦500. Download and watch offline. Producers paid 70%, weekly.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
```

- [ ] **Step 10.4: Initialize shadcn/ui**

Run from `web/`:
```bash
npx shadcn@latest init --yes --base-color slate
```

Expected: `components.json` is created; `src/lib/utils.ts` is created with the `cn()` helper; `src/app/globals.css` is updated with shadcn tokens; `tsconfig.json` aliases are added.

- [ ] **Step 10.5: Install one shadcn component to verify the toolchain**

Run from `web/`:
```bash
npx shadcn@latest add button --yes
```

Expected: `src/components/ui/button.tsx` is created.

- [ ] **Step 10.6: Run the web dev server and verify the landing page renders**

Run from `web/`:
```bash
npm run dev
```

In another terminal:
```bash
sleep 5
curl -sL http://localhost:3000 | grep -c "Alaba"
```

Expected: at least 1 (page contains the word "Alaba"). Kill the dev server with Ctrl+C.

- [ ] **Step 10.7: Commit**

Run from project root:
```bash
git add web/
git commit -m "feat(web): Next.js 15 scaffold with Tailwind + shadcn/ui and landing page"
```

---

## Task 11: Add web service to Docker Compose

**Files:**
- Create: `web/Dockerfile`
- Create: `web/.dockerignore`
- Modify: `infra/docker-compose.yml`

- [ ] **Step 11.1: Create `web/.dockerignore`**

Create `web/.dockerignore`:
```
node_modules
.next
.turbo
out
.git
.env*.local
```

- [ ] **Step 11.2: Create `web/Dockerfile` (dev-only, for compose)**

Create `web/Dockerfile`:
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "-p", "3000", "-H", "0.0.0.0"]
```

- [ ] **Step 11.3: Add web service to `infra/docker-compose.yml`**

Open `infra/docker-compose.yml` and add this service block under `services:` (after `backend-worker`):

```yaml
  web:
    build:
      context: ../web
      dockerfile: Dockerfile
    container_name: alaba-web
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
      BACKEND_INTERNAL_URL: ${BACKEND_INTERNAL_URL}
    ports:
      - "3000:3000"
    volumes:
      - ../web/src:/app/src
      - ../web/public:/app/public
    depends_on:
      backend-api:
        condition: service_healthy
```

- [ ] **Step 11.4: Build and bring up the web service**

Run from project root:
```bash
docker compose --env-file infra/.env -f infra/docker-compose.yml up -d --build web
```

Expected: web image builds; container starts.

- [ ] **Step 11.5: Verify the landing page is served**

Run:
```bash
sleep 8
curl -sL http://localhost:3000 | grep -c "Alaba"
```

Expected: at least 1.

- [ ] **Step 11.6: Commit**

Run:
```bash
git add web/Dockerfile web/.dockerignore infra/docker-compose.yml
git commit -m "feat(infra): web service in docker compose"
```

---

## Task 12: Android app skeleton

**Files:**
- Create: `android/settings.gradle.kts`
- Create: `android/build.gradle.kts`
- Create: `android/gradle.properties`
- Create: `android/app/build.gradle.kts`
- Create: `android/app/src/main/AndroidManifest.xml`
- Create: `android/app/src/main/java/com/orbanforest/alaba/AlabaApplication.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/MainActivity.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/di/NetworkModule.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/data/api/HealthApi.kt`
- Create: `android/app/src/main/java/com/orbanforest/alaba/ui/theme/{Color,Theme,Type}.kt`
- Create: `android/app/src/main/res/values/{strings,colors,themes}.xml`
- Create: `android/.gitignore`

For Wave 0, the Android app shows a single Compose screen that fetches `/health` and displays the JSON. The engineer is expected to open the `android/` directory in Android Studio after creating these files; Android Studio will generate `gradlew`, `local.properties`, etc.

- [ ] **Step 12.1: Create `android/.gitignore`**

Create `android/.gitignore`:
```gitignore
*.iml
.gradle
/local.properties
/.idea/
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
local.properties
app/release
```

- [ ] **Step 12.2: Create `android/settings.gradle.kts`**

Create `android/settings.gradle.kts`:
```kotlin
pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "Alaba"
include(":app")
```

- [ ] **Step 12.3: Create `android/build.gradle.kts`**

Create `android/build.gradle.kts`:
```kotlin
plugins {
    id("com.android.application") version "8.7.2" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
    id("com.google.dagger.hilt.android") version "2.52" apply false
    id("com.google.devtools.ksp") version "2.0.21-1.0.27" apply false
}
```

- [ ] **Step 12.4: Create `android/gradle.properties`**

Create `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
```

- [ ] **Step 12.5: Create `android/app/build.gradle.kts`**

Create `android/app/build.gradle.kts`:
```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.dagger.hilt.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "com.orbanforest.alaba"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.orbanforest.alaba"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        debug {
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000\"")
        }
        release {
            isMinifyEnabled = false
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000\"")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.core:core-ktx:1.15.0")

    // Hilt
    implementation("com.google.dagger:hilt-android:2.52")
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")
    ksp("com.google.dagger:hilt-compiler:2.52")

    // Retrofit + OkHttp + Moshi
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("com.squareup.moshi:moshi:1.15.1")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.1")

    // Tests
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2024.12.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
```

- [ ] **Step 12.6: Create `android/app/src/main/AndroidManifest.xml`**

Create `android/app/src/main/AndroidManifest.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:name=".AlabaApplication"
        android:allowBackup="false"
        android:icon="@android:drawable/sym_def_app_icon"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.Alaba"
        android:usesCleartextTraffic="true">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@style/Theme.Alaba">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

Note: `android:usesCleartextTraffic="true"` is required for development against `http://10.0.2.2:8000`. Remove or restrict in the DRM/payouts cycle.

- [ ] **Step 12.7: Create string and theme resources**

Create `android/app/src/main/res/values/strings.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Alaba</string>
</resources>
```

Create `android/app/src/main/res/values/themes.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<resources xmlns:tools="http://schemas.android.com/tools">
    <style name="Theme.Alaba" parent="android:Theme.Material.Light.NoActionBar" />
</resources>
```

- [ ] **Step 12.8: Create `android/app/src/main/java/com/orbanforest/alaba/AlabaApplication.kt`**

Create `android/app/src/main/java/com/orbanforest/alaba/AlabaApplication.kt`:
```kotlin
package com.orbanforest.alaba

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class AlabaApplication : Application()
```

- [ ] **Step 12.9: Create `android/app/src/main/java/com/orbanforest/alaba/data/api/HealthApi.kt`**

Create `android/app/src/main/java/com/orbanforest/alaba/data/api/HealthApi.kt`:
```kotlin
package com.orbanforest.alaba.data.api

import com.squareup.moshi.JsonClass
import retrofit2.http.GET

@JsonClass(generateAdapter = true)
data class HealthResponse(
    val status: String,
    val service: String,
    val checks: Map<String, String>
)

interface HealthApi {
    @GET("/health")
    suspend fun getHealth(): HealthResponse
}
```

- [ ] **Step 12.10: Create `android/app/src/main/java/com/orbanforest/alaba/di/NetworkModule.kt`**

Create `android/app/src/main/java/com/orbanforest/alaba/di/NetworkModule.kt`:
```kotlin
package com.orbanforest.alaba.di

import com.orbanforest.alaba.BuildConfig
import com.orbanforest.alaba.data.api.HealthApi
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
    fun provideOkHttpClient(): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        return OkHttpClient.Builder()
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

- [ ] **Step 12.11: Create `android/app/src/main/java/com/orbanforest/alaba/MainActivity.kt`**

Create `android/app/src/main/java/com/orbanforest/alaba/MainActivity.kt`:
```kotlin
package com.orbanforest.alaba

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.orbanforest.alaba.data.api.HealthApi
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var healthApi: HealthApi

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    HealthScreen(healthApi)
                }
            }
        }
    }
}

@Composable
fun HealthScreen(api: HealthApi) {
    var result by remember { mutableStateOf("Calling /health...") }

    LaunchedEffect(Unit) {
        result = try {
            val resp = api.getHealth()
            "status=${resp.status}\nservice=${resp.service}\nchecks=${resp.checks}"
        } catch (e: Throwable) {
            "Error: ${e.javaClass.simpleName}: ${e.message}"
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = "Alaba — backend ping", style = MaterialTheme.typography.headlineSmall)
        Text(text = result, modifier = Modifier.padding(top = 16.dp))
    }
}
```

- [ ] **Step 12.12: Open in Android Studio and build**

In Android Studio (on Windows host), open the `android/` directory. Android Studio will:

- Generate `gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.jar`, and `gradle/wrapper/gradle-wrapper.properties`
- Sync Gradle
- Create `local.properties` with the SDK path

When sync completes, click **Build → Make Project**.

Expected: builds without error. `BuildConfig.API_BASE_URL` is generated.

- [ ] **Step 12.13: Run on emulator with backend reachable**

Make sure `docker compose ... up -d` has the backend running (Task 9 step 9.4). Start an Android emulator from Android Studio's Device Manager (API 34+ recommended).

Click **Run 'app'** in Android Studio.

Expected: emulator shows the Alaba app with text like:
```
Alaba — backend ping

status=ok
service=alaba-backend
checks={database=ok}
```

- [ ] **Step 12.14: Commit**

Run from project root:
```bash
git add android/
git commit -m "feat(android): Kotlin + Compose + Hilt + Retrofit skeleton, calls /health"
```

---

## Task 13: Makefile with dev commands

**Files:**
- Create: `Makefile`

- [ ] **Step 13.1: Create `Makefile` at project root**

Create `Makefile`:
```makefile
.PHONY: help up down logs ps psql migrate migration backend-shell worker-shell test seed make-admin android-url web-dev clean reset-db build

COMPOSE := docker compose --env-file infra/.env -f infra/docker-compose.yml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Bring up the full stack
	$(COMPOSE) up -d
	@sh infra/scripts/wait-for-services.sh

down: ## Stop and remove containers (preserves volumes)
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

build: ## Rebuild app images (backend-api, backend-worker, web)
	$(COMPOSE) build backend-api backend-worker web

psql: ## Open a psql shell against the dev database
	docker exec -it alaba-postgres psql -U alaba -d alaba

migrate: ## Apply pending Alembic migrations
	docker exec alaba-backend-api alembic upgrade head

migration: ## Create a new migration. Usage: make migration msg="add foo"
	@if [ -z "$(msg)" ]; then echo "Usage: make migration msg=\"description\""; exit 1; fi
	docker exec alaba-backend-api alembic revision --autogenerate -m "$(msg)"

backend-shell: ## Exec into backend-api container
	docker exec -it alaba-backend-api bash

worker-shell: ## Exec into backend-worker container
	docker exec -it alaba-backend-worker bash

test: ## Run backend pytest
	docker exec alaba-backend-api pytest -v

seed: ## Seed sample films, producers, viewers, licenses (script arrives in Wave 3)
	@echo "make seed is not yet wired. The seed script (infra/scripts/seed_films.py) is created in Wave 3."
	@exit 1

make-admin: ## Bootstrap an admin user (script arrives in Wave 1)
	@echo "make make-admin is not yet wired. The script (infra/scripts/make_admin.py) is created in Wave 1."
	@exit 1

android-url: ## Print the backend URL Android should hit
	@echo "Android emulator → http://10.0.2.2:8000"
	@ip=$$(ip route get 1 2>/dev/null | awk '{print $$7; exit}' || hostname -I | awk '{print $$1}'); \
	  echo "Android real device → http://$$ip:8000"

web-dev: ## Run Next.js dev server locally (alternative to docker)
	cd web && npm run dev

reset-db: ## Drop and recreate the dev database, re-apply migrations
	docker exec alaba-postgres psql -U alaba -c "DROP DATABASE IF EXISTS alaba;"
	docker exec alaba-postgres psql -U alaba -c "CREATE DATABASE alaba;"
	docker exec alaba-backend-api alembic upgrade head

clean: ## Stop everything and DELETE all volumes (data loss!)
	$(COMPOSE) down -v
```

- [ ] **Step 13.2: Verify the Makefile loads**

Run from project root:
```bash
make help
```

Expected: prints a list of targets with descriptions.

- [ ] **Step 13.3: Try a few targets**

Run:
```bash
make ps
make android-url
```

Expected:
- `make ps` shows the compose services state.
- `make android-url` prints `Android emulator → http://10.0.2.2:8000` and `Android real device → http://<WSL2-host-IP>:8000`.

- [ ] **Step 13.4: Commit**

Run:
```bash
git add Makefile
git commit -m "feat(infra): Makefile with dev commands"
```

---

## Task 14: Root README with quickstart

**Files:**
- Modify: `README.md`

- [ ] **Step 14.1: Replace `README.md` with a real quickstart**

Replace contents of `README.md`:
```markdown
# Alaba

Nigerian Nollywood film distribution platform. Viewers license films at ₦500, downloadable for offline playback. Producers receive 70% of each license, paid weekly.

- **Product brief:** `consolidated-brief.md`
- **Engineering spec (current slice):** `docs/superpowers/specs/2026-05-20-mvp-vertical-slice-design.md`
- **Implementation plans:** `docs/superpowers/plans/`

## Quickstart (dev)

Prerequisites: Docker Desktop or Docker Engine ≥ 24, Docker Compose v2, `uv` for any local Python work, Node.js 20 + npm, Android Studio (Hedgehog or later) for the mobile client.

### 1. First-time setup

```bash
git clone <this-repo> alaba && cd alaba
cp infra/.env.example infra/.env  # adjust if needed
```

### 2. Bring up the stack

```bash
make up
make migrate
```

Verify:

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"alaba-backend","checks":{"database":"ok"}}
```

Visit the landing page at <http://localhost:3000>.

### 3. Run the Android app

Open `android/` in Android Studio. When sync completes, start an emulator (API 34+ recommended) and click **Run 'app'**. The app calls `/health` on startup and shows the JSON.

To find the backend URL for a real device on your LAN:

```bash
make android-url
```

### Common commands

| Command | What it does |
|---|---|
| `make up` | Start the full stack |
| `make down` | Stop containers (volumes preserved) |
| `make logs` | Tail all logs |
| `make psql` | Open a psql shell against the dev DB |
| `make migrate` | Apply pending Alembic migrations |
| `make migration msg="..."` | Generate a new migration from model changes |
| `make backend-shell` | Bash inside backend-api |
| `make test` | Run backend pytest suite |
| `make android-url` | Print backend URLs for Android emulator + real device |
| `make reset-db` | Drop + recreate + remigrate the dev DB |
| `make clean` | Stop + DELETE all volumes (destroys data) |

### Service URLs (dev)

| Service | URL |
|---|---|
| Backend API | <http://localhost:8000> |
| Backend docs (Swagger) | <http://localhost:8000/docs> |
| Web portals (Next.js) | <http://localhost:3000> |
| MinIO console | <http://localhost:9001> (alaba_minio_admin / alaba_minio_dev_password) |
| tusd upload endpoint | <http://localhost:1080/files/> |
| mailhog (dev mail catcher) | <http://localhost:8025> |

### Repo layout

```
backend/   FastAPI + Celery worker (Python)
web/       Next.js 15 App Router (admin + producer)
android/   Kotlin + Compose consumer app
infra/     docker-compose + scripts + .env
docs/      specs and plans
```

### Conventions

- All UI copy uses "license" / "get" — never "buy" / "purchase".
- Naira amounts: integer kobo internally, formatted as `₦500` in UI (no decimals).
- Timestamps stored as `TIMESTAMPTZ` (UTC), displayed in `Africa/Lagos`.
- Branch convention: `wave-N-<short-name>` for wave-scoped work.
```

- [ ] **Step 14.2: Commit**

Run:
```bash
git add README.md
git commit -m "docs: root README with quickstart for Wave 0 stack"
```

---

## Task 15: End-to-end Wave 0 smoke test

This task verifies that everything in Wave 0 works together. No code changes — just a clean reproduction of the success criteria.

- [ ] **Step 15.1: Stop everything and verify clean restart**

Run:
```bash
make down
make up
```

Expected: `make up` completes; `wait-for-services.sh` reports all services healthy.

- [ ] **Step 15.2: Run migrations**

Run:
```bash
make migrate
```

Expected: `alembic upgrade head` reports no upgrades (already at 0001) or upgrades cleanly.

- [ ] **Step 15.3: Verify `/health`**

Run:
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

Expected output:
```json
{
    "status": "ok",
    "service": "alaba-backend",
    "checks": {
        "database": "ok"
    }
}
```

- [ ] **Step 15.4: Verify web landing page**

Run:
```bash
curl -sL http://localhost:3000 | grep -c "Alaba"
```

Expected: at least 1.

- [ ] **Step 15.5: Verify Swagger docs are reachable**

Run:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs
```

Expected: `200`.

- [ ] **Step 15.6: Verify all 10 tables exist (9 application + alembic_version)**

Run:
```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "\dt" | grep -E "(users|user_devices|otp_codes|producers|films|licenses|ratings|payouts|admin_actions|alembic_version)" | wc -l
```

Expected: `10`.

- [ ] **Step 15.7: Verify `users` table does NOT have `device_id` column**

Run:
```bash
docker exec alaba-postgres psql -U alaba -d alaba -c "\d users" | grep -c "device_id" || echo 0
```

Expected: `0`.

- [ ] **Step 15.8: Verify pytest passes inside the backend container**

Run:
```bash
make test
```

Expected: all tests in `tests/test_config.py`, `tests/test_db.py`, `tests/test_health.py`, `tests/test_models.py` pass.

- [ ] **Step 15.9: Verify Android app builds and runs (manual)**

In Android Studio, with `make up` running:

1. Sync Gradle on the `android/` project.
2. Start an emulator (Pixel 7, API 34+).
3. Click **Run 'app'**.
4. Confirm the running app shows `status=ok`, `service=alaba-backend`, `checks={database=ok}`.

This is a manual step. If it doesn't work, the most common cause on WSL2 is the emulator can't reach `10.0.2.2:8000`. Check that `make ps` shows `alaba-backend-api` listening on `0.0.0.0:8000` and that `curl http://localhost:8000/health` works from Windows host (PowerShell or browser).

- [ ] **Step 15.10: Final commit (if any uncommitted changes)**

Run:
```bash
git status
# If anything is dirty:
git add -A
git commit -m "chore: wave 0 stabilization"
```

- [ ] **Step 15.11: Tag the Wave 0 completion**

Run:
```bash
git tag -a wave-0-complete -m "Wave 0 (Foundations) complete: stack up, /health green, DB migrated, Android calls backend"
git log --oneline | head -20
```

Expected: tag is created; recent commits visible.

---

## Wave 0 success criteria recap

You should now be able to:

1. Run `make up` from a clean state and see the full stack come up.
2. `curl http://localhost:8000/health` returns `{"status":"ok",...}`.
3. Visit <http://localhost:3000> in a browser and see the Alaba landing page.
4. Open the Android app on an emulator and see the `/health` JSON rendered.
5. Verify 10 tables exist in Postgres (9 application + `alembic_version`).
6. Verify `users.device_id` is absent (replaced by `user_devices` relation).
7. Run `make test` and see all backend tests pass.

If all seven hold, Wave 0 is complete. Begin the brainstorming cycle for Wave 1 (auth + multi-device) next.

---

## Next steps

After Wave 0 is shipped and verified:

1. Re-open the brainstorming flow for Wave 1 (`/superpowers:brainstorming` or equivalent). Use what was learned in Wave 0 to refine Wave 1's plan.
2. Wave 1 covers: phone OTP auth (`MockOTPProvider`), producer email+password, admin auth, JWT minting, web auth middleware, Android auth screens, **multi-device** support (N=2 cap, 90-day cooldown, Settings → Devices, admin user-devices panel).
3. Subsequent waves are listed in the spec's implementation-waves table.
