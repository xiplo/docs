"""Circuit breaker — protects against cascading failures in API calls.

States:
  CLOSED   → Normal operation, calls go through
  OPEN     → Failing, all calls rejected immediately
  HALF_OPEN → Testing recovery, limited calls allowed
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for external API calls."""

    name: str
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 60.0  # Seconds before half-open
    half_open_max_calls: int = 2  # Test calls in half-open
    success_threshold: int = 2  # Successes to close again

    _state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _success_count: int = 0
    _last_failure_time: float = 0.0
    _half_open_calls: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    async def call(self, func: Callable, *args, **kwargs):
        """Execute a function through the circuit breaker."""
        async with self._lock:
            state = self.state

            # Transition _state to HALF_OPEN when recovery timeout expires
            if state == CircuitState.HALF_OPEN and self._state == CircuitState.OPEN:
                self._state = CircuitState.HALF_OPEN

            if state == CircuitState.OPEN:
                remaining = self.recovery_timeout - (time.monotonic() - self._last_failure_time)
                logger.warning(
                    "circuit_breaker.open",
                    name=self.name,
                    retry_in=f"{remaining:.0f}s",
                )
                raise CircuitOpenError(
                    f"{self.name} circuit is OPEN. "
                    f"Retry in {remaining:.0f}s"
                )

            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(
                        f"{self.name} circuit is HALF_OPEN, max test calls reached"
                    )
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except CircuitOpenError:
            raise
        except Exception as exc:
            await self._on_failure(exc)
            raise

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self._half_open_calls = 0
                    logger.info("circuit_breaker.closed", name=self.name)
            else:
                self._failure_count = max(0, self._failure_count - 1)

    async def _on_failure(self, exc: Exception) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                self._half_open_calls = 0
                logger.warning("circuit_breaker.reopened", name=self.name, error=str(exc)[:100])
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker.opened",
                    name=self.name,
                    failures=self._failure_count,
                    error=str(exc)[:100],
                )

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self._failure_count,
            "last_failure": self._last_failure_time,
        }


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open."""


# Pre-configured breakers for each service
CIRCUIT_BREAKERS: dict[str, CircuitBreaker] = {
    "nano_banana": CircuitBreaker("nano_banana", failure_threshold=3, recovery_timeout=120),
    "kling": CircuitBreaker("kling", failure_threshold=3, recovery_timeout=180),
    "elevenlabs": CircuitBreaker("elevenlabs", failure_threshold=5, recovery_timeout=60),
    "instagram": CircuitBreaker("instagram", failure_threshold=5, recovery_timeout=300),
    "cdn": CircuitBreaker("cdn", failure_threshold=5, recovery_timeout=60),
}


def get_breaker(service: str) -> CircuitBreaker:
    if service not in CIRCUIT_BREAKERS:
        CIRCUIT_BREAKERS[service] = CircuitBreaker(service)
    return CIRCUIT_BREAKERS[service]
