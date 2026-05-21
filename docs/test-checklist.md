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

> **DEFERRED — requires Android Studio + two emulators/devices. Cannot run in WSL2 headless environment.**

- [ ] Device A: sign in with phone X
- [ ] Device B (different `device_id`): sign in with phone X → SignedIn (both devices active)
- [ ] Device C (third device_id): sign in with phone X → DeviceCapReached screen
- [ ] Pick one of A/B to deactivate → Mode B verify-ticket → C signs in successfully
- [ ] The deactivated device's next API call (e.g., open Settings → Devices) returns 403 → bounces to "This device is signed out"

### Cooldown

> **DEFERRED — requires Android emulator(s).**

- [ ] On Device A (active), open Settings → Devices → Deactivate "Device B" → 90-day cooldown begins
- [ ] Immediately try to deactivate "Device C" (if a third exists) or sign in a third device → returns 429 cooldown_active with unlock date

### Admin force-deactivate path

> **DEFERRED — requires Android emulator. Web side verified via curl automation below.**

- [ ] On Device A, sign in. Then via web admin, force-deactivate Device A
- [ ] Device A's next request returns 403 → app navigates to "This device is signed out"
- [ ] Verify `admin_actions` row exists in DB with the reason text
