"""Tests for event endpoints."""
import pytest
from httpx import AsyncClient

from app.schemas import EventCreate


@pytest.mark.asyncio
async def test_create_event(client: AsyncClient, auth_headers: dict):
    """Test creating an event."""
    event_data = {
        "source": "test-server",
        "event_type": "api_request",
        "severity": "WARNING",
        "message": "Test event message",
        "event_metadata": {"endpoint": "/test", "status": 200},
    }

    response = await client.post("/api/v1/events", json=event_data, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "test-server"
    assert data["event_type"] == "api_request"
    assert data["severity"] == "WARNING"


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient, auth_headers: dict):
    """Test listing events."""
    # Create an event first
    event_data = {
        "source": "test-server",
        "event_type": "api_request",
        "severity": "INFO",
        "message": "Test event",
    }
    await client.post("/api/v1/events", json=event_data, headers=auth_headers)

    # List events
    response = await client.get("/api/v1/events", headers=auth_headers)

    assert response.status_code == 200
    events = response.json()
    assert len(events) > 0
    assert events[0]["source"] == "test-server"


@pytest.mark.asyncio
async def test_invalid_severity(client: AsyncClient, auth_headers: dict):
    """Test creating event with invalid severity."""
    event_data = {
        "source": "test-server",
        "event_type": "api_request",
        "severity": "INVALID",
        "message": "Test event",
    }

    response = await client.post("/api/v1/events", json=event_data, headers=auth_headers)
    assert response.status_code == 422
