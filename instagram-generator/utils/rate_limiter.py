"""Rate limiter — token bucket algorithm for API call throttling.

Prevents hitting API rate limits across all clients. Each API provider
gets its own bucket with configurable rates.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TokenBucket:
    """Token bucket rate limiter."""

    rate: float  # Tokens per second
    capacity: int  # Maximum burst size
    _tokens: float = 0.0
    _last_refill: float = field(default_factory=time.monotonic)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self):
        self._tokens = float(self.capacity)

    async def acquire(self, tokens: int = 1) -> None:
        """Wait until enough tokens are available, then consume them."""
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                # Calculate wait time for needed tokens
                needed = tokens - self._tokens
                wait = needed / self.rate
                await asyncio.sleep(wait)
                self._refill()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now


# Pre-configured rate limiters for each API provider
# Adjust rates based on your API tier

RATE_LIMITERS: dict[str, TokenBucket] = {
    # Nano Banana: ~30 requests/minute
    "nano_banana": TokenBucket(rate=0.5, capacity=5),
    # Kling: ~10 requests/minute (video generation is heavy)
    "kling": TokenBucket(rate=0.17, capacity=3),
    # ElevenLabs: ~20 requests/minute
    "elevenlabs": TokenBucket(rate=0.33, capacity=4),
    # Instagram Graph API: ~200 calls/hour
    "instagram": TokenBucket(rate=3.3, capacity=10),
    # CDN upload: ~60/minute
    "cdn": TokenBucket(rate=1.0, capacity=10),
}


def get_limiter(provider: str) -> TokenBucket:
    """Get rate limiter for a provider, creating if needed."""
    if provider not in RATE_LIMITERS:
        RATE_LIMITERS[provider] = TokenBucket(rate=1.0, capacity=10)
    return RATE_LIMITERS[provider]
