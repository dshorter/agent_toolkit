# tests/test_api/middleware/test_rate_limit.py
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.api.middleware.rate_limit import RateLimitMiddleware

@pytest.fixture
def mock_redis():
    async def mock_pipeline():
        mock = AsyncMock()
        mock.execute.return_value = [0, 1, 1, 1]
        return mock
    
    redis = AsyncMock()
    redis.client.return_value.__aenter__.return_value = AsyncMock()
    redis.pipeline = mock_pipeline
    return redis

@pytest.fixture
def app(mock_redis):
    app = FastAPI()
    
    class MockServer:
        def __init__(self):
            self.redis = mock_redis
    app.state.logger = MagicMock()
    
    app.state.server = MockServer()
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    app.add_middleware(RateLimitMiddleware)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_successful_request(client):
    response = client.get("/test")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers

def test_rate_limit_headers(client):
    response = client.get("/test")
    assert response.headers["X-RateLimit-Limit"] == "100"
    assert response.headers["X-RateLimit-Remaining"] == "99"
    assert response.headers["X-RateLimit-Reset"].isdigit()

def test_rate_limit_exceeded(client, mock_redis):
    # Setup mock to return high count
    async def mock_high_count():
        mock = AsyncMock()
        mock.execute.return_value = [0, 1, 101, 1]
        return mock
    
    mock_redis.pipeline = mock_high_count
    response = client.get("/test")
    assert response.status_code == 429
    assert "error" in response.json()

def test_redis_error_handling(client, mock_redis):
    # Setup mock to raise error
    async def mock_error():
        raise Exception("Redis error")
    
    mock_redis.pipeline = mock_error
    response = client.get("/test")
    assert response.status_code == 200

def test_different_clients(client):
    response1 = client.get("/test", headers={"X-Forwarded-For": "1.1.1.1"})
    response2 = client.get("/test", headers={"X-Forwarded-For": "2.2.2.2"})
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.headers["X-RateLimit-Remaining"] == response2.headers["X-RateLimit-Remaining"]