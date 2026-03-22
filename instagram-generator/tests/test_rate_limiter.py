"""Tests for rate limiter."""

from __future__ import annotations

import asyncio
import time

import pytest

from utils.rate_limiter import TokenBucket, get_limiter


@pytest.mark.asyncio
class TestTokenBucket:
    async def test_acquire_within_capacity(self):
        bucket = TokenBucket(rate=10.0, capacity=5)
        # Should not block — we have 5 tokens
        start = time.monotonic()
        await bucket.acquire(3)
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    async def test_acquire_blocks_when_empty(self):
        bucket = TokenBucket(rate=10.0, capacity=1)
        await bucket.acquire(1)  # Drain the bucket
        start = time.monotonic()
        await bucket.acquire(1)  # Should wait ~0.1s for refill
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05  # At least some waiting

    async def test_refill_adds_tokens(self):
        bucket = TokenBucket(rate=100.0, capacity=10)
        await bucket.acquire(10)  # Drain
        await asyncio.sleep(0.1)  # Wait for ~10 tokens to refill
        # Should be able to acquire again without long wait
        start = time.monotonic()
        await bucket.acquire(5)
        elapsed = time.monotonic() - start
        assert elapsed < 0.1


class TestGetLimiter:
    def test_returns_existing_limiter(self):
        limiter = get_limiter("nano_banana")
        assert limiter is not None
        assert limiter.capacity == 5

    def test_creates_new_limiter(self):
        limiter = get_limiter("new_service_xyz")
        assert limiter is not None
        assert limiter.capacity == 10  # default

    def test_same_instance_returned(self):
        a = get_limiter("nano_banana")
        b = get_limiter("nano_banana")
        assert a is b
