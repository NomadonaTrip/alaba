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
