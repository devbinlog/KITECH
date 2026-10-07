"""Tests for CircuitBreaker service."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from src.app.services.circuit_breaker import (
    Circuit,
    CircuitBreaker,
    CircuitConfig,
    CircuitOpenError,
    CircuitState,
    CircuitStats,
    circuit_breaker,
    get_circuit_breaker,
)


class TestCircuitState:
    """Test CircuitState enum values."""

    def test_states_have_correct_values(self):
        assert CircuitState.CLOSED == "closed"
        assert CircuitState.OPEN == "open"
        assert CircuitState.HALF_OPEN == "half_open"


class TestCircuit:
    """Test individual Circuit behavior."""

    def _make_circuit(self, **config_kwargs) -> Circuit:
        config = CircuitConfig(**config_kwargs)
        return Circuit(name="test", config=config)

    # --- CLOSED state ---

    def test_closed_circuit_allows_requests(self):
        circuit = self._make_circuit()
        assert circuit.should_allow_request() is True

    def test_closed_circuit_opens_after_failure_threshold(self):
        circuit = self._make_circuit(failure_threshold=3)
        for _ in range(3):
            circuit.record_failure("err")
        assert circuit.state == CircuitState.OPEN

    def test_closed_circuit_resets_failure_count_on_success(self):
        circuit = self._make_circuit(failure_threshold=3)
        circuit.record_failure("err")
        circuit.record_failure("err")
        circuit.record_success()
        # Failure count should reset to 0 after success
        assert circuit.stats.failure_count == 0
        assert circuit.state == CircuitState.CLOSED

    def test_closed_circuit_does_not_open_below_threshold(self):
        circuit = self._make_circuit(failure_threshold=5)
        for _ in range(4):
            circuit.record_failure("err")
        assert circuit.state == CircuitState.CLOSED

    # --- OPEN state ---

    def test_open_circuit_rejects_requests(self):
        circuit = self._make_circuit(failure_threshold=1, timeout_seconds=60)
        circuit.record_failure("err")
        assert circuit.state == CircuitState.OPEN
        assert circuit.should_allow_request() is False

    def test_open_circuit_transitions_to_half_open_after_timeout(self):
        circuit = self._make_circuit(failure_threshold=1, timeout_seconds=1)
        circuit.record_failure("err")
        # Backdate the opened_at so the timeout has elapsed
        circuit.opened_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        result = circuit.should_allow_request()
        assert result is True
        assert circuit.state == CircuitState.HALF_OPEN

    def test_open_circuit_stays_open_before_timeout(self):
        circuit = self._make_circuit(failure_threshold=1, timeout_seconds=60)
        circuit.record_failure("err")
        assert circuit.should_allow_request() is False
        assert circuit.state == CircuitState.OPEN

    # --- HALF_OPEN state ---

    def test_half_open_allows_limited_calls(self):
        circuit = self._make_circuit(failure_threshold=1, timeout_seconds=0, half_open_max_calls=2)
        circuit.record_failure("err")
        circuit.opened_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        # Move to HALF_OPEN
        circuit.should_allow_request()
        assert circuit.state == CircuitState.HALF_OPEN

        # Simulate calls being counted
        circuit.half_open_calls = 0
        assert circuit.should_allow_request() is True
        circuit.half_open_calls = 1
        assert circuit.should_allow_request() is True
        circuit.half_open_calls = 2
        assert circuit.should_allow_request() is False

    def test_half_open_closes_after_enough_successes(self):
        circuit = self._make_circuit(
            failure_threshold=1, timeout_seconds=0, success_threshold=3
        )
        circuit.record_failure("err")
        circuit.opened_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        circuit.should_allow_request()  # triggers HALF_OPEN
        assert circuit.state == CircuitState.HALF_OPEN

        for _ in range(3):
            circuit.record_success()
        assert circuit.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self):
        circuit = self._make_circuit(failure_threshold=1, timeout_seconds=0)
        circuit.record_failure("err")
        circuit.opened_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        circuit.should_allow_request()  # transitions to HALF_OPEN
        assert circuit.state == CircuitState.HALF_OPEN

        circuit.record_failure("err again")
        assert circuit.state == CircuitState.OPEN

    # --- Stats ---

    def test_stats_track_totals(self):
        circuit = self._make_circuit(failure_threshold=10)
        circuit.record_success()
        circuit.record_success()
        circuit.record_failure("err")
        assert circuit.stats.total_requests == 3
        assert circuit.stats.total_failures == 1
        assert circuit.stats.success_count == 2

    def test_get_status_returns_dict(self):
        circuit = self._make_circuit()
        status = circuit.get_status()
        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert "failure_count" in status
        assert "last_failure" in status
        assert "last_success" in status

    def test_get_status_last_failure_is_iso_string(self):
        circuit = self._make_circuit(failure_threshold=10)
        circuit.record_failure("err")
        status = circuit.get_status()
        assert status["last_failure"] is not None
        # Should be a valid ISO 8601 string
        datetime.fromisoformat(status["last_failure"])


class TestCircuitBreaker:
    """Test CircuitBreaker manager."""

    def test_allow_returns_true_for_new_endpoint(self):
        breaker = CircuitBreaker()
        assert breaker.allow("new_ep") is True

    def test_creates_circuit_on_first_access(self):
        breaker = CircuitBreaker()
        breaker.allow("ep1")
        assert "ep1" in breaker._circuits

    def test_get_state_returns_closed_initially(self):
        breaker = CircuitBreaker()
        assert breaker.get_state("ep1") == CircuitState.CLOSED

    def test_record_failure_opens_circuit_at_threshold(self):
        config = CircuitConfig(failure_threshold=3)
        breaker = CircuitBreaker(default_config=config)
        for _ in range(3):
            breaker.record_failure("ep1", "error")
        assert breaker.get_state("ep1") == CircuitState.OPEN
        assert breaker.allow("ep1") is False

    def test_record_success_resets_failure_count(self):
        config = CircuitConfig(failure_threshold=5)
        breaker = CircuitBreaker(default_config=config)
        breaker.record_failure("ep1", "err")
        breaker.record_failure("ep1", "err")
        breaker.record_success("ep1")
        assert breaker._circuits["ep1"].stats.failure_count == 0

    def test_reset_single_endpoint(self):
        config = CircuitConfig(failure_threshold=1)
        breaker = CircuitBreaker(default_config=config)
        breaker.record_failure("ep1", "err")
        assert breaker.get_state("ep1") == CircuitState.OPEN
        breaker.reset("ep1")
        assert breaker.get_state("ep1") == CircuitState.CLOSED
        assert breaker.allow("ep1") is True

    def test_reset_all_endpoints(self):
        config = CircuitConfig(failure_threshold=1)
        breaker = CircuitBreaker(default_config=config)
        breaker.record_failure("ep1", "err")
        breaker.record_failure("ep2", "err")
        breaker.reset()
        assert breaker.get_state("ep1") == CircuitState.CLOSED
        assert breaker.get_state("ep2") == CircuitState.CLOSED

    def test_get_status_all_circuits(self):
        breaker = CircuitBreaker()
        breaker.allow("ep1")
        breaker.allow("ep2")
        status = breaker.get_status()
        assert "circuits" in status
        assert "total_open" in status
        assert "total_half_open" in status
        assert len(status["circuits"]) == 2

    def test_get_status_single_endpoint(self):
        breaker = CircuitBreaker()
        status = breaker.get_status("ep1")
        assert status["name"] == "ep1"
        assert status["state"] == "closed"

    def test_configure_overrides_default(self):
        breaker = CircuitBreaker(default_config=CircuitConfig(failure_threshold=5))
        custom_config = CircuitConfig(failure_threshold=2)
        breaker.configure("ep1", custom_config)
        assert breaker._circuits["ep1"].config.failure_threshold == 2

    def test_total_open_count_in_status(self):
        config = CircuitConfig(failure_threshold=1)
        breaker = CircuitBreaker(default_config=config)
        breaker.record_failure("ep1", "err")
        breaker.record_failure("ep2", "err")
        status = breaker.get_status()
        assert status["total_open"] == 2


class TestCircuitOpenError:
    """Test CircuitOpenError exception."""

    def test_default_message(self):
        err = CircuitOpenError("my_circuit")
        assert "my_circuit" in str(err)
        assert err.circuit_name == "my_circuit"

    def test_custom_message(self):
        err = CircuitOpenError("ep", "Custom error message")
        assert err.message == "Custom error message"


class TestCircuitBreakerDecorator:
    """Test the circuit_breaker decorator."""

    @pytest.mark.asyncio
    async def test_decorator_allows_successful_calls(self):
        breaker = CircuitBreaker()

        @circuit_breaker(breaker, "ep_success")
        async def my_func():
            return "ok"

        result = await my_func()
        assert result == "ok"
        assert breaker._circuits["ep_success"].stats.success_count == 1

    @pytest.mark.asyncio
    async def test_decorator_records_failure_on_exception(self):
        config = CircuitConfig(failure_threshold=10)
        breaker = CircuitBreaker(default_config=config)

        @circuit_breaker(breaker, "ep_fail")
        async def my_func():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await my_func()

        assert breaker._circuits["ep_fail"].stats.total_failures == 1

    @pytest.mark.asyncio
    async def test_decorator_raises_circuit_open_error_when_open(self):
        config = CircuitConfig(failure_threshold=1)
        breaker = CircuitBreaker(default_config=config)

        @circuit_breaker(breaker, "ep_open")
        async def my_func():
            raise RuntimeError("fail")

        # Trip the circuit
        with pytest.raises(RuntimeError):
            await my_func()

        # Next call should raise CircuitOpenError
        with pytest.raises(CircuitOpenError) as exc_info:
            await my_func()
        assert exc_info.value.circuit_name == "ep_open"

    @pytest.mark.asyncio
    async def test_decorator_uses_fallback_when_circuit_open(self):
        config = CircuitConfig(failure_threshold=1)
        breaker = CircuitBreaker(default_config=config)

        @circuit_breaker(breaker, "ep_fallback", fallback=lambda: {"data": "fallback"})
        async def my_func():
            raise RuntimeError("fail")

        # Trip the circuit
        result1 = await my_func()
        # Second call: circuit open, use fallback
        result2 = await my_func()
        assert result2 == {"data": "fallback"}

    @pytest.mark.asyncio
    async def test_decorator_uses_fallback_on_function_failure(self):
        config = CircuitConfig(failure_threshold=5)
        breaker = CircuitBreaker(default_config=config)

        @circuit_breaker(breaker, "ep_fb_on_err", fallback=lambda: "fallback_val")
        async def my_func():
            raise RuntimeError("fail")

        result = await my_func()
        assert result == "fallback_val"


class TestGetCircuitBreaker:
    """Test global circuit breaker singleton."""

    def test_returns_same_instance(self):
        cb1 = get_circuit_breaker()
        cb2 = get_circuit_breaker()
        assert cb1 is cb2

    def test_returns_circuit_breaker_instance(self):
        assert isinstance(get_circuit_breaker(), CircuitBreaker)
