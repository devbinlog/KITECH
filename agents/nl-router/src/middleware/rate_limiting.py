"""
Rate Limiter Middleware for NL Router

Provides rate limiting with:
- Token bucket algorithm
- Per-user and global limits
- LLM API call cost tracking
- Sliding window support
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LimitType(str, Enum):
    """Types of rate limits"""

    REQUESTS = "requests"  # Number of requests
    LLM_TOKENS = "llm_tokens"  # LLM token usage
    LLM_CALLS = "llm_calls"  # Number of LLM API calls


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    llm_calls_per_minute: int = 20
    llm_calls_per_hour: int = 200
    llm_tokens_per_minute: int = 100000
    llm_tokens_per_hour: int = 1000000
    enable_user_limits: bool = True
    enable_global_limits: bool = True


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""

    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, returns True if successful"""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait until tokens are available"""
        self._refill()
        if self.tokens >= tokens:
            return 0
        return (tokens - self.tokens) / self.refill_rate


@dataclass
class SlidingWindow:
    """Sliding window counter for rate limiting"""

    window_size_seconds: int
    max_requests: int
    requests: list = field(default_factory=list)

    def add_request(self) -> bool:
        """Add request if within limit, returns True if allowed"""
        self._cleanup()
        if len(self.requests) >= self.max_requests:
            return False
        self.requests.append(time.time())
        return True

    def _cleanup(self):
        """Remove expired entries"""
        cutoff = time.time() - self.window_size_seconds
        self.requests = [t for t in self.requests if t > cutoff]

    def get_remaining(self) -> int:
        """Get remaining requests in current window"""
        self._cleanup()
        return max(0, self.max_requests - len(self.requests))

    def get_reset_time(self) -> float:
        """Get seconds until window resets"""
        if not self.requests:
            return 0
        oldest = min(self.requests)
        return max(0, self.window_size_seconds - (time.time() - oldest))


@dataclass
class UserQuota:
    """Per-user rate limit tracking"""

    user_id: str
    requests_minute: SlidingWindow
    requests_hour: SlidingWindow
    llm_calls_minute: SlidingWindow
    llm_calls_hour: SlidingWindow
    llm_tokens_minute: int = 0
    llm_tokens_hour: int = 0
    last_token_reset_minute: float = field(default_factory=time.time)
    last_token_reset_hour: float = field(default_factory=time.time)


class RateLimiter:
    """
    Rate limiter with multiple strategies

    Usage:
        limiter = RateLimiter()

        # Check before processing
        if limiter.check("user_123"):
            process_request()
            limiter.record_llm_usage("user_123", tokens=1500)
        else:
            raise HTTPException(429, "Rate limit exceeded")
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self._config = config or RateLimitConfig()
        self._user_quotas: Dict[str, UserQuota] = {}
        self._global_bucket = TokenBucket(
            capacity=self._config.requests_per_minute,
            tokens=self._config.requests_per_minute,
            refill_rate=self._config.requests_per_minute / 60,
        )
        self._global_llm_bucket = TokenBucket(
            capacity=self._config.llm_calls_per_minute,
            tokens=self._config.llm_calls_per_minute,
            refill_rate=self._config.llm_calls_per_minute / 60,
        )
        self._lock = asyncio.Lock()

    def _get_user_quota(self, user_id: str) -> UserQuota:
        """Get or create user quota"""
        if user_id not in self._user_quotas:
            self._user_quotas[user_id] = UserQuota(
                user_id=user_id,
                requests_minute=SlidingWindow(60, self._config.requests_per_minute),
                requests_hour=SlidingWindow(3600, self._config.requests_per_hour),
                llm_calls_minute=SlidingWindow(60, self._config.llm_calls_per_minute),
                llm_calls_hour=SlidingWindow(3600, self._config.llm_calls_per_hour),
            )
        return self._user_quotas[user_id]

    def check(self, user_id: Optional[str] = None) -> bool:
        """Check if request is allowed"""
        # Check global limit
        if self._config.enable_global_limits:
            if not self._global_bucket.consume():
                logger.warning("Global rate limit exceeded")
                return False

        # Check user limit
        if user_id and self._config.enable_user_limits:
            quota = self._get_user_quota(user_id)
            if not quota.requests_minute.add_request():
                logger.warning(f"User {user_id} rate limit exceeded (per minute)")
                return False
            if not quota.requests_hour.add_request():
                logger.warning(f"User {user_id} rate limit exceeded (per hour)")
                return False

        return True

    def check_llm(self, user_id: Optional[str] = None) -> bool:
        """Check if LLM call is allowed"""
        # Check global LLM limit
        if self._config.enable_global_limits:
            if not self._global_llm_bucket.consume():
                logger.warning("Global LLM rate limit exceeded")
                return False

        # Check user LLM limit
        if user_id and self._config.enable_user_limits:
            quota = self._get_user_quota(user_id)
            if not quota.llm_calls_minute.add_request():
                logger.warning(f"User {user_id} LLM rate limit exceeded (per minute)")
                return False
            if not quota.llm_calls_hour.add_request():
                logger.warning(f"User {user_id} LLM rate limit exceeded (per hour)")
                return False

        return True

    def record_llm_usage(self, user_id: Optional[str], tokens: int):
        """Record LLM token usage"""
        if user_id and self._config.enable_user_limits:
            quota = self._get_user_quota(user_id)

            # Reset counters if window expired
            now = time.time()
            if now - quota.last_token_reset_minute > 60:
                quota.llm_tokens_minute = 0
                quota.last_token_reset_minute = now
            if now - quota.last_token_reset_hour > 3600:
                quota.llm_tokens_hour = 0
                quota.last_token_reset_hour = now

            quota.llm_tokens_minute += tokens
            quota.llm_tokens_hour += tokens

    def check_token_limit(self, user_id: Optional[str], tokens: int) -> bool:
        """Check if token usage is within limits"""
        if not user_id or not self._config.enable_user_limits:
            return True

        quota = self._get_user_quota(user_id)

        # Reset if window expired
        now = time.time()
        if now - quota.last_token_reset_minute > 60:
            quota.llm_tokens_minute = 0

        if quota.llm_tokens_minute + tokens > self._config.llm_tokens_per_minute:
            return False

        if now - quota.last_token_reset_hour > 3600:
            quota.llm_tokens_hour = 0

        if quota.llm_tokens_hour + tokens > self._config.llm_tokens_per_hour:
            return False

        return True

    def get_quota_status(self, user_id: str) -> Dict[str, Any]:
        """Get quota status for a user"""
        quota = self._get_user_quota(user_id)
        return {
            "user_id": user_id,
            "requests": {
                "remaining_minute": quota.requests_minute.get_remaining(),
                "remaining_hour": quota.requests_hour.get_remaining(),
                "reset_minute": quota.requests_minute.get_reset_time(),
                "reset_hour": quota.requests_hour.get_reset_time(),
            },
            "llm_calls": {
                "remaining_minute": quota.llm_calls_minute.get_remaining(),
                "remaining_hour": quota.llm_calls_hour.get_remaining(),
            },
            "llm_tokens": {
                "used_minute": quota.llm_tokens_minute,
                "used_hour": quota.llm_tokens_hour,
                "limit_minute": self._config.llm_tokens_per_minute,
                "limit_hour": self._config.llm_tokens_per_hour,
            },
        }

    def get_global_status(self) -> Dict[str, Any]:
        """Get global rate limit status"""
        return {
            "requests": {
                "tokens_available": int(self._global_bucket.tokens),
                "capacity": self._global_bucket.capacity,
            },
            "llm_calls": {
                "tokens_available": int(self._global_llm_bucket.tokens),
                "capacity": self._global_llm_bucket.capacity,
            },
            "active_users": len(self._user_quotas),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(self, app, limiter: RateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        # Extract user ID from request (from auth header or IP)
        user_id = self._get_user_id(request)

        # Check rate limit
        if not self.limiter.check(user_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        if user_id:
            quota = self.limiter.get_quota_status(user_id)
            response.headers["X-RateLimit-Remaining"] = str(quota["requests"]["remaining_minute"])
            response.headers["X-RateLimit-Reset"] = str(int(quota["requests"]["reset_minute"]))

        return response

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try auth header
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            # In real app, decode JWT to get user ID
            return f"token:{auth[7:20]}"

        # Fall back to IP
        client = request.client
        if client:
            return f"ip:{client.host}"

        return None


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
