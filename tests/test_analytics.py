"""Tests for analytics endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_statistics(client: AsyncClient, auth_headers: dict):
    """Test getting event statistics."""
    # Create some events
    for i in range(3):
        await client.post(
            "/api/v1/events",
            json={
                "source": "test-server",
                "event_type": "api_request",
                "severity": "INFO",
                "message": f"Event {i}",
            },
            headers=auth_headers,
        )

    # Get statistics
    response = await client.get("/api/v1/analytics/statistics", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total_events"] > 0
    assert "by_severity" in data["data"]
    assert "by_type" in data["data"]


@pytest.mark.asyncio
async def test_get_summary(client: AsyncClient, auth_headers: dict):
    """Test getting analytics summary."""
    response = await client.get("/api/v1/analytics/summary", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "timestamp" in data
