# MVP Vertical Slice — Design Spec

**Status:** Approved (2026-05-20)
**Sub-project:** 1 of 3 (slice → DRM → payouts)
**Parent brief:** `consolidated-brief.md` v2.0

---

## Context

Alaba is a Nigeria-first Nollywood film distribution platform: viewers license films at ₦500 each (offline, perpetual, usable on up to 2 personal devices per viewer), producers receive 70% paid weekly. Full thesis, schema, API surface, and product rules live in `consolidated-brief.md`. This spec does not restate those — it covers only what's needed to bring the **first sub-project** to life. Note: the brief's "single-device" framing in Promise #3 is being relaxed to multi-device (N=2) per the decision recorded in this spec; the brief should be updated externally to match.

The MVP is being delivered as three sequential sub-projects:

1. **Thickest vertical slice** (this spec) — everything in MVP scope except Widevine DRM and Paystack live payouts. Dev-runnable end-to-end on localhost, not customer-facing.
2. **DRM cycle** — Widevine L3 via 3rd-party provider, ExoPlayer DRM, Play Integrity, license revocation, real Termii SMS, real B2/Cloudflare, staging deployment. Closed-beta-capable.
3. **Payouts + production cycle** — Paystack live + Transfers API, withholding execution, production infrastructure, Play Store submission.

The product is Nigeria-first. Sub-Saharan Africa expansion comes after Nigeria validates. Architecture preserves swap-friendliness via protocols (`PaymentProvider`, `OTPProvider`, `StorageBackend`) but does not pre-build multi-country features.

The implementation context is solo founder + Claude Code, localhost development, no production infrastructure yet.

## Goal

Bring up a working end-to-end thin-but-complete version of the Alaba platform on a single developer machine, exercising every system in the MVP except DRM and live payouts. The slice proves the rails: a producer can register, accept the Distribution Agreement, upload a film, see it transcoded; an admin can review and approve it; a viewer can sign in with phone OTP, browse the catalog, complete a Paystack test-mode license, download the film, play it locally with `FLAG_SECURE`, rate it, and share to WhatsApp; dashboards on both portal sides reflect activity in real time.

Done means: a single `make up` brings the whole stack alive, seeded with sample data, and Claude Code or any developer can walk through the full producer/admin/viewer flows end-to-end without writing additional code.

## Non-goals

This spec does NOT cover:

- Widevine L3, Shaka Packager, license proxy, Play Integrity, HDMI block, license revocation surface — DRM cycle
- Paystack live mode, Transfers API, weekly payout disbursement, withholding execution, chargebacks — payouts cycle
- OPay integration, push notifications, Termii real SMS — later cycles
- Production deployment, Cloudflare CDN, real B2, Caddy reverse proxy, TLS, secrets management — payouts cycle
- iOS, web playback, streaming, bundles, airtime, USSD, social layer, crowdfunding, sub-Saharan expansion — out of MVP per brief
- Legal-document drafting (T&C, Distribution Agreement, Privacy Policy) — calendar dependency owned by Nigerian counsel, parallel workstream
- Producer outreach, Play Store submission, merchant-account provisioning — calendar dependencies

## Architecturally significant decisions

The brief commits the high-level tech stack (FastAPI, Postgres, Celery, Redis, Next.js, Kotlin/Compose, Widevine, Paystack). This spec records the decisions the brief leaves open.

| Decision | Choice | Reason |
|---|---|---|
| Repo layout | Single monorepo, simple folders (no Turborepo) | Solo dev, cross-cutting changes common, minimal ceremony |
| Next.js version | 15.x with App Router + Server Components | Modern default; better data fetching ergonomics |
| Next.js auth | Custom JWT-in-httpOnly-cookie middleware against backend's `/auth/producer/login` | Backend already issues JWTs; Auth.js would duplicate that layer |
| Producer + admin UI | Single Next.js app, role-gated route groups `(producer)` and `(admin)` | Brief: "Same Next.js codebase, role-based routing" |
| UI components | shadcn/ui + Tailwind + Radix | Code-you-own components, no runtime dep, fast iteration |
| Android HTTP | Retrofit + OkHttp + Moshi | Kotlin/Android standard; mature ecosystem |
| Android DI | Hilt | Google-standard, compile-time safe, Compose-friendly |
| Android navigation | Single-Activity + Compose Navigation, with PlayerActivity as the one exception (for clean `FLAG_SECURE`) | Compose-idiomatic; pragmatic exception for window-flag handling |
| Android image loading | Coil | Compose-first, Kotlin-first |
| Paystack in slice | Real Paystack test API (sandbox) | Free, real network, no separate mock to maintain |
| OTP in slice | `MockOTPProvider` printing codes to stdout | Zero account setup; production refuses to boot with mock |
| Object storage in slice | MinIO via Docker Compose (S3-compatible) | API-compatible with B2 → swap config without code change |
| Backend storage SDK | `boto3` with `endpoint_url` overrides | Works against MinIO and B2 identically |
| Sample films | Public-domain MP4s (Big Buck Bunny, Sintel, etc.), downloaded by seed script | Avoids dev licensing concerns; swappable |
| Migrations | Alembic from day 1, autogenerated from SQLAlchemy models | Standard FastAPI/SQLAlchemy pattern |
| Background jobs | Celery + Redis (broker + result backend) | Brief specifies Celery |
| Resumable upload | `tus-js-client` (browser) → `tusd` (Go server, in Docker) | Canonical tus server; battle-tested |
| Webhook delivery during dev | `ngrok http 8000` documented; fallback poll-based reconciliation in backend | Paystack needs HTTPS public endpoint |
| Device model | Multi-device per user, capped at N=2 with 90-day deactivation cooldown (Netflix/Spotify-style "authorized devices") | Resolves brief's open Q#6; matches Nigerian household reality; aligns with Widevine's inherent per-device CDM semantics in DRM cycle |

