"""Test configuration."""
import os

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app import app
from app.db.base import Base
from app.db import get_db

# Tests run against a real PostgreSQL instance because models use Postgres-only
# column types (UUID, JSONB) that SQLite cannot compile. CI provisions a
# disposable Postgres service automatically; locally run `docker-compose up -d db`
# first, or override with TEST_DATABASE_URL.
DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql+asyncpg://logpulse:logpulse@localhost:5432/logpulse_db"),
)


@pytest.fixture
async def test_db():
    """Create test database schema."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client.

    Uses an allowed host (see Settings.ALLOWED_HOSTS / TrustedHostMiddleware) so
    requests aren't rejected with "Invalid host header".
    """
    async with AsyncClient(app=app, base_url="http://localhost") as client:
        yield client


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register and log in a test user, returning a bearer auth header."""
    credentials = {
        "username": "authtestuser",
        "email": "authtestuser@example.com",
        "password": "securepassword123",
    }
    await client.post("/api/v1/auth/register", json=credentials)

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": credentials["username"], "password": credentials["password"]},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
