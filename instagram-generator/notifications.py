"""Notification system — send alerts via Telegram, webhook, or log.

Channels:
  - telegram: Send to Telegram bot (requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
  - webhook:  POST to external URL (Slack, Discord, custom)
  - log:      Just log the message (always active as fallback)

All channels are non-blocking — failures don't stop the pipeline.
"""

from __future__ import annotations

import os

import httpx
import structlog

logger = structlog.get_logger(__name__)


class NotificationManager:
    """Sends notifications through configured channels."""

    def __init__(self) -> None:
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.notify_webhook_url = os.getenv("NOTIFY_WEBHOOK_URL", "")

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_token and self.telegram_chat_id)

    @property
    def webhook_enabled(self) -> bool:
        return bool(self.notify_webhook_url)

    async def send(self, message: str, level: str = "info") -> None:
        """Send a notification through all configured channels."""
        # Always log
        logger.info("notification", message=message[:200], level=level)

        if self.telegram_enabled:
            await self._send_telegram(message)

        if self.webhook_enabled:
            await self._send_webhook(message, level)

    async def send_published(self, label: str, media_id: str) -> None:
        """Shortcut: notify about a published post."""
        await self.send(
            f"Published: {label}\nMedia ID: {media_id}",
            level="info",
        )

    async def send_failed(self, label: str, error: str) -> None:
        """Shortcut: notify about a failed post."""
        await self.send(
            f"FAILED: {label}\nError: {error[:200]}",
            level="error",
        )

    async def send_daily_summary(self, stats: dict) -> None:
        """Send daily performance summary."""
        lines = [
            "Daily Summary",
            f"Published: {stats.get('published', 0)}",
            f"Failed: {stats.get('failed', 0)}",
            f"Queue pending: {stats.get('queue_pending', 0)}",
        ]
        await self.send("\n".join(lines), level="info")

    # ------------------------------------------------------------------
    # Telegram
    # ------------------------------------------------------------------

    async def _send_telegram(self, message: str) -> None:
        """Send message via Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": f"Instagram Bot\n\n{message}",
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.warning(
                        "telegram.send_failed",
                        status=resp.status_code,
                        body=resp.text[:200],
                    )
        except Exception as exc:
            logger.warning("telegram.error", error=str(exc))

    # ------------------------------------------------------------------
    # Webhook (Slack, Discord, custom)
    # ------------------------------------------------------------------

    async def _send_webhook(self, message: str, level: str = "info") -> None:
        """POST notification to external webhook URL."""
        payload = {
            "text": message,
            "level": level,
            "source": "instagram-generator",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.notify_webhook_url, json=payload)
                if resp.status_code >= 400:
                    logger.warning(
                        "webhook.notify_failed",
                        status=resp.status_code,
                    )
        except Exception as exc:
            logger.warning("webhook.notify_error", error=str(exc))
