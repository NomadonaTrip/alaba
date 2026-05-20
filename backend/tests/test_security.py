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
