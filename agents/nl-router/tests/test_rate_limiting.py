"""Tests for Rate Limiter Middleware"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from src.middleware.rate_limiting import (
    RateLimiter,
    RateLimitConfig,
    RateLimitMiddleware,
    TokenBucket,
    SlidingWindow,
    LimitType,
    get_rate_limiter,
)


class TestTokenBucket:
    """Tests for TokenBucket algorithm"""

    def test_initial_tokens(self):
        """Test bucket starts with full tokens"""
        bucket = TokenBucket(capacity=10, tokens=10, refill_rate=1.0)
        assert bucket.tokens == 10

    def test_consume_success(self):
        """Test successful token consumption"""
        bucket = TokenBucket(capacity=10, tokens=10, refill_rate=1.0)

        result = bucket.consume(1)

        assert result is True
        assert bucket.tokens == 9

    def test_consume_multiple(self):
        """Test consuming multiple tokens"""
        bucket = TokenBucket(capacity=10, tokens=10, refill_rate=1.0)

        result = bucket.consume(5)

        assert result is True
        assert bucket.tokens == 5

    def test_consume_fail_insufficient(self):
        """Test consumption fails when insufficient tokens"""
        bucket = TokenBucket(capacity=10, tokens=3, refill_rate=1.0)

        result = bucket.consume(5)

        assert result is False
        assert int(bucket.tokens) == 3  # Unchanged (use int for float precision)

    def test_refill_over_time(self):
        """Test tokens refill over time"""
        bucket = TokenBucket(capacity=10, tokens=5, refill_rate=2.0)
        bucket.last_refill = time.time() - 2  # 2 seconds ago

        bucket._refill()

        # Should have added 4 tokens (2 per second * 2 seconds)
        assert int(bucket.tokens) == 9  # Use int for float precision

    def test_refill_capped_at_capacity(self):
        """Test refill doesn't exceed capacity"""
        bucket = TokenBucket(capacity=10, tokens=9, refill_rate=5.0)
        bucket.last_refill = time.time() - 10  # 10 seconds ago

        bucket._refill()

        assert bucket.tokens == 10  # Capped at capacity

    def test_get_wait_time_zero(self):
        """Test wait time is zero when tokens available"""
        bucket = TokenBucket(capacity=10, tokens=5, refill_rate=1.0)

        wait = bucket.get_wait_time(3)

        assert wait == 0

    def test_get_wait_time_positive(self):
        """Test wait time calculation when tokens needed"""
        bucket = TokenBucket(capacity=10, tokens=2, refill_rate=1.0)

        wait = bucket.get_wait_time(5)

        # Need 3 more tokens at 1 per second = 3 seconds
        assert wait == pytest.approx(3.0, rel=0.1)


class TestSlidingWindow:
    """Tests for SlidingWindow algorithm"""

    def test_add_request_success(self):
        """Test adding request within limit"""
        window = SlidingWindow(window_size_seconds=60, max_requests=10)

        result = window.add_request()

        assert result is True
        assert len(window.requests) == 1

    def test_add_request_at_limit(self):
        """Test adding request at limit fails"""
        window = SlidingWindow(window_size_seconds=60, max_requests=2)
        window.add_request()
        window.add_request()

        result = window.add_request()

        assert result is False
        assert len(window.requests) == 2

    def test_cleanup_expired(self):
        """Test expired requests are cleaned up"""
        window = SlidingWindow(window_size_seconds=1, max_requests=10)
        window.requests = [time.time() - 2, time.time() - 2]  # Expired

        window._cleanup()

        assert len(window.requests) == 0

    def test_get_remaining(self):
        """Test getting remaining requests"""
        window = SlidingWindow(window_size_seconds=60, max_requests=10)
        window.add_request()
        window.add_request()
        window.add_request()

        remaining = window.get_remaining()

        assert remaining == 7

    def test_get_reset_time(self):
        """Test getting reset time"""
        window = SlidingWindow(window_size_seconds=60, max_requests=10)
        window.requests = [time.time()]

        reset = window.get_reset_time()

        assert reset > 0
        assert reset <= 60

    def test_get_reset_time_empty(self):
        """Test reset time is zero when no requests"""
        window = SlidingWindow(window_size_seconds=60, max_requests=10)

        reset = window.get_reset_time()

        assert reset == 0


