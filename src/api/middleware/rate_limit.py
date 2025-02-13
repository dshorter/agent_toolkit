# src/api/middleware/rate_limit.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import time
import json
from typing import Callable, Dict, Any, Tuple
import uuid

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with sequence-aware logging.
    
    Implements a sliding window rate limiter using Redis, with detailed
    logging of all rate limiting decisions and operations.
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize the middleware with default settings."""
        super().__init__(app)
        self.window_size = None
        self.max_requests = None

    async def _get_settings(self, request: Request) -> None:
        """Load rate limiting settings from application configuration."""
        if self.window_size is None:
            settings = request.app.state.settings
            self.window_size = settings.middleware.RATE_LIMIT_WINDOW_SECONDS
            self.max_requests = settings.middleware.RATE_LIMIT_MAX_REQUESTS

    async def _check_rate_limit(self, request: Request, client_ip: str) -> Tuple[int, int]:
        """
        Check if the request exceeds the rate limit.
        
        Uses Redis sorted sets to implement a sliding window:
        1. Remove old entries outside our window
        2. Add the current request
        3. Count total requests in the window
        4. Set expiration on the key
        """
        now = time.time()
        redis = request.app.state.server.redis
        key = f"ratelimit:{client_ip}"
        logger = request.app.state.logger
        
        try:
            async with logger.tool_sequence("redis_check", f"Check rate limit for {client_ip}"):
                pipe = await redis.pipeline()
                window_start = now - self.window_size
                
                # Remove old entries and add new one atomically
                await pipe.zremrangebyscore(key, 0, window_start)
                await pipe.zadd(key, {str(now): now})
                await pipe.zcount(key, window_start, now)
                await pipe.expire(key, self.window_size)
                
                results = await pipe.execute()
                current_count = results[2]
                window_reset = int(now + self.window_size)
                
                logger.log_with_context(
                    logging.INFO,
                    f"Rate limit check: {current_count}/{self.max_requests} requests",
                    client_ip=client_ip,
                    count=current_count,
                    limit=self.max_requests
                )
                
                return current_count, window_reset
                
        except Exception as e:
            logger.log_with_context(
                logging.ERROR,
                f"Rate limit error: {str(e)}",
                client_ip=client_ip,
                error=str(e)
            )
            # Return values that won't trigger rate limit
            return 0, int(now + self.window_size)

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """Process an incoming request and apply rate limiting."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        await self._get_settings(request)
        
        client_ip = request.client.host if request.client else "unknown"
        task_id = str(uuid.uuid4())
        logger = request.app.state.logger

        async with logger.task_sequence(task_id, f"Rate limit request from {client_ip}") as seq:
            current_count, window_reset = await self._check_rate_limit(request, client_ip)
            is_rate_limited = current_count > self.max_requests

            if is_rate_limited:
                logger.log_with_context(
                    logging.WARNING,
                    f"Rate limit exceeded for client: {client_ip}",
                    client_ip=client_ip,
                    reset_time=window_reset
                )

            async def send_wrapper(message: Message) -> None:
                """Add rate limit headers to response."""
                if message["type"] == "http.response.start":
                    headers = message.setdefault("headers", [])
                    headers.extend([
                        (b"X-RateLimit-Limit", str(self.max_requests).encode()),
                        (b"X-RateLimit-Remaining", str(max(0, self.max_requests - current_count)).encode()),
                        (b"X-RateLimit-Reset", str(window_reset).encode())
                    ])
                    if is_rate_limited:
                        message["status"] = 429
                await send(message)

            if is_rate_limited:
                # Return rate limit exceeded response
                await send({
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"X-RateLimit-Limit", str(self.max_requests).encode()),
                        (b"X-RateLimit-Remaining", b"0"),
                        (b"X-RateLimit-Reset", str(window_reset).encode())
                    ]
                })
                error_message = {
                    "error": "Rate limit exceeded",
                    "reset_at": window_reset
                }
                await send({
                    "type": "http.response.body",
                    "body": json.dumps(error_message).encode()
                })
            else:
                logger.log_with_context(
                    logging.INFO,
                    f"Request allowed for client: {client_ip}",
                    client_ip=client_ip,
                    remaining=self.max_requests - current_count
                )
                await self.app(scope, receive, send_wrapper)