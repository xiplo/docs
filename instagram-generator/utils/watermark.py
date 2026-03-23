"""Watermark system — apply brand watermarks to images and videos.

Supports:
  - Text watermarks (brand name, @handle)
  - Image overlay watermarks (logo PNG)
  - Position options (bottom-right, bottom-left, center, etc.)
  - Opacity control
  - Per-platform watermark rules
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class WatermarkConfig:
    """Watermark configuration."""

    enabled: bool = False
    text: str = ""
    logo_path: str = ""
    position: str = "bottom-right"  # bottom-right, bottom-left, top-right, top-left, center
    opacity: float = 0.5  # 0.0 to 1.0
    font_size: int = 24
    color: str = "white"
    margin: int = 20

    # Per-platform rules
    skip_platforms: list[str] | None = None  # Don't watermark for these platforms


# Position mapping for Pillow coordinates
POSITION_MAP = {
    "bottom-right": lambda w, h, wm_w, wm_h, m: (w - wm_w - m, h - wm_h - m),
    "bottom-left": lambda w, h, wm_w, wm_h, m: (m, h - wm_h - m),
    "top-right": lambda w, h, wm_w, wm_h, m: (w - wm_w - m, m),
    "top-left": lambda w, h, wm_w, wm_h, m: (m, m),
    "center": lambda w, h, wm_w, wm_h, m: ((w - wm_w) // 2, (h - wm_h) // 2),
}


class WatermarkEngine:
    """Apply watermarks to media files."""

    def __init__(self, config: WatermarkConfig | None = None) -> None:
        self.config = config or WatermarkConfig()

    def apply_to_image(self, image_path: Path, output_path: Path | None = None) -> Path:
        """Apply watermark to an image file. Returns output path."""
        if not self.config.enabled:
            return image_path

        out = output_path or image_path.with_name(f"{image_path.stem}_wm{image_path.suffix}")

        try:
            from PIL import Image, ImageDraw, ImageFont

            with Image.open(image_path) as img:
                # Create transparent overlay
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)

                if self.config.logo_path and Path(self.config.logo_path).exists():
                    self._apply_logo(overlay, img.size)
                elif self.config.text:
                    self._apply_text(draw, img.size)

                # Composite
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                result = Image.alpha_composite(img, overlay)
                result = result.convert("RGB")
                result.save(out, quality=95)

            logger.info("watermark.applied", path=str(out))
            return out

        except ImportError:
            logger.warning("watermark.pillow_missing")
            return image_path
        except Exception as exc:
            logger.warning("watermark.failed", error=str(exc))
            return image_path

    def apply_to_video(self, video_path: Path, output_path: Path | None = None) -> Path:
        """Apply watermark to video using ffmpeg."""
        if not self.config.enabled:
            return video_path

        out = output_path or video_path.with_name(f"{video_path.stem}_wm{video_path.suffix}")

        try:
            import subprocess

            if self.config.logo_path and Path(self.config.logo_path).exists():
                # Overlay logo on video
                pos = self._ffmpeg_position()
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-i", str(self.config.logo_path),
                    "-filter_complex",
                    f"[1:v]format=rgba,colorchannelmixer=aa={self.config.opacity}[wm];"
                    f"[0:v][wm]overlay={pos}",
                    "-codec:a", "copy",
                    str(out),
                ]
            elif self.config.text:
                # Text watermark on video
                pos = self._ffmpeg_text_position()
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-vf",
                    f"drawtext=text='{self.config.text}':"
                    f"fontsize={self.config.font_size}:"
                    f"fontcolor={self.config.color}@{self.config.opacity}:"
                    f"{pos}",
                    "-codec:a", "copy",
                    str(out),
                ]
            else:
                return video_path

            subprocess.run(cmd, capture_output=True, check=True)
            logger.info("watermark.video_applied", path=str(out))
            return out

        except FileNotFoundError:
            logger.warning("watermark.ffmpeg_missing")
            return video_path
        except Exception as exc:
            logger.warning("watermark.video_failed", error=str(exc))
            return video_path

    def should_watermark(self, platform: str) -> bool:
        """Check if watermark should be applied for a platform."""
        if not self.config.enabled:
            return False
        if self.config.skip_platforms and platform in self.config.skip_platforms:
            return False
        return True

    def _apply_text(self, draw, img_size: tuple) -> None:
        """Draw text watermark on image."""
        from PIL import ImageFont

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.config.font_size)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), self.config.text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        pos_fn = POSITION_MAP.get(self.config.position, POSITION_MAP["bottom-right"])
        x, y = pos_fn(img_size[0], img_size[1], text_w, text_h, self.config.margin)

        # Semi-transparent text
        alpha = int(self.config.opacity * 255)
        color = self.config.color
        if color == "white":
            fill = (255, 255, 255, alpha)
        elif color == "black":
            fill = (0, 0, 0, alpha)
        else:
            fill = (255, 255, 255, alpha)

        draw.text((x, y), self.config.text, font=font, fill=fill)

    def _apply_logo(self, overlay, img_size: tuple) -> None:
        """Paste logo watermark on overlay."""
        from PIL import Image

        logo = Image.open(self.config.logo_path).convert("RGBA")

        # Scale logo to ~15% of image width
        max_w = int(img_size[0] * 0.15)
        if logo.width > max_w:
            ratio = max_w / logo.width
            logo = logo.resize((max_w, int(logo.height * ratio)))

        # Apply opacity
        alpha = logo.split()[3]
        alpha = alpha.point(lambda p: int(p * self.config.opacity))
        logo.putalpha(alpha)

        pos_fn = POSITION_MAP.get(self.config.position, POSITION_MAP["bottom-right"])
        x, y = pos_fn(img_size[0], img_size[1], logo.width, logo.height, self.config.margin)

        overlay.paste(logo, (x, y), logo)

    def _ffmpeg_position(self) -> str:
        """Get ffmpeg overlay position string."""
        m = self.config.margin
        mapping = {
            "bottom-right": f"W-w-{m}:H-h-{m}",
            "bottom-left": f"{m}:H-h-{m}",
            "top-right": f"W-w-{m}:{m}",
            "top-left": f"{m}:{m}",
            "center": "(W-w)/2:(H-h)/2",
        }
        return mapping.get(self.config.position, f"W-w-{m}:H-h-{m}")

    def _ffmpeg_text_position(self) -> str:
        """Get ffmpeg drawtext position string."""
        m = self.config.margin
        mapping = {
            "bottom-right": f"x=w-tw-{m}:y=h-th-{m}",
            "bottom-left": f"x={m}:y=h-th-{m}",
            "top-right": f"x=w-tw-{m}:y={m}",
            "top-left": f"x={m}:y={m}",
            "center": "x=(w-tw)/2:y=(h-th)/2",
        }
        return mapping.get(self.config.position, f"x=w-tw-{m}:y=h-th-{m}")
