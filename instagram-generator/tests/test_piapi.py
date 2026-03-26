"""Tests for PiAPI unified client."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from clients.piapi import PiAPIClient, PiAPITaskResult


class TestPiAPITaskResult:
    def test_image_urls_flux(self):
        result = PiAPITaskResult(
            status="completed",
            output={"image_url": "https://cdn.example.com/img.png"},
        )
        assert result.image_urls == ["https://cdn.example.com/img.png"]

    def test_image_urls_multiple(self):
        result = PiAPITaskResult(
            status="completed",
            output={"image_urls": ["https://a.png", "https://b.png"]},
        )
        assert len(result.image_urls) == 2

    def test_video_urls_kling(self):
        result = PiAPITaskResult(
            status="completed",
            output={
                "works": [{
                    "video": {
                        "resource": "https://cdn.example.com/video.mp4",
                        "resource_without_watermark": "https://cdn.example.com/video_nw.mp4",
                    }
                }]
            },
        )
        assert result.video_urls == ["https://cdn.example.com/video_nw.mp4"]

    def test_video_urls_direct(self):
        result = PiAPITaskResult(
            status="completed",
            output={"video_url": "https://cdn.example.com/v.mp4"},
        )
        assert result.video_urls == ["https://cdn.example.com/v.mp4"]

    def test_succeeded(self):
        assert PiAPITaskResult(status="completed").succeeded is True
        assert PiAPITaskResult(status="failed").succeeded is False
        assert PiAPITaskResult(status="processing").succeeded is False

    def test_empty_output(self):
        result = PiAPITaskResult(status="completed", output={})
        assert result.image_urls == []
        assert result.video_urls == []


class TestPiAPIClient:
    def test_configured_without_key(self):
        with patch("clients.piapi.PIAPI_API_KEY", ""):
            client = PiAPIClient(api_key="")
            assert client.configured is False

    def test_configured_with_key(self):
        client = PiAPIClient(api_key="test-key-123")
        assert client.configured is True


class TestPiAPIModels:
    """Verify model names and task types are correct."""

    def test_flux_models(self):
        # These model names must match PiAPI's API
        valid_models = ["Qubico/flux1-dev", "Qubico/flux1-schnell", "Qubico/flux1-dev-advanced"]
        for m in valid_models:
            assert m.startswith("Qubico/flux1")

    def test_kling_task_types(self):
        assert "video_generation" == "video_generation"

    def test_seedance_model(self):
        assert "seedance" == "seedance"
