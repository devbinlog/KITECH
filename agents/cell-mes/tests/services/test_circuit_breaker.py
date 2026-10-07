"""Tests for Circuit Breaker Service"""

import pytest
from datetime import datetime, timedelta, timezone

from src.app.services.circuit_breaker import (
    CircuitBreaker,
    Circuit,
    CircuitState,
    CircuitConfig,
    CircuitOpenError,
    circuit_breaker,
    get_circuit_breaker,
)


class TestCircuit:
    """Tests for individual Circuit"""

    def test_circuit_initial_state(self):
        """Test circuit starts in CLOSED state"""
        circuit = Circuit(name="test")
        assert circuit.state == CircuitState.CLOSED
        assert circuit.stats.failure_count == 0
        assert circuit.stats.success_count == 0

    def test_should_allow_request_when_closed(self):
        """Test requests allowed when circuit is closed"""
        circuit = Circuit(name="test")
        assert circuit.should_allow_request() is True

    def test_should_block_request_when_open(self):
        """Test requests blocked when circuit is open"""
        circuit = Circuit(name="test")
        circuit.state = CircuitState.OPEN
        circuit.opened_at = datetime.now(timezone.utc)

        assert circuit.should_allow_request() is False

    def test_transition_to_half_open_after_timeout(self):
        """Test circuit transitions to half-open after timeout"""
        config = CircuitConfig(timeout_seconds=1)
        circuit = Circuit(name="test", config=config)
        circuit.state = CircuitState.OPEN
        circuit.opened_at = datetime.now(timezone.utc) - timedelta(seconds=2)

        # Should transition to half-open
        assert circuit.should_allow_request() is True
        assert circuit.state == CircuitState.HALF_OPEN

    def test_half_open_limits_calls(self):
        """Test half-open state limits number of calls"""
        config = CircuitConfig(half_open_max_calls=2)
        circuit = Circuit(name="test", config=config)
        circuit.state = CircuitState.HALF_OPEN

        assert circuit.should_allow_request() is True
        circuit.half_open_calls = 1
        assert circuit.should_allow_request() is True
        circuit.half_open_calls = 2
        assert circuit.should_allow_request() is False

    def test_record_success_resets_failure_count(self):
        """Test success resets failure count when closed"""
        circuit = Circuit(name="test")
        circuit.stats.failure_count = 3

        circuit.record_success()

        assert circuit.stats.failure_count == 0
        assert circuit.stats.success_count == 1
        assert circuit.stats.total_requests == 1

    def test_record_success_closes_circuit_from_half_open(self):
        """Test enough successes in half-open closes circuit"""
        config = CircuitConfig(success_threshold=2)
        circuit = Circuit(name="test", config=config)
        circuit.state = CircuitState.HALF_OPEN

        circuit.record_success()
        assert circuit.state == CircuitState.HALF_OPEN

        circuit.record_success()
        assert circuit.state == CircuitState.CLOSED

    def test_record_failure_opens_circuit_at_threshold(self):
        """Test circuit opens after failure threshold"""
        config = CircuitConfig(failure_threshold=3)
        circuit = Circuit(name="test", config=config)

        circuit.record_failure("error 1")
        assert circuit.state == CircuitState.CLOSED

        circuit.record_failure("error 2")
        assert circuit.state == CircuitState.CLOSED

        circuit.record_failure("error 3")
        assert circuit.state == CircuitState.OPEN
        assert circuit.opened_at is not None

    def test_record_failure_in_half_open_reopens(self):
        """Test failure in half-open reopens circuit"""
        circuit = Circuit(name="test")
        circuit.state = CircuitState.HALF_OPEN

        circuit.record_failure("error")

        assert circuit.state == CircuitState.OPEN

    def test_get_status(self):
        """Test circuit status report"""
        circuit = Circuit(name="test")
        circuit.record_success()
        circuit.record_failure("test error")

        status = circuit.get_status()

        assert status["name"] == "test"
        assert status["state"] == "closed"
        assert status["success_count"] == 1
        assert status["failure_count"] == 1
        assert status["total_requests"] == 2


