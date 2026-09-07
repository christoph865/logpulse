"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
    }

    response = await client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    """Test registering duplicate user."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
    }

    # Register first user
    await client.post("/api/v1/auth/register", json=user_data)

    # Try to register duplicate
    response = await client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
