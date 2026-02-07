import hashlib
import time
from collections import defaultdict, deque
from collections.abc import Callable
from functools import lru_cache
from typing import Deque, Dict, List, Optional, Set, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from chatbi.config import get_config
from chatbi.exceptions import RateLimitError


class RateLimiter(BaseHTTPMiddleware):
    """
    Rate limiting middleware to protect API endpoints from abuse.
    Implements a sliding window algorithm for accurate rate limiting with
    memory optimization and whitelisting capabilities.
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_limit: int = 60,
        window_seconds: int = 60,
        exclude_paths: Optional[list[str]] = None,
        whitelist_ips: Optional[list[str]] = None,
        max_clients_to_track: int = 10000,
        burst_multiplier: float = 2.0,
    ):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.burst_limit = int(
            requests_limit * burst_multiplier
        )  # Allow occasional bursts

        # Dictionary to store request timestamps for each client
        self.request_records: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=self.burst_limit)
        )

        # Track when we last cleaned up to avoid doing it too often
        self.last_cleanup = time.time()
        self.cleanup_interval = 60  # Cleanup every minute
        self.max_clients_to_track = max_clients_to_track

        # Paths that should not be rate-limited (health checks, docs, etc.)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/metrics",
        ]

        # IP whitelist - these IPs bypass rate limiting entirely
        self.whitelist_ips = set(whitelist_ips or [])

        # Add localhost to whitelist by default for development environments
        if get_config().env != "production":
            self.whitelist_ips.update(["127.0.0.1", "::1", "localhost"])

        # Track metrics
        self.metrics = {
            "total_requests": 0,
            "limited_requests": 0,
            "bypassed_requests": 0,
            "clients_tracked": 0,
        }

        logger.info(
            f"Rate limiter initialized: {requests_limit} requests per {window_seconds}s, "
            f"tracking up to {max_clients_to_track} clients"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and apply rate limiting if necessary.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response object
        """
        # Update metrics
        self.metrics["total_requests"] += 1

        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            self.metrics["bypassed_requests"] += 1
            return await call_next(request)

        # Use client IP as identifier (with X-Forwarded-For header support)
        client_ip = self._get_client_ip(request)

        # Skip rate limiting for whitelisted IPs
        if client_ip in self.whitelist_ips:
            self.metrics["bypassed_requests"] += 1
            return await call_next(request)

        # Get client identifier including API key if available
        client_id = self._get_client_identifier(request, client_ip)

        # Periodically clean up stale records
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_records(current_time)

        # Check if client has exceeded rate limit
        if not self._is_rate_limited(client_id, current_time):
            # Client hasn't exceeded limit, process request
            self.request_records[client_id].append(current_time)
            self.metrics["clients_tracked"] = len(self.request_records)

            # Process the request
            response = await call_next(request)

            # Add rate limit headers to response
            remaining = self._get_remaining_requests(client_id, current_time)
            response.headers["X-RateLimit-Limit"] = str(self.requests_limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(
                int(current_time + self.window_seconds)
            )

            return response
        else:
            # Client has exceeded rate limit
            self.metrics["limited_requests"] += 1

            # Calculate retry after time
            oldest_timestamp = self._get_oldest_valid_timestamp(client_id, current_time)
            retry_after = max(
                1, int(oldest_timestamp + self.window_seconds - current_time)
            )

            # Return rate limit error
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after)),
                },
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Rate limit of {self.requests_limit} requests per {self.window_seconds} seconds exceeded. Please try again in {retry_after} seconds.",
                },
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, properly handling proxies"""
        # First check for X-Forwarded-For header (standard for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the list (client IP)
            return forwarded_for.split(",")[0].strip()

        # Check for other common proxy headers
        if "X-Real-IP" in request.headers:
            return request.headers.get("X-Real-IP")

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _get_client_identifier(self, request: Request, client_ip: str) -> str:
        """
        Generate a unique identifier for the client based on IP and other attributes.

        This creates a composite key that can distinguish between different users
        from the same IP address (e.g., behind NAT) based on their API key or
        session/user identifiers.
        """
        # Start with client IP
        identifier_parts = [client_ip]

        # Add API key if present
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            # Only use a hash of the API key for privacy/security
            identifier_parts.append(hashlib.md5(api_key.encode()).hexdigest()[:8])

        # Add authorization header hash if present (for JWT tokens, etc.)
        auth_header = request.headers.get("Authorization", "")
        if auth_header and auth_header.startswith("Bearer "):
            # Only use a short hash of the token
            token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]
            identifier_parts.append(token_hash)

        # Add user-agent for better differentiation
        user_agent = request.headers.get("User-Agent", "")
        if user_agent:
            user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:6]
            identifier_parts.append(user_agent_hash)

        # Combine all parts
        return ":".join(identifier_parts)

    def _is_rate_limited(self, client_id: str, current_time: float) -> bool:
        """
        Check if client has exceeded rate limit using sliding window algorithm.

        Args:
            client_id: Unique client identifier
            current_time: Current timestamp

        Returns:
            Boolean indicating if client should be rate limited
        """
        # If this is the first request from this client, they're not rate limited
        if client_id not in self.request_records:
            return False

        # Count requests in the current window
        window_start = current_time - self.window_seconds
        request_count = sum(
            1
            for timestamp in self.request_records[client_id]
            if timestamp > window_start
        )

        # Return True if client has exceeded rate limit
        return request_count >= self.requests_limit

    def _get_remaining_requests(self, client_id: str, current_time: float) -> int:
        """Get remaining requests allowed in the current window"""
        if client_id not in self.request_records:
            return self.requests_limit

        window_start = current_time - self.window_seconds
        request_count = sum(
            1
            for timestamp in self.request_records[client_id]
            if timestamp > window_start
        )

        return max(0, self.requests_limit - request_count)

    def _get_oldest_valid_timestamp(self, client_id: str, current_time: float) -> float:
        """Get the oldest timestamp still in the current window"""
        if client_id not in self.request_records or not self.request_records[client_id]:
            return current_time

        window_start = current_time - self.window_seconds
        valid_timestamps = [
            ts for ts in self.request_records[client_id] if ts > window_start
        ]

        if not valid_timestamps:
            return current_time

        return min(valid_timestamps)

    def reset_for_client(self, client_id: str) -> None:
        """
        Reset rate limit for a specific client.
        """
        if client_id in self.request_records:
            del self.request_records[client_id]

    def _cleanup_records(self, current_time: float) -> None:
        """
        Clean up stale records and enforce maximum tracked clients.

        This prevents memory growth by:
        1. Removing records for clients who haven't made requests recently
        2. Ensuring we don't track more than max_clients_to_track clients
        """
        self.last_cleanup = current_time

        # 1. Remove records older than 2x the window time
        stale_threshold = current_time - (self.window_seconds * 2)

        clients_to_remove = []
        for client_id, timestamps in self.request_records.items():
            # If all timestamps are old, remove this client
            if not timestamps or max(timestamps) < stale_threshold:
                clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            del self.request_records[client_id]

        # 2. If still tracking too many clients, remove the least recently active
        if len(self.request_records) > self.max_clients_to_track:
            # Sort clients by their most recent activity
            clients_by_recency = sorted(
                self.request_records.items(), key=lambda x: max(x[1]) if x[1] else 0
            )

            # Remove least recently active clients until we're under the limit
            clients_to_remove = clients_by_recency[
                : len(self.request_records) - self.max_clients_to_track
            ]
            for client_id, _ in clients_to_remove:
                del self.request_records[client_id]

        # Update metrics
        self.metrics["clients_tracked"] = len(self.request_records)

        # Log cleanup results
        if clients_to_remove:
            logger.debug(
                f"Rate limiter cleanup: removed {len(clients_to_remove)} stale client records"
            )

    def get_metrics(self) -> dict[str, int]:
        """Get current rate limiter metrics"""
        return self.metrics
