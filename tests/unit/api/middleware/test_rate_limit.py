# tests/test_api/middleware/test_rate_limit.py

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import json
import logging

from src.api.middleware.rate_limit import RateLimitMiddleware
from src.core.logging import log_manager

@pytest.fixture
def mock_redis():
    """Provide a mock Redis instance."""
    async def mock_pipeline():
        mock = AsyncMock()
        mock.execute.return_value = [0, 1, 1, 1]  # Simulated Redis pipeline response
        return mock
    
    redis = AsyncMock()
    redis.client.return_value.__aenter__.return_value = AsyncMock()
    redis.pipeline = mock_pipeline
    return redis

@pytest.fixture
def app(mock_redis):
    """Create test FastAPI application with logging configuration."""
    app = FastAPI()
    
    class MockServer:
        def __init__(self):
            self.redis = mock_redis
    
    # Configure application state
    app.state.server = MockServer()
    app.state.logger = log_manager
    
    # Add test endpoint
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    # Add middleware with logging
    app.add_middleware(RateLimitMiddleware)
    
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def caplog(caplog):
    """Configure log capture."""
    caplog.set_level(logging.INFO)
    return caplog

def test_successful_request_logging(client, caplog):
    """Test that successful requests are properly logged."""
    with log_manager.task_sequence("test_request", "Rate limit check") as seq:
        response = client.get("/test")
        
    assert response.status_code == 200
    assert "Starting task sequence: Rate limit check" in caplog.text
    assert "Completed task sequence: Rate limit check" in caplog.text
    assert response.headers["X-RateLimit-Limit"]

def test_rate_limit_exceeded_logging(client, mock_redis, caplog):
    """Test that rate limit exceeded events are properly logged."""
    # Setup mock to simulate rate limit exceeded
    async def mock_high_count():
        mock = AsyncMock()
        mock.execute.return_value = [0, 1, 101, 1]  # Count exceeds limit
        return mock
    
    mock_redis.pipeline = mock_high_count
    
    with log_manager.task_sequence("test_rate_limit", "Rate limit exceeded check") as seq:
        response = client.get("/test")
    
    assert response.status_code == 429
    assert "Rate limit exceeded for client" in caplog.text
    assert response.json()["error"] == "Rate limit exceeded"

def test_redis_error_handling_logging(client, mock_redis, caplog):
    """Test that Redis errors are properly logged."""
    # Setup mock to simulate Redis error
    async def mock_error():
        raise Exception("Redis connection error")
    
    mock_redis.pipeline = mock_error
    
    with log_manager.task_sequence("test_redis_error", "Redis error check") as seq:
        response = client.get("/test")
    
    assert response.status_code == 200  # Should still work despite Redis error
    assert "Redis error" in caplog.text

def test_multiple_clients_logging(client, caplog):
    """Test logging of requests from different clients."""
    with log_manager.task_sequence("test_multiple_clients", "Multiple client check") as seq:
        response1 = client.get("/test", headers={"X-Forwarded-For": "1.1.1.1"})
        response2 = client.get("/test", headers={"X-Forwarded-For": "2.2.2.2"})
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert "client: 1.1.1.1" in caplog.text
    assert "client: 2.2.2.2" in caplog.text

@pytest.mark.asyncio
async def test_nested_tool_sequence_logging(app, caplog):
    """Test nested logging for Redis operations."""
    async with log_manager.task_sequence("test_nested", "Nested operation check") as main_seq:
        async with log_manager.tool_sequence("redis_check", "Redis rate check") as tool_seq:
            redis = app.state.server.redis
            await redis.pipeline()
    
    assert "Starting task sequence: Nested operation check" in caplog.text
    assert "Starting tool sequence: Redis rate check" in caplog.text
    assert "Completed tool sequence: Redis rate check" in caplog.text
    assert "Completed task sequence: Nested operation check" in caplog.text

def test_concurrent_request_logging(client, caplog):
    """Test logging of concurrent requests."""
    import threading
    import queue
    
    results = queue.Queue()
    
    def make_request():
        with log_manager.task_sequence("concurrent_test", "Concurrent request") as seq:
            response = client.get("/test")
            results.put(response.status_code)
    
    # Create and run multiple threads
    threads = [threading.Thread(target=make_request) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    # Check results
    status_codes = []
    while not results.empty():
        status_codes.append(results.get())
    
    assert all(code == 200 for code in status_codes)
    assert len([msg for msg in caplog.messages if "Concurrent request" in msg]) == 3
    
    
    
    