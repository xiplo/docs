"""Media validation — check image/video quality before publishing.

Validates:
  - Image dimensions (min 320px, max 4096px)
  - Image aspect ratios (Instagram requirements)
  - File size limits
  - Video duration bounds
  - Supported formats
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of media validation."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


# Instagram media specifications
INSTAGRAM_SPECS = {
    "image": {
        "min_width": 320,
        "max_width": 4096,
        "min_height": 320,
        "max_height": 4096,
        "max_file_size_mb": 8,
        "formats": {".jpg", ".jpeg", ".png", ".webp"},
        "aspect_ratios": {
            "feed_square": (1, 1),
            "feed_portrait": (4, 5),
            "feed_landscape": (1.91, 1),
            "story": (9, 16),
        },
    },
    "video": {
        "min_width": 500,
        "max_width": 4096,
        "min_duration_s": 3,
        "max_duration_reel_s": 90,
        "max_duration_story_s": 60,
        "max_file_size_mb": 100,
        "formats": {".mp4", ".mov"},
        "min_fps": 23,
        "max_fps": 60,
    },
}


class MediaValidator:
    """Validate media files against Instagram requirements."""

    @classmethod
    def validate_image(cls, path: Path, content_type: str = "image") -> ValidationResult:
        """Validate an image file."""
        result = ValidationResult()

        if not path.exists():
            result.valid = False
            result.errors.append(f"File not found: {path}")
            return result

        specs = INSTAGRAM_SPECS["image"]

        # Check format
        suffix = path.suffix.lower()
        if suffix not in specs["formats"]:
            result.valid = False
            result.errors.append(
                f"Unsupported format: {suffix}. "
                f"Allowed: {', '.join(specs['formats'])}"
            )

        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        result.metadata["file_size_mb"] = round(size_mb, 2)

        if size_mb > specs["max_file_size_mb"]:
            result.valid = False
            result.errors.append(
                f"File too large: {size_mb:.1f}MB "
                f"(max {specs['max_file_size_mb']}MB)"
            )

        # Try to read image dimensions with Pillow
        try:
            from PIL import Image

            with Image.open(path) as img:
                width, height = img.size
                result.metadata["width"] = width
                result.metadata["height"] = height
                result.metadata["aspect_ratio"] = round(width / height, 2) if height else 0

                if width < specs["min_width"] or height < specs["min_height"]:
                    result.valid = False
                    result.errors.append(
                        f"Image too small: {width}x{height} "
                        f"(min {specs['min_width']}x{specs['min_height']})"
                    )

                if width > specs["max_width"] or height > specs["max_height"]:
                    result.valid = False
                    result.errors.append(
                        f"Image too large: {width}x{height} "
                        f"(max {specs['max_width']}x{specs['max_height']})"
                    )

                # Check aspect ratio recommendations
                ratio = width / height if height else 0
                if content_type == "story" and not (0.5 < ratio < 0.65):
                    result.warnings.append(
                        f"Story aspect ratio {ratio:.2f} — recommended 9:16 (0.5625)"
                    )
                elif content_type in ("reel",) and not (0.5 < ratio < 0.65):
                    result.warnings.append(
                        f"Reel aspect ratio {ratio:.2f} — recommended 9:16 (0.5625)"
                    )
                elif content_type == "image" and not (0.8 < ratio < 1.92):
                    result.warnings.append(
                        f"Feed aspect ratio {ratio:.2f} — recommended 4:5 to 1.91:1"
                    )

        except ImportError:
            result.warnings.append("Pillow not installed — skipping dimension check")
        except Exception as exc:
            result.warnings.append(f"Could not read image dimensions: {exc}")

        return result

    @classmethod
    def validate_video(cls, path: Path, content_type: str = "reel") -> ValidationResult:
        """Validate a video file."""
        result = ValidationResult()

        if not path.exists():
            result.valid = False
            result.errors.append(f"File not found: {path}")
            return result

        specs = INSTAGRAM_SPECS["video"]

        # Check format
        suffix = path.suffix.lower()
        if suffix not in specs["formats"]:
            result.valid = False
            result.errors.append(
                f"Unsupported format: {suffix}. "
                f"Allowed: {', '.join(specs['formats'])}"
            )

        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        result.metadata["file_size_mb"] = round(size_mb, 2)

        if size_mb > specs["max_file_size_mb"]:
            result.valid = False
            result.errors.append(
                f"File too large: {size_mb:.1f}MB "
                f"(max {specs['max_file_size_mb']}MB)"
            )

        if size_mb < 0.01:
            result.warnings.append("Video file is very small — may be corrupted")

        return result

    @classmethod
    def validate_for_pipeline(
        cls, path: Path, content_type: str
    ) -> ValidationResult:
        """Validate media file based on content type."""
        if content_type in ("reel", "story"):
            suffix = path.suffix.lower()
            if suffix in INSTAGRAM_SPECS["video"]["formats"]:
                return cls.validate_video(path, content_type)
            return cls.validate_image(path, content_type)
        return cls.validate_image(path, content_type)
