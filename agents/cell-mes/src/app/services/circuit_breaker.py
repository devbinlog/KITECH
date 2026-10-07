"""
Circuit Breaker Service for NL-Driven MES

Provides fault tolerance with:
- Circuit states: CLOSED, OPEN, HALF_OPEN
- Automatic recovery after timeout
- Per-endpoint failure tracking
- Partial response support
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, Callable, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitStats:
    """Statistics for a circuit"""

    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    total_failures: int = 0


@dataclass
class CircuitConfig:
    """Configuration for a circuit breaker"""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 3  # Successes in half-open before closing
    timeout_seconds: int = 30  # Time before attempting recovery
    half_open_max_calls: int = 3  # Max calls allowed in half-open state


@dataclass
class Circuit:
    """Individual circuit for an endpoint"""

    name: str
    state: CircuitState = CircuitState.CLOSED
    stats: CircuitStats = field(default_factory=CircuitStats)
    config: CircuitConfig = field(default_factory=CircuitConfig)
    opened_at: Optional[datetime] = None
    half_open_calls: int = 0

    def should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.opened_at and datetime.now(timezone.utc) > self.opened_at + timedelta(
                seconds=self.config.timeout_seconds
            ):
                self._transition_to_half_open()
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self.half_open_calls < self.config.half_open_max_calls

        return False

    def record_success(self):
        """Record a successful call"""
        self.stats.success_count += 1
        self.stats.total_requests += 1
        self.stats.last_success_time = datetime.now(timezone.utc)

        if self.state == CircuitState.HALF_OPEN:
            if self.stats.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.stats.failure_count = 0

    def record_failure(self, error: Optional[str] = None):
        """Record a failed call"""
        self.stats.failure_count += 1
        self.stats.total_requests += 1
        self.stats.total_failures += 1
        self.stats.last_failure_time = datetime.now(timezone.utc)

        logger.warning(f"Circuit '{self.name}' failure #{self.stats.failure_count}: {error}")

        if self.state == CircuitState.CLOSED:
            if self.stats.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state"""
        logger.warning(f"Circuit '{self.name}' OPENED after {self.stats.failure_count} failures")
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now(timezone.utc)
        self.stats.success_count = 0

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.stats.success_count = 0
        self.stats.failure_count = 0

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        logger.info(f"Circuit '{self.name}' CLOSED - recovery successful")
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.half_open_calls = 0
        self.stats.failure_count = 0

    def get_status(self) -> Dict[str, Any]:
        """Get circuit status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "last_failure": self.stats.last_failure_time.isoformat()
            if self.stats.last_failure_time
            else None,
            "last_success": self.stats.last_success_time.isoformat()
            if self.stats.last_success_time
            else None,
        }


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is rejected"""

    def __init__(self, circuit_name: str, message: str = ""):
        self.circuit_name = circuit_name
        self.message = message or f"Circuit '{circuit_name}' is open"
        super().__init__(self.message)


class CircuitBreaker:
    """
    Circuit Breaker manager for multiple endpoints

    Usage:
        breaker = CircuitBreaker()

        # Check before making request
        if breaker.allow("api_endpoint"):
            try:
                result = await make_api_call()
                breaker.record_success("api_endpoint")
            except Exception as e:
                breaker.record_failure("api_endpoint", str(e))
        else:
            # Return fallback or cached data
            pass
    """

    def __init__(self, default_config: Optional[CircuitConfig] = None):
        self._circuits: Dict[str, Circuit] = {}
        self._default_config = default_config or CircuitConfig()
        self._lock = asyncio.Lock()

    def _get_or_create_circuit(self, name: str) -> Circuit:
        """Get existing circuit or create new one"""
        if name not in self._circuits:
            self._circuits[name] = Circuit(
                name=name,
                config=CircuitConfig(**vars(self._default_config)),
            )
        return self._circuits[name]

    def allow(self, endpoint: str) -> bool:
        """Check if request to endpoint should be allowed"""
        circuit = self._get_or_create_circuit(endpoint)
        return circuit.should_allow_request()

    def record_success(self, endpoint: str):
        """Record successful call to endpoint"""
        circuit = self._get_or_create_circuit(endpoint)
        circuit.record_success()

    def record_failure(self, endpoint: str, error: Optional[str] = None):
        """Record failed call to endpoint"""
        circuit = self._get_or_create_circuit(endpoint)
        circuit.record_failure(error)

    def get_state(self, endpoint: str) -> CircuitState:
        """Get current state of circuit for endpoint"""
        circuit = self._get_or_create_circuit(endpoint)
        return circuit.state

    def get_status(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get status of one or all circuits"""
        if endpoint:
            circuit = self._get_or_create_circuit(endpoint)
            return circuit.get_status()

        return {
            "circuits": [c.get_status() for c in self._circuits.values()],
            "total_open": sum(1 for c in self._circuits.values() if c.state == CircuitState.OPEN),
            "total_half_open": sum(
                1 for c in self._circuits.values() if c.state == CircuitState.HALF_OPEN
            ),
        }

    def reset(self, endpoint: Optional[str] = None):
        """Reset circuit(s) to closed state"""
        if endpoint:
            if endpoint in self._circuits:
                circuit = self._circuits[endpoint]
                circuit.state = CircuitState.CLOSED
                circuit.stats = CircuitStats()
                circuit.opened_at = None
        else:
            for circuit in self._circuits.values():
                circuit.state = CircuitState.CLOSED
                circuit.stats = CircuitStats()
                circuit.opened_at = None

    def configure(self, endpoint: str, config: CircuitConfig):
        """Configure specific endpoint circuit"""
        circuit = self._get_or_create_circuit(endpoint)
        circuit.config = config


def circuit_breaker(
    breaker: CircuitBreaker,
    endpoint: str,
    fallback: Optional[Callable[[], T]] = None,
):
    """
    Decorator for applying circuit breaker to async functions

    Usage:
        @circuit_breaker(breaker, "api_endpoint", fallback=lambda: {})
        async def call_api():
            return await http_client.get("/api")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not breaker.allow(endpoint):
                if fallback:
                    logger.warning(f"Circuit open for '{endpoint}', using fallback")
                    result = fallback()
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                raise CircuitOpenError(endpoint)

            try:
                result = await func(*args, **kwargs)
                breaker.record_success(endpoint)
                return result
            except Exception as e:
                breaker.record_failure(endpoint, str(e))
                if fallback:
                    logger.warning(f"Call failed for '{endpoint}', using fallback: {e}")
                    result = fallback()
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                raise

        return wrapper

    return decorator


# Global circuit breaker instance
_circuit_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get global circuit breaker instance"""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker
