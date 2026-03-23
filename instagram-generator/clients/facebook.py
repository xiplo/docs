"""Facebook Pages API client — post to Facebook Pages."""

from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class FacebookClient:
    """Publish content to Facebook Pages via the Graph API."""

    BASE_URL = "https://graph.facebook.com/v21.0"

    def __init__(
        self,
        page_access_token: str = "",
        page_id: str = "",
    ) -> None:
        self._token = page_access_token
        self._page_id = page_id
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=120.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_text(self, message: str) -> str:
        """Post a text update. Returns post ID."""
        resp = await self._client.post(
            f"/{self._page_id}/feed",
            params={
                "message": message,
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        post_id = resp.json()["id"]
        logger.info("facebook.posted_text", post_id=post_id)
        return post_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_photo(
        self, image_url: str, caption: str = ""
    ) -> str:
        """Post a photo. Returns post ID."""
        resp = await self._client.post(
            f"/{self._page_id}/photos",
            params={
                "url": image_url,
                "caption": caption,
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        post_id = resp.json()["id"]
        logger.info("facebook.posted_photo", post_id=post_id)
        return post_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_video(
        self,
        video_url: str,
        title: str = "",
        description: str = "",
    ) -> str:
        """Post a video (Reel). Returns post ID."""
        resp = await self._client.post(
            f"/{self._page_id}/videos",
            params={
                "file_url": video_url,
                "title": title,
                "description": description,
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        post_id = resp.json()["id"]
        logger.info("facebook.posted_video", post_id=post_id)
        return post_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_reel(
        self,
        video_url: str,
        description: str = "",
    ) -> str:
        """Post a Facebook Reel. Returns post ID."""
        # Step 1: Create reel container
        resp = await self._client.post(
            f"/{self._page_id}/video_reels",
            params={
                "upload_phase": "start",
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        video_id = resp.json()["video_id"]

        # Step 2: Upload video
        resp = await self._client.post(
            f"/{video_id}",
            params={
                "upload_phase": "finish",
                "video_file_url": video_url,
                "description": description,
                "access_token": self._token,
            },
        )
        resp.raise_for_status()

        logger.info("facebook.posted_reel", video_id=video_id)
        return video_id

    async def get_page_insights(self, metric: str = "page_impressions,page_engaged_users") -> dict:
        resp = await self._client.get(
            f"/{self._page_id}/insights",
            params={
                "metric": metric,
                "period": "day",
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self) -> None:
        await self._client.aclose()
