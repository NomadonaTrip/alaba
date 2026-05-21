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