## Multi-device model

Each user may have **up to N=2 authorized devices** simultaneously. Authorizing a 3rd device requires deactivating an existing one. Deactivation is rate-limited: a user can deactivate at most one device per 90 days, preventing trivial sharing-rotation.

**Why N=2:** Realistic for Nigerian users who often own a phone plus a secondary device (tablet, backup phone, partner's phone). Higher N invites account-sharing abuse without much added user value.

**License semantics:** A license is still per (user, film). The license is consumable on any active device of that user. Each download is per (license, active device) — when DRM lands, this becomes one Widevine offline license per (license, device) pair.

**Product-facing reframe** (for the brief and Distribution Agreement, owned by user outside this spec):

- Old phrasing: "encrypted, device-locked, never leaves the app"
- New phrasing: "encrypted and locked to viewer accounts (up to 2 personal devices per viewer), never leaves the app, never plays on unauthorized devices"

The Distribution Agreement DRM disclaimer should explicitly mention N=2 multi-device per viewer so producers cannot later claim surprise.

**Brief's Promise #3 alignment:** Multi-device per user does not weaken content protection — each device is still individually authorized and (in DRM cycle) cryptographically attested. It changes the unit of binding from "license = 1 device" to "license = 1 user, up to N personal devices."

**Abuse vectors and mitigations:**

| Vector | Mitigation |
|---|---|
| Account sharing among friends | N=2 cap is primary defense. 90-day cooldown makes rotating slots through multiple friends cost ~90 days per swap. Anomaly detection (rapid IP/geo jumps, simultaneous activity) added in payouts cycle. |
| Device-id spoofing | DRM cycle: Play Integrity attestation + Widevine CDM hardware provisioning. Slice: cap alone. |
| Reactivating sold/lost phone | Soft-deactivate by previous owner. Admin force-deactivate for support cases. |

**Out of scope (not now, not in this product):** concurrent-stream caps, primary/companion device hierarchies, family-plan tiers, per-tier device counts.

## Slice scope

### In scope

**Backend (FastAPI + Celery worker):**

- Phone OTP auth (`MockOTPProvider`), producer email+password auth, admin auth (bootstrap-only via script)
- Multi-device support: device registration on OTP verify, N=2 cap, 90-day deactivation cooldown
- Device endpoints: `GET /devices` (list current user's), `POST /devices/{id}/deactivate` (cooldown-enforced), admin variants for support
- All catalog endpoints (list, detail)
- License endpoints (initiate, list-mine, get-one) + Paystack webhook
- Download endpoint returning presigned MinIO URL with active-license + active-device validation
- Ratings endpoint
- Producer endpoints (profile, agreement accept, upload-url, films CRUD, dashboard, per-film stats, withdrawal request)
- Admin endpoints (review queue, approve/reject, producer verification, catalog management, platform dashboard, payouts queue read-only, user-devices view + force-deactivate)
- Webhook idempotency, signature verification, rate limiting on OTP
- Celery tasks: `quality_check`, `transcode` (FFmpeg → H.265 480p, no encryption), `generate_admin_preview` (watermarked), `payout_run` (calculate only, do not transfer)

**Web portal (single Next.js 15 App Router app):**

- Public landing page (minimal — thesis + Play Store link placeholder)
- Producer routes: login, register, agreement acceptance, dashboard, films list, per-film stats with deep-link copier, upload (tus), payouts (read-only), withdrawal request, settings
- Admin routes: login, review queue, per-film review with preview player, producers list + per-producer page + verify action, catalog management, platform dashboard, payouts queue (read-only), user detail with **Devices panel** (list active devices, force-deactivate for support cases like lost/stolen phones)
- shadcn/ui + Tailwind + Radix
- JWT-in-httpOnly-cookie auth with middleware role gating
- Server Components for initial data; TanStack Query for interactive data
- Forms via react-hook-form + zod
- Naira formatter, Africa/Lagos timezone display
- Legal-document markdown placeholders served at `/legal/terms` and `/legal/privacy`

**Android consumer app (Kotlin + Compose):**

- Phone OTP login, JWT in EncryptedSharedPreferences, device ID generation, device-cap enforcement flow (with "you've reached your 2-device limit" remediation UX)
- Onboarding (3 screens, first-launch only)
- Catalog: language + genre filter chips, "New This Week" horizontal scroll, grid
- Film detail with poster, synopsis, "Get — ₦500" CTA
- Pre-license confirmation + Paystack WebView/Custom Tabs flow
- Payment processing screen with polling
- My Films library with download status
- Download via WorkManager (chunked, resumable, Range headers)
- PlayerActivity with ExoPlayer + Media3, `FLAG_SECURE` on window, DataStore-backed resume position
- Rate bottom sheet after first complete playback
- WhatsApp deep link share (to placeholder Play Store URL)
- Settings: account, **Devices** (list authorized devices with model/last-seen/deactivate, with cooldown messaging), storage, T&C, Privacy, logout
- Device-deactivated detection: backend 403 with reason → wipe local content + token, return to PhoneEntry

**Infrastructure (Docker Compose on localhost):**

- Postgres, Redis, MinIO, tusd, backend-api, backend-worker, web, mailhog
- Healthchecks + startup ordering
- Bind-mounted source for hot reload (backend, web)
- Single `Makefile` exposes the dev loop: `up`, `down`, `logs`, `migrate`, `migration`, `psql`, `seed`, `make-admin`, `reset-db`, `test`, `android-url`

**Data layer:**

- All 7 tables from brief's schema (`users`, `producers`, `films`, `licenses`, `ratings`, `payouts`, `admin_actions`)
- Plus two slice-specific tables: `otp_codes` (phone, code_hash, expires_at, attempts) and `user_devices` (user_id, device_id, display_name, model, platform, activated_at, deactivated_at, last_seen_at, UNIQUE on user_id+device_id)
- `users.device_id` column from brief's schema is **dropped** — superseded by `user_devices` relation
- All brief-specified indexes, plus `idx_user_devices_user` and partial index `idx_user_devices_active` on rows where `deactivated_at IS NULL`
- Alembic migrations from a single initial baseline

### Out of scope (deferred)

See "Non-goals" above. The deferred surfaces are:

- DRM end-to-end → DRM cycle
- Live payouts disbursement, withholding execution, OPay → payouts cycle
- Push notifications, Termii real SMS → payouts cycle
- Production deployment → payouts cycle
- License revocation (paired with DRM) → DRM cycle
- Multi-country features → indefinitely

## Repo layout

```
alaba/
├── README.md
├── consolidated-brief.md
├── docs/superpowers/specs/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── alaba/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── deps.py
│   │   ├── security.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── catalog.py
│   │   │   ├── licenses.py
│   │   │   ├── downloads.py
│   │   │   ├── ratings.py
│   │   │   ├── producer.py
│   │   │   ├── admin.py
│   │   │   └── webhooks.py
│   │   ├── services/
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── tasks/
│   │   └── integrations/
│   │       ├── storage.py        # boto3 wrapper, MinIO/B2 compatible
│   │       ├── paystack.py       # PaymentProvider impl
│   │       └── otp.py            # OTPProvider protocol + MockOTPProvider
│   ├── tests/
│   └── Dockerfile
├── web/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── (auth)/
│   │   │   ├── (producer)/producer/
│   │   │   ├── (admin)/admin/
│   │   │   ├── legal/
│   │   │   └── api/auth/logout/
│   │   ├── components/
│   │   ├── lib/
│   │   │   ├── api-client.ts
│   │   │   ├── auth.ts
│   │   │   ├── currency.ts
│   │   │   └── validators/
│   │   ├── middleware.ts
│   │   └── content/distribution-agreement.md   # placeholder
│   └── Dockerfile
├── android/
│   ├── settings.gradle.kts
│   ├── build.gradle.kts
│   ├── app/
│   │   ├── build.gradle.kts
│   │   └── src/main/java/com/orbanforest/alaba/
│   │       ├── AlabaApplication.kt
│   │       ├── MainActivity.kt
│   │       ├── di/
│   │       ├── data/
│   │       │   ├── api/
│   │       │   ├── auth/
│   │       │   ├── catalog/
│   │       │   ├── license/
│   │       │   ├── download/
│   │       │   ├── rating/
│   │       │   └── db/
│   │       ├── domain/{model,usecase}/
│   │       ├── ui/
│   │       │   ├── theme/
│   │       │   ├── components/
│   │       │   ├── nav/
│   │       │   ├── onboarding/, auth/, catalog/, film/, license/, library/, ratings/, settings/
│   │       └── player/           # PlayerActivity for FLAG_SECURE
│   └── gradle/
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml.example
│   ├── .env.example
│   └── scripts/
│       ├── seed_films.py
│       ├── make_admin.py
│       └── reset_db.sh
├── .gitignore
└── Makefile
```

Open: the Android package name is currently `com.orbanforest.alaba` based on the brief's "Orban Forest Inc." ownership. Adjust if needed before Wave 0.

## Backend architecture

### Single Python package, two processes

Same codebase. Two entry points:

- `alaba.main:app` — FastAPI app served by uvicorn
- `alaba.workers.celery_app:app` — Celery worker, with beat scheduler for `payout_run` cron

Both load the same `Settings` (pydantic-settings), connect to the same Postgres, share models, schemas, services.

### Layered structure

- **`api/`** — FastAPI routers. Thin: parse, authenticate, call service, serialize.
- **`services/`** — business logic. Framework-free. Receives `db: AsyncSession` and pure args. Raises domain exceptions; routers translate to `HTTPException`.
- **`models/`** — SQLAlchemy 2.0 declarative models. One file per logical grouping.
- **`schemas/`** — Pydantic models for request/response shapes.
- **`workers/tasks/`** — Celery task definitions. Sync (Celery doesn't compose with async cleanly).
- **`integrations/`** — external system adapters. Each is a protocol + concrete impl(s) selected by `Settings`.
- **`security.py`** — JWT encode/decode, OTP code generation, bcrypt.
- **`db.py`** — async engine, `SessionLocal`, `get_db()` dependency.
- **`deps.py`** — FastAPI dependencies: `get_current_user`, `get_current_producer`, `get_current_admin`, `require_verified_producer`.
- **`config.py`** — `Settings` class. All env-driven.

### Auth model

- **Viewers**: phone + OTP. JWT, 24h expiry, refresh flow. Claims: `sub` (user UUID), `role=viewer`, `user_device_id` (UUID of the `user_devices` row, NOT the raw hardware id). Backend resolves device on every authenticated call.
- **Producers**: email + bcrypt password. JWT, 24h expiry, refresh flow. Claims: `sub` (producer UUID), `role=producer`.
- **Admins**: email + bcrypt password. Bootstrap only via `make_admin` script. No self-service registration in slice.
- **OTP**: 6-digit numeric. 10-minute expiry. Max 5 verify attempts before invalidation. Stored in slice-specific `otp_codes` table with phone, code (hashed), expires_at, attempts.

### Multi-device flow

On `/auth/otp/verify`:

1. Validate phone + code as today.
2. Read submitted `device_id` (hardware-fingerprint UUID from Android), `display_name`, `model`, `platform` from request body.
3. Check `user_devices` for existing row where `(user_id, device_id)` matches:
   - **If exists and active** (`deactivated_at IS NULL`): update `last_seen_at`, mint JWT with that `user_device_id`.
   - **If exists but deactivated**: reactivate only if doing so doesn't exceed cap AND last `deactivated_at` is >90 days old (cooldown for reactivation of own device); else require activating as a "new device" via cap-handling path below.
   - **If not exists** (new device): count current active devices for user. If `< N=2`, insert row, mint JWT. If `>= N`, return `409 Conflict` with body `{ "error": "device_cap_reached", "active_devices": [...summary...] }`. Android shows remediation UX (pick one to deactivate, then retry OTP verify).
4. Deactivation endpoint `POST /devices/{id}/deactivate`:
   - Soft-deactivate: set `deactivated_at = now()`.
   - Enforce cooldown: if any device the same user has deactivated within the last 90 days, reject with `429` and the cooldown unlock date.
   - Idempotent: deactivating an already-deactivated device returns 200.
   - Cascade for the device being deactivated: any in-flight presigned download URLs remain valid until expiry (1h); subsequent calls are blocked.
5. Admin force-deactivate (`POST /admin/users/{user_id}/devices/{device_id}/deactivate`):
   - Bypasses the 90-day cooldown. Logs to `admin_actions` with reason (e.g., "lost phone").
   - Used for support cases.

`get_current_user` dependency reads `user_device_id` from JWT, joins to `user_devices`, and rejects if `deactivated_at IS NOT NULL` with `403` and reason code `device_deactivated`. Android client interprets that code → wipes local content + token → returns to PhoneEntry.

### Integration protocols

```python
class OTPProvider(Protocol):
    async def send(self, phone: str, code: str) -> None: ...

class PaymentProvider(Protocol):
    async def initialize(
        self, *, amount: int, email: str, reference: str,
        callback_url: str, metadata: dict,
    ) -> InitializeResult: ...
    def verify_webhook(self, body: bytes, signature: str) -> bool: ...
    def parse_webhook(self, body: bytes) -> WebhookEvent: ...

class StorageBackend(Protocol):
    async def presign_get(self, key: str, expires_in: int) -> str: ...
    async def presign_put(self, key: str, expires_in: int) -> str: ...
    async def head(self, key: str) -> ObjectMetadata: ...
    async def delete(self, key: str) -> None: ...

class PayoutProvider(Protocol):
    # Defined but unused in slice; NoopPayoutProvider records intent only.
    async def transfer(self, *, amount: int, bank_code: str,
                       account_number: str, reference: str) -> TransferResult: ...
```

DI wiring in `deps.py` reads `Settings.OTP_PROVIDER`, `Settings.PAYMENT_PROVIDER`, etc., and returns the concrete class.

### MockOTPProvider safety gate

`MockOTPProvider.__init__` asserts `Settings.environment != "production"`. Production refuses to boot if `OTP_PROVIDER=mock` is set.

### Storage layout (MinIO buckets)

- `alaba-source/{film_id}/{original_filename}` — original producer upload
- `alaba-transcoded/{film_id}/480p.mp4` — FFmpeg H.265 output
- `alaba-previews/{film_id}/admin_preview.mp4` — watermarked admin review rendition

Buckets are private; access only via presigned URLs. Lifecycle: source kept forever; previews expire after 90 days.

### Content pipeline (Celery DAG)

```
tus pre-finish webhook → upload_service.finalize(film_id, key)
                       → enqueue quality_check
quality_check (ffprobe: resolution >= 720p, duration >= 30 min, audio track, file integrity)
  PASS → film.status = 'pending' (awaiting admin review); generate admin_preview rendition (watermarked)
  FAIL → film.status = 'rejected' with specific reason; producer notified via mailhog email
admin_approve → enqueue transcode
transcode (ffmpeg -c:v libx265 -crf 28 -vf scale=-2:480 -c:a aac -b:a 128k, target 300-500MB)
  SUCCESS → film.status = 'approved', published_at = NOW()
  FAILURE → film.status = 'transcode_failed', admin sees in needs-attention queue
admin_reject (alternative to approve) → film.status = 'rejected' with reason; producer notified
```

Celery retries: max 3 with exponential backoff (1m, 5m, 15m). After max retries on transcode, status flips to `transcode_failed` for admin attention.

### License flow (Paystack test mode)

```
POST /licenses/initiate (viewer JWT)
  license_service.initiate(user, film_id):
    creates pending License row with unique payment_ref UUID
    calls paystack.initialize(amount=50000 [kobo], email=user.phone+"@alaba.test",
                              reference=payment_ref, callback_url, metadata={user_id, film_id})
    returns InitializeResult { authorization_url, reference }
  → app opens authorization_url in WebView/Custom Tabs
  → Paystack sandbox completes, user redirected to callback_url
POST /webhooks/paystack (Paystack signature header)
  verify HMAC SHA512 signature against shared secret
  parse event
  if event.event == 'charge.success':
    license_service.activate(payment_ref)
      finds License by payment_ref
      idempotent: if already active, return 200 OK
      else: set status='active', set producer_share/platform_share, return 200
  else: log + 200 (acknowledge)
App polls GET /licenses/{license_id} every 2s for 60s, then user-driven retry
  status='active' → navigate to MyFilms, start download
```

Idempotency: `licenses.payment_ref` UNIQUE; activate uses INSERT ... ON CONFLICT or SELECT-then-UPDATE in a transaction.

### Download flow

```
GET /download/{film_id} (viewer JWT, user_device_id in token)
  validate active license for (user, film)
  validate user_device_id is an active (not deactivated) device of user
  generate presigned MinIO URL for alaba-transcoded/{film_id}/480p.mp4, 1h expiry
  return { download_url, file_size_bytes, sha256 }
Android DownloadWorker (WorkManager):
  uses OkHttp Range headers for resumable chunked download
  persists progress in DownloadStateDao (Room)
  on completion: verify sha256, mark download_state='complete'
  on failure: retry with backoff, max 5 attempts
```

Download URL re-issued on demand if expired (app re-calls `/download/{film_id}`).

### Failure modes handled in slice

- Paystack down: pending license stays pending; app polls + shows "Processing payment..."; backend reconciliation task re-checks long-pending licenses against Paystack verification API.
- MinIO down: transcode tasks retry; on exhaust → `transcode_failed` status.
- FFmpeg crash on bad input: quality-check catches most; otherwise transcode_failed.
- OTP brute force: rate limit 5 attempts per phone per 15min; current code invalidates after 5 wrong attempts.
- Webhook replay: payment_ref UNIQUE → duplicate webhooks no-op.
- Webhook signature mismatch: 401, log, do not process.

## Web portal architecture

Next.js 15 App Router. Single app, role-gated route groups.

### Routing

```
src/app/
├── layout.tsx              # Root: Tailwind, fonts, providers
├── page.tsx                # Public landing
├── legal/{terms,privacy}/page.tsx   # Markdown-driven legal pages
├── (auth)/
│   ├── producer/{login,register,agreement}/page.tsx
│   └── admin/login/page.tsx
├── (producer)/producer/
│   ├── layout.tsx          # Sidebar nav, role check
│   ├── dashboard/page.tsx
│   ├── films/page.tsx
│   ├── films/[id]/page.tsx
│   ├── films/[id]/withdraw/page.tsx
│   ├── upload/page.tsx
│   ├── payouts/page.tsx
│   └── settings/page.tsx
├── (admin)/admin/
│   ├── layout.tsx          # Sidebar nav, role check
│   ├── dashboard/page.tsx
│   ├── review/page.tsx
│   ├── review/[film_id]/page.tsx
│   ├── producers/page.tsx
│   ├── producers/[id]/page.tsx
│   ├── catalog/page.tsx
│   └── payouts/page.tsx
└── api/auth/logout/route.ts
```

### Auth + middleware

`src/middleware.ts` runs on every request matching `/producer/*` or `/admin/*`. Reads `auth_token` httpOnly cookie. Verifies JWT signature against shared `JWT_SECRET` (HS256 in slice — switch to RS256 keys in production cycle). Reads `role` claim and gates accordingly.

- `producer` role → allowed on `/producer/*`; redirected from `/admin/*` to `/admin/login`.
- `admin` role → allowed on `/admin/*`; redirected from `/producer/*` to `/producer/login`.
- Unauthenticated → corresponding `/login`.

Login flow: form posts credentials to a server action; server action calls backend `/auth/{producer,admin}/login`; on success, sets `auth_token` httpOnly cookie with the JWT, redirects to dashboard.

### Data fetching

- **Server Components** for initial page data via `lib/api-client.ts` (Server-side, reads cookie, attaches `Authorization: Bearer`).
- **TanStack Query** on the client for interactive/refreshing data (upload progress, transcode status polling, dashboard refresh).
- **Server Actions** for mutations where ergonomic; otherwise client-side via api-client.
- REST over typed clients. No GraphQL or tRPC; types maintained manually for now.

### Producer agreement flow

After register → redirect to `/producer/agreement` → render the Distribution Agreement markdown (`web/content/distribution-agreement.md`, placeholder until lawyer-drafted version arrives) → "I have read and accept" checkbox + submit → backend records `agreement_accepted_at` → redirect to `/producer/dashboard` in unverified state with a banner. Upload is gated by `producers.verified = true`.

### Admin preview during review

`/admin/review/[film_id]` shows the watermarked `admin_preview.mp4` rendition via standard HTML5 video. The watermark ("ADMIN PREVIEW — DO NOT DISTRIBUTE — {timestamp}") is burned in during the preview-generation Celery task. This surface goes away in the DRM cycle.

### UI conventions

- **shadcn/ui components** generated into `components/ui/`, owned in our repo.
- **Feature components** colocated with route files; promoted to `components/` only on reuse.
- **Forms** via react-hook-form + zod schemas in `lib/validators/` (used both client and server side).
- **Currency** via `lib/currency.ts::formatNaira(amount)` → `₦500`, no decimals. Single call site; future-proofs multi-currency.
- **Dates** in WAT via a `lib/datetime.ts` helper formatting in `Africa/Lagos`.

### Not in this slice

- Revocation UI (paired with DRM cycle)
- Withholding execution (button can render as disabled placeholder; flag-flip lives in payouts cycle)
- Payout transfer trigger (payouts page lists computed records with "Disbursement begins in production cycle" notice)
- Referral analytics beyond counts
- Producer marketing assets / creative kit

## Android app architecture

Single-Activity Compose + Hilt + MVVM with `StateFlow`. Kotlin 2.x, Compose 1.7+, Media3 (ExoPlayer). One exception to single-Activity: `PlayerActivity` for clean `FLAG_SECURE` window-flag handling.

### Modules and conventions

- **Single module** for the slice. Split into multi-module later if build times demand it.
- **MVVM**: `ViewModel` exposes `StateFlow<UiState>`; Composables `collectAsStateWithLifecycle()`.
- **`UiState` sealed classes** per screen: `Loading | Success(data) | Error(message)`.
- **Repositories return `Result<T, Error>`** — sealed type, not exceptions for expected failures.
- **Hilt**: `NetworkModule`, `DatabaseModule`, `StorageModule`, `PlayerModule`.
- **Room** for cached license metadata and download state.
- **EncryptedSharedPreferences** for JWT and device_id.
- **DataStore** for resume positions and onboarding-completed flag.
- **Coil** for poster images.
- **WorkManager** for downloads; chunked, resumable, OkHttp `Range` headers.
- **BuildConfig.API_BASE_URL** — emulator uses `http://10.0.2.2:8000`; real device uses WSL2 host LAN IP (printed by `make android-url`).

### AuthInterceptor + 401 handling

OkHttp interceptor attaches `Authorization: Bearer <jwt>`. On 401 from backend, interceptor emits to a singleton `AuthEventBus.expired` `SharedFlow`. `MainActivity` collects and navigates to PhoneEntry, clearing TokenStore.

### Device ID and multi-device flow

Generated once on first launch (`UUID.randomUUID()`), stored in EncryptedSharedPreferences. Sent on OTP verify along with `display_name` (e.g., user-editable default "John's TECNO Camon 18" derived from `Build.MODEL`), `model`, and `platform="android"`.

Server resolves to a `user_device_id` and embeds it in the JWT. Client treats the JWT as opaque.

On OTP verify, if backend returns `409 device_cap_reached`, the app shows a "You already have 2 devices" screen listing the user's active devices (model + last seen) with a "Deactivate" action per device. Selecting one triggers `POST /devices/{id}/deactivate`. On success, app retries OTP verify automatically.

On any authenticated call returning `403 device_deactivated`, the app: wipes local downloads, clears EncryptedSharedPreferences, navigates to PhoneEntry, shows a one-shot informational dialog explaining the device was deactivated.

### Settings → Devices screen

Lists user's active devices: model, display name (editable inline), last-seen timestamp (WAT), current-device indicator, "Deactivate" button. Tapping deactivate on the current device confirms with strong warning ("This device will lose access to all licensed content"). Tapping deactivate on another device proceeds with confirm. Cooldown messaging if applicable: "You can deactivate another device after 2026-08-18."

### Storage

Downloaded MP4s in app-private dir: `context.filesDir/downloads/{film_id}.mp4`. Verified by sha256 on completion. DRM cycle will swap content with Widevine-protected streams in the same location structure.

### Player

`PlayerActivity` sets `WindowManager.LayoutParams.FLAG_SECURE` in `onCreate`. ExoPlayer plays local file URI. Resume position persisted in DataStore per film, restored on resume.

### Payment WebView flow

`PreLicenseConfirm` → "Confirm" → `POST /licenses/initiate` → opens Custom Tabs at `authorization_url` (preferred over WebView for sandboxed payment surface) → user completes sandbox flow → custom URL scheme callback brings user back into app → app polls `GET /licenses/{license_id}` every 2s for 60s → on `active` → navigate to MyFilms, kick off download.

### Stubbed/missing in slice

- No Play Integrity / root detection (DRM cycle)
- No Widevine DRM session manager (DRM cycle)
- No license revocation handler (paired with DRM)
- No HDMI/Miracast block (DRM cycle)
- No push notifications
- WhatsApp share opens WhatsApp with a deep link to a Play Store URL placeholder

## Local dev orchestration

`infra/docker-compose.yml` runs the full stack on localhost.

### Services

- **postgres** — `alaba:alaba@postgres:5432/alaba` — host port 5432
- **redis** — `redis://redis:6379` — host port 6379
- **minio** — S3 API on host port 9000, console on 9001 — three buckets initialized by an init container on first up
- **tusd** — host port 1080, hooks pointed at `backend-api:8000`
- **backend-api** — FastAPI via `uvicorn --reload`, bind-mounted source, host port 8000, bound to `0.0.0.0` for Android reachability
- **backend-worker** — same image as backend-api, runs `celery -A alaba.workers worker --beat`
- **web** — Next.js dev server, host port 3000
- **mailhog** — outbound dev SMTP, UI on host port 8025

### Networking notes

- Inside compose: service-name DNS (`postgres`, `redis`, `minio`).
- Android emulator on Windows → backend at `http://10.0.2.2:8000`.
- Android real device → backend at WSL2 host LAN IP (`make android-url` prints it).
- MinIO presigned URLs use a *host-reachable* endpoint, not the in-network `minio:9000`. `Settings.S3_PUBLIC_ENDPOINT` is separate from `S3_INTERNAL_ENDPOINT`.

### Volumes

- `postgres_data`, `minio_data`, `redis_data` — persistent service data
- Bind mounts: `./backend:/app`, `./web:/app` for hot reload
- Android source not in Docker (Android Studio on Windows host)

### Makefile surface

```
make up                  # docker compose up -d, wait for healthchecks
make down                # docker compose down
make logs                # docker compose logs -f
make backend-shell       # exec into backend-api
make worker-shell        # exec into backend-worker
make psql                # psql into postgres
make migrate             # alembic upgrade head
make migration msg="..." # alembic revision --autogenerate
make seed                # python infra/scripts/seed_films.py
make make-admin          # python infra/scripts/make_admin.py
make reset-db            # drop + recreate + migrate + seed
make test                # backend pytest
make web-dev             # npm run dev (if running web outside compose)
make android-url         # print backend URL for Android
```

### `.env` strategy

`infra/.env.example` committed with dev defaults and dummy keys. `infra/.env` gitignored. Compose reads via `env_file:`. Backend's `Settings` reads from env vars (compose injects). Web reads `NEXT_PUBLIC_*` for client and bare names for server.

### Webhook delivery during dev

Document `ngrok http 8000` in README. Backend additionally has a reconciliation task that polls Paystack's verification API for pending licenses older than 60 seconds — fallback when ngrok isn't running.

## Stub strategy

| Integration | Slice | Future cycle |
|---|---|---|
| OTP delivery | `MockOTPProvider` prints to stdout; production refuses to boot with this | Termii (`TermiiOTPProvider`) — DRM cycle |
| Payments in | Real Paystack test API (`sk_test_*`) | Paystack live (`sk_live_*`) — payouts cycle |
| Payouts out | `NoopPayoutProvider` (records intent, never transfers) | `PaystackTransfersProvider` — payouts cycle |
| Object storage | MinIO via Docker Compose | B2 — DRM cycle |
| Storage SDK | `boto3` with MinIO endpoint URL | Same `boto3`, B2 endpoint URL |
| CDN | None — direct MinIO presigned URLs | Cloudflare in front of B2 — DRM cycle |
| Push notifications | None | FCM — payouts cycle |
| Monitoring | None | Sentry + Uptime Robot — payouts cycle |
| DRM | None — clear MP4 download | Widevine L3 via 3rd-party provider — DRM cycle |
| SMS for producer email-OTP-on-sensitive-actions | Same MockOTPProvider | Termii — DRM cycle |

## Testing strategy

### Backend (`backend/tests/`)

- `pytest-asyncio` with `asyncio_mode=auto`.
- Per-test transaction-rollback DB fixture against real Postgres (testcontainers or compose-running Postgres with a test schema).
- Fake providers under `tests/fakes/`: `FakeOTPProvider` (collects codes in memory), `FakePaymentProvider` (simulates webhook delivery immediately).
- Folder structure: `unit/`, `integration/api/`, `integration/workers/`, `e2e/`.
- Coverage target: 70%+ on `services/` and `api/`.
- `pytest -m slow` skipped by default; includes FFmpeg-running transcode tests.
- Critical paths: webhook signature verification, replay idempotency, OTP rate limiting, license activation, download URL signing.

### Web (`web/`)

- Type safety + ESLint + `tsc --noEmit` as primary correctness mechanism. Pre-commit hook in slice (CI in production cycle).
- Vitest unit tests only for non-trivial pure functions (`formatNaira`, validators, JWT cookie parsing).
- Playwright e2e: one happy-path per major flow — producer register/agreement/dashboard, admin login/review/approve, producer-sees-film-approved.
- No snapshot tests, no visual regression in slice.

### Android (`android/app/src/{test,androidTest}/`)

- Unit tests (JVM): ViewModels with Turbine, repositories with MockK, use cases with fakes.
- Instrumented tests: one happy-path per critical screen on emulator.
- No screenshot tests; no DRM-related tests in slice.

### Manual test checklist (`docs/test-checklist.md`)

Maintained by hand. Run before each milestone. Covers what automated tests miss: real-device OTP, slow-network downloads, kill-and-resume, flaky upload, currency/timezone display, WhatsApp share, etc.

### Seed data

`infra/scripts/seed_films.py` creates:

- 1 admin (`admin@alaba.test`, password printed)
- 3 producers (1 unverified, 1 verified-no-films, 1 verified-with-films)
- 5 films in mixed states (pending upload, awaiting review, approved, rejected, withdrawn)
- 10 viewer users with mixed license combinations
- 50 sample licenses across films/users for dashboard exercise
- Sample MP4s downloaded from public-domain sources (committed by reference, not checked into git)

`make reset-db` flattens and reseeds in one command.

## Implementation waves (planning scaffold, not the plan)

The writing-plans skill will produce the detailed implementation plan. This is the wave scaffold to guide it.

| Wave | Focus | Estimate | Deliverable end-state |
|---|---|---|---|
| 0 | Foundations | 3-5d | `make up` brings everything up; `/health` works; Android shows placeholder |
| 1 | Auth (all three roles) + multi-device | 6-9d | Sign-in works on web (producer+admin) and Android (phone OTP via mock); `user_devices` table + N=2 cap + 90-day cooldown enforced; Settings → Devices screen on Android with deactivate flow; admin user-devices panel; `403 device_deactivated` handling |
| 2 | Producer onboarding + admin verification | 3-4d | Producer registers → accepts agreement → admin verifies → producer dashboard unlocked |
| 3 | Content pipeline + admin review | 6-8d | Producer uploads via tus → quality check → transcode → admin reviews → approves → film available |
| 4 | Catalog + film detail on Android | 3-4d | Approved films appear in Android catalog; film detail screen functional |
| 5 | Licensing + payment | 5-7d | Android user completes Paystack test purchase end-to-end |
| 6 | Download + playback | 4-6d | Licensed film downloads, plays in PlayerActivity with FLAG_SECURE |
| 7 | Ratings + WhatsApp share + settings | 2-3d | Rate bottom sheet, share link, settings screen complete |
| 8 | Dashboards | 5-7d | Producer + admin dashboards with real aggregates and weekly payout calculation |
| 9 | Withdrawal + polish + bug bash | 3-5d | Withdrawal flow, pre-commit hooks, READMEs, manual test pass |

Total: ~40-58 days of focused solo + Claude Code work. At 4-6 productive hours/day, ~9-14 calendar weeks. (Multi-device adds ~2-3 days net over baseline single-device.)

## Open items to resolve before or during implementation

- **Android package name** — currently `com.orbanforest.alaba`. Confirm or change before Wave 0.
- **Sample MP4 sources** — confirm public-domain set (Big Buck Bunny, Sintel, Tears of Steel). User may want different test content.
- **Distribution Agreement placeholder text** — slice ships with a placeholder. Track lawyer-drafted version delivery as a calendar dep. Distribution Agreement must explicitly disclose multi-device N=2 to producers.
- **T&C and Privacy Policy placeholders** — same. T&C should explain device-cap and cooldown to viewers.
- **Brief Promise #3 reframe** — brief currently reads "device-locked." Update wording to "locked to viewer accounts, up to 2 personal devices per viewer." Owned outside this spec but blocks accurate producer outreach.
- **`make android-url` helper script** — must handle the WSL2 → Windows host LAN IP detection robustly. Develop alongside Wave 0.
- **Backend cors origins** for Next.js dev — set in `Settings.CORS_ORIGINS`.
- **JWT secret strategy** — slice uses HS256 with shared secret in env. Switch to RS256 with separate public key for web/Android verification in production cycle.
- **Device cap value (N=2) and cooldown (90 days)** — committed for this slice. Revisit if abuse signals appear post-launch or if user research suggests N=3 is needed for typical household composition.

## Risks specific to this slice

- **WSL2 networking surprises** for Android device testing. Mitigated by `make android-url` helper and documenting the LAN IP setup.
- **Paystack webhook delivery in dev** requires ngrok or the polling fallback. Document both.
- **tus / tusd hook configuration** is fiddly — pin a specific tusd version and document the exact `--hooks-http` setup.
- **FFmpeg version drift** — pin a specific image (e.g., `linuxserver/ffmpeg:7.1-cli` or use the worker container's bundled binary).
- **Time pressure to add DRM mid-slice** — explicit non-goal here. If the temptation arises, finish the slice first, then start the DRM cycle's brainstorm.
- **Multi-device abuse signals** before launch — slice cannot detect account sharing (no analytics, no Play Integrity). Mitigation is the N=2 cap + cooldown alone. If post-launch data shows rampant sharing, anomaly detection lives in the payouts cycle.
- **Device-id collisions** — Android `UUID.randomUUID()` is statistically safe but not cryptographically attested. Slice trusts the client. Real attestation (Play Integrity) arrives in DRM cycle.

## Success criteria for the slice

A new developer (or Claude Code in a fresh context) can:

1. Clone the repo, run `make up`, wait for healthchecks, run `make seed`.
2. Open Android Studio, build the app, run on emulator, see the catalog populated.
3. Complete a license flow with Paystack test card (`4084 0840 8408 4081` etc.), see the film download, play it with `FLAG_SECURE` active.
4. Open `http://localhost:3000/producer/login`, log in as a seeded verified producer, upload a film via tus, see it transcode, see status updates in the films list.
5. Log out, log in as admin at `http://localhost:3000/admin/login`, see the producer's uploaded film in the review queue, approve it, confirm it appears in the Android catalog.
6. See dashboard aggregates updating on both portal sides as the above flows happen.
7. Run `make test` and have all backend tests pass.
8. **Multi-device verification:** Sign in on a second Android device/emulator with the same phone number; both devices reach Settings → Devices and see both listed; attempt a 3rd device → see device-cap UX; deactivate one device → 3rd device authorizes; verify deactivated device's downloads stop working and app returns to PhoneEntry; attempt second deactivation within 90 days → see cooldown messaging.

If all eight hold, the slice is done and the next brainstorm (DRM cycle) can begin.
