"""Redis-based distributed lock for scheduler operations.

Replaces class-level `_solving: bool` flag (lines 76, 573-586 in original
scheduler_integration.py) which had TOCTOU race + multi-worker uvicorn loss.

Pattern: SET NX EX with auto-expire.
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)

SOLVER_LOCK_KEY = "cell-mes:scheduler:solver"
DEFAULT_LOCK_TTL_SEC = 300  # 5 min auto-expire (solver is usually 1-60s)

_client: Optional[object] = None  # redis.asyncio.Redis


def _get_client():
    """Lazy-init Redis client from REDIS_URL env var."""
    global _client
    if _client is None:
        try:
            import redis.asyncio as redis
        except ImportError as exc:
            raise RuntimeError(
                "redis package is required for distributed locking. "
                "Add 'redis' to dependencies."
            ) from exc
        url = os.getenv("REDIS_URL", "redis://redis:6379")
        _client = redis.from_url(url, decode_responses=True)
    return _client


@asynccontextmanager
async def with_solver_lock(timeout_sec: int = DEFAULT_LOCK_TTL_SEC) -> AsyncIterator[bool]:
    """Acquire the global solver lock or yield False.

    Usage::

        async with with_solver_lock() as acquired:
            if not acquired:
                raise HTTPException(409, "scheduling already in progress")
            # critical section

    The lock key expires automatically after *timeout_sec* seconds even if the
    process crashes, preventing permanent deadlocks across uvicorn workers.

    **Graceful degradation**: if Redis is unreachable, the lock is skipped and
    ``True`` is yielded so the operation proceeds.  Distributed exclusion is lost
    but the service remains functional (same behaviour as the original
    single-process asyncio.Lock).
    """
    try:
        client = _get_client()
        token = str(uuid.uuid4())
        acquired = await client.set(SOLVER_LOCK_KEY, token, nx=True, ex=timeout_sec)
    except Exception as exc:
        global _client
        _client = None  # reset so next call retries the connection
        logger.warning(
            "Redis unavailable, proceeding without distributed lock: %s", exc
        )
        yield True
        return

    try:
        yield bool(acquired)
    finally:
        if acquired:
            # Lua script: only delete if token matches (prevents accidentally
            # releasing a lock another worker has already re-acquired after expiry).
            try:
                lua = (
                    "if redis.call('get', KEYS[1]) == ARGV[1] then "
                    "return redis.call('del', KEYS[1]) "
                    "else return 0 end"
                )
                await client.eval(lua, 1, SOLVER_LOCK_KEY, token)
            except Exception as exc:
                logger.warning("solver lock release failed: %s", exc)


async def is_solving() -> bool:
    """Return True if any worker currently holds the solver lock."""
    client = _get_client()
    return bool(await client.exists(SOLVER_LOCK_KEY))


async def force_release() -> None:
    """Admin escape hatch — unconditionally delete the solver lock key."""
    await _get_client().delete(SOLVER_LOCK_KEY)
