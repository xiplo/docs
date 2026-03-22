"""Tests for circuit breaker."""

from __future__ import annotations

import pytest

from utils.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState


@pytest.mark.asyncio
class TestCircuitBreaker:
    async def test_closed_allows_calls(self):
        cb = CircuitBreaker("test", failure_threshold=3)

        async def ok():
            return "success"

        result = await cb.call(ok)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    async def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=60)

        async def fail():
            raise RuntimeError("API error")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(fail)

        assert cb.state == CircuitState.OPEN

    async def test_open_rejects_calls(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=60)

        async def fail():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await cb.call(fail)

        with pytest.raises(CircuitOpenError):
            await cb.call(fail)

    async def test_half_open_allows_test_calls(self):
        cb = CircuitBreaker(
            "test",
            failure_threshold=1,
            recovery_timeout=0.01,  # Very short for testing
            half_open_max_calls=2,
            success_threshold=1,
        )

        async def fail():
            raise RuntimeError("fail")

        async def ok():
            return "recovered"

        # Trip the breaker
        with pytest.raises(RuntimeError):
            await cb.call(fail)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery
        import asyncio
        await asyncio.sleep(0.02)

        assert cb.state == CircuitState.HALF_OPEN

        # Successful call should close it
        result = await cb.call(ok)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    async def test_get_status(self):
        cb = CircuitBreaker("myservice", failure_threshold=5)
        status = cb.get_status()
        assert status["name"] == "myservice"
        assert status["state"] == "closed"
        assert status["failures"] == 0
