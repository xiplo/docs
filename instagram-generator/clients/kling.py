"""Kling 3.0 (KIE) API client — video generation for Instagram Reels."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Literal

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = structlog.get_logger(__name__)

VideoMode = Literal["standard", "professional"]
VideoLength = Literal["5", "10"]


class KlingClient:
    """Generate videos via Kling 3.0 API for Instagram Reels/Stories."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.kling_api_key
        self._base_url = base_url or settings.kling_base_url
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=180.0,
        )

    # ------------------------------------------------------------------
    # Text-to-Video
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=60))
    async def text_to_video(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        duration: VideoLength = "5",
        mode: VideoMode = "professional",
        aspect_ratio: str = "9:16",  # Vertical for Reels
        cfg_scale: float = 0.5,
    ) -> bytes:
        """Generate a video from a text prompt."""
        payload = {
            "model": "kling-v3",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "duration": duration,
            "mode": mode,
            "aspect_ratio": aspect_ratio,
            "cfg_scale": cfg_scale,
        }

        logger.info("kling.text_to_video", prompt=prompt[:80], duration=duration)
        resp = await self._client.post(
            "/videos/text2video/generation", json=payload
        )
        resp.raise_for_status()
        task_id = resp.json()["data"]["task_id"]

        video_url = await self._poll_task(task_id)
        return await self._download(video_url)

    # ------------------------------------------------------------------
    # Image-to-Video (animate a Nano Banana image)
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=60))
    async def image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        *,
        duration: VideoLength = "5",
        mode: VideoMode = "professional",
    ) -> bytes:
        """Animate a static image into a short video clip."""
        payload = {
            "model": "kling-v3",
            "image": image_url,
            "prompt": prompt,
            "duration": duration,
            "mode": mode,
        }

        logger.info("kling.image_to_video", prompt=prompt[:80])
        resp = await self._client.post(
            "/videos/image2video/generation", json=payload
        )
        resp.raise_for_status()
        task_id = resp.json()["data"]["task_id"]

        video_url = await self._poll_task(task_id)
        return await self._download(video_url)

    # ------------------------------------------------------------------
    # Lip-sync (combine video + Uzbek voiceover)
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=60))
    async def lip_sync(
        self,
        video_url: str,
        audio_url: str,
    ) -> bytes:
        """Apply lip-sync to a video using provided audio track."""
        payload = {
            "model": "kling-v3",
            "video_url": video_url,
            "audio_url": audio_url,
            "mode": "professional",
        }

        logger.info("kling.lip_sync")
        resp = await self._client.post("/videos/lip-sync", json=payload)
        resp.raise_for_status()
        task_id = resp.json()["data"]["task_id"]

        video_url = await self._poll_task(task_id)
        return await self._download(video_url)

    # ------------------------------------------------------------------
    # Save helpers
    # ------------------------------------------------------------------

    async def save_video(self, video_bytes: bytes, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(video_bytes)
        logger.info("kling.saved", path=str(output_path))
        return output_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _poll_task(self, task_id: str, timeout: float = 600) -> str:
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            resp = await self._client.get(
                f"/videos/tasks/{task_id}",
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})

            status = data.get("task_status", "")
            if status == "succeed":
                videos = data.get("task_result", {}).get("videos", [])
                if videos:
                    return videos[0]["url"]
                raise RuntimeError("Task succeeded but no video URL returned")
            if status == "failed":
                raise RuntimeError(f"Video generation failed: {data.get('error')}")

            await asyncio.sleep(10)
        raise TimeoutError(f"Video generation timed out after {timeout}s")

    async def _download(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=120.0) as tmp:
            resp = await tmp.get(url)
            resp.raise_for_status()
            return resp.content

    async def close(self) -> None:
        await self._client.aclose()
