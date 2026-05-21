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