class TestRateLimitConfig:
    """Tests for RateLimitConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.llm_calls_per_minute == 20
        assert config.llm_calls_per_hour == 200
        assert config.enable_user_limits is True
        assert config.enable_global_limits is True

    def test_custom_config(self):
        """Test custom configuration"""
        config = RateLimitConfig(
            requests_per_minute=100,
            llm_calls_per_minute=50,
            enable_global_limits=False,
        )

        assert config.requests_per_minute == 100
        assert config.llm_calls_per_minute == 50
        assert config.enable_global_limits is False


class TestRateLimiter:
    """Tests for RateLimiter"""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter with default config"""
        return RateLimiter()

    @pytest.fixture
    def strict_limiter(self):
        """Create rate limiter with strict limits"""
        config = RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=5,
            llm_calls_per_minute=1,
            llm_calls_per_hour=2,
        )
        return RateLimiter(config)

    def test_check_allows_request(self, limiter):
        """Test check allows normal requests"""
        result = limiter.check("user_123")
        assert result is True

    def test_check_global_limit(self, strict_limiter):
        """Test global rate limit"""
        # Exhaust global limit
        strict_limiter.check()
        strict_limiter.check()

        result = strict_limiter.check()
        assert result is False

    def test_check_user_limit(self, strict_limiter):
        """Test user rate limit"""
        strict_limiter.check("user_123")
        strict_limiter.check("user_123")

        result = strict_limiter.check("user_123")
        assert result is False

    def test_check_different_users_independent(self):
        """Test different users have independent limits"""
        # Disable global limits to isolate per-user limits
        config = RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=5,
            enable_global_limits=False,  # Disable global to test user isolation
        )
        limiter = RateLimiter(config)
        limiter.check("user_1")
        limiter.check("user_1")

        result = limiter.check("user_2")
        assert result is True

    def test_check_llm_allows(self, limiter):
        """Test LLM check allows normal requests"""
        result = limiter.check_llm("user_123")
        assert result is True

    def test_check_llm_limit(self, strict_limiter):
        """Test LLM rate limit"""
        strict_limiter.check_llm("user_123")

        result = strict_limiter.check_llm("user_123")
        assert result is False

    def test_record_llm_usage(self, limiter):
        """Test recording LLM token usage"""
        limiter.record_llm_usage("user_123", 1000)

        quota = limiter._get_user_quota("user_123")
        assert quota.llm_tokens_minute == 1000
        assert quota.llm_tokens_hour == 1000

    def test_check_token_limit_within(self, limiter):
        """Test token limit check when within limits"""
        result = limiter.check_token_limit("user_123", 1000)
        assert result is True

    def test_check_token_limit_exceeded(self):
        """Test token limit check when exceeded"""
        config = RateLimitConfig(
            llm_tokens_per_minute=1000,
            llm_tokens_per_hour=5000,
        )
        limiter = RateLimiter(config)

        limiter.record_llm_usage("user_123", 900)
        result = limiter.check_token_limit("user_123", 200)

        assert result is False

    def test_get_quota_status(self, limiter):
        """Test getting quota status for user"""
        limiter.check("user_123")
        limiter.record_llm_usage("user_123", 500)

        status = limiter.get_quota_status("user_123")

        assert status["user_id"] == "user_123"
        assert "requests" in status
        assert "llm_calls" in status
        assert "llm_tokens" in status
        assert status["llm_tokens"]["used_minute"] == 500

    def test_get_global_status(self, limiter):
        """Test getting global rate limit status"""
        limiter.check("user_1")
        limiter.check("user_2")

        status = limiter.get_global_status()

        assert "requests" in status
        assert "llm_calls" in status
        assert status["active_users"] == 2

    def test_user_quota_creation(self, limiter):
        """Test user quota created on first check"""
        assert "new_user" not in limiter._user_quotas

        limiter.check("new_user")

        assert "new_user" in limiter._user_quotas

    def test_token_reset_after_window(self, limiter):
        """Test token counters reset after window expires"""
        limiter.record_llm_usage("user_123", 1000)
        quota = limiter._get_user_quota("user_123")

        # Simulate window expiration
        quota.last_token_reset_minute = time.time() - 61

        limiter.record_llm_usage("user_123", 500)

        assert quota.llm_tokens_minute == 500  # Reset + new usage


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware"""

    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app"""
        return AsyncMock()

    @pytest.fixture
    def limiter(self):
        """Create rate limiter"""
        return RateLimiter()

    @pytest.mark.asyncio
    async def test_middleware_allows_request(self, mock_app, limiter):
        """Test middleware allows normal request"""
        middleware = RateLimitMiddleware(mock_app, limiter)

        request = MagicMock()
        request.headers = {"Authorization": "Bearer test_token"}
        request.client.host = "127.0.0.1"

        response = MagicMock()
        response.headers = {}
        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        call_next.assert_called_once_with(request)
        assert "X-RateLimit-Remaining" in result.headers

    @pytest.mark.asyncio
    async def test_middleware_blocks_when_limited(self, mock_app):
        """Test middleware blocks when rate limited"""
        config = RateLimitConfig(requests_per_minute=1)
        limiter = RateLimiter(config)
        middleware = RateLimitMiddleware(mock_app, limiter)

        request = MagicMock()
        request.headers = {}
        request.client.host = "127.0.0.1"

        call_next = AsyncMock()

        # First request succeeds
        response1 = MagicMock()
        response1.headers = {}
        call_next.return_value = response1
        await middleware.dispatch(request, call_next)

        # Second request blocked
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)

        assert exc_info.value.status_code == 429

    def test_get_user_id_from_bearer(self, mock_app, limiter):
        """Test user ID extraction from Bearer token"""
        middleware = RateLimitMiddleware(mock_app, limiter)

        request = MagicMock()
        request.headers = {"Authorization": "Bearer abc123xyz456789"}
        request.client = None

        user_id = middleware._get_user_id(request)

        # Extracts characters 7:20 from auth header (13 chars after "Bearer ")
        assert user_id == "token:abc123xyz4567"

    def test_get_user_id_from_ip(self, mock_app, limiter):
        """Test user ID extraction from IP"""
        middleware = RateLimitMiddleware(mock_app, limiter)

        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.100"

        user_id = middleware._get_user_id(request)

        assert user_id == "ip:192.168.1.100"

    def test_get_user_id_none(self, mock_app, limiter):
        """Test user ID returns None when no identifier"""
        middleware = RateLimitMiddleware(mock_app, limiter)

        request = MagicMock()
        request.headers = {}
        request.client = None

        user_id = middleware._get_user_id(request)

        assert user_id is None


