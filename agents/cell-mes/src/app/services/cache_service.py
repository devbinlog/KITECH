"""
Cache Service for NL-Driven MES

Provides caching layer with:
- In-memory cache (default)
- Redis support (optional)
- TTL-based expiration
- Cache invalidation rules
"""

import asyncio
import hashlib
import json
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""

    value: Any
    created_at: datetime
    ttl_seconds: int
    hit_count: int = 0
    last_accessed_at: datetime = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.last_accessed_at is None:
            self.last_accessed_at = self.created_at

    @property
    def expires_at(self) -> datetime:
        return self.created_at + timedelta(seconds=self.ttl_seconds)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


# Cache configuration by key pattern
CACHE_CONFIG = {
    # Real-time data - short TTL
    "equipment:status:*": {"ttl": 10, "strategy": "write_through"},
    # Aggregated data - medium TTL
    "daily:production:*": {"ttl": 300, "strategy": "cache_aside"},
    "kpi:utilization:*": {"ttl": 600, "strategy": "cache_aside"},
    "analytics:*": {"ttl": 300, "strategy": "cache_aside"},
    # Master data - long TTL
    "master:products": {"ttl": 3600, "strategy": "cache_aside"},
    "master:processes": {"ttl": 3600, "strategy": "cache_aside"},
    "master:equipments": {"ttl": 1800, "strategy": "cache_aside"},
    # LOT history - long TTL (rarely changes)
    "lot:history:*": {"ttl": 1800, "strategy": "cache_aside"},
    # Default
    "*": {"ttl": 300, "strategy": "cache_aside"},
}

# Invalidation rules: event -> [cache key patterns to invalidate]
INVALIDATION_RULES = {
    "work_order_status_change": ["daily:production:*", "kpi:*", "analytics:daily:*"],
    "production_result_created": [
        "daily:production:*",
        "lot:history:*",
        "kpi:utilization:*",
        "analytics:*",
    ],
    "equipment_sync": ["equipment:status:*", "master:equipments"],
    "equipment_status_change": ["equipment:status:*", "analytics:equipment:*"],
    "product_change": ["master:products", "analytics:*"],
    "process_change": ["master:processes"],
}


class InMemoryCache:
    """Simple in-memory cache implementation"""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired:
                del self._cache[key]
                return None

            entry.hit_count += 1
            entry.last_accessed_at = datetime.now(timezone.utc)
            return entry.value

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size:
                await self._evict_expired()
                if len(self._cache) >= self._max_size:
                    await self._evict_lru()

            self._cache[key] = CacheEntry(
                value=value, created_at=datetime.now(timezone.utc), ttl_seconds=ttl
            )
            return True

    async def delete(self, key: str) -> bool:
        """Delete specific key"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern (supports * wildcard)"""
        async with self._lock:
            if pattern == "*":
                count = len(self._cache)
                self._cache.clear()
                return count

            # Convert pattern to simple matching
            prefix = pattern.rstrip("*")
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix) or k == pattern]

            for key in keys_to_delete:
                del self._cache[key]

            return len(keys_to_delete)

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        value = await self.get(key)
        return value is not None

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            expired_count = sum(1 for e in self._cache.values() if e.is_expired)
            total_hits = sum(e.hit_count for e in self._cache.values())

            return {
                "total_keys": len(self._cache),
                "expired_keys": expired_count,
                "active_keys": len(self._cache) - expired_count,
                "total_hits": total_hits,
                "max_size": self._max_size,
            }

    async def _evict_expired(self) -> int:
        """Remove expired entries"""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    async def _evict_lru(self) -> None:
        """Evict least recently used (oldest last_accessed_at)"""
        if not self._cache:
            return

        # Sort by last access time (ascending) and remove bottom 10%
        sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k].last_accessed_at)
        evict_count = max(1, len(sorted_keys) // 10)

        for key in sorted_keys[:evict_count]:
            del self._cache[key]


class CacheService:
    """Main cache service with pattern-based TTL and invalidation"""

    def __init__(self, backend: Optional[InMemoryCache] = None):
        self._backend = backend or InMemoryCache()
        self._config = CACHE_CONFIG
        self._invalidation_rules = INVALIDATION_RULES

    def _get_ttl_for_key(self, key: str) -> int:
        """Get TTL based on key pattern matching"""
        for pattern, config in self._config.items():
            if pattern == "*":
                continue
            if pattern.endswith("*"):
                prefix = pattern.rstrip("*")
                if key.startswith(prefix):
                    return config["ttl"]
            elif key == pattern:
                return config["ttl"]

        # Default TTL
        return self._config.get("*", {}).get("ttl", 300)

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        return await self._backend.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value with automatic TTL from config"""
        if ttl is None:
            ttl = self._get_ttl_for_key(key)
        return await self._backend.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete specific key"""
        return await self._backend.delete(key)

    async def invalidate(self, event: str) -> int:
        """Invalidate cache based on event"""
        patterns = self._invalidation_rules.get(event, [])
        total_deleted = 0

        for pattern in patterns:
            deleted = await self._backend.delete_pattern(pattern)
            total_deleted += deleted
            logger.debug(f"Cache invalidation: event={event}, pattern={pattern}, deleted={deleted}")

        return total_deleted

    async def get_or_set(
        self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or compute and set"""
        value = await self.get(key)
        if value is not None:
            return value

        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        await self.set(key, value, ttl)
        return value

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self._backend.get_stats()

    @staticmethod
    def make_key(*parts: Any) -> str:
        """Create cache key from parts"""
        return ":".join(str(p) for p in parts)

    @staticmethod
    def hash_params(params: Dict[str, Any]) -> str:
        """Create hash from parameters for cache key (not for security)"""
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        return hashlib.md5(sorted_params.encode(), usedforsecurity=False).hexdigest()[:8]


# Decorator for caching function results
def cached(
    key_prefix: str, ttl: Optional[int] = None, key_builder: Optional[Callable[..., str]] = None
):
    """
    Decorator to cache function results

    Args:
        key_prefix: Prefix for cache key
        ttl: TTL override (uses config if None)
        key_builder: Custom function to build cache key from args

    Usage:
        @cached("daily:production", ttl=300)
        async def get_daily_production(date: str):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache service from first arg if it's self with cache
            cache = None
            if args and hasattr(args[0], "_cache"):
                cache = args[0]._cache
            elif args and hasattr(args[0], "cache"):
                cache = args[0].cache

            # Skip caching if no cache available
            if cache is None:
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default key: prefix + hash of args
                params_hash = CacheService.hash_params(
                    {
                        "args": args[1:],  # Skip self
                        "kwargs": kwargs,
                    }
                )
                key = f"{key_prefix}:{params_hash}"

            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(key, result, ttl)

            return result

        return wrapper

    return decorator


# Global cache instance (singleton)
_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance


async def invalidate_cache(event: str) -> int:
    """Invalidate cache for an event using global instance"""
    cache = get_cache()
    return await cache.invalidate(event)
