"""Tests for notification system."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from notifications import NotificationManager


class TestNotificationManager:
    def test_telegram_disabled_by_default(self):
        manager = NotificationManager()
        assert manager.telegram_enabled is False

    def test_webhook_disabled_by_default(self):
        manager = NotificationManager()
        assert manager.webhook_enabled is False

    @patch.dict("os.environ", {
        "TELEGRAM_BOT_TOKEN": "123:ABC",
        "TELEGRAM_CHAT_ID": "-100123456",
    })
    def test_telegram_enabled_with_env(self):
        manager = NotificationManager()
        assert manager.telegram_enabled is True

    @patch.dict("os.environ", {
        "NOTIFY_WEBHOOK_URL": "https://hooks.slack.com/test",
    })
    def test_webhook_enabled_with_env(self):
        manager = NotificationManager()
        assert manager.webhook_enabled is True

    @pytest.mark.asyncio
    async def test_send_logs_even_without_channels(self):
        """send() should always work (at minimum logs the message)."""
        manager = NotificationManager()
        # Should not raise even with no channels configured
        await manager.send("Test message")

    @pytest.mark.asyncio
    async def test_send_published_shortcut(self):
        manager = NotificationManager()
        await manager.send_published("test_label", "media_123")

    @pytest.mark.asyncio
    async def test_send_daily_summary(self):
        manager = NotificationManager()
        await manager.send_daily_summary({
            "published": 3, "failed": 0, "queue_pending": 5,
        })
