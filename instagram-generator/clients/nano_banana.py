"""Nano Banana API client — image generation for Instagram creatives."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = structlog.get_logger(__name__)

ImageStyle = Literal[
    "photorealistic",
    "illustration",
    "3d_render",
    "anime",
    "watercolor",
    "flat_design",
]

# Instagram-optimized aspect ratios
ASPECT_RATIOS = {
    "feed_square": (1080, 1080),
    "feed_portrait": (1080, 1350),
    "feed_landscape": (1080, 566),
    "story": (1080, 1920),
    "reel_cover": (1080, 1920),
}


class NanoBananaClient:
    """Generate images via Nano Banana API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.nano_banana_api_key
        self._base_url = base_url or settings.nano_banana_base_url
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=120.0,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    async def generate_image(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        style: ImageStyle = "photorealistic",
        aspect_ratio: str = "feed_square",
        seed: int | None = None,
    ) -> bytes:
        """Generate a single image and return raw bytes."""
        w, h = ASPECT_RATIOS.get(aspect_ratio, (1080, 1080))
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "style": style,
            "width": w,
            "height": h,
            "num_images": 1,
        }
        if seed is not None:
            payload["seed"] = seed

        logger.info("nano_banana.generate", prompt=prompt[:80], size=f"{w}x{h}")

        # Submit generation task
        resp = await self._client.post("/images/generate", json=payload)
        resp.raise_for_status()
        task = resp.json()
        task_id = task["id"]

        # Poll until ready
        image_url = await self._poll_task(task_id)
        return await self._download(image_url)

    async def generate_carousel(
        self,
        prompts: list[str],
        *,
        style: ImageStyle = "photorealistic",
        aspect_ratio: str = "feed_square",
    ) -> list[bytes]:
        """Generate multiple images for a carousel post."""
        tasks = [
            self.generate_image(p, style=style, aspect_ratio=aspect_ratio)
            for p in prompts
        ]
        return await asyncio.gather(*tasks)

    async def save_image(
        self,
        image_bytes: bytes,
        output_path: Path,
    ) -> Path:
        """Persist generated image to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        logger.info("nano_banana.saved", path=str(output_path))
        return output_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _poll_task(self, task_id: str, timeout: float = 300) -> str:
        """Poll a generation task until completion, return image URL."""
        import time

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            resp = await self._client.get(f"/images/tasks/{task_id}")
            resp.raise_for_status()
            data = resp.json()

            if data["status"] == "completed":
                return data["output"]["images"][0]["url"]
            if data["status"] == "failed":
                raise RuntimeError(f"Image generation failed: {data.get('error')}")

            await asyncio.sleep(3)
        raise TimeoutError(f"Image generation timed out after {timeout}s")

    async def _download(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=60.0) as tmp:
            resp = await tmp.get(url)
            resp.raise_for_status()
            return resp.content

    async def close(self) -> None:
        await self._client.aclose()
