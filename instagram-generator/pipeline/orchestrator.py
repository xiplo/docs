"""Content pipeline — orchestrates the full creative generation flow.

Flow for a Reel:
  1. Moderation check
  2. Generate image via Nano Banana
  3. Animate image into video via Kling 3.0
  4. Synthesize Uzbek voiceover via Eleven Labs
  5. Merge audio + video (ffmpeg)
  6. Add text overlay (optional)
  7. Upload final asset to CDN
  8. Publish to Instagram

Flow for Image Post:
  1. Moderation check
  2. Generate image(s) via Nano Banana
  3. Upload to CDN
  4. Publish to Instagram (single or carousel)

All stages are instrumented with metrics (latency, counts, errors).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

import structlog

from clients import ElevenLabsClient, InstagramClient, KlingClient, NanoBananaClient
from config import settings
from skills.moderation import ContentModerator
from utils.cdn import upload_to_cdn
from utils.circuit_breaker import get_breaker
from utils.media import add_text_overlay, merge_audio_video
from utils.metrics import metrics
from utils.rate_limiter import get_limiter

logger = structlog.get_logger(__name__)

ContentType = Literal["reel", "image", "carousel", "story"]


@dataclass
class ContentRequest:
    """Describes what content to generate."""

    content_type: ContentType
    image_prompt: str
    caption: str
    voiceover_text: str = ""
    image_style: str = "photorealistic"
    video_duration: str = "5"
    subtitle_text: str = ""
    carousel_prompts: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)


@dataclass
class ContentResult:
    """Result of a content pipeline run."""

    request_id: str
    content_type: ContentType
    media_id: str = ""
    local_paths: list[str] = field(default_factory=list)
    cdn_urls: list[str] = field(default_factory=list)
    status: str = "pending"
    error: str = ""
    created_at: str = ""


class ContentPipeline:
    """End-to-end creative generation and publishing pipeline."""

    def __init__(self) -> None:
        self.nano_banana = NanoBananaClient()
        self.kling = KlingClient()
        self.elevenlabs = ElevenLabsClient()
        self.instagram = InstagramClient()
        self._output_dir = settings.content_output_dir

    async def run(self, request: ContentRequest) -> ContentResult:
        """Execute the full pipeline for a content request."""
        request_id = uuid.uuid4().hex[:12]
        run_dir = self._output_dir / request_id
        run_dir.mkdir(parents=True, exist_ok=True)

        result = ContentResult(
            request_id=request_id,
            content_type=request.content_type,
            created_at=datetime.now().isoformat(),
        )

        metrics.inc("pipeline_runs_total", content_type=request.content_type)

        try:
            # Pre-publish moderation check
            with metrics.timer("pipeline_moderation_seconds"):
                moderation = ContentModerator.check_content_request(
                    caption=request.caption,
                    hashtags=request.hashtags,
                    voiceover=request.voiceover_text,
                )
            if not moderation.passed:
                logger.warning(
                    "pipeline.moderation_blocked",
                    request_id=request_id,
                    score=moderation.score,
                    flags=moderation.flags,
                )
                result.status = "blocked"
                result.error = f"Content moderation failed: {', '.join(moderation.flags)}"
                metrics.inc("pipeline_blocked_total", content_type=request.content_type)
                return result

            with metrics.timer("pipeline_generation_seconds", content_type=request.content_type):
                if request.content_type == "reel":
                    await self._produce_reel(request, run_dir, result)
                elif request.content_type == "story":
                    await self._produce_story(request, run_dir, result)
                elif request.content_type == "carousel":
                    await self._produce_carousel(request, run_dir, result)
                else:
                    await self._produce_image(request, run_dir, result)

            result.status = "published"
            metrics.inc("pipeline_published_total", content_type=request.content_type)
        except Exception as exc:
            logger.error("pipeline.failed", request_id=request_id, error=str(exc))
            result.status = "failed"
            result.error = str(exc)
            metrics.inc("pipeline_errors_total", content_type=request.content_type)

        return result

    # ------------------------------------------------------------------
    # Reel pipeline
    # ------------------------------------------------------------------

    async def _produce_reel(
        self,
        req: ContentRequest,
        run_dir: Path,
        result: ContentResult,
    ) -> None:
        logger.info("pipeline.reel.start", prompt=req.image_prompt[:60])

        # 1. Generate base image (rate-limited + circuit-breaker)
        await get_limiter("nano_banana").acquire()
        with metrics.timer("api_latency_seconds", provider="nano_banana"):
            image_bytes = await get_breaker("nano_banana").call(
                self.nano_banana.generate_image,
                req.image_prompt,
                style=req.image_style,
                aspect_ratio="story",  # 9:16
            )
        metrics.inc("api_calls_total", provider="nano_banana")
        image_path = run_dir / "base_image.png"
        await self.nano_banana.save_image(image_bytes, image_path)
        result.local_paths.append(str(image_path))

        # 2. Upload image to CDN for Kling input
        with metrics.timer("cdn_upload_seconds"):
            image_cdn_url = await upload_to_cdn(image_path)

        # 3. Animate image → video via Kling 3.0
        await get_limiter("kling").acquire()
        with metrics.timer("api_latency_seconds", provider="kling"):
            video_bytes = await get_breaker("kling").call(
                self.kling.image_to_video,
                image_url=image_cdn_url,
                prompt=req.image_prompt,
                duration=req.video_duration,
            )
        metrics.inc("api_calls_total", provider="kling")
        raw_video_path = run_dir / "raw_video.mp4"
        await self.kling.save_video(video_bytes, raw_video_path)

        # 4. Generate Uzbek voiceover
        final_video_path = raw_video_path
        if req.voiceover_text:
            await get_limiter("elevenlabs").acquire()
            with metrics.timer("api_latency_seconds", provider="elevenlabs"):
                audio_bytes = await get_breaker("elevenlabs").call(
                    self.elevenlabs.synthesize, req.voiceover_text
                )
            metrics.inc("api_calls_total", provider="elevenlabs")
            audio_path = run_dir / "voiceover.mp3"
            await self.elevenlabs.save_audio(audio_bytes, audio_path)
            result.local_paths.append(str(audio_path))

            # 5. Merge audio + video
            with metrics.timer("ffmpeg_merge_seconds"):
                merged_path = run_dir / "merged.mp4"
                merge_audio_video(raw_video_path, audio_path, merged_path)
            final_video_path = merged_path

        # 6. Add subtitle overlay (optional)
        if req.subtitle_text:
            subtitled_path = run_dir / "final.mp4"
            add_text_overlay(final_video_path, req.subtitle_text, subtitled_path)
            final_video_path = subtitled_path

        result.local_paths.append(str(final_video_path))

        # 7. Upload final video to CDN
        with metrics.timer("cdn_upload_seconds"):
            video_cdn_url = await upload_to_cdn(final_video_path)
        result.cdn_urls.append(video_cdn_url)

        # 8. Build caption with hashtags
        full_caption = self._build_caption(req.caption, req.hashtags)

        # 9. Publish Reel to Instagram
        await get_limiter("instagram").acquire()
        with metrics.timer("api_latency_seconds", provider="instagram"):
            media_id = await get_breaker("instagram").call(
                self.instagram.post_reel,
                video_url=video_cdn_url,
                caption=full_caption,
            )
        metrics.inc("api_calls_total", provider="instagram")
        result.media_id = media_id

    # ------------------------------------------------------------------
    # Story pipeline
    # ------------------------------------------------------------------

    async def _produce_story(
        self,
        req: ContentRequest,
        run_dir: Path,
        result: ContentResult,
    ) -> None:
        logger.info("pipeline.story.start")

        # Generate image for story
        with metrics.timer("api_latency_seconds", provider="nano_banana"):
            image_bytes = await self.nano_banana.generate_image(
                req.image_prompt,
                style=req.image_style,
                aspect_ratio="story",
            )
        metrics.inc("api_calls_total", provider="nano_banana")
        image_path = run_dir / "story_image.png"
        await self.nano_banana.save_image(image_bytes, image_path)

        with metrics.timer("cdn_upload_seconds"):
            image_cdn_url = await upload_to_cdn(image_path)
        result.cdn_urls.append(image_cdn_url)

        with metrics.timer("api_latency_seconds", provider="instagram"):
            media_id = await self.instagram.post_story(media_url=image_cdn_url)
        metrics.inc("api_calls_total", provider="instagram")
        result.media_id = media_id

    # ------------------------------------------------------------------
    # Carousel pipeline
    # ------------------------------------------------------------------

    async def _produce_carousel(
        self,
        req: ContentRequest,
        run_dir: Path,
        result: ContentResult,
    ) -> None:
        logger.info("pipeline.carousel.start", slides=len(req.carousel_prompts))

        prompts = req.carousel_prompts or [req.image_prompt]
        with metrics.timer("api_latency_seconds", provider="nano_banana"):
            images = await self.nano_banana.generate_carousel(
                prompts, style=req.image_style
            )
        metrics.inc("api_calls_total", provider="nano_banana")

        media_items = []
        for i, img_bytes in enumerate(images):
            path = run_dir / f"slide_{i}.png"
            await self.nano_banana.save_image(img_bytes, path)
            cdn_url = await upload_to_cdn(path)
            result.cdn_urls.append(cdn_url)
            media_items.append({"url": cdn_url, "type": "IMAGE"})

        full_caption = self._build_caption(req.caption, req.hashtags)

        with metrics.timer("api_latency_seconds", provider="instagram"):
            media_id = await self.instagram.post_carousel(media_items, full_caption)
        metrics.inc("api_calls_total", provider="instagram")
        result.media_id = media_id

    # ------------------------------------------------------------------
    # Single image pipeline
    # ------------------------------------------------------------------

    async def _produce_image(
        self,
        req: ContentRequest,
        run_dir: Path,
        result: ContentResult,
    ) -> None:
        logger.info("pipeline.image.start")

        with metrics.timer("api_latency_seconds", provider="nano_banana"):
            image_bytes = await self.nano_banana.generate_image(
                req.image_prompt,
                style=req.image_style,
                aspect_ratio="feed_portrait",
            )
        metrics.inc("api_calls_total", provider="nano_banana")
        image_path = run_dir / "post_image.png"
        await self.nano_banana.save_image(image_bytes, image_path)
        result.local_paths.append(str(image_path))

        with metrics.timer("cdn_upload_seconds"):
            cdn_url = await upload_to_cdn(image_path)
        result.cdn_urls.append(cdn_url)

        full_caption = self._build_caption(req.caption, req.hashtags)

        with metrics.timer("api_latency_seconds", provider="instagram"):
            media_id = await self.instagram.post_image(
                image_url=cdn_url, caption=full_caption
            )
        metrics.inc("api_calls_total", provider="instagram")
        result.media_id = media_id

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_caption(text: str, hashtags: list[str]) -> str:
        if hashtags:
            tag_str = " ".join(f"#{t.strip('#')}" for t in hashtags)
            return f"{text}\n\n{tag_str}"
        return text

    async def close(self) -> None:
        await self.nano_banana.close()
        await self.kling.close()
        await self.elevenlabs.close()
        await self.instagram.close()
