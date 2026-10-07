"""Tests for Cache Service"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone

from src.app.services.cache_service import (
    CacheEntry,
    InMemoryCache,
    CacheService,
    CACHE_CONFIG,
    INVALIDATION_RULES,
    get_cache,
    invalidate_cache,
    cached,
)


class TestCacheEntry:
    """Tests for CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test CacheEntry creation with defaults"""
        entry = CacheEntry(value={"data": "test"}, created_at=datetime.now(timezone.utc), ttl_seconds=300)

        assert entry.value == {"data": "test"}
        assert entry.hit_count == 0
        assert entry.ttl_seconds == 300

    def test_expires_at_calculation(self):
        """Test expires_at property"""
        created = datetime(2024, 1, 24, 10, 0, 0)
        entry = CacheEntry(value="test", created_at=created, ttl_seconds=300)

        expected_expiry = created + timedelta(seconds=300)
        assert entry.expires_at == expected_expiry

    def test_is_expired_false(self):
        """Test is_expired when not expired"""
        entry = CacheEntry(
            value="test",
            created_at=datetime.now(timezone.utc),
            ttl_seconds=3600,  # 1 hour
        )

        assert entry.is_expired is False

    def test_is_expired_true(self):
        """Test is_expired when expired"""
        entry = CacheEntry(
            value="test",
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            ttl_seconds=300,  # 5 minutes ago
        )

        assert entry.is_expired is True


class TestInMemoryCache:
    """Tests for InMemoryCache class"""

    @pytest.fixture
    def cache(self):
        """Create InMemoryCache instance"""
        return InMemoryCache(max_size=100)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get operations"""
        await cache.set("key1", "value1", ttl=300)
        result = await cache.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache):
        """Test getting non-existent key returns None"""
        result = await cache.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_expired_key(self, cache):
        """Test getting expired key returns None and removes entry"""
        # Set with 0 TTL (immediately expired)
        await cache.set("expired_key", "value", ttl=0)

        # Wait a tiny bit to ensure expiration
        await asyncio.sleep(0.01)

        result = await cache.get("expired_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_hit_count_increment(self, cache):
        """Test hit count increments on get"""
        await cache.set("key1", "value1", ttl=300)

        # Access multiple times
        await cache.get("key1")
        await cache.get("key1")
        await cache.get("key1")

        # Check hit count via stats
        stats = await cache.get_stats()
        assert stats["total_hits"] >= 3

    @pytest.mark.asyncio
    async def test_delete_key(self, cache):
        """Test delete specific key"""
        await cache.set("key1", "value1")
        result = await cache.delete("key1")

        assert result is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache):
        """Test delete non-existent key returns False"""
        result = await cache.delete("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_pattern_wildcard(self, cache):
        """Test delete with wildcard pattern"""
        await cache.set("prefix:key1", "value1")
        await cache.set("prefix:key2", "value2")
        await cache.set("other:key3", "value3")

        deleted_count = await cache.delete_pattern("prefix:*")

        assert deleted_count == 2
        assert await cache.get("prefix:key1") is None
        assert await cache.get("prefix:key2") is None
        assert await cache.get("other:key3") == "value3"

    @pytest.mark.asyncio
    async def test_delete_pattern_all(self, cache):
        """Test delete all keys with * pattern"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        deleted_count = await cache.delete_pattern("*")

        assert deleted_count == 2
        stats = await cache.get_stats()
        assert stats["total_keys"] == 0

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Test exists method"""
        await cache.set("key1", "value1")

        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_get_stats(self, cache):
        """Test get_stats method"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.get("key1")

        stats = await cache.get_stats()

        assert stats["total_keys"] == 2
        assert stats["active_keys"] == 2
        assert stats["total_hits"] >= 1
        assert stats["max_size"] == 100

    @pytest.mark.asyncio
    async def test_eviction_on_max_size(self):
        """Test eviction when max size reached"""
        cache = InMemoryCache(max_size=3)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to increase hit count
        await cache.get("key1")
        await cache.get("key1")

        # Add another key - should trigger eviction
        await cache.set("key4", "value4")

        stats = await cache.get_stats()
        assert stats["total_keys"] <= 3


class TestCacheService:
    """Tests for CacheService class"""

    @pytest.fixture
    def service(self):
        """Create CacheService instance"""
        return CacheService()

    @pytest.mark.asyncio
    async def test_get_ttl_for_key_equipment_status(self, service):
        """Test TTL lookup for equipment status keys"""
        ttl = service._get_ttl_for_key("equipment:status:cnc001")

        assert ttl == 10  # From CACHE_CONFIG

    @pytest.mark.asyncio
    async def test_get_ttl_for_key_daily_production(self, service):
        """Test TTL lookup for daily production keys"""
        ttl = service._get_ttl_for_key("daily:production:2024-01-24")

        assert ttl == 300

    @pytest.mark.asyncio
    async def test_get_ttl_for_key_master_data(self, service):
        """Test TTL lookup for master data keys"""
        ttl = service._get_ttl_for_key("master:products")

        assert ttl == 3600

    @pytest.mark.asyncio
    async def test_get_ttl_for_key_default(self, service):
        """Test default TTL for unmatched keys"""
        ttl = service._get_ttl_for_key("unknown:key:pattern")

        assert ttl == 300  # Default TTL

    @pytest.mark.asyncio
    async def test_set_with_auto_ttl(self, service):
        """Test set uses auto TTL from config"""
        await service.set("equipment:status:cnc001", {"status": "RUN"})
        result = await service.get("equipment:status:cnc001")

        assert result == {"status": "RUN"}

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, service):
        """Test set with custom TTL override"""
        await service.set("custom:key", "value", ttl=60)
        result = await service.get("custom:key")

        assert result == "value"

    @pytest.mark.asyncio
    async def test_invalidate_by_event(self, service):
        """Test cache invalidation by event"""
        # Set some cached data
        await service.set("daily:production:2024-01-24", {"data": "test"})
        await service.set("kpi:completion", 85.0)

        # Invalidate on work_order_status_change event
        await service.invalidate("work_order_status_change")

        # Verify keys were deleted
        assert await service.get("daily:production:2024-01-24") is None

    @pytest.mark.asyncio
    async def test_invalidate_unknown_event(self, service):
        """Test invalidation with unknown event"""
        deleted_count = await service.invalidate("unknown_event")

        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self, service):
        """Test get_or_set with cache hit"""
        await service.set("key1", "cached_value")

        factory_called = False

        async def factory():
            nonlocal factory_called
            factory_called = True
            return "new_value"

        result = await service.get_or_set("key1", factory)

        assert result == "cached_value"
        assert factory_called is False

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self, service):
        """Test get_or_set with cache miss"""
        factory_called = False

        async def factory():
            nonlocal factory_called
            factory_called = True
            return "computed_value"

        result = await service.get_or_set("new_key", factory)

        assert result == "computed_value"
        assert factory_called is True

        # Verify value was cached
        assert await service.get("new_key") == "computed_value"

    @pytest.mark.asyncio
    async def test_get_or_set_sync_factory(self, service):
        """Test get_or_set with synchronous factory"""

        def sync_factory():
            return "sync_value"

        result = await service.get_or_set("sync_key", sync_factory)

        assert result == "sync_value"

    def test_make_key(self, service):
        """Test static make_key method"""
        key = CacheService.make_key("daily", "production", "2024-01-24")

        assert key == "daily:production:2024-01-24"

    def test_hash_params(self, service):
        """Test static hash_params method"""
        hash1 = CacheService.hash_params({"a": 1, "b": 2})
        hash2 = CacheService.hash_params({"b": 2, "a": 1})  # Same params, different order

        # Hashes should be identical regardless of key order
        assert hash1 == hash2
        assert len(hash1) == 8  # MD5 hex truncated to 8 chars


class TestCacheConfig:
    """Tests for cache configuration"""

    def test_cache_config_structure(self):
        """Test CACHE_CONFIG has expected keys"""
        assert "equipment:status:*" in CACHE_CONFIG
        assert "daily:production:*" in CACHE_CONFIG
        assert "master:products" in CACHE_CONFIG
        assert "*" in CACHE_CONFIG  # Default

    def test_cache_config_ttl_values(self):
        """Test CACHE_CONFIG TTL values"""
        assert CACHE_CONFIG["equipment:status:*"]["ttl"] == 10
        assert CACHE_CONFIG["master:products"]["ttl"] == 3600

    def test_invalidation_rules_structure(self):
        """Test INVALIDATION_RULES has expected events"""
        assert "work_order_status_change" in INVALIDATION_RULES
        assert "production_result_created" in INVALIDATION_RULES
        assert "equipment_sync" in INVALIDATION_RULES

    def test_invalidation_rules_patterns(self):
        """Test INVALIDATION_RULES patterns"""
        patterns = INVALIDATION_RULES["work_order_status_change"]
        assert "daily:production:*" in patterns
        assert "kpi:*" in patterns


class TestGlobalCacheInstance:
    """Tests for global cache instance functions"""

    def test_get_cache_singleton(self):
        """Test get_cache returns singleton"""
        # Reset global instance
        import src.app.services.cache_service as cache_module

        cache_module._cache_instance = None

        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2

    @pytest.mark.asyncio
    async def test_invalidate_cache_function(self):
        """Test invalidate_cache convenience function"""
        # Reset global instance
        import src.app.services.cache_service as cache_module

        cache_module._cache_instance = None

        cache = get_cache()
        await cache.set("daily:production:test", "value")

        await invalidate_cache("work_order_status_change")

        # Should have deleted the key
        assert await cache.get("daily:production:test") is None


class TestCachedDecorator:
    """Tests for @cached decorator"""

    @pytest.mark.asyncio
    async def test_cached_decorator_basic(self):
        """Test basic @cached decorator usage"""
        call_count = 0

        class MockService:
            def __init__(self):
                self._cache = CacheService()

            @cached("test:prefix")
            async def get_data(self, key: str):
                nonlocal call_count
                call_count += 1
                return f"data_for_{key}"

        service = MockService()

        # First call - should hit the function
        result1 = await service.get_data("key1")
        assert result1 == "data_for_key1"
        assert call_count == 1

        # Second call with same key - should use cache
        result2 = await service.get_data("key1")
        assert result2 == "data_for_key1"
        assert call_count == 1  # Still 1

        # Call with different key - should hit function again
        result3 = await service.get_data("key2")
        assert result3 == "data_for_key2"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cached_decorator_custom_key_builder(self):
        """Test @cached decorator with custom key builder"""

        def custom_key_builder(self, date_str: str):
            return f"custom:{date_str}"

        class MockService:
            def __init__(self):
                self._cache = CacheService()

            @cached("prefix", key_builder=custom_key_builder)
            async def get_data(self, date_str: str):
                return f"data_for_{date_str}"

        service = MockService()

        result = await service.get_data("2024-01-24")
        assert result == "data_for_2024-01-24"

        # Verify custom key was used
        cached_value = await service._cache.get("custom:2024-01-24")
        assert cached_value == "data_for_2024-01-24"

    @pytest.mark.asyncio
    async def test_cached_decorator_no_cache(self):
        """Test @cached decorator when service has no cache"""

        class ServiceWithoutCache:
            @cached("test:prefix")
            async def get_data(self, key: str):
                return f"data_for_{key}"

        service = ServiceWithoutCache()

        # Should work without caching
        result = await service.get_data("key1")
        assert result == "data_for_key1"


class TestConcurrency:
    """Tests for concurrent cache access"""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self):
        """Test concurrent cache reads"""
        cache = InMemoryCache()
        await cache.set("shared_key", "shared_value")

        async def read_key():
            return await cache.get("shared_key")

        # Run 10 concurrent reads
        results = await asyncio.gather(*[read_key() for _ in range(10)])

        assert all(r == "shared_value" for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_writes(self):
        """Test concurrent cache writes"""
        cache = InMemoryCache()

        async def write_key(i: int):
            await cache.set(f"key_{i}", f"value_{i}")
            return True

        # Run 10 concurrent writes
        results = await asyncio.gather(*[write_key(i) for i in range(10)])

        assert all(results)
        stats = await cache.get_stats()
        assert stats["total_keys"] == 10
