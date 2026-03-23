"""Tests for media validation."""

from pathlib import Path

import pytest

from utils.media_validator import MediaValidator, INSTAGRAM_SPECS


@pytest.fixture
def small_image(tmp_path):
    """Create a tiny PNG for testing."""
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), "red")
        path = tmp_path / "small.png"
        img.save(path)
        return path
    except ImportError:
        pytest.skip("Pillow not installed")


@pytest.fixture
def valid_image(tmp_path):
    """Create a valid-sized PNG."""
    try:
        from PIL import Image
        img = Image.new("RGB", (1080, 1350), "blue")  # 4:5 portrait
        path = tmp_path / "valid.png"
        img.save(path)
        return path
    except ImportError:
        pytest.skip("Pillow not installed")


@pytest.fixture
def valid_story_image(tmp_path):
    """Create a 9:16 story image."""
    try:
        from PIL import Image
        img = Image.new("RGB", (1080, 1920), "green")
        path = tmp_path / "story.png"
        img.save(path)
        return path
    except ImportError:
        pytest.skip("Pillow not installed")


class TestImageValidation:
    def test_nonexistent_file(self):
        result = MediaValidator.validate_image(Path("/nonexistent.png"))
        assert result.valid is False
        assert "not found" in result.errors[0].lower()

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "test.bmp"
        path.write_bytes(b"\x00" * 100)
        result = MediaValidator.validate_image(path)
        assert result.valid is False
        assert any("format" in e.lower() for e in result.errors)

    def test_small_image_fails(self, small_image):
        result = MediaValidator.validate_image(small_image)
        assert result.valid is False
        assert any("small" in e.lower() for e in result.errors)

    def test_valid_image_passes(self, valid_image):
        result = MediaValidator.validate_image(valid_image)
        assert result.valid is True
        assert result.metadata["width"] == 1080
        assert result.metadata["height"] == 1350

    def test_story_aspect_ratio_warning(self, valid_image):
        # 4:5 image used as story should get warning
        result = MediaValidator.validate_image(valid_image, content_type="story")
        assert any("aspect ratio" in w.lower() for w in result.warnings)

    def test_story_correct_ratio(self, valid_story_image):
        result = MediaValidator.validate_image(valid_story_image, content_type="story")
        assert result.valid is True
        assert len(result.warnings) == 0 or not any("aspect" in w.lower() for w in result.warnings)


class TestVideoValidation:
    def test_nonexistent_video(self):
        result = MediaValidator.validate_video(Path("/nonexistent.mp4"))
        assert result.valid is False

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "test.avi"
        path.write_bytes(b"\x00" * 100)
        result = MediaValidator.validate_video(path)
        assert result.valid is False

    def test_valid_format(self, tmp_path):
        path = tmp_path / "test.mp4"
        path.write_bytes(b"\x00" * 5000)
        result = MediaValidator.validate_video(path)
        assert result.valid is True
        assert result.metadata["file_size_mb"] >= 0

    def test_tiny_video_warning(self, tmp_path):
        path = tmp_path / "tiny.mp4"
        path.write_bytes(b"\x00" * 5)
        result = MediaValidator.validate_video(path)
        assert any("small" in w.lower() or "corrupted" in w.lower() for w in result.warnings)


class TestSpecs:
    def test_image_specs(self):
        assert INSTAGRAM_SPECS["image"]["min_width"] == 320
        assert ".png" in INSTAGRAM_SPECS["image"]["formats"]

    def test_video_specs(self):
        assert INSTAGRAM_SPECS["video"]["max_duration_reel_s"] == 90
        assert ".mp4" in INSTAGRAM_SPECS["video"]["formats"]
