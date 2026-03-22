"""Shared fixtures for all tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.base import CreativeBrief
from pipeline.orchestrator import ContentRequest, ContentResult


# ------------------------------------------------------------------
# Event loop
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ------------------------------------------------------------------
# Fixtures: data objects
# ------------------------------------------------------------------

@pytest.fixture
def sample_brief() -> CreativeBrief:
    return CreativeBrief(
        topic="Muvaffaqiyat sirlari",
        category="motivational",
        content_type="reel",
        target_audience="Uzbek-speaking Instagram users, 18-35",
        brand_voice="inspiring, modern, culturally authentic",
        language="uz",
        duration="5",
        script="Har kuni kichik qadamlar bilan maqsadga erishing",
        voiceover_text="Har bir katta muvaffaqiyat kichik qadamlardan boshlanadi.",
        caption="Bugun qanday qadam tashlaysiz?",
        hashtags=["motivatsiya", "muvaffaqiyat", "uzbek"],
        hook_line="Ko'pchilik bilmaydigan sir...",
        cta="Fikringizni yozing!",
        image_prompt="Inspiring sunrise over Tashkent skyline, golden light",
        style_preset="photorealistic",
        color_palette=["#FF6B35", "#FFD700", "#1A1A2E"],
        lighting_setup="golden_hour",
        mood="inspirational",
        pacing="moderate",
        approved=True,
        quality_scores={
            "visual_quality": 8.5,
            "script_quality": 8.0,
            "cultural_sensitivity": 9.0,
            "brand_alignment": 7.5,
        },
    )


@pytest.fixture
def sample_request() -> ContentRequest:
    return ContentRequest(
        content_type="reel",
        image_prompt="A beautiful sunrise over Tashkent, photorealistic, 9:16",
        caption="Bugun yangi kun — yangi imkoniyatlar!",
        voiceover_text="Har bir tong yangi imkoniyat olib keladi.",
        image_style="photorealistic",
        video_duration="5",
        subtitle_text="Yangi imkoniyatlar",
        hashtags=["motivatsiya", "tashkent", "uzbekistan"],
    )


@pytest.fixture
def sample_result() -> ContentResult:
    return ContentResult(
        request_id="abc123",
        content_type="reel",
        media_id="17890012345678",
        cdn_urls=["https://cdn.example.com/instagram/video.mp4"],
        status="published",
        created_at="2026-03-22T09:00:00",
    )


@pytest.fixture
def tmp_output(tmp_path) -> Path:
    """Temporary output directory for tests."""
    output = tmp_path / "output"
    output.mkdir()
    return output


# ------------------------------------------------------------------
# Mock clients
# ------------------------------------------------------------------

@pytest.fixture
def mock_nano_banana():
    client = AsyncMock()
    client.generate_image.return_value = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    client.generate_carousel.return_value = [b"\x89PNG" + b"\x00" * 50] * 3
    client.save_image = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_kling():
    client = AsyncMock()
    client.image_to_video.return_value = b"\x00\x00\x00\x1c" + b"\x00" * 100
    client.text_to_video.return_value = b"\x00\x00\x00\x1c" + b"\x00" * 100
    client.save_video = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_elevenlabs():
    client = AsyncMock()
    client.synthesize.return_value = b"ID3" + b"\x00" * 100
    client.save_audio = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_instagram():
    client = AsyncMock()
    client.post_reel.return_value = "17890012345678"
    client.post_image.return_value = "17890012345679"
    client.post_carousel.return_value = "17890012345680"
    client.post_story.return_value = "17890012345681"
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_cdn():
    """Mock CDN upload returning predictable URLs."""
    with patch("utils.cdn.upload_to_cdn") as mock:
        call_count = {"n": 0}

        async def fake_upload(path):
            call_count["n"] += 1
            return f"https://cdn.example.com/instagram/file_{call_count['n']}.{path.suffix.lstrip('.')}"

        mock.side_effect = fake_upload
        yield mock


@pytest.fixture
def mock_media():
    """Mock ffmpeg media operations."""
    with patch("utils.media.merge_audio_video") as merge, \
         patch("utils.media.add_text_overlay") as overlay:
        # These are sync functions that create output files
        def fake_merge(video, audio, output):
            output.write_bytes(b"\x00" * 50)

        def fake_overlay(video, text, output):
            output.write_bytes(b"\x00" * 50)

        merge.side_effect = fake_merge
        overlay.side_effect = fake_overlay
        yield {"merge": merge, "overlay": overlay}
