"""TikTok API client — post videos via Content Posting API."""

from __future__ import annotations

import asyncio

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class TikTokClient:
    """Publish videos to TikTok via the Content Posting API v2."""

    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self, access_token: str = "") -> None:
        self._token = access_token
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=120.0,
            headers={"Authorization": f"Bearer {self._token}"},
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_video(
        self,
        video_url: str,
        caption: str,
        *,
        privacy_level: str = "PUBLIC_TO_EVERYONE",
        disable_duet: bool = False,
        disable_stitch: bool = False,
    ) -> str:
        """Post a video to TikTok. Returns publish_id."""
        # Step 1: Initialize upload
        init_resp = await self._client.post(
            "/post/publish/video/init/",
            json={
                "post_info": {
                    "title": caption[:150],
                    "privacy_level": privacy_level,
                    "disable_duet": disable_duet,
                    "disable_stitch": disable_stitch,
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "video_url": video_url,
                },
            },
        )
        init_resp.raise_for_status()
        data = init_resp.json()
        publish_id = data["data"]["publish_id"]

        logger.info("tiktok.upload_init", publish_id=publish_id)

        # Step 2: Poll for completion
        await self._wait_for_publish(publish_id)
        return publish_id

    async def post_photo(
        self,
        image_urls: list[str],
        caption: str,
        *,
        privacy_level: str = "PUBLIC_TO_EVERYONE",
    ) -> str:
        """Post photo carousel to TikTok. Returns publish_id."""
        resp = await self._client.post(
            "/post/publish/content/init/",
            json={
                "post_info": {
                    "title": caption[:150],
                    "privacy_level": privacy_level,
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "photo_images": image_urls,
                    "post_mode": "DIRECT_POST",
                },
                "media_type": "PHOTO",
            },
        )
        resp.raise_for_status()
        publish_id = resp.json()["data"]["publish_id"]
        logger.info("tiktok.photo_posted", publish_id=publish_id)
        return publish_id

    async def _wait_for_publish(self, publish_id: str, timeout: float = 300) -> None:
        """Poll TikTok for publish status."""
        import time

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            resp = await self._client.post(
                "/post/publish/status/fetch/",
                json={"publish_id": publish_id},
            )
            if resp.status_code == 200:
                status = resp.json().get("data", {}).get("status")
                if status == "PUBLISH_COMPLETE":
                    logger.info("tiktok.published", publish_id=publish_id)
                    return
                if status == "FAILED":
                    raise RuntimeError(f"TikTok publish failed: {publish_id}")
            await asyncio.sleep(5)

        raise TimeoutError(f"TikTok publish timed out: {publish_id}")

    async def close(self) -> None:
        await self._client.aclose()
