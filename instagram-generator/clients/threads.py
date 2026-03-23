"""Threads API client — post to Meta's Threads platform.

Threads shares infrastructure with Instagram Graph API.
Content types: text, image, video, carousel.
"""

from __future__ import annotations

import asyncio

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class ThreadsClient:
    """Publish content to Threads via the Threads API."""

    BASE_URL = "https://graph.threads.net/v1.0"

    def __init__(
        self,
        access_token: str = "",
        user_id: str = "",
    ) -> None:
        self._token = access_token
        self._user_id = user_id
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=120.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_text(self, text: str) -> str:
        """Post a text thread. Returns media ID."""
        container_id = await self._create_container(
            media_type="TEXT",
            text=text,
        )
        return await self._publish(container_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_image(self, image_url: str, text: str = "") -> str:
        """Post an image thread. Returns media ID."""
        container_id = await self._create_container(
            media_type="IMAGE",
            image_url=image_url,
            text=text,
        )
        return await self._publish(container_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_video(self, video_url: str, text: str = "") -> str:
        """Post a video thread. Returns media ID."""
        container_id = await self._create_container(
            media_type="VIDEO",
            video_url=video_url,
            text=text,
        )
        await self._wait_for_container(container_id)
        return await self._publish(container_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_carousel(
        self, items: list[dict], text: str = ""
    ) -> str:
        """Post a carousel thread.

        items: [{"type": "IMAGE"|"VIDEO", "url": "..."}]
        """
        child_ids = []
        for item in items:
            if item["type"] == "IMAGE":
                cid = await self._create_container(
                    media_type="IMAGE",
                    image_url=item["url"],
                    is_carousel_item=True,
                )
            else:
                cid = await self._create_container(
                    media_type="VIDEO",
                    video_url=item["url"],
                    is_carousel_item=True,
                )
            child_ids.append(cid)

        container_id = await self._create_container(
            media_type="CAROUSEL",
            children=child_ids,
            text=text,
        )
        return await self._publish(container_id)

    async def _create_container(
        self,
        media_type: str,
        text: str = "",
        image_url: str = "",
        video_url: str = "",
        is_carousel_item: bool = False,
        children: list[str] | None = None,
    ) -> str:
        """Create a media container."""
        params: dict = {
            "media_type": media_type,
            "access_token": self._token,
        }
        if text:
            params["text"] = text[:500]
        if image_url:
            params["image_url"] = image_url
        if video_url:
            params["video_url"] = video_url
        if is_carousel_item:
            params["is_carousel_item"] = "true"
        if children:
            params["children"] = ",".join(children)

        resp = await self._client.post(
            f"/{self._user_id}/threads", params=params
        )
        resp.raise_for_status()
        return resp.json()["id"]

    async def _publish(self, container_id: str) -> str:
        """Publish a container."""
        resp = await self._client.post(
            f"/{self._user_id}/threads_publish",
            params={
                "creation_id": container_id,
                "access_token": self._token,
            },
        )
        resp.raise_for_status()
        media_id = resp.json()["id"]
        logger.info("threads.published", media_id=media_id)
        return media_id

    async def _wait_for_container(
        self, container_id: str, timeout: float = 300
    ) -> None:
        """Wait for video container processing."""
        import time

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            resp = await self._client.get(
                f"/{container_id}",
                params={
                    "fields": "status",
                    "access_token": self._token,
                },
            )
            if resp.status_code == 200:
                status = resp.json().get("status")
                if status == "FINISHED":
                    return
                if status == "ERROR":
                    raise RuntimeError(f"Threads container failed: {container_id}")
            await asyncio.sleep(5)
        raise TimeoutError("Threads video processing timed out")

    async def close(self) -> None:
        await self._client.aclose()