class TestCircuitBreaker:
    """Tests for CircuitBreaker manager"""

    @pytest.fixture
    def breaker(self):
        """Create circuit breaker instance"""
        return CircuitBreaker()

    def test_allow_creates_circuit(self, breaker):
        """Test allow() creates circuit if not exists"""
        assert "new_endpoint" not in breaker._circuits
        result = breaker.allow("new_endpoint")
        assert result is True
        assert "new_endpoint" in breaker._circuits

    def test_allow_returns_false_when_open(self, breaker):
        """Test allow() returns false when circuit is open"""
        breaker.allow("test")
        circuit = breaker._circuits["test"]
        circuit.state = CircuitState.OPEN
        circuit.opened_at = datetime.now(timezone.utc)

        assert breaker.allow("test") is False

    def test_record_success(self, breaker):
        """Test recording success"""
        breaker.allow("test")
        breaker.record_success("test")

        circuit = breaker._circuits["test"]
        assert circuit.stats.success_count == 1

    def test_record_failure(self, breaker):
        """Test recording failure"""
        breaker.allow("test")
        breaker.record_failure("test", "connection error")

        circuit = breaker._circuits["test"]
        assert circuit.stats.failure_count == 1
        assert circuit.stats.total_failures == 1

    def test_get_state(self, breaker):
        """Test getting circuit state"""
        breaker.allow("test")
        state = breaker.get_state("test")
        assert state == CircuitState.CLOSED

    def test_get_status_single(self, breaker):
        """Test getting status for single endpoint"""
        breaker.allow("test")
        breaker.record_success("test")

        status = breaker.get_status("test")

        assert status["name"] == "test"
        assert status["success_count"] == 1

    def test_get_status_all(self, breaker):
        """Test getting status for all circuits"""
        breaker.allow("endpoint1")
        breaker.allow("endpoint2")

        status = breaker.get_status()

        assert "circuits" in status
        assert len(status["circuits"]) == 2
        assert status["total_open"] == 0

    def test_reset_single(self, breaker):
        """Test resetting single circuit"""
        breaker.allow("test")
        breaker.record_failure("test", "error")
        breaker.record_failure("test", "error")

        breaker.reset("test")

        circuit = breaker._circuits["test"]
        assert circuit.state == CircuitState.CLOSED
        assert circuit.stats.failure_count == 0

    def test_reset_all(self, breaker):
        """Test resetting all circuits"""
        breaker.allow("endpoint1")
        breaker.allow("endpoint2")
        breaker._circuits["endpoint1"].state = CircuitState.OPEN
        breaker._circuits["endpoint2"].state = CircuitState.HALF_OPEN

        breaker.reset()

        assert breaker._circuits["endpoint1"].state == CircuitState.CLOSED
        assert breaker._circuits["endpoint2"].state == CircuitState.CLOSED

    def test_configure_endpoint(self, breaker):
        """Test configuring specific endpoint"""
        config = CircuitConfig(failure_threshold=10, timeout_seconds=120)
        breaker.configure("test", config)

        circuit = breaker._circuits["test"]
        assert circuit.config.failure_threshold == 10
        assert circuit.config.timeout_seconds == 120


class TestCircuitBreakerDecorator:
    """Tests for circuit_breaker decorator"""

    @pytest.fixture
    def breaker(self):
        """Create circuit breaker instance"""
        return CircuitBreaker()

    @pytest.mark.asyncio
    async def test_decorator_allows_successful_call(self, breaker):
        """Test decorator allows successful calls"""

        @circuit_breaker(breaker, "test_endpoint")
        async def success_func():
            return "success"

        result = await success_func()

        assert result == "success"
        assert breaker._circuits["test_endpoint"].stats.success_count == 1

    @pytest.mark.asyncio
    async def test_decorator_records_failure(self, breaker):
        """Test decorator records failures"""

        @circuit_breaker(breaker, "test_endpoint")
        async def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await fail_func()

        assert breaker._circuits["test_endpoint"].stats.failure_count == 1

    @pytest.mark.asyncio
    async def test_decorator_uses_fallback_when_open(self, breaker):
        """Test decorator uses fallback when circuit is open"""
        breaker.allow("test_endpoint")
        breaker._circuits["test_endpoint"].state = CircuitState.OPEN
        breaker._circuits["test_endpoint"].opened_at = datetime.now(timezone.utc)

        @circuit_breaker(breaker, "test_endpoint", fallback=lambda: "fallback_value")
        async def func():
            return "success"

        result = await func()

        assert result == "fallback_value"

    @pytest.mark.asyncio
    async def test_decorator_raises_when_open_no_fallback(self, breaker):
        """Test decorator raises CircuitOpenError when open without fallback"""
        breaker.allow("test_endpoint")
        breaker._circuits["test_endpoint"].state = CircuitState.OPEN
        breaker._circuits["test_endpoint"].opened_at = datetime.now(timezone.utc)

        @circuit_breaker(breaker, "test_endpoint")
        async def func():
            return "success"

        with pytest.raises(CircuitOpenError) as exc_info:
            await func()

        assert exc_info.value.circuit_name == "test_endpoint"

    @pytest.mark.asyncio
    async def test_decorator_fallback_on_exception(self, breaker):
        """Test decorator uses fallback when function raises exception"""

        @circuit_breaker(breaker, "test_endpoint", fallback=lambda: {"error": True})
        async def fail_func():
            raise RuntimeError("service unavailable")

        result = await fail_func()

        assert result == {"error": True}
        assert breaker._circuits["test_endpoint"].stats.failure_count == 1

    @pytest.mark.asyncio
    async def test_decorator_async_fallback(self, breaker):
        """Test decorator works with async fallback"""

        async def async_fallback():
            return "async_fallback"

        @circuit_breaker(breaker, "test_endpoint", fallback=async_fallback)
        async def fail_func():
            raise RuntimeError("error")

        result = await fail_func()

        assert result == "async_fallback"


class TestCircuitOpenError:
    """Tests for CircuitOpenError exception"""

    def test_error_message(self):
        """Test error contains circuit name"""
        error = CircuitOpenError("test_endpoint")
        assert "test_endpoint" in str(error)
        assert error.circuit_name == "test_endpoint"

    def test_custom_message(self):
        """Test custom error message"""
        error = CircuitOpenError("test", "Custom message")
        assert error.message == "Custom message"


class TestGlobalCircuitBreaker:
    """Tests for global circuit breaker instance"""

    def test_get_circuit_breaker_singleton(self):
        """Test get_circuit_breaker returns same instance"""
        import src.app.services.circuit_breaker as cb_module

        # Reset global instance
        cb_module._circuit_breaker = None

        breaker1 = get_circuit_breaker()
        breaker2 = get_circuit_breaker()

        assert breaker1 is breaker2
