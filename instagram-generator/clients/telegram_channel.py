"""Telegram Channel client — post to Telegram channels/groups."""

from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class TelegramChannelClient:
    """Publish content to Telegram channels via the Bot API."""

    BASE_URL = "https://api.telegram.org"

    def __init__(self, bot_token: str = "", channel_id: str = "") -> None:
        self._token = bot_token
        self._channel_id = channel_id
        self._client = httpx.AsyncClient(timeout=60.0)

    @property
    def _api_base(self) -> str:
        return f"{self.BASE_URL}/bot{self._token}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def send_message(self, text: str, parse_mode: str = "HTML") -> int:
        """Send a text message to channel. Returns message_id."""
        resp = await self._client.post(
            f"{self._api_base}/sendMessage",
            json={
                "chat_id": self._channel_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": False,
            },
        )
        resp.raise_for_status()
        msg_id = resp.json()["result"]["message_id"]
        logger.info("telegram.message_sent", message_id=msg_id)
        return msg_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def send_photo(
        self, photo_url: str, caption: str = ""
    ) -> int:
        """Send a photo to channel. Returns message_id."""
        resp = await self._client.post(
            f"{self._api_base}/sendPhoto",
            json={
                "chat_id": self._channel_id,
                "photo": photo_url,
                "caption": caption[:1024],
                "parse_mode": "HTML",
            },
        )
        resp.raise_for_status()
        msg_id = resp.json()["result"]["message_id"]
        logger.info("telegram.photo_sent", message_id=msg_id)
        return msg_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def send_video(
        self,
        video_url: str,
        caption: str = "",
        *,
        duration: int = 0,
        width: int = 0,
        height: int = 0,
    ) -> int:
        """Send a video to channel. Returns message_id."""
        payload: dict = {
            "chat_id": self._channel_id,
            "video": video_url,
            "caption": caption[:1024],
            "parse_mode": "HTML",
            "supports_streaming": True,
        }
        if duration:
            payload["duration"] = duration
        if width:
            payload["width"] = width
        if height:
            payload["height"] = height

        resp = await self._client.post(
            f"{self._api_base}/sendVideo",
            json=payload,
        )
        resp.raise_for_status()
        msg_id = resp.json()["result"]["message_id"]
        logger.info("telegram.video_sent", message_id=msg_id)
        return msg_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def send_media_group(
        self, media_items: list[dict]
    ) -> list[int]:
        """Send album (multiple photos/videos). Returns message_ids."""
        resp = await self._client.post(
            f"{self._api_base}/sendMediaGroup",
            json={
                "chat_id": self._channel_id,
                "media": media_items,
            },
        )
        resp.raise_for_status()
        results = resp.json()["result"]
        ids = [r["message_id"] for r in results]
        logger.info("telegram.media_group_sent", count=len(ids))
        return ids

    async def close(self) -> None:
        await self._client.aclose()
