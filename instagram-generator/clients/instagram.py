"""Instagram Graph API client — auto-posting images, carousels, reels & stories."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = structlog.get_logger(__name__)

MediaType = Literal["IMAGE", "VIDEO", "CAROUSEL_ALBUM", "STORIES", "REELS"]


class InstagramClient:
    """Publish content to Instagram via the Graph API."""

    BASE_URL = "https://graph.facebook.com/v21.0"

    def __init__(
        self,
        access_token: str | None = None,
        account_id: str | None = None,
    ) -> None:
        self._token = access_token or settings.instagram_access_token
        self._account_id = account_id or settings.instagram_business_account_id
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=120.0,
        )

    # ------------------------------------------------------------------
    # Single image post
    # ------------------------------------------------------------------

    async def post_image(
        self,
        image_url: str,
        caption: str,
    ) -> str:
        """Publish a single-image post. Returns the media ID."""
        container_id = await self._create_media_container(
            image_url=image_url,
            caption=caption,
            media_type="IMAGE",
        )
        return await self._publish(container_id)

    # ------------------------------------------------------------------
    # Carousel (up to 10 images/videos)
    # ------------------------------------------------------------------

    async def post_carousel(
        self,
        media_urls: list[dict],
        caption: str,
    ) -> str:
        """Publish a carousel.

        media_urls: [{"url": "...", "type": "IMAGE"|"VIDEO"}, ...]
        """
        child_ids = []
        for item in media_urls:
            cid = await self._create_media_container(
                image_url=item["url"] if item["type"] == "IMAGE" else None,
                video_url=item["url"] if item["type"] == "VIDEO" else None,
                is_carousel_item=True,
            )
            child_ids.append(cid)

        # Create carousel container
        container_id = await self._create_carousel_container(child_ids, caption)
        return await self._publish(container_id)

    # ------------------------------------------------------------------
    # Reels (short video)
    # ------------------------------------------------------------------

    async def post_reel(
        self,
        video_url: str,
        caption: str,
        *,
        cover_url: str | None = None,
        share_to_feed: bool = True,
    ) -> str:
        """Publish a Reel. Returns the media ID."""
        container_id = await self._create_media_container(
            video_url=video_url,
            caption=caption,
            media_type="REELS",
            cover_url=cover_url,
            share_to_feed=share_to_feed,
        )
        # Reels need time to process on IG side
        await self._wait_for_container(container_id)
        return await self._publish(container_id)

    # ------------------------------------------------------------------
    # Stories
    # ------------------------------------------------------------------

    async def post_story(
        self,
        media_url: str,
        *,
        is_video: bool = False,
    ) -> str:
        """Publish an image or video as a Story."""
        container_id = await self._create_media_container(
            image_url=media_url if not is_video else None,
            video_url=media_url if is_video else None,
            media_type="STORIES",
        )
        if is_video:
            await self._wait_for_container(container_id)
        return await self._publish(container_id)

    # ------------------------------------------------------------------
    # Account insights (useful for scheduling optimization)
    # ------------------------------------------------------------------

    async def get_insights(
        self,
        metric: str = "impressions,reach,profile_views",
        period: str = "day",
    ) -> dict:
        resp = await self._client.get(
            f"/{self._account_id}/insights",
            params={
                "metric": metric,
                "period": period,
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _create_media_container(
        self,
        *,
        image_url: str | None = None,
        video_url: str | None = None,
        caption: str = "",
        media_type: MediaType = "IMAGE",
        is_carousel_item: bool = False,
        cover_url: str | None = None,
        share_to_feed: bool = True,
    ) -> str:
        params: dict = {"access_token": self._token}

        if image_url:
            params["image_url"] = image_url
        if video_url:
            params["video_url"] = video_url
        if caption:
            params["caption"] = caption
        if media_type in ("REELS", "STORIES"):
            params["media_type"] = media_type
        if is_carousel_item:
            params["is_carousel_item"] = "true"
        if cover_url:
            params["cover_url"] = cover_url
        if media_type == "REELS":
            params["share_to_feed"] = str(share_to_feed).lower()

        logger.info("instagram.create_container", media_type=media_type)
        resp = await self._client.post(
            f"/{self._account_id}/media", params=params
        )
        resp.raise_for_status()
        return resp.json()["id"]

    async def _create_carousel_container(
        self, child_ids: list[str], caption: str
    ) -> str:
        params = {
            "access_token": self._token,
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
        }
        resp = await self._client.post(
            f"/{self._account_id}/media", params=params
        )
        resp.raise_for_status()
        return resp.json()["id"]

    async def _wait_for_container(
        self, container_id: str, timeout: float = 300
    ) -> None:
        """Wait until a video container finishes processing on IG side."""
        import time

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            resp = await self._client.get(
                f"/{container_id}",
                params={
                    "fields": "status_code",
                    "access_token": self._token,
                },
            )
            resp.raise_for_status()
            status = resp.json().get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Container {container_id} processing failed")
            await asyncio.sleep(5)
        raise TimeoutError("Video container processing timed out")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _publish(self, container_id: str) -> str:
        logger.info("instagram.publish", container_id=container_id)
        resp = await self._client.post(
            f"/{self._account_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        media_id = resp.json()["id"]
        logger.info("instagram.published", media_id=media_id)
        return media_id

    async def close(self) -> None:
        await self._client.aclose()
