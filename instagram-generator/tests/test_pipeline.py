"""Integration tests for the content pipeline (mocked APIs)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from pipeline.orchestrator import ContentPipeline, ContentRequest, ContentResult


@pytest.fixture
def pipeline_with_mocks(
    mock_nano_banana, mock_kling, mock_elevenlabs, mock_instagram, mock_cdn, mock_media
):
    """Create a pipeline with all external dependencies mocked."""
    pipeline = ContentPipeline()
    pipeline.nano_banana = mock_nano_banana
    pipeline.kling = mock_kling
    pipeline.elevenlabs = mock_elevenlabs
    pipeline.instagram = mock_instagram
    return pipeline


@pytest.mark.asyncio
class TestReelPipeline:
    async def test_full_reel_flow(self, pipeline_with_mocks, tmp_path, mock_cdn):
        """Test the complete reel generation flow."""
        with patch.object(pipeline_with_mocks, '_output_dir', tmp_path):
            # Patch circuit breaker to pass through
            with patch("pipeline.orchestrator.get_breaker") as mock_breaker, \
                 patch("pipeline.orchestrator.get_limiter") as mock_limiter:
                # Make breaker.call just call the function
                async def passthrough_call(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.return_value.call = passthrough_call
                mock_limiter.return_value.acquire = AsyncMock()

                request = ContentRequest(
                    content_type="reel",
                    image_prompt="Beautiful sunset over Tashkent",
                    caption="Ajoyib kun!",
                    voiceover_text="Bugun ajoyib kun.",
                    hashtags=["tashkent"],
                )

                result = await pipeline_with_mocks.run(request)

        assert result.content_type == "reel"
        assert result.request_id  # Non-empty

    async def test_reel_without_voiceover(self, pipeline_with_mocks, tmp_path, mock_cdn):
        """Test reel without voiceover (simpler flow)."""
        with patch.object(pipeline_with_mocks, '_output_dir', tmp_path):
            with patch("pipeline.orchestrator.get_breaker") as mock_breaker, \
                 patch("pipeline.orchestrator.get_limiter") as mock_limiter:
                async def passthrough_call(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.return_value.call = passthrough_call
                mock_limiter.return_value.acquire = AsyncMock()

                request = ContentRequest(
                    content_type="reel",
                    image_prompt="Mountain landscape",
                    caption="Toglar!",
                )

                result = await pipeline_with_mocks.run(request)

        assert result.content_type == "reel"


@pytest.mark.asyncio
class TestModerationIntegration:
    async def test_blocked_content_does_not_publish(self, pipeline_with_mocks, tmp_path):
        """Content with blocked words should be stopped before API calls."""
        with patch.object(pipeline_with_mocks, '_output_dir', tmp_path):
            request = ContentRequest(
                content_type="image",
                image_prompt="Normal image",
                caption="This is a scam and fraud scheme",
                hashtags=["follow4follow"],
            )

            result = await pipeline_with_mocks.run(request)

        assert result.status == "blocked"
        assert "moderation" in result.error.lower()
        # Ensure no API calls were made
        pipeline_with_mocks.nano_banana.generate_image.assert_not_called()
        pipeline_with_mocks.instagram.post_image.assert_not_called()


@pytest.mark.asyncio
class TestImagePipeline:
    async def test_single_image(self, pipeline_with_mocks, tmp_path, mock_cdn):
        with patch.object(pipeline_with_mocks, '_output_dir', tmp_path):
            with patch("pipeline.orchestrator.get_breaker") as mock_breaker, \
                 patch("pipeline.orchestrator.get_limiter") as mock_limiter:
                async def passthrough_call(func, *args, **kwargs):
                    return await func(*args, **kwargs)

                mock_breaker.return_value.call = passthrough_call
                mock_limiter.return_value.acquire = AsyncMock()

                request = ContentRequest(
                    content_type="image",
                    image_prompt="Uzbek breakfast spread",
                    caption="Nonushta!",
                )

                result = await pipeline_with_mocks.run(request)

        assert result.content_type == "image"


class TestBuildCaption:
    def test_with_hashtags(self):
        caption = ContentPipeline._build_caption("Hello!", ["uzbek", "tashkent"])
        assert "#uzbek" in caption
        assert "#tashkent" in caption

    def test_without_hashtags(self):
        caption = ContentPipeline._build_caption("Hello!", [])
        assert caption == "Hello!"

    def test_strips_hash_from_tags(self):
        caption = ContentPipeline._build_caption("Text", ["#already_hashed"])
        assert "##" not in caption
