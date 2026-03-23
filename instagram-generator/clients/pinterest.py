"""Pinterest API client — post Pins to boards."""

from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class PinterestClient:
    """Publish Pins to Pinterest via the API v5."""

    BASE_URL = "https://api.pinterest.com/v5"

    def __init__(self, access_token: str = "", board_id: str = "") -> None:
        self._token = access_token
        self._board_id = board_id
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=60.0,
            headers={"Authorization": f"Bearer {self._token}"},
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def create_pin(
        self,
        image_url: str,
        title: str = "",
        description: str = "",
        link: str = "",
        board_id: str = "",
        alt_text: str = "",
    ) -> str:
        """Create a Pin. Returns pin ID."""
        payload: dict = {
            "board_id": board_id or self._board_id,
            "media_source": {
                "source_type": "image_url",
                "url": image_url,
            },
        }
        if title:
            payload["title"] = title[:100]
        if description:
            payload["description"] = description[:500]
        if link:
            payload["link"] = link
        if alt_text:
            payload["alt_text"] = alt_text[:500]

        resp = await self._client.post("/pins", json=payload)
        resp.raise_for_status()
        pin_id = resp.json()["id"]
        logger.info("pinterest.pin_created", pin_id=pin_id)
        return pin_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def create_video_pin(
        self,
        video_url: str,
        cover_image_url: str = "",
        title: str = "",
        description: str = "",
        board_id: str = "",
    ) -> str:
        """Create a video Pin. Returns pin ID."""
        media_source: dict = {
            "source_type": "video_url",
            "url": video_url,
        }
        if cover_image_url:
            media_source["cover_image_url"] = cover_image_url

        payload: dict = {
            "board_id": board_id or self._board_id,
            "media_source": media_source,
        }
        if title:
            payload["title"] = title[:100]
        if description:
            payload["description"] = description[:500]

        resp = await self._client.post("/pins", json=payload)
        resp.raise_for_status()
        pin_id = resp.json()["id"]
        logger.info("pinterest.video_pin_created", pin_id=pin_id)
        return pin_id

    async def get_boards(self) -> list[dict]:
        """List user's boards."""
        resp = await self._client.get("/boards")
        resp.raise_for_status()
        return resp.json().get("items", [])

    async def get_pin_analytics(self, pin_id: str) -> dict:
        """Get analytics for a pin."""
        resp = await self._client.get(
            f"/pins/{pin_id}/analytics",
            params={"start_date": "2026-01-01", "end_date": "2026-12-31", "metric_types": "IMPRESSION,PIN_CLICK,SAVE"},
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()
