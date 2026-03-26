"""PiAPI unified client — single gateway for all generative AI models.

PiAPI provides a unified API schema with just two endpoints:
  POST /api/v1/task  — Create a task
  GET  /api/v1/task/{task_id} — Get task status/result

Supports:
  - Flux (image generation): flux1-dev, flux1-schnell, flux1-dev-advanced
  - Kling (video generation): 1.0, 1.5, 2.0, 2.5 — text-to-video, image-to-video
  - Seedance 2.0 (video): cinematic video generation
  - Veo3 (video): Google's video model via PiAPI

All models share the same create/poll pattern.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

PIAPI_BASE_URL = "https://api.piapi.ai/api/v1"
PIAPI_API_KEY = os.getenv("PIAPI_API_KEY", "")


@dataclass
class PiAPITaskResult:
    """Result from a PiAPI task."""

    task_id: str = ""
    status: str = ""  # pending, processing, completed, failed
    model: str = ""
    task_type: str = ""
    output: dict = field(default_factory=dict)
    error: dict = field(default_factory=dict)
    duration_s: float = 0.0

    @property
    def succeeded(self) -> bool:
        return self.status == "completed"

    @property
    def image_urls(self) -> list[str]:
        """Extract image URLs from output."""
        urls = []
        # Flux format
        if "image_url" in self.output:
            urls.append(self.output["image_url"])
        if "image_urls" in self.output:
            urls.extend(self.output["image_urls"])
        # Works format (Kling etc.)
        for work in self.output.get("works", []):
            if "image" in work and "resource" in work["image"]:
                urls.append(work["image"]["resource"])
        return urls

    @property
    def video_urls(self) -> list[str]:
        """Extract video URLs from output."""
        urls = []
        # Works format (Kling, Seedance)
        for work in self.output.get("works", []):
            vid = work.get("video", {})
            url = vid.get("resource_without_watermark") or vid.get("resource", "")
            if url:
                urls.append(url)
        # Direct video_url (Framepack, etc.)
        if "video_url" in self.output:
            urls.append(self.output["video_url"])
        # Luma/Veo format
        if "video" in self.output and isinstance(self.output["video"], dict):
            url = self.output["video"].get("url", "")
            if url:
                urls.append(url)
        return urls


class PiAPIClient:
    """Unified PiAPI client for all generative AI models."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key or PIAPI_API_KEY
        self._client = httpx.AsyncClient(
            base_url=PIAPI_BASE_URL,
            timeout=30.0,
            headers={
                "x-api-key": self._api_key,
                "Content-Type": "application/json",
            },
        )

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    # ------------------------------------------------------------------
    # Core: Create + Poll
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def create_task(
        self,
        model: str,
        task_type: str,
        input_data: dict,
        config: dict | None = None,
    ) -> str:
        """Create a task and return the task_id."""
        payload: dict = {
            "model": model,
            "task_type": task_type,
            "input": input_data,
        }
        if config:
            payload["config"] = config

        logger.info("piapi.create_task", model=model, task_type=task_type)
        resp = await self._client.post("/task", json=payload)
        resp.raise_for_status()
        data = resp.json()
        task_id = data.get("data", {}).get("task_id", "")

        if not task_id:
            raise RuntimeError(f"PiAPI did not return task_id: {data}")

        logger.info("piapi.task_created", task_id=task_id)
        return task_id

    async def get_task(self, task_id: str) -> PiAPITaskResult:
        """Fetch task status and result."""
        resp = await self._client.get(f"/task/{task_id}")
        resp.raise_for_status()
        data = resp.json().get("data", {})

        return PiAPITaskResult(
            task_id=data.get("task_id", task_id),
            status=data.get("status", "unknown"),
            model=data.get("model", ""),
            task_type=data.get("task_type", ""),
            output=data.get("output", {}),
            error=data.get("error", {}),
        )

    async def wait_for_task(
        self, task_id: str, timeout: float = 300, poll_interval: float = 3.0
    ) -> PiAPITaskResult:
        """Poll until task completes or times out."""
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            result = await self.get_task(task_id)

            if result.status == "completed":
                result.duration_s = round(time.monotonic() - start, 1)
                logger.info("piapi.task_completed", task_id=task_id, duration=result.duration_s)
                return result
            elif result.status == "failed":
                error_msg = result.error.get("message", "Unknown error")
                logger.error("piapi.task_failed", task_id=task_id, error=error_msg)
                raise RuntimeError(f"PiAPI task failed: {error_msg}")

            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"PiAPI task {task_id} timed out after {timeout}s")

    async def run_task(
        self,
        model: str,
        task_type: str,
        input_data: dict,
        config: dict | None = None,
        timeout: float = 300,
    ) -> PiAPITaskResult:
        """Create a task and wait for completion. Full end-to-end."""
        task_id = await self.create_task(model, task_type, input_data, config)
        return await self.wait_for_task(task_id, timeout)

    # ------------------------------------------------------------------
    # Flux — Image Generation
    # ------------------------------------------------------------------

    async def flux_text_to_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        model: str = "Qubico/flux1-dev",
        negative_prompt: str = "",
    ) -> PiAPITaskResult:
        """Generate an image from text using Flux."""
        input_data: dict = {
            "prompt": prompt,
            "width": width,
            "height": height,
        }
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt

        return await self.run_task(model, "txt2img", input_data, timeout=120)

    async def flux_image_to_image(
        self,
        prompt: str,
        image_url: str,
        model: str = "Qubico/flux1-dev",
    ) -> PiAPITaskResult:
        """Transform an image using Flux."""
        return await self.run_task(
            model, "img2img",
            {"prompt": prompt, "image": image_url},
            timeout=120,
        )

    # ------------------------------------------------------------------
    # Kling — Video Generation
    # ------------------------------------------------------------------

    async def kling_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        mode: str = "std",
        negative_prompt: str = "",
        cfg_scale: float = 0.5,
        version: str = "3.0",
    ) -> PiAPITaskResult:
        """Generate video from text using Kling.

        version: "1.0", "1.5", "2.0", "2.5", "3.0" (default: 3.0, best value 2026)
        mode: "std" (standard) or "pro" (higher quality, 2x cost)
        """
        input_data: dict = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "mode": mode,
            "cfg_scale": cfg_scale,
            "version": version,
        }
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt

        return await self.run_task("kling", "video_generation", input_data, timeout=600)

    async def kling_image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 5,
        aspect_ratio: str = "9:16",
        mode: str = "std",
        version: str = "3.0",
    ) -> PiAPITaskResult:
        """Animate an image into video using Kling.

        Kling 3.0: Best motion quality at lowest cost (2026).
        """
        input_data: dict = {
            "image_url": image_url,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "mode": mode,
            "version": version,
        }
        return await self.run_task("kling", "video_generation", input_data, timeout=600)

    # ------------------------------------------------------------------
    # Seedance 2.0 — Cinematic Video (ByteDance)
    # ------------------------------------------------------------------

    async def seedance_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
    ) -> PiAPITaskResult:
        """Generate cinematic video using Seedance 2.0.

        Best for: cinematic, ultra-realistic, immersive content.
        Supports: text-to-video, image-to-video, video edit.
        """
        return await self.run_task(
            "seedance", "seedance-2-preview",
            {
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
            },
            timeout=600,
        )

    async def seedance_image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 5,
        aspect_ratio: str = "9:16",
    ) -> PiAPITaskResult:
        """Animate image with Seedance 2.0."""
        input_data: dict = {
            "prompt": prompt,
            "image_urls": [image_url],
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        return await self.run_task(
            "seedance", "seedance-2-preview",
            input_data,
            timeout=600,
        )

    # ------------------------------------------------------------------
    # Veo3 — Google Video
    # ------------------------------------------------------------------

    async def veo3_image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 8,
        aspect_ratio: str = "9:16",
        enable_audio: bool = False,
    ) -> PiAPITaskResult:
        """Generate video from image using Veo3."""
        return await self.run_task(
            "veo3", "image_to_video",
            {
                "image_url": image_url,
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "generate_audio": enable_audio,
            },
            timeout=600,
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    async def download(self, url: str, output_path: Path) -> Path:
        """Download a generated file from URL."""
        async with httpx.AsyncClient(timeout=120.0) as dl:
            resp = await dl.get(url)
            resp.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(resp.content)
            logger.info("piapi.downloaded", path=str(output_path), size=len(resp.content))
            return output_path

    async def close(self) -> None:
        await self._client.aclose()