class TestLimitType:
    """Tests for LimitType enum"""

    def test_limit_types(self):
        """Test limit type values"""
        assert LimitType.REQUESTS.value == "requests"
        assert LimitType.LLM_TOKENS.value == "llm_tokens"
        assert LimitType.LLM_CALLS.value == "llm_calls"


class TestGlobalRateLimiter:
    """Tests for global rate limiter instance"""

    def test_get_rate_limiter_singleton(self):
        """Test get_rate_limiter returns same instance"""
        import src.middleware.rate_limiting as rl_module

        # Reset global instance
        rl_module._rate_limiter = None

        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2


# ============================================================================
# 보강된 테스트: 계산 로직 검증
# ============================================================================

class TestTokenBucketCalculations:
    """TokenBucket 알고리즘 계산 정확성 검증"""

    def test_refill_rate_calculation(self):
        """토큰 리필 속도 계산 정확성"""
        # 초당 2개 토큰 리필, 5개 사용 후 2초 경과
        bucket = TokenBucket(capacity=10, tokens=5, refill_rate=2.0)
        bucket.last_refill = time.time() - 2  # 2초 전

        bucket._refill()

        # 5 + (2 * 2) = 9 토큰
        assert 8 <= bucket.tokens <= 10  # 약간의 시간 오차 허용

    def test_wait_time_calculation_precision(self):
        """대기 시간 계산 정밀도"""
        bucket = TokenBucket(capacity=10, tokens=0, refill_rate=1.0)

        # 5개 토큰 필요, 초당 1개 리필 → 5초 대기
        wait = bucket.get_wait_time(5)
        assert 4.9 <= wait <= 5.1

    def test_consume_with_partial_refill(self):
        """부분 리필 후 소비 테스트"""
        bucket = TokenBucket(capacity=10, tokens=3, refill_rate=2.0)
        bucket.last_refill = time.time() - 1  # 1초 전 (2개 리필)

        result = bucket.consume(4)  # 3 + 2 = 5 토큰, 4개 소비

        assert result is True
        assert bucket.tokens >= 0

    def test_capacity_is_absolute_maximum(self):
        """용량이 절대 최대값임을 검증"""
        bucket = TokenBucket(capacity=10, tokens=10, refill_rate=100.0)
        bucket.last_refill = time.time() - 100  # 오래된 시간

        bucket._refill()

        # 용량 초과 불가
        assert bucket.tokens == 10


