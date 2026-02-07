"""
Enhanced Rate Limiting with Per-User Limits and Redis Storage

Features:
- Per-user rate limiting (authenticated users)
- Multiple time windows (per minute, per hour, per day)
- Redis-backed storage for distributed systems
- Graceful fallback to in-memory storage
- Sliding window algorithm for accurate rate limiting
"""

import hashlib
import time
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple

from fastapi import Request
from loguru import logger

try:
    import redis
    from redis.asyncio import Redis as AsyncRedis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory rate limiting")

from chatbi.config import get_config

config = get_config()


class EnhancedRateLimiter:
    """Enhanced rate limiter with per-user limits and Redis support.
    
    Rate Limit Tiers:
    - Anonymous users: 10 requests/minute, 100 requests/hour
    - Authenticated users: 60 requests/minute, 1000 requests/hour
    - Admin users: Unlimited
    
    Uses Redis for distributed rate limiting, falls back to in-memory.
    """
    
    def __init__(
        self,
        redis_client: Optional[AsyncRedis] = None,
        anonymous_limits: Tuple[int, int] = (10, 100),  # (per_minute, per_hour)
        user_limits: Tuple[int, int] = (60, 1000),
        use_redis: bool = True,
    ):
        """Initialize enhanced rate limiter.
        
        Args:
            redis_client: Optional Redis client for distributed storage
            anonymous_limits: (requests_per_minute, requests_per_hour) for anonymous users
            user_limits: (requests_per_minute, requests_per_hour) for authenticated users
            use_redis: Whether to use Redis (if available)
        """
        self.redis_client = redis_client if use_redis and REDIS_AVAILABLE else None
        self.anonymous_limits = anonymous_limits
        self.user_limits = user_limits
        
        # Fallback in-memory storage
        self.memory_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "limited_requests": 0,
            "bypassed_requests": 0,
            "redis_hits": 0,
            "memory_hits": 0,
        }
        
        logger.info(
            f"Enhanced rate limiter initialized: "
            f"anonymous={anonymous_limits}, user={user_limits}, "
            f"redis={'enabled' if self.redis_client else 'disabled'}"
        )
    
    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """Check if request should be rate limited.
        
        Args:
            request: FastAPI request
            user_id: Optional authenticated user ID
            is_admin: Whether user is admin (unlimited access)
        
        Returns:
            Tuple of (is_allowed, error_message, retry_after_seconds)
        """
        self.metrics["total_requests"] += 1
        
        # Admin users bypass rate limiting
        if is_admin:
            self.metrics["bypassed_requests"] += 1
            return True, None, None
        
        # Determine limits based on authentication status
        if user_id:
            identifier = f"user:{user_id}"
            limits = self.user_limits
        else:
            # Use IP address for anonymous users
            client_ip = self._get_client_ip(request)
            identifier = f"ip:{client_ip}"
            limits = self.anonymous_limits
        
        per_minute_limit, per_hour_limit = limits
        current_time = time.time()
        
        # Check both time windows
        for window_seconds, limit in [(60, per_minute_limit), (3600, per_hour_limit)]:
            allowed, retry_after = await self._check_window(
                identifier,
                window_seconds,
                limit,
                current_time,
            )
            
            if not allowed:
                self.metrics["limited_requests"] += 1
                window_name = "minute" if window_seconds == 60 else "hour"
                error_msg = (
                    f"Rate limit exceeded: {limit} requests per {window_name}. "
                    f"Retry after {retry_after} seconds."
                )
                return False, error_msg, retry_after
        
        return True, None, None
    
    async def _check_window(
        self,
        identifier: str,
        window_seconds: int,
        limit: int,
        current_time: float,
    ) -> Tuple[bool, Optional[int]]:
        """Check rate limit for a specific time window.
        
        Args:
            identifier: Unique identifier (user:xxx or ip:xxx)
            window_seconds: Time window in seconds (60 or 3600)
            limit: Maximum requests in this window
            current_time: Current timestamp
        
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        if self.redis_client:
            return await self._check_window_redis(
                identifier, window_seconds, limit, current_time
            )
        else:
            return await self._check_window_memory(
                identifier, window_seconds, limit, current_time
            )
    
    async def _check_window_redis(
        self,
        identifier: str,
        window_seconds: int,
        limit: int,
        current_time: float,
    ) -> Tuple[bool, Optional[int]]:
        """Check rate limit using Redis (sliding window with sorted sets).
        
        Redis keys: ratelimit:{identifier}:{window}
        Sorted set: timestamp -> score
        """
        try:
            key = f"ratelimit:{identifier}:{window_seconds}"
            window_start = current_time - window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, window_seconds * 2)
            
            results = await pipe.execute()
            request_count = results[1]  # zcard result
            
            self.metrics["redis_hits"] += 1
            
            if request_count >= limit:
                # Calculate retry_after based on oldest request in window
                oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    retry_after = int(oldest_time + window_seconds - current_time) + 1
                    return False, retry_after
                return False, window_seconds
            
            return True, None
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}, falling back to memory")
            return await self._check_window_memory(
                identifier, window_seconds, limit, current_time
            )
    
    async def _check_window_memory(
        self,
        identifier: str,
        window_seconds: int,
        limit: int,
        current_time: float,
    ) -> Tuple[bool, Optional[int]]:
        """Check rate limit using in-memory storage (fallback).
        
        Uses deque to store timestamps with sliding window.
        """
        key = f"{identifier}:{window_seconds}"
        window_start = current_time - window_seconds
        
        # Get or create deque for this identifier
        timestamps = self.memory_store[key]
        
        # Remove old timestamps outside the window
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()
        
        # Check if limit exceeded
        if len(timestamps) >= limit:
            retry_after = int(timestamps[0] + window_seconds - current_time) + 1
            self.metrics["memory_hits"] += 1
            return False, retry_after
        
        # Add current request
        timestamps.append(current_time)
        self.metrics["memory_hits"] += 1
        
        return True, None
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request (considering proxies).
        
        Args:
            request: FastAPI request
        
        Returns:
            Client IP address as string
        """
        # Check X-Forwarded-For header (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2...)
            # Take the first one as the original client IP
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header (alternative header used by some proxies)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct connection IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def get_metrics(self) -> Dict:
        """Get current rate limiting metrics.
        
        Returns:
            Dict with metrics
        """
        return {
            **self.metrics,
            "memory_clients": len(self.memory_store),
            "redis_enabled": self.redis_client is not None,
        }
    
    async def reset_user_limits(self, user_id: str):
        """Manually reset rate limits for a specific user (admin function).
        
        Args:
            user_id: User ID to reset
        """
        identifier = f"user:{user_id}"
        
        if self.redis_client:
            try:
                keys_to_delete = [
                    f"ratelimit:{identifier}:60",
                    f"ratelimit:{identifier}:3600",
                ]
                await self.redis_client.delete(*keys_to_delete)
                logger.info(f"Reset rate limits for user {user_id} in Redis")
            except Exception as e:
                logger.error(f"Failed to reset Redis rate limits: {e}")
        
        # Also reset memory store
        for window in [60, 3600]:
            key = f"{identifier}:{window}"
            if key in self.memory_store:
                del self.memory_store[key]
                logger.info(f"Reset rate limits for user {user_id} in memory")


# Global singleton instance
_global_rate_limiter: Optional[EnhancedRateLimiter] = None


def get_rate_limiter(redis_client: Optional[AsyncRedis] = None) -> EnhancedRateLimiter:
    """Get the global rate limiter instance.
    
    Args:
        redis_client: Optional Redis client to use
    
    Returns:
        Singleton EnhancedRateLimiter instance
    """
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = EnhancedRateLimiter(redis_client=redis_client)
    return _global_rate_limiter
