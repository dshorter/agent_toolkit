# src/api/middleware/rate_limit.py
# Status: CURRENT
# Version: 1.0
# Last Updated: 2025-02-08
# Superseded By: N/A
# Historical Context: Initial implementation of rate limiting middleware using Redis
# for request tracking. Designed to work within free-tier service constraints.
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import time
import json
from typing import Callable, Dict, Any, Tuple

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.window_size = 60
        self.max_requests = 100

    async def _check_rate_limit(self, request: Request, client_ip: str) -> Tuple[int, int]:
        now = time.time()
        redis = request.app.state.server.redis
        key = f"ratelimit:{client_ip}"
        
        pipe = await redis.pipeline()
        window_start = now - self.window_size
        
        await pipe.zremrangebyscore(key, 0, window_start)
        await pipe.zadd(key, {str(now): now})
        await pipe.zcount(key, window_start, now)
        await pipe.expire(key, self.window_size)
        
        results = await pipe.execute()
        current_count = results[2]
        window_reset = int(now + self.window_size)
        
        return current_count, window_reset

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"

        try:
            current_count, window_reset = await self._check_rate_limit(request, client_ip)
            is_rate_limited = current_count > self.max_requests

            async def send_wrapper(message: Message) -> None:
                if message["type"] == "http.response.start":
                    headers = message.setdefault("headers", [])
                    # Add rate limit headers
                    headers.extend([
                        (b"X-RateLimit-Limit", str(self.max_requests).encode()),
                        (b"X-RateLimit-Remaining", str(max(0, self.max_requests - current_count)).encode()),
                        (b"X-RateLimit-Reset", str(window_reset).encode())
                    ])
                    if is_rate_limited:
                        message["status"] = 429
                await send(message)

            if is_rate_limited:
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
                await self.app(scope, receive, send_wrapper)

        except Exception as e:
            request.app.state.logger.error(f"Rate limit error: {str(e)}", exc_info=True)
            await self.app(scope, receive, send)