class TestSlidingWindowCalculations:
    """SlidingWindow 알고리즘 계산 정확성 검증"""

    def test_window_expiration_calculation(self):
        """윈도우 만료 계산 정확성"""
        window = SlidingWindow(window_size_seconds=60, max_requests=10)

        # 요청 추가
        window.add_request()
        oldest_request = window.requests[0]

        # 리셋 시간은 가장 오래된 요청 기준
        reset_time = window.get_reset_time()
        expected_reset = 60 - (time.time() - oldest_request)

        assert abs(reset_time - expected_reset) < 0.1

    def test_remaining_requests_calculation(self):
        """남은 요청 수 계산 정확성"""
        window = SlidingWindow(window_size_seconds=60, max_requests=10)

        # 7개 요청
        for _ in range(7):
            window.add_request()

        remaining = window.get_remaining()
        assert remaining == 3

    def test_expired_requests_not_counted(self):
        """만료된 요청은 카운트에서 제외"""
        window = SlidingWindow(window_size_seconds=1, max_requests=5)

        # 오래된 요청 추가
        window.requests = [time.time() - 2, time.time() - 2, time.time() - 2]

        # 새 요청 가능해야 함
        result = window.add_request()
        assert result is True

        # 오래된 것들은 정리됨
        assert len(window.requests) == 1


class TestRateLimiterCalculations:
    """RateLimiter 종합 계산 검증"""

    def test_user_quota_isolation(self):
        """사용자별 할당량 격리 검증"""
        config = RateLimitConfig(
            requests_per_minute=5,
            enable_global_limits=False,
        )
        limiter = RateLimiter(config)

        # user1: 5개 소진
        for _ in range(5):
            limiter.check("user1")

        # user2: 여전히 가능
        result = limiter.check("user2")
        assert result is True

        # user1: 불가능
        result = limiter.check("user1")
        assert result is False

    def test_token_usage_accumulation(self):
        """LLM 토큰 사용량 누적 검증"""
        limiter = RateLimiter()

        limiter.record_llm_usage("user1", 500)
        limiter.record_llm_usage("user1", 300)
        limiter.record_llm_usage("user1", 200)

        quota = limiter._get_user_quota("user1")
        assert quota.llm_tokens_minute == 1000
        assert quota.llm_tokens_hour == 1000

    def test_per_minute_vs_per_hour_limits(self):
        """분당/시간당 제한 독립성 검증"""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=15,  # 분당 < 시간당
            enable_global_limits=False,
        )
        limiter = RateLimiter(config)

        # 10개 요청 (분당 제한 도달)
        for _ in range(10):
            limiter.check("user1")

        # 분당 제한으로 차단
        result = limiter.check("user1")
        assert result is False


class TestRateLimitEdgeCases:
    """Rate Limiting 엣지 케이스"""

    def test_zero_capacity_bucket(self):
        """용량 0인 버킷"""
        bucket = TokenBucket(capacity=0, tokens=0, refill_rate=1.0)
        result = bucket.consume(1)
        assert result is False

    def test_very_high_refill_rate(self):
        """매우 높은 리필 속도"""
        bucket = TokenBucket(capacity=1000, tokens=0, refill_rate=1000.0)
        bucket.last_refill = time.time() - 1

        bucket._refill()

        assert bucket.tokens == 1000  # capacity로 제한

    def test_concurrent_user_pattern(self):
        """다수 사용자 동시 패턴"""
        config = RateLimitConfig(
            requests_per_minute=100,
            enable_user_limits=True,
        )
        limiter = RateLimiter(config)

        # 50명의 사용자가 각각 2개씩 요청
        for i in range(50):
            limiter.check(f"user_{i}")
            limiter.check(f"user_{i}")

        # 모든 사용자의 요청이 성공해야 함
        status = limiter.get_global_status()
        assert status["active_users"] == 50
