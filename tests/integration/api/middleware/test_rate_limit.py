# tests/test_api/middleware/test_rate_limit.py
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

from src.config.settings import Settings
from src.api.middleware.rate_limit import RateLimitMiddleware

@pytest.fixture
def test_settings() -> Settings:
    """Creates test configuration with specific rate limiting settings.
    
    We use a short window and low request limit to make testing faster
    and more predictable. The 2-second window allows us to test window
    reset behavior without long waits.
    """
    settings = Settings(
        ENVIRONMENT="test",
        middleware=dict(
            RATE_LIMIT_WINDOW_SECONDS=2,
            RATE_LIMIT_MAX_REQUESTS=3
        )
    )
    return settings

@pytest.fixture
def mock_redis():
    """Creates mock Redis instance that tracks requests in memory.
    
    This mock implements just enough Redis functionality to support
    our sliding window rate limiting, including pipeline operations
    and sorted set commands.
    """
    class MockRedis:
        def __init__(self):
            self.storage = {}  # Stores our rate limit data
            self._current_key = ""  # Tracks current operation's key
            
        async def pipeline(self):
            """Returns self since we'll implement pipeline operations directly."""
            return self
            
        async def zremrangebyscore(self, key: str, min_score: float, max_score: float):
            """Removes entries outside our time window."""
            self._current_key = key
            if key not in self.storage:
                return 0
            self.storage[key] = {
                ts: score for ts, score in self.storage[key].items()
                if score > max_score
            }
            return 0
            
        async def zadd(self, key: str, members: dict):
            """Adds a new request timestamp to our set."""
            if key not in self.storage:
                self.storage[key] = {}
            timestamp = float(list(members.keys())[0])
            self.storage[key][timestamp] = timestamp
            return 1
            
        async def zcount(self, key: str, min_score: float, max_score: float):
            """Counts requests within our time window."""
            if key not in self.storage:
                return 0
            return len([
                score for score in self.storage[key].values()
                if min_score <= score <= max_score
            ])
            
        async def expire(self, key: str, seconds: int):
            """Sets expiration on our rate limit keys."""
            return 1
            
        async def execute(self):
            """Simulates pipeline execution by returning counts."""
            count = len(self.storage.get(self._current_key, {}))
            return [0, 1, count, 1]
    
    return MockRedis()

@pytest.fixture
def app(test_settings, mock_redis) -> FastAPI:
    """Creates FastAPI test application with rate limiting configured."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    class MockServer:
        def __init__(self):
            self.redis = mock_redis
            
    app.state.server = MockServer()
    app.state.settings = test_settings
    app.state.logger = MagicMock()
    app.add_middleware(RateLimitMiddleware)
    
    return app

@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Creates an async test client for our FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_rate_limit_configuration(client: AsyncClient, test_settings: Settings):
    """Tests that rate limiter correctly enforces configured limits."""
    # First request should succeed
    response = await client.get("/test")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == str(test_settings.middleware.RATE_LIMIT_MAX_REQUESTS)
    assert response.headers["X-RateLimit-Remaining"] == str(test_settings.middleware.RATE_LIMIT_MAX_REQUESTS - 1)
    
    # Second request should succeed
    response = await client.get("/test")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Remaining"] == str(test_settings.middleware.RATE_LIMIT_MAX_REQUESTS - 2)
    
    # Third request should succeed (hitting limit)
    response = await client.get("/test")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Remaining"] == "0"
    
    # Fourth request should be rate limited
    response = await client.get("/test")
    assert response.status_code == 429
    error_data = response.json()
    assert "error" in error_data
    assert "reset_at" in error_data

@pytest.mark.asyncio
async def test_window_reset(client: AsyncClient, test_settings: Settings):
    """Tests that rate limit window correctly resets after configured time."""
    # Use up the rate limit
    for _ in range(test_settings.middleware.RATE_LIMIT_MAX_REQUESTS):
        response = await client.get("/test")
        assert response.status_code == 200
    
    # Verify we're now rate limited
    response = await client.get("/test")
    assert response.status_code == 429
    
    # Wait for window to reset
    await asyncio.sleep(test_settings.middleware.RATE_LIMIT_WINDOW_SECONDS)
    
    # Verify we can make requests again
    response = await client.get("/test")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Remaining"] == str(test_settings.middleware.RATE_LIMIT_MAX_REQUESTS - 1)

@pytest.mark.asyncio
async def test_different_endpoints_share_limit(client: AsyncClient, test_settings: Settings, app: FastAPI):
    """Tests that rate limits apply across different endpoints."""
    @app.get("/another")
    async def another_endpoint():
        return {"status": "ok"}
    
    # Use up most of the limit on first endpoint
    for _ in range(test_settings.middleware.RATE_LIMIT_MAX_REQUESTS - 1):
        response = await client.get("/test")
        assert response.status_code == 200
    
    # Verify the limit carries over to the other endpoint
    response = await client.get("/another")
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Remaining"] == "0"
    
    # Next request to either endpoint should be limited
    response = await client.get("/test")
    assert response.status_code == 429
    assert "error" in response.json()

@pytest.mark.asyncio
async def test_redis_error_handling(client: AsyncClient, mock_redis):
    """Tests graceful handling of Redis errors."""
    async def mock_error():
        raise Exception("Redis error")
    
    mock_redis.pipeline = mock_error
    
    # Request should still succeed even with Redis error
    response = await client.get("/test")
    assert response.status_code == 200
    
    # Logger should have recorded the error
    client.app.state.logger.error.assert_called_once()
    
    