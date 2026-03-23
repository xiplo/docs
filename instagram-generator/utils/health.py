"""API provider health monitoring — check uptime and latency.

Monitors:
  - NanoBanana, Kling, ElevenLabs (generation APIs)
  - Instagram, Twitter, TikTok, YouTube, Facebook, Telegram, LinkedIn (publishing APIs)
  - CDN (S3/R2)

Reports:
  - Current status (up/down/degraded)
  - Response latency
  - Last check timestamp
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class HealthStatus:
    """Health check result for a provider."""

    provider: str
    status: str = "unknown"  # up, down, degraded, unknown
    latency_ms: float = 0.0
    error: str = ""
    checked_at: str = ""

    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = datetime.now().isoformat()


# Health check endpoints per provider
HEALTH_ENDPOINTS = {
    "nano_banana": {"url": "https://api.nanobanana.com/v1/health", "method": "GET"},
    "kling": {"url": "https://api.klingai.com/v1/health", "method": "GET"},
    "elevenlabs": {"url": "https://api.elevenlabs.io/v1/health", "method": "GET"},
    "instagram": {"url": "https://graph.facebook.com/v21.0/me", "method": "GET"},
    "twitter": {"url": "https://api.twitter.com/2/tweets/search/recent", "method": "GET"},
    "tiktok": {"url": "https://open.tiktokapis.com/v2/post/publish/status/fetch/", "method": "GET"},
    "youtube": {"url": "https://www.googleapis.com/youtube/v3/videos", "method": "GET"},
    "facebook": {"url": "https://graph.facebook.com/v21.0/me", "method": "GET"},
    "telegram": {"url": "https://api.telegram.org/bot/getMe", "method": "GET"},
    "linkedin": {"url": "https://api.linkedin.com/v2/me", "method": "GET"},
    "pinterest": {"url": "https://api.pinterest.com/v5/user_account", "method": "GET"},
    "threads": {"url": "https://graph.threads.net/v1.0/me", "method": "GET"},
}


class HealthMonitor:
    """Monitor API provider health."""

    _last_results: dict[str, HealthStatus] = {}

    @classmethod
    async def check(cls, provider: str) -> HealthStatus:
        """Check a single provider's health."""
        endpoint = HEALTH_ENDPOINTS.get(provider)
        if not endpoint:
            return HealthStatus(provider=provider, status="unknown", error="No endpoint configured")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.monotonic()
                resp = await client.get(endpoint["url"])
                latency = (time.monotonic() - start) * 1000

                if resp.status_code < 500:
                    status = HealthStatus(
                        provider=provider,
                        status="up",
                        latency_ms=round(latency, 1),
                    )
                else:
                    status = HealthStatus(
                        provider=provider,
                        status="degraded",
                        latency_ms=round(latency, 1),
                        error=f"HTTP {resp.status_code}",
                    )

        except httpx.ConnectError:
            status = HealthStatus(provider=provider, status="down", error="Connection refused")
        except httpx.TimeoutException:
            status = HealthStatus(provider=provider, status="down", error="Timeout")
        except Exception as exc:
            status = HealthStatus(provider=provider, status="down", error=str(exc)[:100])

        cls._last_results[provider] = status
        return status

    @classmethod
    async def check_all(cls) -> list[HealthStatus]:
        """Check all configured providers."""
        results = []
        for provider in HEALTH_ENDPOINTS:
            result = await cls.check(provider)
            results.append(result)
        return results

    @classmethod
    async def check_critical(cls) -> list[HealthStatus]:
        """Check only critical generation + publishing APIs."""
        critical = ["nano_banana", "kling", "elevenlabs", "instagram"]
        results = []
        for provider in critical:
            result = await cls.check(provider)
            results.append(result)
        return results

    @classmethod
    def get_last_results(cls) -> dict[str, HealthStatus]:
        return dict(cls._last_results)

    @classmethod
    def display(cls, results: list[HealthStatus] | None = None) -> str:
        data = results or list(cls._last_results.values())
        lines = [
            "=" * 65,
            "  API Provider Health",
            "=" * 65,
        ]

        if not data:
            lines.append("  No health checks run yet. Use: python main.py health --check")
        else:
            status_icons = {"up": "[OK]", "down": "[!!]", "degraded": "[~~]", "unknown": "[??]"}
            for s in data:
                icon = status_icons.get(s.status, "[??]")
                latency = f"{s.latency_ms:.0f}ms" if s.latency_ms else "—"
                error = f"  {s.error}" if s.error else ""
                lines.append(
                    f"  {icon} {s.provider:<14} {s.status:<10} {latency:<8}{error}"
                )

            up = sum(1 for s in data if s.status == "up")
            lines.append(f"\n  {up}/{len(data)} providers healthy")

        lines.append("=" * 65)
        return "\n".join(lines)
