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
