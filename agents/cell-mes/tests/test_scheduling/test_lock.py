"""Tests for scheduling/lock.py — Redis distributed lock.

Uses fakeredis (or unittest.mock) so no real Redis is needed.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_redis(set_return=True, exists_return=1, eval_return=1):
    """Build an AsyncMock that mimics redis.asyncio.Redis for lock operations."""
    r = AsyncMock()
    r.set = AsyncMock(return_value=set_return)
    r.exists = AsyncMock(return_value=exists_return)
    r.eval = AsyncMock(return_value=eval_return)
    r.delete = AsyncMock(return_value=1)
    return r


# ---------------------------------------------------------------------------
# with_solver_lock
# ---------------------------------------------------------------------------


class TestWithSolverLock:
    """Tests for the with_solver_lock context manager."""

    @pytest.mark.asyncio
    async def test_acquired_yields_true(self):
        """When Redis SET NX succeeds, context yields True."""
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(set_return=True)
        with patch.object(lock_mod, "_get_client", return_value=fake):
            async with lock_mod.with_solver_lock() as acquired:
                assert acquired is True

    @pytest.mark.asyncio
    async def test_not_acquired_yields_false(self):
        """When Redis SET NX returns None/False (key already exists), context yields False."""
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(set_return=None)
        with patch.object(lock_mod, "_get_client", return_value=fake):
            async with lock_mod.with_solver_lock() as acquired:
                assert acquired is False

    @pytest.mark.asyncio
    async def test_lock_released_on_exit(self):
        """After exiting, Lua eval is called to delete the key."""
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(set_return=True)
        with patch.object(lock_mod, "_get_client", return_value=fake):
            async with lock_mod.with_solver_lock():
                pass

        fake.eval.assert_awaited_once()
        # KEYS[1] is SOLVER_LOCK_KEY
        call_args = fake.eval.call_args
        assert lock_mod.SOLVER_LOCK_KEY in call_args.args

    @pytest.mark.asyncio
    async def test_lock_not_released_when_not_acquired(self):
        """If lock was not acquired, eval must NOT be called on exit."""
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(set_return=None)
        with patch.object(lock_mod, "_get_client", return_value=fake):
            async with lock_mod.with_solver_lock():
                pass

        fake.eval.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_release_failure_logged_not_raised(self):
        """Eval failure on release is swallowed (lock.py catches it)."""
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(set_return=True)
        fake.eval = AsyncMock(side_effect=Exception("Redis down"))
        with patch.object(lock_mod, "_get_client", return_value=fake):
            # Should NOT raise
            async with lock_mod.with_solver_lock() as acquired:
                assert acquired is True

    @pytest.mark.asyncio
    async def test_lock_released_on_exception_inside_block(self):
        """Lock is always released even if the protected block raises."""
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(set_return=True)
        with patch.object(lock_mod, "_get_client", return_value=fake):
            with pytest.raises(RuntimeError):
                async with lock_mod.with_solver_lock():
                    raise RuntimeError("boom")

        fake.eval.assert_awaited_once()


# ---------------------------------------------------------------------------
# is_solving / force_release
# ---------------------------------------------------------------------------


class TestIsSolving:
    @pytest.mark.asyncio
    async def test_returns_true_when_key_exists(self):
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(exists_return=1)
        with patch.object(lock_mod, "_get_client", return_value=fake):
            assert await lock_mod.is_solving() is True

    @pytest.mark.asyncio
    async def test_returns_false_when_key_absent(self):
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis(exists_return=0)
        with patch.object(lock_mod, "_get_client", return_value=fake):
            assert await lock_mod.is_solving() is False


class TestForceRelease:
    @pytest.mark.asyncio
    async def test_calls_delete(self):
        import src.app.services.scheduling.lock as lock_mod

        fake = _make_fake_redis()
        with patch.object(lock_mod, "_get_client", return_value=fake):
            await lock_mod.force_release()

        fake.delete.assert_awaited_once_with(lock_mod.SOLVER_LOCK_KEY)
